"""PostgreSQL inbox that makes at-least-once delivery idempotent."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresInbox:
    """Check and record processed events per consumer group."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seen(self, consumer: str, event_id: uuid.UUID) -> bool:
        """Whether the consumer already handled this event."""
        found = await self._session.scalar(
            text("SELECT 1 FROM inbox_events WHERE consumer = :consumer AND event_id = :event"),
            {"consumer": consumer, "event": event_id},
        )
        return found is not None

    async def mark(self, consumer: str, event_id: uuid.UUID, topic: str) -> None:
        """Record the event; duplicates are ignored."""
        await self._session.execute(
            text("""
                INSERT INTO inbox_events (consumer, event_id, topic, processed_at)
                VALUES (:consumer, :event, :topic, :now)
                ON CONFLICT DO NOTHING
                """),
            {
                "consumer": consumer,
                "event": event_id,
                "topic": topic,
                "now": datetime.now(UTC),
            },
        )
        await self._session.commit()
