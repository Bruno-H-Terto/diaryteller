"""Persistence ports for federated identities and OIDC transactions."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from identity.domain.federation import FederatedIdentity, OidcTransaction


class FederationRepository(Protocol):
    """External identity links and one-time login transactions."""

    async def find(self, issuer: str, subject: str) -> FederatedIdentity | None:
        """Find the link for an issuer/subject pair."""
        ...

    async def link(
        self,
        user_id: UUID,
        *,
        issuer: str,
        subject: str,
        provider: str,
        email: str | None,
        now: datetime,
    ) -> FederatedIdentity:
        """Bind an external identity to one account."""
        ...

    async def touch(self, identity_id: UUID, now: datetime) -> None:
        """Record a successful federated login."""
        ...

    async def start_transaction(
        self,
        *,
        provider: str,
        state_hash: str,
        nonce_hash: str,
        redirect_uri: str,
        device_id: UUID,
        code_challenge: str,
        now: datetime,
        expires_at: datetime,
    ) -> UUID:
        """Persist a transaction with hashed state and nonce."""
        ...

    async def lock_transaction(self, transaction_id: UUID, now: datetime) -> OidcTransaction | None:
        """Lock an open transaction for one-time exchange."""
        ...

    async def consume_transaction(self, transaction_id: UUID, user_id: UUID, now: datetime) -> None:
        """Mark the transaction used by the resolved account."""
        ...

    async def purge_transactions(self, before: datetime) -> int:
        """Delete expired, unconsumed transactions."""
        ...
