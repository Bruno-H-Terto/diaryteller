"""Owner-scoped persistence for context copies."""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.context_ref import ContextPurpose, ContextState, RetentionPolicy
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from exchange.domain.context import ContextCopy, ContextSource

from .tables import ContextSourceTable, ContextTable


def _copy(row: ContextTable) -> ContextCopy:
    return ContextCopy(
        id=row.id,
        owner_id=row.owner_id,
        client_context_id=row.client_context_id,
        state=ContextState(row.state),
        purpose=ContextPurpose(row.purpose),
        retention_policy=RetentionPolicy(row.retention_policy),
        revision=row.revision,
        created_at=row.created_at,
        updated_at=row.updated_at,
        expires_at=row.expires_at,
        storage_key=row.storage_key,
        content_sha256=row.content_sha256,
        record_count=row.record_count,
        text_bytes=row.text_bytes,
        deletion_id=row.deletion_id,
    )


def _source(row: ContextSourceTable) -> ContextSource:
    return ContextSource(
        context_id=row.context_id,
        local_record_id=row.local_record_id,
        local_version_id=row.local_version_id,
        content_sha256=row.content_sha256,
    )


class PostgresContextRepository:
    """Context persistence bound to one request transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_client_id(
        self, owner_id: uuid.UUID, client_context_id: uuid.UUID
    ) -> ContextCopy | None:
        """Find an idempotent copy."""
        row = await self._session.scalar(
            select(ContextTable).where(
                ContextTable.owner_id == owner_id,
                ContextTable.client_context_id == client_context_id,
            )
        )
        return _copy(row) if row else None

    async def by_id(self, owner_id: uuid.UUID, context_id: uuid.UUID) -> ContextCopy | None:
        """Load a copy only for its owner."""
        row = await self._session.scalar(
            select(ContextTable).where(
                ContextTable.id == context_id, ContextTable.owner_id == owner_id
            )
        )
        return _copy(row) if row else None

    async def create(self, copy: ContextCopy, sources: list[ContextSource]) -> bool:
        """Insert once; a duplicate client id keeps the existing copy."""
        inserted = await self._session.scalar(
            insert(ContextTable)
            .values(
                id=copy.id,
                owner_id=copy.owner_id,
                client_context_id=copy.client_context_id,
                state=copy.state.value,
                purpose=copy.purpose.value,
                retention_policy=copy.retention_policy.value,
                revision=copy.revision,
                created_at=copy.created_at,
                updated_at=copy.updated_at,
                expires_at=copy.expires_at,
                storage_key=copy.storage_key,
                content_sha256=copy.content_sha256,
                record_count=copy.record_count,
                text_bytes=copy.text_bytes,
                deletion_id=copy.deletion_id,
            )
            .on_conflict_do_nothing(constraint="uq_context_client_id")
            .returning(ContextTable.id)
        )
        if inserted is None:
            return False
        if sources:
            await self._session.execute(
                insert(ContextSourceTable)
                .values(
                    [
                        {
                            "context_id": source.context_id,
                            "local_record_id": source.local_record_id,
                            "local_version_id": source.local_version_id,
                            "content_sha256": source.content_sha256,
                        }
                        for source in sources
                    ]
                )
                .on_conflict_do_nothing()
            )
        return True

    async def sources(self, context_id: uuid.UUID) -> list[ContextSource]:
        """List provenance rows for one copy."""
        rows = await self._session.scalars(
            select(ContextSourceTable).where(ContextSourceTable.context_id == context_id)
        )
        return [_source(row) for row in rows]

    async def update_retention(
        self,
        owner_id: uuid.UUID,
        context_id: uuid.UUID,
        policy: RetentionPolicy,
        expected_revision: int,
        now: datetime,
    ) -> ContextCopy | None:
        """Compare-and-set retention; a pending deletion is never promoted."""
        row = await self._session.scalar(
            update(ContextTable)
            .where(
                ContextTable.id == context_id,
                ContextTable.owner_id == owner_id,
                ContextTable.revision == expected_revision,
                ContextTable.state.notin_(
                    [ContextState.DELETE_PENDING.value, ContextState.DELETED.value]
                ),
            )
            .values(
                retention_policy=policy.value,
                revision=ContextTable.revision + 1,
                updated_at=now,
            )
            .returning(ContextTable)
        )
        return _copy(row) if row else None

    async def seal(
        self, owner_id: uuid.UUID, context_id: uuid.UUID, now: datetime
    ) -> ContextCopy | None:
        """Draft to READY; already sealed copies are returned unchanged."""
        row = await self._session.scalar(
            update(ContextTable)
            .where(
                ContextTable.id == context_id,
                ContextTable.owner_id == owner_id,
                ContextTable.state == ContextState.DRAFT.value,
            )
            .values(
                state=ContextState.READY.value, revision=ContextTable.revision + 1, updated_at=now
            )
            .returning(ContextTable)
        )
        if row is not None:
            return _copy(row)
        return await self.by_id(owner_id, context_id)

    async def mark_delete_pending(
        self, owner_id: uuid.UUID, context_id: uuid.UUID, deletion_id: uuid.UUID, now: datetime
    ) -> None:
        """Freeze the copy while the purge worker runs."""
        await self._session.execute(
            update(ContextTable)
            .where(ContextTable.id == context_id, ContextTable.owner_id == owner_id)
            .values(
                state=ContextState.DELETE_PENDING.value,
                deletion_id=deletion_id,
                updated_at=now,
            )
        )
