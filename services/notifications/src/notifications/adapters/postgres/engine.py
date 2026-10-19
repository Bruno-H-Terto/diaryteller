"""Async engine and declarative base for the notifications inbox."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for notifications tables."""


class InboxEventTable(Base):
    """One processed event per consumer group."""

    __tablename__ = "inbox_events"

    consumer: Mapped[str] = mapped_column(String(80), primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    topic: Mapped[str] = mapped_column(String(120))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def build_engine(url: str, *, pool_size: int, max_overflow: int) -> AsyncEngine:
    """Create the async engine."""
    return create_async_engine(
        url, pool_size=pool_size, max_overflow=max_overflow, pool_pre_ping=True
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory without expire-on-commit."""
    return async_sessionmaker(engine, expire_on_commit=False)
