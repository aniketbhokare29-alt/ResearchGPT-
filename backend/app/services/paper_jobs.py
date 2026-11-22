import logging
import threading
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.session import SessionLocal
from app.models import PaperChunk, PaperPage, ResearchPaper
from app.services.chunking import chunk_pages
from app.services.embeddings import encode_texts
from app.services.pdf_processing import extract_pdf
from app.services.summarization import create_structured_summary
from app.services.vector_store import remove_vectors, replace_paper

logger = logging.getLogger(__name__)
_job_lock = threading.Lock()


def _set_processing_failure(db, paper_id: UUID, exc: Exception) -> None:
    db.rollback()
    paper = db.get(ResearchPaper, paper_id)
    if paper is not None:
        paper.processing_status = "failed"
        paper.processing_step = "failed"
        paper.processing_error = (str(exc).strip() or "Paper processing failed.")[:2000]
        db.commit()


def process_paper(paper_id: str) -> None:
    identifier = UUID(paper_id)
    with _job_lock:
        db = SessionLocal()
        try:
            paper = db.get(ResearchPaper, identifier)
            if paper is None:
                return
            paper.processing_status = "running"
            paper.processing_step = "extracting text"
            paper.processing_error = None
            db.commit()

            root = settings.upload_directory.resolve()
            pdf_path = (root / paper.storage_key).resolve()
            if not pdf_path.is_relative_to(root) or not pdf_path.is_file():
                raise ValueError("The stored PDF file is missing or its storage path is invalid.")
            extracted = extract_pdf(pdf_path)

            paper.processing_step = "chunking text"
            paper.page_count = len(extracted.pages)
            db.commit()
            chunks = chunk_pages(extracted.pages)
            if not chunks:
                raise ValueError("The PDF did not contain enough selectable text to create search chunks.")

            paper.processing_step = "creating embeddings"
            db.commit()
            vectors = encode_texts([chunk.text for chunk in chunks])
            if vectors.shape[0] != len(chunks) or vectors.shape[1] == 0:
                raise ValueError("The embedding model returned an invalid result.")

            previous_ids = list(
                db.scalars(select(PaperChunk.id).where(PaperChunk.paper_id == paper.id)).all()
            )
            new_chunk_rows = []
            for chunk, vector in zip(chunks, vectors):
                chunk_id = uuid4()
                new_chunk_rows.append(
                    PaperChunk(
                        id=chunk_id,
                        paper_id=paper.id,
                        chunk_index=chunk.chunk_index,
                        start_page=chunk.start_page,
                        end_page=chunk.end_page,
                        text=chunk.text,
                        token_count=chunk.token_count,
                        vector_id=str(chunk_id),
                        embedding=vector.tolist(),
                        embedding_model=settings.embedding_model_name,
                    )
                )

            db.execute(delete(PaperPage).where(PaperPage.paper_id == paper.id))
            db.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper.id))
            paper.title = extracted.title or paper.title
            paper.authors = extracted.authors
            paper.abstract = extracted.abstract
            paper.publication_year = extracted.publication_year
            paper.page_count = len(extracted.pages)
            paper.processing_step = "indexing vectors"
            db.add_all(
                PaperPage(paper_id=paper.id, page_number=number, text=page_text)
                for number, page_text in enumerate(extracted.pages, start=1)
            )
            db.add_all(new_chunk_rows)
            db.commit()

            replace_paper(
                paper.owner_id,
                [str(chunk_id) for chunk_id in previous_ids],
                [str(row.id) for row in new_chunk_rows],
                vectors,
            )
            paper.processing_status = "completed"
            paper.processing_step = "completed"
            paper.processing_error = None
            db.commit()
        except Exception as exc:
            logger.exception("PDF processing failed for paper %s", identifier)
            try:
                _set_processing_failure(db, identifier, exc)
            except SQLAlchemyError:
                logger.exception("Could not persist processing failure status for paper %s", identifier)
        finally:
            db.close()


def summarize_paper(paper_id: str, detail: str) -> None:
    identifier = UUID(paper_id)
    with _job_lock:
        db = SessionLocal()
        try:
            paper = db.get(ResearchPaper, identifier)
            if paper is None:
                return
            paper.summary_status = "running"
            paper.summary_error = None
            db.commit()
            pages = db.scalars(
                select(PaperPage).where(PaperPage.paper_id == paper.id).order_by(PaperPage.page_number)
            ).all()
            full_text = "\n\n".join(page.text for page in pages if page.text)
            if not full_text.strip():
                raise ValueError("Extract the PDF text before generating a summary.")
            paper.summary = create_structured_summary(paper, full_text, detail=detail)
            paper.summary_status = "completed"
            paper.summary_error = None
            db.commit()
        except Exception as exc:
            logger.exception("Summary generation failed for paper %s", identifier)
            db.rollback()
            paper = db.get(ResearchPaper, identifier)
            if paper is not None:
                paper.summary_status = "failed"
                paper.summary_error = (str(exc).strip() or "Summary generation failed.")[:2000]
                db.commit()
        finally:
            db.close()
