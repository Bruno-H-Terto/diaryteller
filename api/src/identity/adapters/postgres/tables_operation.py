"""Operation receipts with idempotency, lease and consumption metadata."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .engine import Base


class OperationReceiptTable(Base):
    """Metadata-only receipt for one billable operation."""

    __tablename__ = "operation_receipts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "operation_type", "idempotency_key", name="uq_operation_idempotency"
        ),
        Index("ix_operations_user_created", "user_id", "created_at"),
        Index("ix_operations_lease", "state", "lease_expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    operation_type: Mapped[str] = mapped_column(String(32))
    permission: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    payload_digest: Mapped[str] = mapped_column(String(64))
    metric: Mapped[str] = mapped_column(String(32))
    reserved_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    actual_amount: Mapped[int | None] = mapped_column(BigInteger)
    state: Mapped[str] = mapped_column(String(24), index=True)
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lease_owner: Mapped[str | None] = mapped_column(String(80))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_available: Mapped[bool] = mapped_column(default=False)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    actual_unknown: Mapped[bool] = mapped_column(default=False)
