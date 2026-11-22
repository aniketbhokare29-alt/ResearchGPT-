import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.session import get_db
from app.models import CollectionPaper, ResearchCollection, ResearchPaper, User
from app.schemas.papers import CollectionCreate, CollectionOut, CollectionUpdate
from app.schemas.papers import PaperOut

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=list[CollectionOut])
def list_collections(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(ResearchCollection)
        .where(ResearchCollection.owner_id == user.id)
        .order_by(ResearchCollection.created_at.desc())
    ).all()


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = ResearchCollection(
        owner_id=user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    if not collection.name:
        raise HTTPException(status_code=422, detail="Collection name cannot be blank.")
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


@router.get("/{collection_id}/papers", response_model=list[PaperOut])
def list_collection_papers(
    collection_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.scalar(
        select(ResearchCollection).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    )
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found.")
    return db.scalars(
        select(ResearchPaper)
        .join(CollectionPaper, CollectionPaper.paper_id == ResearchPaper.id)
        .where(CollectionPaper.collection_id == collection_id, ResearchPaper.owner_id == user.id)
        .order_by(ResearchPaper.created_at.desc())
    ).all()


@router.patch("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: uuid.UUID,
    payload: CollectionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.scalar(
        select(ResearchCollection).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    )
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found.")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        values["name"] = (values["name"] or "").strip()
        if not values["name"]:
            raise HTTPException(status_code=422, detail="Collection name cannot be blank.")
    if "description" in values and values["description"] is not None:
        values["description"] = values["description"].strip() or None
    for field, value in values.items():
        setattr(collection, field, value)
    db.commit()
    db.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.scalar(
        select(ResearchCollection).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    )
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found.")
    db.delete(collection)
    db.commit()


@router.put("/{collection_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_paper_to_collection(
    collection_id: uuid.UUID,
    paper_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.scalar(
        select(ResearchCollection).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    )
    paper = db.scalar(
        select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id)
    )
    if collection is None or paper is None:
        raise HTTPException(status_code=404, detail="Collection or paper not found.")
    key = (collection_id, paper_id)
    if db.get(CollectionPaper, key) is None:
        db.add(CollectionPaper(collection_id=collection_id, paper_id=paper_id))
        db.commit()


@router.delete("/{collection_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_paper_from_collection(
    collection_id: uuid.UUID,
    paper_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    collection = db.scalar(
        select(ResearchCollection).where(
            ResearchCollection.id == collection_id,
            ResearchCollection.owner_id == user.id,
        )
    )
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found.")
    paper = db.scalar(
        select(ResearchPaper).where(ResearchPaper.id == paper_id, ResearchPaper.owner_id == user.id)
    )
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    link = db.get(CollectionPaper, (collection_id, paper_id))
    if link is not None:
        db.delete(link)
        db.commit()
