"""Add document analysis and structured summary state.

Revision ID: 0003_document_analysis
Revises: 0002_revoked_tokens
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_document_analysis"
down_revision = "0002_revoked_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("research_papers", sa.Column("processing_step", sa.String(40), nullable=True))
    op.add_column("research_papers", sa.Column("summary", sa.JSON(), nullable=True))
    op.add_column(
        "research_papers",
        sa.Column("summary_status", sa.String(24), server_default="not_requested", nullable=False),
    )
    op.add_column("research_papers", sa.Column("summary_error", sa.Text(), nullable=True))
    op.add_column("paper_chunks", sa.Column("embedding", sa.JSON(), nullable=True))
    op.add_column("paper_chunks", sa.Column("embedding_model", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("paper_chunks", "embedding_model")
    op.drop_column("paper_chunks", "embedding")
    op.drop_column("research_papers", "summary_error")
    op.drop_column("research_papers", "summary_status")
    op.drop_column("research_papers", "summary")
    op.drop_column("research_papers", "processing_step")
