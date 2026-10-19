"""PostgreSQL refresh credential rotation storage."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.session import RefreshCredential

from .tables_session import RefreshCredentialTable


def _credential(row: RefreshCredentialTable) -> RefreshCredential:
    return RefreshCredential(
        id=row.id,
        session_id=row.session_id,
        family_id=row.family_id,
        digest=row.digest,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        consumed_at=row.consumed_at,
        replacement_id=row.replacement_id,
    )


class PostgresRefreshRepository:
    """Refresh rotation storage."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, value: RefreshCredential) -> None:
        """Insert a credential digest."""
        self._session.add(
            RefreshCredentialTable(
                id=value.id,
                session_id=value.session_id,
                family_id=value.family_id,
                digest=value.digest,
                issued_at=value.issued_at,
                expires_at=value.expires_at,
                consumed_at=value.consumed_at,
                replacement_id=value.replacement_id,
            )
        )
        await self._session.flush()

    async def lock_by_digest(self, digest: str) -> RefreshCredential | None:
        """Select for update so concurrent refreshes serialize."""
        row = await self._session.scalar(
            select(RefreshCredentialTable)
            .where(RefreshCredentialTable.digest == digest)
            .with_for_update()
        )
        return _credential(row) if row else None

    async def consume(
        self, credential_id: uuid.UUID, replacement_id: uuid.UUID, now: datetime
    ) -> None:
        """Mark consumed exactly once."""
        await self._session.execute(
            update(RefreshCredentialTable)
            .where(
                RefreshCredentialTable.id == credential_id,
                RefreshCredentialTable.consumed_at.is_(None),
            )
            .values(consumed_at=now, replacement_id=replacement_id)
        )

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        """Invalidate outstanding credentials in a family."""
        await self._session.execute(
            update(RefreshCredentialTable)
            .where(
                RefreshCredentialTable.family_id == family_id,
                RefreshCredentialTable.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
