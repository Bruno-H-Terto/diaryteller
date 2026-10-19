"""Subscriptions, store transactions and idempotent webhook state."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.subscription import (
    Subscription,
    SubscriptionRecord,
    SubscriptionStatus,
)

from .tables_access import SubscriptionTable


def _subscription(row: SubscriptionTable) -> Subscription:
    return Subscription(
        user_id=row.user_id,
        plan_code=row.plan_code,
        provider=row.provider,
        external_transaction_id=row.external_transaction_id,
        status=SubscriptionStatus(row.status),
        current_period_end=row.current_period_end,
        updated_at=row.updated_at,
    )


class PostgresSubscriptionRepository:
    """Store-neutral subscription persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, user_id: uuid.UUID) -> Subscription | None:
        """Most recently updated subscription for the account."""
        row = await self._session.scalar(
            select(SubscriptionTable)
            .where(SubscriptionTable.user_id == user_id)
            .order_by(SubscriptionTable.updated_at.desc())
            .limit(1)
        )
        return _subscription(row) if row else None

    async def by_purchase_digest(self, digest: str) -> Subscription | None:
        """Resolve a purchase token digest to its owning subscription."""
        row = await self._session.scalar(
            select(SubscriptionTable).where(SubscriptionTable.purchase_token_digest == digest)
        )
        return _subscription(row) if row else None

    async def upsert(
        self,
        value: Subscription,
        token_digest: str,
        token_ciphertext: str,
        now: datetime,
    ) -> None:
        """Insert or update without ever moving period end backwards."""
        stmt = insert(SubscriptionTable).values(
            id=uuid.uuid4(),
            user_id=value.user_id,
            plan_code=value.plan_code,
            provider=value.provider,
            external_transaction_id=value.external_transaction_id,
            purchase_token_digest=token_digest,
            purchase_token_ciphertext=token_ciphertext,
            status=value.status.value,
            current_period_end=value.current_period_end,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_sub_provider_tx",
            set_={
                "plan_code": stmt.excluded.plan_code,
                "status": stmt.excluded.status,
                "current_period_end": stmt.excluded.current_period_end,
                "purchase_token_ciphertext": stmt.excluded.purchase_token_ciphertext,
                "updated_at": stmt.excluded.updated_at,
            },
            where=SubscriptionTable.current_period_end <= stmt.excluded.current_period_end,
        )
        await self._session.execute(stmt)

    async def record_by_digest(self, digest: str) -> SubscriptionRecord | None:
        """Load internal record including encrypted provider token."""
        row = await self._session.scalar(
            select(SubscriptionTable).where(SubscriptionTable.purchase_token_digest == digest)
        )
        if row is None:
            return None
        return SubscriptionRecord(
            id=row.id,
            user_id=row.user_id,
            plan_code=row.plan_code,
            provider=row.provider,
            external_transaction_id=row.external_transaction_id,
            purchase_token_digest=row.purchase_token_digest,
            purchase_token_ciphertext=row.purchase_token_ciphertext,
            status=SubscriptionStatus(row.status),
            current_period_end=row.current_period_end,
        )

    async def apply_webhook(
        self, digest: str, status: str, period_end: datetime, now: datetime
    ) -> bool:
        """Apply normalized provider state; never extends access incorrectly."""
        row = await self._session.scalar(
            select(SubscriptionTable)
            .where(SubscriptionTable.purchase_token_digest == digest)
            .with_for_update()
        )
        if row is None:
            return False
        row.status = status
        row.current_period_end = period_end
        row.updated_at = now
        await self._session.flush()
        return True

    async def due_for_reconcile(self, before: datetime, limit: int) -> list[Subscription]:
        """Subscriptions whose period ended or is about to end."""
        rows = await self._session.scalars(
            select(SubscriptionTable)
            .where(SubscriptionTable.current_period_end <= before)
            .order_by(SubscriptionTable.current_period_end)
            .limit(limit)
        )
        return [_subscription(row) for row in rows]
