import hashlib
import logging
import uuid
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.database.session import get_db
from app.models import CollectionPaper, PaperChunk, PaperPage, ResearchCollection, ResearchPaper, User
from app.schemas.papers import (
    PaperOut,
    PaperPageOut,
    SemanticSearchResult,
    SummaryJobOut,
    UploadBatchResponse,
    UploadItemResult,
)
from app.services.embeddings import encode_texts
from app.services.paper_jobs import process_paper, summarize_paper
from app.services.vector_store import has_index, rebuild_from_chunks, remove_vectors, search as vector_search

router = APIRouter(prefix="/papers", tags=["papers"])
logger = logging.getLogger(__name__)
CHUNK_BYTES = 1024 * 1024


def _user_upload_dir(user_id) -> tuple[Path, Path]:
    root = settings.upload_directory.resolve()
    user_dir = (root / str(user_id)).resolve()
    if not user_dir.is_relative_to(root):
        raise HTTPException(status_code=500, detail="Invalid upload storage configuration.")
    user_dir.mkdir(parents=True, exist_ok=True)
    return root, user_dir


def _safe_filename(filename: str | None) -> str:
    name = (filename or "research-paper.pdf").replace("\\", "/").split("/")[-1]
    name = "".join(char for char in name if char.isprintable()).strip()
    if not name or not name.lower().endswith(".pdf"):
        raise ValueError("Only files with a .pdf extension are accepted.")
    return name[:255]


async def _store_one(file: UploadFile, user: User, db: Session) -> UploadItemResult:
    display_name = file.filename or "research-paper.pdf"
    try:
        safe_name = _safe_filename(display_name)
    except ValueError as exc:
        await file.close()
        return UploadItemResult(filename=display_name, status="rejected", message=str(exc))

    try:
        root, user_dir = _user_upload_dir(user.id)
    except OSError:
        await file.close()
        logger.exception("Could not create PDF storage directory for user %s", user.id)
        return UploadItemResult(filename=safe_name, status="rejected", message="File storage is unavailable.")
    temp_path = user_dir / f".{uuid.uuid4().hex}.upload"
    digest = hashlib.sha256()
    size = 0
    header = bytearray()
    max_bytes = settings.max_pdf_size_mb * 1024 * 1024
    try:
        with temp_path.open("xb") as destination:
            while chunk := await file.read(CHUNK_BYTES):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(f"File exceeds the {settings.max_pdf_size_mb} MB upload limit.")
                if len(header) < 1024:
                    header.extend(chunk[: 1024 - len(header)])
                digest.update(chunk)
                destination.write(chunk)

        if size == 0 or b"%PDF-" not in header:
            raise ValueError("The file does not contain a valid PDF header.")

        file_hash = digest.hexdigest()
        duplicate = db.scalar(
            select(ResearchPaper).where(
                ResearchPaper.owner_id == user.id,
                ResearchPaper.sha256 == file_hash,
            )
        )
        if duplicate is not None:
            temp_path.unlink(missing_ok=True)
            return UploadItemResult(
                filename=safe_name,
                status="duplicate",
                paper=PaperOut.model_validate(duplicate),
                message="This PDF is already in your library.",
            )

        paper_id = uuid.uuid4()
        storage_key = f"{user.id}/{paper_id}.pdf"
        final_path = user_dir / f"{paper_id}.pdf"
        temp_path.replace(final_path)
        paper = ResearchPaper(
            id=paper_id,
            owner_id=user.id,
            original_filename=safe_name,
            storage_key=storage_key,
            mime_type="application/pdf",
            file_size_bytes=size,
            sha256=file_hash,
            processing_status="pending",
            processing_step="queued",
        )
        db.add(paper)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            final_path.unlink(missing_ok=True)
            duplicate = db.scalar(
                select(ResearchPaper).where(
                    ResearchPaper.owner_id == user.id,
                    ResearchPaper.sha256 == file_hash,
                )
            )
            if duplicate is not None:
                return UploadItemResult(
                    filename=safe_name,
                    status="duplicate",
                    paper=PaperOut.model_validate(duplicate),
                    message="This PDF is already in your library.",
                )
            return UploadItemResult(filename=safe_name, status="rejected", message="Could not save this PDF record.")
        except SQLAlchemyError:
            db.rollback()
            final_path.unlink(missing_ok=True)
            raise
        db.refresh(paper)
        return UploadItemResult(
            filename=safe_name,
            status="uploaded",
            paper=PaperOut.model_validate(paper),
            message="Uploaded. PDF extraction and indexing have been queued.",
        )
    except ValueError as exc:
        temp_path.unlink(missing_ok=True)
        return UploadItemResult(filename=safe_name, status="rejected", message=str(exc))
    except OSError:
        temp_path.unlink(missing_ok=True)
        logger.exception("PDF storage failed for user %s", user.id)
        return UploadItemResult(filename=safe_name, status="rejected", message="File storage failed. Try again.")
    finally:
        await file.close()


@router.get("", response_model=list[PaperOut])
def list_papers(
    offset: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="Use offset >= 0 and limit between 1 and 100.")
    return db.scalars(
        select(ResearchPaper)
        .where(ResearchPaper.owner_id == user.id)
        .order_by(ResearchPaper.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()


@router.post("/upload", response_model=UploadBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_papers(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=422, detail="Choose at least one PDF file.")
    if len(files) > 20:
        for file in files:
            await file.close()
        raise HTTPException(status_code=413, detail="Upload at most 20 PDFs in one batch.")

    results = [await _store_one(file, user, db) for file in files]
    for result in results:
        if result.status == "uploaded" and result.paper is not None:
            background_tasks.add_task(process_paper, str(result.paper.id))
    accepted = sum(result.status in {"uploaded", "duplicate"} for result in results)
    return UploadBatchResponse(results=results, accepted=accepted, rejected=len(results) - accepted)


@router.get("/search", response_model=list[SemanticSearchResult])
def semantic_search(
    q: str = Query(min_length=2, max_length=1000),
    top_k: int = Query(default=8, ge=1, le=30),
    paper_id: uuid.UUID | None = None,
    collection_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if paper_id and collection_id:
        raise HTTPException(status_code=422, detail="Choose either one paper or one collection as the search scope.")
    if paper_id is not None and db.scalar(
        select(ResearchPaper.id).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id)
    ) is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if collection_id is not None and db.scalar(
        select(ResearchCollection.id).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    ) is None:
        raise HTTPException(status_code=404, detail="Collection not found.")

    chunks = list(
        db.scalars(
            select(PaperChunk)
            .join(ResearchPaper, ResearchPaper.id == PaperChunk.paper_id)
            .where(ResearchPaper.owner_id == user.id, ResearchPaper.processing_status == "completed")
        ).all()
    )
    try:
        if chunks and (
            not has_index(user.id)
            or any(chunk.embedding_model != settings.embedding_model_name for chunk in chunks)
        ):
            rebuild_from_chunks(user.id, chunks)
            db.commit()
        query_vector = encode_texts([q])[0]
        try:
            candidates = vector_search(user.id, query_vector, limit=1000)
        except (ValueError, OSError):
            rebuild_from_chunks(user.id, chunks)
            db.commit()
            candidates = vector_search(user.id, query_vector, limit=1000)
    except Exception as exc:
        logger.exception("Semantic search failed for user %s", user.id)
        raise HTTPException(
            status_code=503,
            detail=f"Semantic search is unavailable. Check the embedding model configuration. ({type(exc).__name__})",
        ) from None
    if not candidates:
        return []

    candidate_order = {uuid.UUID(chunk_id): (position, score) for position, (chunk_id, score) in enumerate(candidates)}
    candidate_ids = list(candidate_order)
    statement = (
        select(PaperChunk, ResearchPaper)
        .join(ResearchPaper, ResearchPaper.id == PaperChunk.paper_id)
        .where(
            PaperChunk.id.in_(candidate_ids),
            ResearchPaper.owner_id == user.id,
            ResearchPaper.processing_status == "completed",
        )
    )
    if paper_id is not None:
        statement = statement.where(ResearchPaper.id == paper_id)
    if collection_id is not None:
        statement = statement.join(CollectionPaper, CollectionPaper.paper_id == ResearchPaper.id).where(
            CollectionPaper.collection_id == collection_id
        )
    matching = db.execute(statement).all()
    matching.sort(key=lambda pair: candidate_order[pair[0].id][0])
    return [
        SemanticSearchResult(
            chunk_id=chunk.id,
            paper_id=paper.id,
            paper_title=paper.title,
            page_start=chunk.start_page,
            page_end=chunk.end_page,
            text=chunk.text,
            similarity=candidate_order[chunk.id][1],
        )
        for chunk, paper in matching[:top_k]
    ]


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.scalar(select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.get("/{paper_id}/pages", response_model=list[PaperPageOut])
def get_paper_pages(
    paper_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.scalar(select(ResearchPaper.id).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return db.scalars(
        select(PaperPage)
        .where(PaperPage.paper_id == paper_id)
        .order_by(PaperPage.page_number)
        .offset(offset)
        .limit(limit)
    ).all()


@router.post("/{paper_id}/process", response_model=PaperOut, status_code=status.HTTP_202_ACCEPTED)
def retry_paper_processing(
    paper_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.scalar(select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.processing_status == "running" or (
        paper.processing_status == "pending" and paper.processing_step == "queued"
    ):
        raise HTTPException(status_code=409, detail="This paper is already being processed.")
    paper.processing_status = "pending"
    paper.processing_step = "queued"
    paper.processing_error = None
    db.commit()
    db.refresh(paper)
    background_tasks.add_task(process_paper, str(paper.id))
    return paper


@router.post("/{paper_id}/summary", response_model=SummaryJobOut, status_code=status.HTTP_202_ACCEPTED)
def request_summary(
    paper_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    detail: Literal["short", "detailed"] = "short",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = db.scalar(select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.processing_status != "completed":
        raise HTTPException(status_code=409, detail="Finish PDF processing before generating a summary.")
    if paper.summary_status in {"running", "pending"}:
        raise HTTPException(status_code=409, detail="A summary is already being generated.")
    paper.summary_status = "pending"
    paper.summary_error = None
    db.commit()
    background_tasks.add_task(summarize_paper, str(paper.id), detail)
    return SummaryJobOut(status="pending", message="Summary generation has been queued.")


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(paper_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.scalar(select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id))
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    chunk_ids = list(db.scalars(select(PaperChunk.id).where(PaperChunk.paper_id == paper.id)).all())
    root = settings.upload_directory.resolve()
    stored_file = (root / paper.storage_key).resolve()
    if not stored_file.is_relative_to(root):
        raise HTTPException(status_code=500, detail="Invalid paper storage path.")
    db.delete(paper)
    db.commit()
    try:
        remove_vectors(user.id, [str(chunk_id) for chunk_id in chunk_ids])
    except Exception:
        logger.exception("Could not update semantic index after deleting paper %s", paper_id)
    try:
        stored_file.unlink(missing_ok=True)
    except OSError:
        logger.exception("Could not remove stored PDF for paper %s", paper_id)
