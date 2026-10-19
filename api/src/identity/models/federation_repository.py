"""PostgreSQL federation and OIDC transaction persistence."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.federation import FederatedIdentity, OidcTransaction

from .tables_federation import FederatedIdentityTable, OidcTransactionTable


def _identity(row: FederatedIdentityTable) -> FederatedIdentity:
    return FederatedIdentity(
        id=row.id,
        user_id=row.user_id,
        issuer=row.issuer,
        subject=row.subject,
        provider=row.provider,
        email_at_link=row.email_at_link,
        created_at=row.created_at,
        last_login_at=row.last_login_at,
    )


class PostgresFederationRepository:
    """Identity links and one-time transactions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, issuer: str, subject: str) -> FederatedIdentity | None:
        """Find by exact issuer and subject; email is never used here."""
        row = await self._session.scalar(
            select(FederatedIdentityTable).where(
                FederatedIdentityTable.issuer == issuer,
                FederatedIdentityTable.subject == subject,
            )
        )
        return _identity(row) if row else None

    async def link(
        self,
        user_id: uuid.UUID,
        issuer: str,
        subject: str,
        provider: str,
        email: str | None,
        now: datetime,
    ) -> FederatedIdentity:
        """Link an external identity; conflicts mean it already belongs elsewhere."""
        identity_id = uuid.uuid4()
        inserted = await self._session.scalar(
            insert(FederatedIdentityTable)
            .values(
                id=identity_id,
                user_id=user_id,
                issuer=issuer,
                subject=subject,
                provider=provider,
                email_at_link=(email or "")[:320] or None,
                created_at=now,
                last_login_at=now,
            )
            .on_conflict_do_nothing(constraint="uq_federation_issuer_subject")
            .returning(FederatedIdentityTable.id)
        )
        if inserted is None:
            existing = await self.find(issuer, subject)
            if existing is None or existing.user_id != user_id:
                raise ValueError("federated identity is already linked")
            return existing
        row = await self._session.get(FederatedIdentityTable, identity_id)
        if row is None:
            raise RuntimeError("federated identity insert failed")
        return _identity(row)

    async def touch(self, identity_id: uuid.UUID, now: datetime) -> None:
        """Update last login without extending anything else."""
        await self._session.execute(
            update(FederatedIdentityTable)
            .where(FederatedIdentityTable.id == identity_id)
            .values(last_login_at=now)
        )

    async def start_transaction(
        self,
        *,
        provider: str,
        state_hash: str,
        nonce_hash: str,
        redirect_uri: str,
        device_id: uuid.UUID,
        code_challenge: str,
        now: datetime,
        expires_at: datetime,
    ) -> uuid.UUID:
        """Persist hashes only; no code, token or verifier is stored."""
        transaction_id = uuid.uuid4()
        self._session.add(
            OidcTransactionTable(
                id=transaction_id,
                provider=provider,
                state_hash=state_hash,
                nonce_hash=nonce_hash,
                redirect_uri=redirect_uri,
                device_id=device_id,
                code_challenge=code_challenge,
                created_at=now,
                expires_at=expires_at,
            )
        )
        await self._session.flush()
        return transaction_id

    async def lock_transaction(
        self, transaction_id: uuid.UUID, now: datetime
    ) -> OidcTransaction | None:
        """Lock an open transaction for one-time consumption."""
        row = await self._session.scalar(
            select(OidcTransactionTable)
            .where(
                OidcTransactionTable.id == transaction_id,
                OidcTransactionTable.consumed_at.is_(None),
                OidcTransactionTable.expires_at > now,
            )
            .with_for_update()
        )
        if row is None:
            return None
        return OidcTransaction(
            id=row.id,
            provider=row.provider,
            state_hash=row.state_hash,
            nonce_hash=row.nonce_hash,
            redirect_uri=row.redirect_uri,
            device_id=row.device_id,
            code_challenge=row.code_challenge,
            created_at=row.created_at,
            expires_at=row.expires_at,
            consumed_at=row.consumed_at,
            user_id=row.user_id,
        )

    async def consume_transaction(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID, now: datetime
    ) -> None:
        """Mark a transaction consumed exactly once."""
        await self._session.execute(
            update(OidcTransactionTable)
            .where(
                OidcTransactionTable.id == transaction_id,
                OidcTransactionTable.consumed_at.is_(None),
            )
            .values(consumed_at=now, user_id=user_id)
        )

    async def delete_for_user(self, user_id: uuid.UUID) -> None:
        """Remove links and transactions during account deletion."""
        await self._session.execute(
            delete(FederatedIdentityTable).where(FederatedIdentityTable.user_id == user_id)
        )
        await self._session.execute(
            delete(OidcTransactionTable).where(OidcTransactionTable.user_id == user_id)
        )

    async def purge_transactions(self, before: datetime) -> int:
        """Delete expired, unconsumed transactions."""
        result = await self._session.execute(
            delete(OidcTransactionTable).where(
                OidcTransactionTable.expires_at < before,
                OidcTransactionTable.consumed_at.is_(None),
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)
