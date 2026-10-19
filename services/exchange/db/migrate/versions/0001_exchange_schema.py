"""context copies, provenance and deletions

Revision ID: 0001_exchange_schema
Revises:
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_exchange_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the exchange-owned tables."""
    op.create_table(
        "contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("retention_policy", sa.String(32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("storage_key", sa.String(300), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("text_bytes", sa.BigInteger(), nullable=False),
        sa.Column("deletion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("owner_id", "client_context_id", name="uq_context_client_id"),
    )
    op.create_index("ix_context_owner", "contexts", ["owner_id"])
    op.create_table(
        "context_sources",
        sa.Column(
            "context_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contexts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("local_record_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("local_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
    )
    op.create_table(
        "deletions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(24), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purge_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_deletion_owner", "deletions", ["owner_id"])


def downgrade() -> None:
    """Drop exchange tables."""
    op.drop_index("ix_deletion_owner", table_name="deletions")
    op.drop_table("deletions")
    op.drop_table("context_sources")
    op.drop_index("ix_context_owner", table_name="contexts")
    op.drop_table("contexts")
