from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaperOut(BaseModel):
    id: UUID
    title: str | None
    authors: list[str] | None
    abstract: str | None
    publication_year: int | None
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    processing_status: str
    processing_step: str | None
    processing_error: str | None
    summary: dict | None
    summary_status: str
    summary_error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class CollectionOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadItemResult(BaseModel):
    filename: str
    status: str
    paper: PaperOut | None = None
    message: str | None = None


class UploadBatchResponse(BaseModel):
    results: list[UploadItemResult]
    accepted: int
    rejected: int


class PaperPageOut(BaseModel):
    page_number: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchResult(BaseModel):
    chunk_id: UUID
    paper_id: UUID
    paper_title: str | None
    page_start: int
    page_end: int
    text: str
    similarity: float


class SummaryRequest(BaseModel):
    detail: str = Field(default="short", pattern="^(short|detailed)$")


class SummaryJobOut(BaseModel):
    status: str
    message: str
