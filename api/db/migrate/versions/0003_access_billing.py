"""access billing

Revision ID: 0003_access_billing
Revises: 0002_sessions_operations
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_access_billing"
down_revision: str | None = "0002_sessions_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=160), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "roles",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=160), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_code", sa.String(length=40), nullable=False),
        sa.Column("permission_code", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["permission_code"], ["permissions.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_code"], ["roles.code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_code", "permission_code"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_code", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["role_code"], ["roles.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_code"),
    )
    op.create_table(
        "plans",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("quotas", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index(op.f("ix_plans_is_default"), "plans", ["is_default"], unique=False)
    op.create_table(
        "plan_permissions",
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("permission_code", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["permission_code"], ["permissions.code"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_code"], ["plans.code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_code", "permission_code"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_transaction_id", sa.String(length=190), nullable=False),
        sa.Column("purchase_token_digest", sa.String(length=64), nullable=False),
        sa.Column("purchase_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_code"],
            ["plans.code"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_transaction_id", name="uq_sub_provider_tx"),
        sa.UniqueConstraint("purchase_token_digest", name="uq_sub_purchase_digest"),
    )
    op.create_index(op.f("ix_subscriptions_status"), "subscriptions", ["status"], unique=False)
    op.create_index(
        "ix_subscriptions_user", "subscriptions", ["user_id", "current_period_end"], unique=False
    )
    op.create_table(
        "usage_buckets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.BigInteger(), nullable=False),
        sa.Column("limit", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "metric", "period_start", name="uq_usage_bucket"),
    )
    op.create_table(
        "usage_reservations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operation_id", name="uq_usage_reservation_operation"),
    )
    op.create_index(
        op.f("ix_usage_reservations_expires_at"), "usage_reservations", ["expires_at"], unique=False
    )
    op.create_index(
        op.f("ix_usage_reservations_state"), "usage_reservations", ["state"], unique=False
    )
    op.create_table(
        "billing_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("event_id", sa.String(length=190), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("transaction_id", sa.String(length=190), nullable=False),
        sa.Column("purchase_token_digest", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=48), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "event_id", name="uq_billing_event"),
    )
    op.create_index(
        op.f("ix_billing_events_purchase_token_digest"),
        "billing_events",
        ["purchase_token_digest"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_events_purchase_token_digest"), table_name="billing_events")
    op.drop_table("billing_events")
    op.drop_index(op.f("ix_usage_reservations_state"), table_name="usage_reservations")
    op.drop_index(op.f("ix_usage_reservations_expires_at"), table_name="usage_reservations")
    op.drop_table("usage_reservations")
    op.drop_table("usage_buckets")
    op.drop_index("ix_subscriptions_user", table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_status"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_table("plan_permissions")
    op.drop_index(op.f("ix_plans_is_default"), table_name="plans")
    op.drop_table("plans")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
