"""runtime grants for notifications and maintenance

Revision ID: 0004_runtime_grants
Revises: 0003_access_billing
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004_runtime_grants"
down_revision: Union[str, None] = "0003_access_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant least privilege for local roles; no-op where roles are absent."""
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'GRANT USAGE ON SCHEMA public TO diary_notifications';
            EXECUTE 'GRANT SELECT, UPDATE ON outbox_events TO diary_notifications';
            EXECUTE 'GRANT SELECT ON users, push_tokens TO diary_notifications';
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_maintenance') THEN
            EXECUTE 'GRANT USAGE, CREATE ON SCHEMA public TO diary_maintenance';
            EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO diary_maintenance';
            EXECUTE 'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO diary_maintenance';
            EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO diary_maintenance';
            EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO diary_maintenance';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Revoke only the grants introduced here."""
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_notifications') THEN
            EXECUTE 'REVOKE SELECT, UPDATE ON outbox_events FROM diary_notifications';
            EXECUTE 'REVOKE SELECT ON users, push_tokens FROM diary_notifications';
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'diary_maintenance') THEN
            EXECUTE 'REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM diary_maintenance';
            EXECUTE 'REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM diary_maintenance';
          END IF;
        END $$;
        """
    )
