"""Create the initial ResearchGPT schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(160)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "research_collections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_collections_owner_id", "research_collections", ["owner_id"])

    op.create_table(
        "research_papers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("authors", sa.JSON()),
        sa.Column("abstract", sa.Text()),
        sa.Column("publication_year", sa.Integer()),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("page_count", sa.Integer()),
        sa.Column("processing_status", sa.String(24), nullable=False),
        sa.Column("processing_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "sha256", name="uq_paper_owner_sha256"),
    )
    op.create_index("ix_research_papers_owner_id", "research_papers", ["owner_id"])
    op.create_index("ix_research_papers_processing_status", "research_papers", ["processing_status"])
    op.create_index("ix_paper_owner_status", "research_papers", ["owner_id", "processing_status"])

    op.create_table(
        "collection_papers",
        sa.Column("collection_id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["research_collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paper_id"], ["research_papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("collection_id", "paper_id"),
    )

    op.create_table(
        "paper_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["research_papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paper_id", "page_number", name="uq_page_paper_number"),
    )
    op.create_index("ix_paper_pages_paper_id", "paper_pages", ["paper_id"])

    op.create_table(
        "paper_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer()),
        sa.Column("vector_id", sa.String(128)),
        sa.ForeignKeyConstraint(["paper_id"], ["research_papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_chunks_paper_id", "paper_chunks", ["paper_id"])
    op.create_index("ix_paper_chunks_vector_id", "paper_chunks", ["vector_id"])
    op.create_index("ix_chunk_paper_pages", "paper_chunks", ["paper_id", "start_page", "end_page"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("collection_id", sa.Uuid()),
        sa.Column("title", sa.String(240)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["research_collections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_owner_id", "conversations", ["owner_id"])

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("scope", sa.JSON()),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_reports_owner_id", "generated_reports", ["owner_id"])

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_name", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("input_data", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_owner_id", "agent_runs", ["owner_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    op.create_table(
        "agent_task_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("task_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("result_data", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_task_results_run_id", "agent_task_results", ["run_id"])
    op.create_index("ix_agent_task_run_status", "agent_task_results", ["run_id", "status"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_message_conversation_created", "messages", ["conversation_id", "created_at"])


def downgrade():
    op.drop_index("ix_message_conversation_created", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_agent_task_run_status", table_name="agent_task_results")
    op.drop_index("ix_agent_task_results_run_id", table_name="agent_task_results")
    op.drop_table("agent_task_results")
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_owner_id", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_generated_reports_owner_id", table_name="generated_reports")
    op.drop_table("generated_reports")
    op.drop_index("ix_conversations_owner_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_paper_chunks_vector_id", table_name="paper_chunks")
    op.drop_index("ix_chunk_paper_pages", table_name="paper_chunks")
    op.drop_index("ix_paper_chunks_paper_id", table_name="paper_chunks")
    op.drop_table("paper_chunks")
    op.drop_index("ix_paper_pages_paper_id", table_name="paper_pages")
    op.drop_table("paper_pages")
    op.drop_table("collection_papers")
    op.drop_index("ix_paper_owner_status", table_name="research_papers")
    op.drop_index("ix_research_papers_processing_status", table_name="research_papers")
    op.drop_index("ix_research_papers_owner_id", table_name="research_papers")
    op.drop_table("research_papers")
    op.drop_index("ix_research_collections_owner_id", table_name="research_collections")
    op.drop_table("research_collections")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
