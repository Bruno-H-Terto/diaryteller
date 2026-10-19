"""notification inbox

Revision ID: 0001_notifications_inbox
Revises:
Create Date: 2026-10-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_notifications_inbox"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the idempotency inbox."""
    op.create_table(
        "inbox_events",
        sa.Column("consumer", sa.String(80), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the inbox."""
    op.drop_table("inbox_events")
