"""Account, profile and device entities.

They contain no framework imports and no secrets beyond an already-hashed
password. Device identifiers are random client labels, never proof of identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from diary_contracts.authorization import AccountStatus


@dataclass(frozen=True, slots=True)
class Profile:
    """Presentation and locale data owned by one account."""

    id: UUID
    display_name: str | None
    locale: str
    timezone: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated account identity."""

    id: UUID
    email: str
    password_hash: str | None
    status: AccountStatus
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        """Only active and not-yet-deleted accounts may authenticate."""
        return self.status is AccountStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class Device:
    """A client-provided random device label owned by one user."""

    id: UUID
    user_id: UUID
    label: str | None
    platform: str
    created_at: datetime
    last_seen_at: datetime
