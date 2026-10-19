"""Shared speech operation preparation and finalization."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.authorization import Permission, UsageMetric
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import (
    FinishRequest,
    OperationState,
    OperationType,
    ReserveRequest,
    ReserveResult,
)

from speech.application.ports import AuthHeaders, IdentityPort


async def prepare(
    *,
    identity: IdentityPort,
    auth: AuthHeaders,
    permission: Permission,
    operation_type: OperationType,
    metric: UsageMetric,
    estimated: int,
    idempotency_key: str,
    payload_digest: str,
) -> ReserveResult:
    """Authorize and reserve; refuse replay of a terminal operation."""
    decision = await identity.authorize(auth, permission)
    if not decision.allowed:
        raise DomainError(
            ErrorCode.SUBSCRIPTION_REQUIRED,
            403,
            "Plan does not allow this speech operation",
            details={"reason": decision.reason or "not_allowed"},
        )
    result = await identity.reserve(
        auth,
        ReserveRequest(
            operation_type=operation_type,
            permission=permission.value,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
            metric=metric,
            estimated_amount=estimated,
        ),
    )
    if not result.created:
        raise DomainError(
            ErrorCode.OPERATION_COMPLETED,
            409,
            "This idempotency key was already processed",
            details={"operation_id": str(result.operation_id), "result_available": False},
        )
    return result


async def finish(
    *,
    identity: IdentityPort,
    auth: AuthHeaders,
    operation_id: UUID,
    state: OperationState,
    actual: int | None,
    error_code: str | None,
) -> None:
    """Finalize the operation with known or unknown consumption."""
    await identity.finish(
        auth,
        operation_id,
        FinishRequest(state=state, actual_amount=actual, error_code=error_code),
    )
