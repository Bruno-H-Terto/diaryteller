"""Async SQLAlchemy engine, declarative base and session factory.

A session is created per request or per job iteration. Sessions are never shared
between concurrent tasks and are not held open during provider streams.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for identity-owned tables."""


def build_engine(
    database_url: str,
    *,
    pool_size: int,
    max_overflow: int,
    echo: bool = False,
) -> AsyncEngine:
    """Create the shared async engine with explicit pool bounds."""
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=echo,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessions that do not autoflush unexpectedly."""
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
