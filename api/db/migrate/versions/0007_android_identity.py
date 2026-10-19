"""federated identities, oidc transactions and upload quotas

Revision ID: 0007_android_identity
Revises: 0006_token_read
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_android_identity"
down_revision: str | None = "0006_token_read"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add passwordless accounts, OIDC links and quota buckets."""
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.add_column(
        "plans",
        sa.Column(
            "upload_limits",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_table(
        "federated_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("email_at_link", sa.String(320), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("issuer", "subject", name="uq_federation_issuer_subject"),
    )
    op.create_index("ix_federation_user", "federated_identities", ["user_id"])
    op.create_table(
        "oidc_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("nonce_hash", sa.String(64), nullable=False),
        sa.Column("redirect_uri", sa.String(500), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_oidc_transactions_expiry", "oidc_transactions", ["expires_at"])
    op.create_table(
        "upload_quota_buckets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("period_kind", sa.String(16), nullable=False),
        sa.Column("bucket_date", sa.Date(), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("limit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.UniqueConstraint("owner_id", "metric", "period_start", name="uq_upload_quota_bucket"),
    )
    op.create_index("ix_upload_quota_owner", "upload_quota_buckets", ["owner_id"])
    op.create_table(
        "upload_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("bucket_date", sa.Date(), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("owner_id", "metric", "reference", name="uq_upload_reservation_ref"),
    )
    op.create_index("ix_upload_reservation_expiry", "upload_reservations", ["state", "expires_at"])
    op.create_table(
        "upload_quota_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(24), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "owner_id", "metric", "reason", "reference", name="uq_upload_adjustment_ref"
        ),
    )


def downgrade() -> None:
    """Drop quota and federation state."""
    op.drop_table("upload_quota_adjustments")
    op.drop_index("ix_upload_reservation_expiry", table_name="upload_reservations")
    op.drop_table("upload_reservations")
    op.drop_index("ix_upload_quota_owner", table_name="upload_quota_buckets")
    op.drop_table("upload_quota_buckets")
    op.drop_index("ix_oidc_transactions_expiry", table_name="oidc_transactions")
    op.drop_table("oidc_transactions")
    op.drop_index("ix_federation_user", table_name="federated_identities")
    op.drop_table("federated_identities")
    op.drop_column("plans", "upload_limits")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
