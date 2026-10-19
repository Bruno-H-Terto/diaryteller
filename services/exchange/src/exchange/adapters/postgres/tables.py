"""Exchange schema: context copies, provenance and deletion requests."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .engine import Base


class ContextTable(Base):
    """Manifest of an authorized copy; content lives encrypted in storage."""

    __tablename__ = "contexts"
    __table_args__ = (
        UniqueConstraint("owner_id", "client_context_id", name="uq_context_client_id"),
        Index("ix_context_owner", "owner_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    client_context_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(24))
    purpose: Mapped[str] = mapped_column(String(24))
    retention_policy: Mapped[str] = mapped_column(String(32))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    storage_key: Mapped[str] = mapped_column(String(300))
    content_sha256: Mapped[str] = mapped_column(String(64))
    record_count: Mapped[int] = mapped_column(Integer)
    text_bytes: Mapped[int] = mapped_column(BigInteger)
    deletion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class ContextSourceTable(Base):
    """Local provenance only; it never becomes a diary version remotely."""

    __tablename__ = "context_sources"

    context_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contexts.id", ondelete="CASCADE"), primary_key=True
    )
    local_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    local_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    content_sha256: Mapped[str] = mapped_column(String(64))


class DeletionTable(Base):
    """Durable purge request; content is gone before COMPLETED."""

    __tablename__ = "deletions"
    __table_args__ = (Index("ix_deletion_owner", "owner_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    resource_type: Mapped[str] = mapped_column(String(24))
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(24))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purge_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
