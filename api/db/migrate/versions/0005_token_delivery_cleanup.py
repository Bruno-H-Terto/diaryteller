"""allow notifications to clear delivered email secrets

Revision ID: 0005_token_cleanup
Revises: 0004_runtime_grants
Create Date: 2026-10-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_token_cleanup"
down_revision: str | None = "0004_runtime_grants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Grant only the column update needed to erase delivery material."""
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'GRANT UPDATE (secret_ciphertext) ON verification_tokens TO diary_notifications';
          END IF;
        END $$;
        """)


def downgrade() -> None:
    """Revoke the column grant."""
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'REVOKE UPDATE (secret_ciphertext) ON verification_tokens FROM diary_notifications';
          END IF;
        END $$;
        """)
