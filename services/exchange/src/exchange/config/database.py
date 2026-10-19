"""Async engine and declarative base for exchange."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for exchange tables."""


def build_engine(url: str, *, pool_size: int, max_overflow: int, echo: bool) -> AsyncEngine:
    """Create the async engine with bounded pooling."""
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
        pool_pre_ping=True,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory that never expires loaded objects."""
    return async_sessionmaker(engine, expire_on_commit=False)
