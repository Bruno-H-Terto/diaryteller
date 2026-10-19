"""Claim outbox rows and mark them published to Kafka.

The outbox stays the source of truth so a broker outage never loses an event.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CLAIM = text("""
    SELECT id, event_type, payload, attempts, created_at, topic
    FROM outbox_events
    WHERE topic IS NOT NULL
      AND ((state = 'pending' AND available_at <= :now)
        OR (state = 'publishing' AND lease_expires_at < :now))
    ORDER BY available_at
    LIMIT :batch
    FOR UPDATE SKIP LOCKED
    """)


class PostgresOutboxRelayRepository:
    """Lease-based relay persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(self, batch: int, lease_seconds: int, worker: str) -> list[dict[str, Any]]:
        """Claim unpublished rows, committing the lease before publishing."""
        now = datetime.now(UTC)
        async with self._session.begin():
            rows = (
                (await self._session.execute(_CLAIM, {"now": now, "batch": batch})).mappings().all()
            )
            claimed: list[dict[str, Any]] = []
            for row in rows:
                await self._session.execute(
                    text("""
                        UPDATE outbox_events
                        SET state = 'publishing', attempts = attempts + 1,
                            lease_owner = :worker, lease_expires_at = :lease
                        WHERE id = :id
                        """),
                    {
                        "id": row["id"],
                        "worker": worker,
                        "lease": now + timedelta(seconds=lease_seconds),
                    },
                )
                claimed.append(dict(row))
        return claimed

    async def published(self, event_id: uuid.UUID, now: datetime | None = None) -> None:
        """Mark the event as published exactly once."""
        await self._session.execute(
            text("""
                UPDATE outbox_events
                SET state = 'published', published_at = :now,
                    lease_owner = NULL, lease_expires_at = NULL, last_error_code = NULL
                WHERE id = :id
                """),
            {"id": event_id, "now": now or datetime.now(UTC)},
        )
        await self._session.commit()

    async def retry(self, event_id: uuid.UUID, attempts: int, max_attempts: int, code: str) -> None:
        """Return to the queue or fail permanently after the attempt budget."""
        if attempts >= max_attempts:
            state, delay = "failed", 0
        else:
            state = "pending"
            delay = min(300, 2**attempts)
        available_at = datetime.now(UTC) + timedelta(seconds=delay)
        await self._session.execute(
            text("""
                UPDATE outbox_events
                SET state = :state, available_at = :available_at,
                    lease_owner = NULL, lease_expires_at = NULL, last_error_code = :code
                WHERE id = :id
                """),
            {
                "id": event_id,
                "state": state,
                "available_at": available_at,
                "code": code[:64],
            },
        )
        await self._session.commit()
