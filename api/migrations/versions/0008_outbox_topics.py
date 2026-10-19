"""route outbox events to kafka topics

Revision ID: 0008_outbox_topics
Revises: 0007_android_identity
Create Date: 2026-10-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_outbox_topics"
down_revision: Union[str, None] = "0007_android_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the target topic and publication timestamp."""
    op.add_column("outbox_events", sa.Column("topic", sa.String(120)))
    op.add_column("outbox_events", sa.Column("published_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_outbox_topic_pending", "outbox_events", ["topic", "state", "available_at"]
    )


def downgrade() -> None:
    """Remove the relay columns."""
    op.drop_index("ix_outbox_topic_pending", table_name="outbox_events")
    op.drop_column("outbox_events", "published_at")
    op.drop_column("outbox_events", "topic")
