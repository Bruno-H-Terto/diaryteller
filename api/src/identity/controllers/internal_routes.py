"""Internal identity routes used only by trusted services."""

from __future__ import annotations

from uuid import UUID

from diary_contracts.authorization import (
    AuthorizeDecision,
    AuthorizeRequest,
    Permission,
    UsageMetric,
)
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import (
    ConsumeRequest,
    FinishRequest,
    OperationControl,
    OperationState,
    OperationType,
    OperationView,
    ReserveRequest,
    ReserveResult,
)
from fastapi import APIRouter, Depends

from identity.controllers.dependencies import (
    AuthContext,
    get_auth,
    get_repositories,
    require_internal_service,
)
from identity.controllers.repositories import Repositories
from identity.models.subscription import daily_period_start
from identity.services.authorize import authorize
from identity.services.common import utcnow
from identity.services.entitlements import evaluate_entitlement
from identity.services.finish_operation import finish_operation
from identity.services.reserve_usage import reserve_usage

router = APIRouter(prefix="/internal", tags=["internal"])

_METRICS = {
    OperationType.AI_RESPONSE: UsageMetric.AI_TOKENS,
    OperationType.TRANSCRIPTION: UsageMetric.SPEECH_SECONDS,
    OperationType.SYNTHESIS: UsageMetric.SPEECH_SECONDS,
}
_PERMISSIONS = {
    OperationType.AI_RESPONSE: Permission.CONVERSATION_USE,
    OperationType.TRANSCRIPTION: Permission.SPEECH_TRANSCRIBE,
    OperationType.SYNTHESIS: Permission.SPEECH_SYNTHESIZE,
}
_MAX_ESTIMATE = {
    OperationType.AI_RESPONSE: 16_000,
    OperationType.TRANSCRIPTION: 120,
    OperationType.SYNTHESIS: 120,
}


@router.post("/authorize", response_model=AuthorizeDecision)
async def internal_authorize(
    body: AuthorizeRequest,
    _: str = Depends(require_internal_service),
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> AuthorizeDecision:
    """Return the authoritative permission decision."""
    return await authorize(
        user=auth.user,
        session=auth.session,
        permission=body.permission,
        plans=repos.plans,
        subscriptions=repos.subscriptions,
        usage=repos.usage,
    )


@router.post("/operations/reserve", response_model=ReserveResult)
async def reserve(
    body: ReserveRequest,
    _: str = Depends(require_internal_service),
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> ReserveResult:
    """Create/reuse a receipt and reserve quota atomically."""
    expected_metric = _METRICS.get(body.operation_type)
    if body.metric is not expected_metric:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Metric does not match operation")
    if body.permission != _PERMISSIONS[body.operation_type].value:
        raise DomainError(ErrorCode.FORBIDDEN, 403, "Permission does not allow operation")
    if body.estimated_amount > _MAX_ESTIMATE[body.operation_type]:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422, "Estimated amount too high")
    return await reserve_usage(
        accounts=repos.accounts,
        operations=repos.operations,
        usage=repos.usage,
        plans=repos.plans,
        subscriptions=repos.subscriptions,
        security=repos.security,
        user=auth.user,
        session=auth.session,
        permission=Permission(body.permission),
        operation_type=body.operation_type,
        idempotency_key=body.idempotency_key,
        payload_digest=body.payload_digest,
        metric=body.metric,
        estimated_amount=body.estimated_amount,
    )


@router.post("/operations/{operation_id}/finish", response_model=OperationView)
async def finish(
    operation_id: UUID,
    body: FinishRequest,
    _: str = Depends(require_internal_service),
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> OperationView:
    """Finalize an own operation idempotently."""
    return await finish_operation(
        operations=repos.operations,
        usage=repos.usage,
        security=repos.security,
        operation_id=operation_id,
        user_id=auth.user.id,
        state=body.state,
        actual_amount=body.actual_amount,
        error_code=body.error_code,
    )


@router.post("/usage/consume", status_code=204)
async def consume(
    body: ConsumeRequest,
    _: str = Depends(require_internal_service),
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> None:
    """Consume incremental usage atomically; blocks when quota is exhausted."""
    view = await evaluate_entitlement(
        user=auth.user,
        session=auth.session,
        plan_repo=repos.plans,
        subscription_repo=repos.subscriptions,
        usage_repo=repos.usage,
        now=utcnow(),
    )
    limit = view.quotas.get(body.metric, 0)
    period = daily_period_start(utcnow())
    ok = await repos.usage.reserve(auth.user.id, body.metric.value, body.amount, limit, period)
    if not ok:
        raise DomainError(ErrorCode.QUOTA_EXCEEDED, 429, "Quota exhausted for this metric")


@router.get("/operations/{operation_id}/control", response_model=OperationControl)
async def control(
    operation_id: UUID,
    _: str = Depends(require_internal_service),
    auth: AuthContext = Depends(get_auth),
    repos: Repositories = Depends(get_repositories),
) -> OperationControl:
    """Report cancellation and session state during a stream."""
    now = utcnow()
    value = await repos.control.control(operation_id, auth.user.id, now)
    if value is None:
        raise DomainError(ErrorCode.OPERATION_NOT_FOUND, 404, "Operation not found")
    state, cancel_requested, session_active = value
    return OperationControl(
        operation_id=operation_id,
        state=state if isinstance(state, OperationState) else OperationState(state),
        cancel_requested=cancel_requested,
        session_active=session_active,
        checked_at=now,
    )
