"""allow notifications to read token digests

Revision ID: 0006_token_read
Revises: 0005_token_cleanup
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006_token_read"
down_revision: Union[str, None] = "0005_token_cleanup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant SELECT needed to locate a delivered token by digest."""
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'GRANT SELECT ON verification_tokens TO diary_notifications';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Revoke the read grant."""
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'REVOKE SELECT ON verification_tokens FROM diary_notifications';
          END IF;
        END $$;
        """
    )
