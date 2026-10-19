"""Transactional outbox persistence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .tables_outbox import OutboxEventTable


class PostgresOutboxRepository:
    """Append-only outbox writer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        available_at: datetime,
        dedupe_key: str | None = None,
        topic: str | None = None,
    ) -> None:
        """Insert an event; dedupe keys make repeated appends harmless."""
        stmt = insert(OutboxEventTable).values(
            id=uuid.uuid4(),
            event_type=event_type,
            payload=payload,
            state="pending",
            attempts=0,
            available_at=available_at,
            created_at=available_at,
            dedupe_key=dedupe_key,
            topic=topic,
        )
        if dedupe_key is not None:
            stmt = stmt.on_conflict_do_nothing(constraint="uq_outbox_dedupe")
        await self._session.execute(stmt)
