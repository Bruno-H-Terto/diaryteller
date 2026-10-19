"""Identity service port for authoritative session validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from diary_contracts.authorization import AccountStatus


@dataclass(frozen=True, slots=True)
class Principal:
    """Validated caller identity and effective plan."""

    user_id: UUID
    session_id: UUID
    account_status: AccountStatus
    plan_code: str


class IdentityAuthorizer(Protocol):
    """Ask identity whether the caller may use exchange resources."""

    async def authorize(self, *, authorization: str, source: str, permission: str) -> Principal:
        """Return the principal or raise a domain error."""
        ...
