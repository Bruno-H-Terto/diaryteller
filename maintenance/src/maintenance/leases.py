"""PostgreSQL advisory locks preventing duplicate scheduled jobs."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


@contextlib.asynccontextmanager
async def job_lock(engine: AsyncEngine, name: str) -> AsyncIterator[bool]:
    """Yield whether the named job lock was acquired; unlock on exit."""
    async with engine.connect() as connection:
        acquired = bool(
            await connection.scalar(
                text("SELECT pg_try_advisory_lock(hashtext(:name))"), {"name": name}
            )
        )
        try:
            yield acquired
        finally:
            if acquired:
                await connection.execute(
                    text("SELECT pg_advisory_unlock(hashtext(:name))"), {"name": name}
                )
                await connection.commit()
