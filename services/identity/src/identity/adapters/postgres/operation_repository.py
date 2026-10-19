"""Operation receipts: idempotent creation, leases and atomic transitions."""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.authorization import UsageMetric
from diary_contracts.operation import OperationState, OperationType
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.operation import OperationReceipt

from .tables_operation import OperationReceiptTable


def _receipt(row: OperationReceiptTable) -> OperationReceipt:
    return OperationReceipt(
        id=row.id,
        user_id=row.user_id,
        session_id=row.session_id,
        operation_type=OperationType(row.operation_type),
        permission=row.permission,
        idempotency_key=row.idempotency_key,
        payload_digest=row.payload_digest,
        metric=UsageMetric(row.metric),
        reserved_amount=row.reserved_amount,
        actual_amount=row.actual_amount,
        state=OperationState(row.state),
        error_code=row.error_code,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        updated_at=row.updated_at,
        lease_owner=row.lease_owner,
        lease_expires_at=row.lease_expires_at,
    )


class PostgresOperationRepository:
    """Receipt persistence with owner checks at every read."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_or_get(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        operation_type: OperationType,
        permission: str,
        idempotency_key: str,
        payload_digest: str,
        metric: UsageMetric,
        reserved_amount: int,
        now: datetime,
    ) -> tuple[OperationReceipt, bool]:
        """Insert or return the existing receipt for this user/key."""
        new_id = uuid.uuid4()
        stmt = (
            insert(OperationReceiptTable)
            .values(
                id=new_id,
                user_id=user_id,
                session_id=session_id,
                operation_type=operation_type.value,
                permission=permission,
                idempotency_key=idempotency_key,
                payload_digest=payload_digest,
                metric=metric.value,
                reserved_amount=reserved_amount,
                state=OperationState.ACCEPTED.value,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(constraint="uq_operation_idempotency")
            .returning(OperationReceiptTable.id)
        )
        inserted = await self._session.scalar(stmt)
        row = await self._session.scalar(
            select(OperationReceiptTable).where(
                OperationReceiptTable.user_id == user_id,
                OperationReceiptTable.operation_type == operation_type.value,
                OperationReceiptTable.idempotency_key == idempotency_key,
            )
        )
        if row is None:
            raise RuntimeError("operation insert did not return a row")
        return _receipt(row), inserted is not None

    async def by_id(self, operation_id: uuid.UUID, user_id: uuid.UUID) -> OperationReceipt | None:
        """Load a receipt only when it belongs to the caller."""
        row = await self._session.scalar(
            select(OperationReceiptTable).where(
                OperationReceiptTable.id == operation_id,
                OperationReceiptTable.user_id == user_id,
            )
        )
        return _receipt(row) if row else None

    async def lock(self, operation_id: uuid.UUID, user_id: uuid.UUID) -> OperationReceipt | None:
        """Lock the receipt for a state transition."""
        row = await self._session.scalar(
            select(OperationReceiptTable)
            .where(
                OperationReceiptTable.id == operation_id,
                OperationReceiptTable.user_id == user_id,
            )
            .with_for_update()
        )
        return _receipt(row) if row else None

    async def apply(self, receipt: OperationReceipt, now: datetime) -> None:
        """Persist a domain-validated transition."""
        await self._session.execute(
            update(OperationReceiptTable)
            .where(OperationReceiptTable.id == receipt.id)
            .values(
                state=receipt.state.value,
                started_at=receipt.started_at,
                finished_at=receipt.finished_at,
                updated_at=now,
                actual_amount=receipt.actual_amount,
                error_code=receipt.error_code,
                lease_owner=receipt.lease_owner,
                lease_expires_at=receipt.lease_expires_at,
            )
        )
