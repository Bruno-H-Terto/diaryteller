"""Session and refresh-credential entities and rotation invariants.

A session is an active, revocable user context. It is never a subclass of user
and never stores a copy of permissions.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID


def utcnow() -> datetime:
    """Current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Session:
    """Persisted login context for one device."""

    id: UUID
    user_id: UUID
    device_id: UUID
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    source_version: int

    def is_active(self, now: datetime | None = None) -> bool:
        """A session is active until revoked or expired."""
        moment = now or utcnow()
        return self.revoked_at is None and self.expires_at > moment

    def revoked(self, reason: str, now: datetime | None = None) -> Session:
        """Return a revoked copy; callers persist it atomically."""
        return replace(self, revoked_at=now or utcnow(), revocation_reason=reason[:64])


@dataclass(frozen=True, slots=True)
class RefreshCredential:
    """Digest-only refresh credential with family reuse detection."""

    id: UUID
    session_id: UUID
    family_id: UUID
    digest: str
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None
    replacement_id: UUID | None

    def is_reusable(self, now: datetime | None = None) -> bool:
        """True only for an unconsumed, unexpired credential."""
        moment = now or utcnow()
        return self.consumed_at is None and self.expires_at > moment
