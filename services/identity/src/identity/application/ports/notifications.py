"""Outbox and administrative notification persistence ports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class OutboxRepository(Protocol):
    """Transactional outbox appended in the same unit of work."""

    async def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        available_at: datetime,
        dedupe_key: str | None = None,
    ) -> None:
        """Store an event for at-least-once delivery."""
        ...


class NotificationRepository(Protocol):
    """In-app administrative notifications (never diary content)."""

    async def create(
        self,
        user_id: UUID,
        *,
        kind: str,
        title: str,
        body: str,
        now: datetime,
    ) -> UUID:
        """Create a notification owned by the user."""
        ...

    async def list_for_user(
        self, user_id: UUID, *, limit: int, before: datetime | None
    ) -> list[dict[str, Any]]:
        """Cursor-paginated notifications, newest first."""
        ...

    async def mark_read(self, user_id: UUID, notification_id: UUID, now: datetime) -> bool:
        """Mark one own notification as read; false when not found."""
        ...


class VerificationTokenRepository(Protocol):
    """Single-use token digests for email verification and password reset."""

    async def create(
        self,
        user_id: UUID,
        purpose: str,
        digest: str,
        secret_ciphertext: str,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        """Store a digest and an encrypted secret for delivery."""
        ...

    async def consume(self, purpose: str, digest: str, now: datetime) -> UUID | None:
        """Atomically mark a token used and return its user id."""
        ...

    async def invalidate_user(self, user_id: UUID, purpose: str, now: datetime) -> None:
        """Invalidate outstanding tokens for a purpose."""
        ...


class SecurityRepository(Protocol):
    """Append-only security audit port."""

    async def record(
        self,
        *,
        user_id: UUID | None,
        session_id: UUID | None,
        event_type: str,
        reference: str | None,
        now: datetime,
    ) -> None:
        """Store an administrative security event."""
        ...


class PushTokenRepository(Protocol):
    """Push registration storage."""

    async def upsert(
        self,
        user_id: UUID,
        device_id: UUID,
        token_ciphertext: str,
        platform: str,
        now: datetime,
    ) -> None:
        """Create or replace a registration."""
        ...

    async def delete(self, user_id: UUID, device_id: UUID) -> None:
        """Remove a registration."""
        ...
