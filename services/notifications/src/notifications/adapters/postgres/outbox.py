"""Outbox and read-only identity queries for the worker.

Events are claimed with `SKIP LOCKED` and a lease. Network calls happen only
after the claim transaction commits. Delivery is at-least-once.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CLAIM = text("""
    SELECT id, event_type, payload, attempts
    FROM outbox_events
    WHERE (state = 'pending' AND available_at <= :now)
       OR (state = 'delivering' AND lease_expires_at < :now)
    ORDER BY available_at
    LIMIT :batch
    FOR UPDATE SKIP LOCKED
    """)


class OutboxRepository:
    """Claim and acknowledge outbox events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(self, batch: int, lease_seconds: int, worker: str) -> list[dict[str, Any]]:
        """Claim a batch and commit before any network call."""
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
                        SET state = 'delivering', attempts = attempts + 1,
                            lease_owner = :worker,
                            lease_expires_at = :lease
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

    async def delivered(self, event_id: UUID) -> None:
        """Mark an event delivered."""
        await self._session.execute(
            text("""
                UPDATE outbox_events
                SET state = 'delivered', delivered_at = now(),
                    lease_owner = NULL, lease_expires_at = NULL
                WHERE id = :id
                """),
            {"id": event_id},
        )
        await self._session.commit()

    async def retry(self, event_id: UUID, attempts: int, max_attempts: int, code: str) -> None:
        """Return an event to the queue or mark it failed."""
        if attempts >= max_attempts:
            state, delay = "failed", 0
        else:
            state = "pending"
            delay = min(300, 2**attempts)
        await self._session.execute(
            text("""
                UPDATE outbox_events
                SET state = :state,
                    available_at = now() + make_interval(secs => :delay),
                    lease_owner = NULL, lease_expires_at = NULL,
                    last_error_code = :code
                WHERE id = :id
                """),
            {"id": event_id, "state": state, "delay": delay, "code": code[:64]},
        )
        await self._session.commit()

    async def clear_email_secret(self, digest: str) -> None:
        """Erase delivery material after a successful send."""
        await self._session.execute(
            text("UPDATE verification_tokens SET secret_ciphertext = '' WHERE digest = :digest"),
            {"digest": digest},
        )
        await self._session.commit()

    async def user_email(self, user_id: UUID) -> str | None:
        """Read-only lookup of the destination address."""
        row = await self._session.execute(
            text("SELECT email FROM users WHERE id = :id"), {"id": user_id}
        )
        value = row.scalar_one_or_none()
        return str(value) if value else None

    async def push_tokens(self, user_id: UUID) -> list[dict[str, Any]]:
        """Read-only push registrations for a user."""
        rows = await self._session.execute(
            text("""
                SELECT device_id, platform, token_ciphertext
                FROM push_tokens WHERE user_id = :id
                """),
            {"id": user_id},
        )
        return [dict(row._mapping) for row in rows]
