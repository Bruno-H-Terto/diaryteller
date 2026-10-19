"""Webhook event deduplication and outcome tracking."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.application.ports.billing import StoreEvent

from .tables_billing import BillingEventTable


class PostgresBillingEventRepository:
    """Deduplicate provider events by (provider, event_id)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(self, provider: str, event: StoreEvent, now: datetime) -> uuid.UUID | None:
        """Insert the event; return None when it was already processed/claimed."""
        event_id = uuid.uuid4()
        stmt = (
            insert(BillingEventTable)
            .values(
                id=event_id,
                provider=provider,
                event_id=event.event_id,
                event_type=event.event_type.value,
                transaction_id=event.transaction_id,
                purchase_token_digest=event.purchase_token_digest,
                occurred_at=event.occurred_at,
                created_at=now,
            )
            .on_conflict_do_nothing(constraint="uq_billing_event")
            .returning(BillingEventTable.id)
        )
        inserted = await self._session.scalar(stmt)
        return inserted

    async def mark(self, event_id: uuid.UUID, outcome: str, now: datetime) -> None:
        """Record a bounded outcome code."""
        await self._session.execute(
            update(BillingEventTable)
            .where(BillingEventTable.id == event_id)
            .values(processed_at=now, outcome=outcome[:48])
        )
