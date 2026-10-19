"""Federated identity and OIDC transaction entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FederatedIdentity:
    """External `(issuer, subject)` bound to exactly one account."""

    id: UUID
    user_id: UUID
    issuer: str
    subject: str
    provider: str
    email_at_link: str | None
    created_at: datetime
    last_login_at: datetime


@dataclass(frozen=True, slots=True)
class OidcTransaction:
    """Server-side authorization-code transaction with hashed secrets."""

    id: UUID
    provider: str
    state_hash: str
    nonce_hash: str
    redirect_uri: str
    device_id: UUID
    code_challenge: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None
    user_id: UUID | None

    def is_open(self, now: datetime) -> bool:
        """A transaction is usable only once and before expiry."""
        return self.consumed_at is None and self.expires_at > now
