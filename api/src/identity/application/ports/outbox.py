"""Transactional outbox relay port."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class OutboxRelayRepository(Protocol):
    """Claim unpublished rows and settle them."""

    async def claim(self, batch: int, lease_seconds: int, worker: str) -> list[dict[str, Any]]:
        """Claim a batch with a lease."""
        ...

    async def published(self, event_id: UUID, now: datetime | None = None) -> None:
        """Mark the event published."""
        ...

    async def retry(self, event_id: UUID, attempts: int, max_attempts: int, code: str) -> None:
        """Reschedule or fail the event."""
        ...
