"""Shared login throttle persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_identity import LoginThrottleTable


class PostgresThrottleRepository:
    """PostgreSQL-backed login throttle shared by replicas."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def locked(self, key_hash: str, now: datetime) -> bool:
        """Check an active lock window."""
        row = await self._session.scalar(
            select(LoginThrottleTable).where(LoginThrottleTable.key_hash == key_hash)
        )
        return bool(row and row.locked_until and row.locked_until > now)

    async def record_failure(
        self, key_hash: str, now: datetime, window_seconds: int, max_attempts: int
    ) -> None:
        """Increment attempts, resetting the window after it expires."""
        row = await self._session.scalar(
            select(LoginThrottleTable)
            .where(LoginThrottleTable.key_hash == key_hash)
            .with_for_update()
        )
        if row is None:
            self._session.add(
                LoginThrottleTable(
                    id=uuid.uuid4(),
                    key_hash=key_hash,
                    attempts=1,
                    window_started_at=now,
                )
            )
            await self._session.flush()
            return
        elapsed = (now - row.window_started_at).total_seconds()
        row.attempts = 1 if elapsed > window_seconds else row.attempts + 1
        if row.attempts == 1:
            row.window_started_at = now
        if row.attempts >= max_attempts and row.locked_until is None:
            row.locked_until = now + timedelta(seconds=window_seconds)
        await self._session.flush()

    async def clear(self, key_hash: str) -> None:
        """Delete throttle state after success."""
        await self._session.execute(
            delete(LoginThrottleTable).where(LoginThrottleTable.key_hash == key_hash)
        )
