"""Upload quota buckets, reservations and idempotent capacity adjustments.

Rows hold counters and IDs only; no content or filename is stored here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..config.database import Base


class UploadQuotaBucketTable(Base):
    """Used/reserved/limit for one owner, metric and period."""

    __tablename__ = "upload_quota_buckets"
    __table_args__ = (
        UniqueConstraint("owner_id", "metric", "period_start", name="uq_upload_quota_bucket"),
        Index("ix_upload_quota_owner", "owner_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    metric: Mapped[str] = mapped_column(String(32))
    period_kind: Mapped[str] = mapped_column(String(16))
    bucket_date: Mapped[date | None] = mapped_column(Date)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[int] = mapped_column(BigInteger, default=0)
    reserved: Mapped[int] = mapped_column(BigInteger, default=0)
    limit: Mapped[int] = mapped_column(BigInteger, default=0)


class UploadReservationTable(Base):
    """Reservation settled exactly once; reference deduplicates retries."""

    __tablename__ = "upload_reservations"
    __table_args__ = (
        UniqueConstraint("owner_id", "metric", "reference", name="uq_upload_reservation_ref"),
        Index("ix_upload_reservation_expiry", "state", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    metric: Mapped[str] = mapped_column(String(32))
    bucket_date: Mapped[date | None] = mapped_column(Date)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[int] = mapped_column(BigInteger)
    state: Mapped[str] = mapped_column(String(16))
    reference: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UploadQuotaAdjustmentTable(Base):
    """Idempotent gauge change (concurrency or retained storage release)."""

    __tablename__ = "upload_quota_adjustments"
    __table_args__ = (
        UniqueConstraint(
            "owner_id", "metric", "reason", "reference", name="uq_upload_adjustment_ref"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    metric: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(24))
    reference: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
