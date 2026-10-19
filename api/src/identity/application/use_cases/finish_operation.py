"""Finalize an operation idempotently with known or unknown consumption.

Unknown provider consumption stays reserved and is not described as avoided
cost. Cancellation is cooperative and may happen after the provider finished.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import TERMINAL_STATES, OperationState, OperationView

from identity.application.ports.notifications import SecurityRepository
from identity.application.ports.operation import OperationRepository
from identity.application.ports.subscription import UsageRepository
from identity.domain.operation import InvalidTransition, OperationReceipt
from identity.domain.subscription import ReservationState, daily_period_start

from .common import utcnow


def operation_view(receipt: OperationReceipt) -> OperationView:
    """Map a domain receipt to the safe public view."""
    return OperationView(
        id=receipt.id,
        type=receipt.operation_type,
        state=receipt.state,
        created_at=receipt.created_at,
        started_at=receipt.started_at,
        finished_at=receipt.finished_at,
        updated_at=receipt.updated_at,
        error_code=receipt.error_code,
        result_available=False,
    )


async def finish_operation(
    *,
    operations: OperationRepository,
    usage: UsageRepository,
    security: SecurityRepository,
    operation_id: uuid.UUID,
    user_id: uuid.UUID,
    state: OperationState,
    actual_amount: int | None,
    error_code: str | None,
    now: datetime | None = None,
) -> OperationView:
    """Apply a terminal transition and adjust the quota bucket."""
    moment = now or utcnow()
    if state not in TERMINAL_STATES:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Finish state must be terminal")
    receipt = await operations.lock(operation_id, user_id)
    if receipt is None:
        raise DomainError(ErrorCode.OPERATION_NOT_FOUND, 404, "Operation not found")
    if receipt.state in TERMINAL_STATES:
        return operation_view(receipt)
    try:
        updated = receipt.finish(
            state, actual_amount=actual_amount, error_code=error_code, now=moment
        )
    except InvalidTransition as exc:
        raise DomainError(
            ErrorCode.IDEMPOTENCY_CONFLICT, 409, "Invalid operation transition"
        ) from exc
    await operations.apply(updated, moment)
    period_start = daily_period_start(receipt.created_at)
    if actual_amount is not None:
        await usage.finalize(
            user_id,
            receipt.metric.value,
            receipt.reserved_amount,
            actual_amount,
            period_start,
        )
    await usage.finish_reservation(operation_id, ReservationState.FINISHED, moment)
    await security.record(
        user_id=user_id,
        session_id=receipt.session_id,
        event_type="operation.finished",
        reference=state.value,
        now=moment,
    )
    return operation_view(updated)
