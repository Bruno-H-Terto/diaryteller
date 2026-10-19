"""Persistence ports for accounts, profiles and devices."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from identity.domain.profile import Device, Profile, User


class AccountRepository(Protocol):
    """Account and profile persistence."""

    async def by_email(self, email: str) -> User | None:
        """Find a user by normalized email."""
        ...

    async def by_id(self, user_id: UUID) -> User | None:
        """Find a user by id."""
        ...

    async def profile(self, user_id: UUID) -> Profile | None:
        """Load the presentation profile."""
        ...

    async def create(
        self, email: str, password_hash: str, locale: str, timezone: str, now: datetime
    ) -> User:
        """Insert profile and user atomically."""
        ...

    async def create_federated(self, email: str, locale: str, timezone: str, now: datetime) -> User:
        """Insert a passwordless, email-verified account atomically."""
        ...

    async def update_profile(
        self,
        user_id: UUID,
        *,
        display_name: str | None,
        locale: str | None,
        timezone: str | None,
        now: datetime,
    ) -> Profile:
        """Update only explicitly editable fields."""
        ...

    async def mark_email_verified(self, user_id: UUID, now: datetime) -> None:
        """Set `email_verified_at` once."""
        ...

    async def update_password(self, user_id: UUID, password_hash: str, now: datetime) -> None:
        """Replace the password hash and bump the source version."""
        ...

    async def schedule_deletion(self, user_id: UUID, now: datetime, due_at: datetime) -> None:
        """Mark the account pending deletion after revoking sessions."""
        ...


class DeviceConflict(Exception):
    """The random device id already belongs to another account."""


class DeviceRepository(Protocol):
    """Device persistence keyed per user."""

    async def upsert(
        self, user_id: UUID, device_id: UUID, label: str | None, platform: str, now: datetime
    ) -> Device:
        """Create or update a user-owned device."""
        ...

    async def touch(self, user_id: UUID, device_id: UUID, now: datetime) -> None:
        """Update last seen without failing an active request."""
        ...

    async def get(self, user_id: UUID, device_id: UUID) -> Device | None:
        """Load a device only when it belongs to the user."""
        ...


class ThrottleRepository(Protocol):
    """Shared authentication attempt throttle."""

    async def locked(self, key_hash: str, now: datetime) -> bool:
        """Whether the identity is currently locked."""
        ...

    async def record_failure(
        self, key_hash: str, now: datetime, window_seconds: int, max_attempts: int
    ) -> None:
        """Record a failed attempt and lock the window when exceeded."""
        ...

    async def clear(self, key_hash: str) -> None:
        """Clear attempts after a successful authentication."""
        ...
