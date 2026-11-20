from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    papers: Mapped[list["ResearchPaper"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    collections: Mapped[list["ResearchCollection"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    reports: Mapped[list["GeneratedReport"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ResearchPaper(TimestampMixin, Base):
    __tablename__ = "research_papers"
    __table_args__ = (
        UniqueConstraint("owner_id", "sha256", name="uq_paper_owner_sha256"),
        Index("ix_paper_owner_status", "owner_id", "processing_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    authors: Mapped[list | None] = mapped_column(JSON)
    abstract: Mapped[str | None] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    page_count: Mapped[int | None] = mapped_column(Integer)
    processing_status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    processing_error: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship(back_populates="papers")
    pages: Mapped[list["PaperPage"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    chunks: Mapped[list["PaperChunk"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    collection_links: Mapped[list["CollectionPaper"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class ResearchCollection(TimestampMixin, Base):
    __tablename__ = "research_collections"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship(back_populates="collections")
    paper_links: Mapped[list["CollectionPaper"]] = relationship(back_populates="collection", cascade="all, delete-orphan")


class CollectionPaper(Base):
    __tablename__ = "collection_papers"

    collection_id: Mapped[UUID] = mapped_column(ForeignKey("research_collections.id", ondelete="CASCADE"), primary_key=True)
    paper_id: Mapped[UUID] = mapped_column(ForeignKey("research_papers.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    collection: Mapped[ResearchCollection] = relationship(back_populates="paper_links")
    paper: Mapped[ResearchPaper] = relationship(back_populates="collection_links")


class PaperPage(Base):
    __tablename__ = "paper_pages"
    __table_args__ = (UniqueConstraint("paper_id", "page_number", name="uq_page_paper_number"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    paper_id: Mapped[UUID] = mapped_column(ForeignKey("research_papers.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")

    paper: Mapped[ResearchPaper] = relationship(back_populates="pages")


class PaperChunk(Base):
    __tablename__ = "paper_chunks"
    __table_args__ = (Index("ix_chunk_paper_pages", "paper_id", "start_page", "end_page"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    paper_id: Mapped[UUID] = mapped_column(ForeignKey("research_papers.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    vector_id: Mapped[str | None] = mapped_column(String(128), index=True)

    paper: Mapped[ResearchPaper] = relationship(back_populates="chunks")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    collection_id: Mapped[UUID | None] = mapped_column(ForeignKey("research_collections.id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(240))

    owner: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_message_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(24))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class GeneratedReport(TimestampMixin, Base):
    __tablename__ = "generated_reports"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    report_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, default="")
    scope: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="draft")

    owner: Mapped[User] = relationship(back_populates="reports")


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workflow_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    input_data: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    owner: Mapped[User] = relationship(back_populates="agent_runs")
    tasks: Mapped[list["AgentTaskResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AgentTaskResult(Base):
    __tablename__ = "agent_task_results"
    __table_args__ = (Index("ix_agent_task_run_status", "run_id", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    task_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    summary: Mapped[str | None] = mapped_column(Text)
    result_data: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    run: Mapped[AgentRun] = relationship(back_populates="tasks")
