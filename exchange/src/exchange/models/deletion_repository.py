"""Durable deletion request persistence."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange.models.context import Deletion

from .tables import DeletionTable


def _deletion(row: DeletionTable) -> Deletion:
    return Deletion(
        id=row.id,
        owner_id=row.owner_id,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        state=row.state,
        requested_at=row.requested_at,
        purge_deadline=row.purge_deadline,
        completed_at=row.completed_at,
    )


class PostgresDeletionRepository:
    """Deletion rows keyed by owner."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        owner_id: uuid.UUID,
        resource_type: str,
        resource_id: uuid.UUID,
        now: datetime,
        purge_deadline: datetime,
    ) -> Deletion:
        """Insert a PENDING deletion request."""
        row = DeletionTable(
            id=uuid.uuid4(),
            owner_id=owner_id,
            resource_type=resource_type,
            resource_id=resource_id,
            state="PENDING",
            requested_at=now,
            purge_deadline=purge_deadline,
            completed_at=None,
        )
        self._session.add(row)
        await self._session.flush()
        return _deletion(row)

    async def by_id(self, owner_id: uuid.UUID, deletion_id: uuid.UUID) -> Deletion | None:
        """Load a deletion only for its owner."""
        row = await self._session.scalar(
            select(DeletionTable).where(
                DeletionTable.id == deletion_id, DeletionTable.owner_id == owner_id
            )
        )
        return _deletion(row) if row else None
