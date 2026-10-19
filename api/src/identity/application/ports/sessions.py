"""Persistence ports for sessions and rotating refresh credentials."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from identity.domain.session import RefreshCredential, Session


class SessionRepository(Protocol):
    """Session reads and revocation."""

    async def by_id(self, session_id: UUID) -> Session | None:
        """Load a session by primary key."""
        ...

    async def create(self, value: Session) -> None:
        """Insert a session."""
        ...

    async def list_for_user(self, user_id: UUID) -> list[Session]:
        """List sessions owned by one user, newest first."""
        ...

    async def revoke(
        self,
        session_id: UUID,
        reason: str,
        now: datetime,
        *,
        bump_source_version: bool = True,
    ) -> None:
        """Revoke one session; idempotent."""
        ...

    async def revoke_others(
        self, user_id: UUID, keep_session_id: UUID, reason: str, now: datetime
    ) -> int:
        """Revoke all other active sessions of the user."""
        ...

    async def revoke_all(self, user_id: UUID, reason: str, now: datetime) -> int:
        """Revoke every active session of the user."""
        ...

    async def revoke_for_device(
        self, user_id: UUID, device_id: UUID, reason: str, now: datetime
    ) -> int:
        """Revoke active sessions for one device."""
        ...

    async def touch(self, session_id: UUID, now: datetime) -> None:
        """Update last seen with throttling applied by the caller."""
        ...

    async def active_count(self, user_id: UUID) -> int:
        """Count non-revoked, non-expired sessions for a user."""
        ...

    async def bump_source_version(self, session_id: UUID) -> int:
        """Increment and return the session source version."""
        ...


class RefreshRepository(Protocol):
    """Refresh credentials are read and consumed with a row lock."""

    async def create(self, value: RefreshCredential) -> None:
        """Insert a new credential digest."""
        ...

    async def lock_by_digest(self, digest: str) -> RefreshCredential | None:
        """Select the credential for update inside the current transaction."""
        ...

    async def consume(self, credential_id: UUID, replacement_id: UUID, now: datetime) -> None:
        """Mark consumed and record its replacement."""
        ...

    async def revoke_family(self, family_id: UUID, now: datetime) -> None:
        """Invalidate every outstanding credential in a family."""
        ...
