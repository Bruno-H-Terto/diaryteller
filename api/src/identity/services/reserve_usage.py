"""Authorize and reserve quota before any external provider call.

Receipt creation is idempotent. Quota is reserved only by the request that
created the receipt, so concurrent retries cannot double-charge the bucket.
"""

from __future__ import annotations

from datetime import datetime

from diary_contracts.authorization import Permission, UsageMetric
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import (
    TERMINAL_STATES,
    OperationState,
    OperationType,
    ReserveResult,
)

from identity.models.ports.accounts import AccountRepository
from identity.models.ports.notifications import SecurityRepository
from identity.models.ports.operation import OperationRepository
from identity.models.ports.subscription import (
    PlanRepository,
    SubscriptionRepository,
    UsageRepository,
)
from identity.models.profile import User
from identity.models.session import Session
from identity.models.subscription import daily_period_start
from identity.services.entitlements import (
    evaluate_entitlement,
    permission_decision,
)

from .common import utcnow


async def reserve_usage(
    *,
    accounts: AccountRepository,
    operations: OperationRepository,
    usage: UsageRepository,
    plans: PlanRepository,
    subscriptions: SubscriptionRepository,
    security: SecurityRepository,
    user: User,
    session: Session,
    permission: Permission,
    operation_type: OperationType,
    idempotency_key: str,
    payload_digest: str,
    metric: UsageMetric,
    estimated_amount: int,
    now: datetime | None = None,
    request_id: str = "",
) -> ReserveResult:
    """Create/reuse a receipt and reserve quota for the creator only."""
    moment = now or utcnow()
    view = await evaluate_entitlement(
        user=user,
        session=session,
        plan_repo=plans,
        subscription_repo=subscriptions,
        usage_repo=usage,
        now=moment,
        request_id=request_id,
    )
    decision = permission_decision(
        view,
        permission,
        email_verified=user.email_verified_at is not None,
        request_id=request_id,
    )
    if not decision.allowed:
        status = 403
        code = (
            ErrorCode.EMAIL_NOT_VERIFIED
            if decision.reason == "email_not_verified"
            else ErrorCode.SUBSCRIPTION_REQUIRED
        )
        raise DomainError(code, status, "Plan does not allow this operation")
    receipt, created = await operations.create_or_get(
        user_id=user.id,
        session_id=session.id,
        operation_type=operation_type,
        permission=permission.value,
        idempotency_key=idempotency_key,
        payload_digest=payload_digest,
        metric=metric,
        reserved_amount=estimated_amount,
        now=moment,
    )
    if not created:
        if receipt.payload_digest != payload_digest:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_CONFLICT,
                409,
                "The idempotency key was used with a different payload",
                details={"operation_id": str(receipt.id)},
            )
        if receipt.state in TERMINAL_STATES:
            return ReserveResult(
                operation_id=receipt.id,
                state=receipt.state,
                created=False,
                result_available=False,
                actual_amount=receipt.actual_amount,
            )
        raise DomainError(
            ErrorCode.OPERATION_IN_PROGRESS,
            409,
            "An operation with this key is still running",
            retryable=True,
            details={"operation_id": str(receipt.id), "state": receipt.state.value},
        )
    limit = view.quotas.get(metric, 0)
    period_start = daily_period_start(moment)
    reserved = await usage.reserve(user.id, metric.value, estimated_amount, limit, period_start)
    if not reserved:
        failed = receipt.finish(OperationState.FAILED, error_code="quota_exceeded", now=moment)
        await operations.apply(failed, moment)
        remaining = view.quota_remaining.get(metric, 0)
        raise DomainError(
            ErrorCode.QUOTA_EXCEEDED,
            429,
            "Quota exhausted for the current period",
            retryable=True,
            details={
                "operation_id": str(receipt.id),
                "metric": metric.value,
                "limit": limit,
                "remaining": remaining,
            },
        )
    await usage.create_reservation(
        receipt.id, user.id, metric.value, estimated_amount, period_start, moment
    )
    running = receipt.transition(OperationState.RUNNING, moment)
    await operations.apply(running, moment)
    await security.record(
        user_id=user.id,
        session_id=session.id,
        event_type="operation.reserved",
        reference=operation_type.value,
        now=moment,
    )
    return ReserveResult(
        operation_id=running.id,
        state=running.state,
        created=True,
        result_available=False,
    )
