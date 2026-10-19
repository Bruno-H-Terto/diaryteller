"""Roles, permissions, plans, subscriptions and usage buckets."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..config.database import Base


class PermissionTable(Base):
    """Permission catalog."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(String(160))


class RoleTable(Base):
    """Role catalog."""

    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    description: Mapped[str] = mapped_column(String(160))


class RolePermissionTable(Base):
    """Role-to-permission grants."""

    __tablename__ = "role_permissions"

    role_code: Mapped[str] = mapped_column(
        String(40), ForeignKey("roles.code", ondelete="CASCADE"), primary_key=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("permissions.code", ondelete="CASCADE"), primary_key=True
    )


class UserRoleTable(Base):
    """Role grant per user; active state is evaluated at authorization time."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_code: Mapped[str] = mapped_column(
        String(40), ForeignKey("roles.code", ondelete="CASCADE"), primary_key=True
    )


class PlanTable(Base):
    """Commercial plan with quota limits per metric."""

    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    quotas: Mapped[dict[str, Any]] = mapped_column(JSONB)
    upload_limits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False, index=True)


class PlanPermissionTable(Base):
    """Permission grant per plan."""

    __tablename__ = "plan_permissions"

    plan_code: Mapped[str] = mapped_column(
        String(40), ForeignKey("plans.code", ondelete="CASCADE"), primary_key=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("permissions.code", ondelete="CASCADE"), primary_key=True
    )


class SubscriptionTable(Base):
    """Provider subscription bound to one account and transaction."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("provider", "external_transaction_id", name="uq_sub_provider_tx"),
        UniqueConstraint("purchase_token_digest", name="uq_sub_purchase_digest"),
        Index("ix_subscriptions_user", "user_id", "current_period_end"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    plan_code: Mapped[str] = mapped_column(String(40), ForeignKey("plans.code"))
    provider: Mapped[str] = mapped_column(String(32))
    external_transaction_id: Mapped[str] = mapped_column(String(190))
    purchase_token_digest: Mapped[str] = mapped_column(String(64))
    purchase_token_ciphertext: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), index=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UsageBucketTable(Base):
    """Consumption per user, metric and period."""

    __tablename__ = "usage_buckets"
    __table_args__ = (
        UniqueConstraint("user_id", "metric", "period_start", name="uq_usage_bucket"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    metric: Mapped[str] = mapped_column(String(32))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[int] = mapped_column(BigInteger, default=0)
    limit: Mapped[int] = mapped_column(BigInteger, default=0)


class UsageReservationTable(Base):
    """Reservation linked to an operation and bucket."""

    __tablename__ = "usage_reservations"
    __table_args__ = (UniqueConstraint("operation_id", name="uq_usage_reservation_operation"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    metric: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(24), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
