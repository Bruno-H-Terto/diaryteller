"""Authorize and reserve the operation before the SSE response starts.

All failures here are normal HTTP errors; once streaming begins, failures become
typed events because the status has already been sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from diary_contracts.authorization import Permission, UsageMetric
from diary_contracts.conversation import ConversationRequest, ResponseMode
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import OperationType, ReserveRequest

from conversation.application.ports import AuthHeaders, IdentityPort

MODE_PERMISSION = {
    ResponseMode.RECALL: Permission.MEMORY_SEARCH,
    ResponseMode.ORGANIZE: Permission.MEMORY_ORGANIZE,
    ResponseMode.TIMELINE: Permission.MEMORY_TIMELINE,
    ResponseMode.SUMMARIZE: Permission.MEMORY_SUMMARIZE,
}


@dataclass(frozen=True, slots=True)
class PreparedOperation:
    """Authorized operation with the exact context bound to it."""

    operation_id: UUID
    user_id: UUID
    session_id: UUID
    request: ConversationRequest
    auth: AuthHeaders
    memory_permission: Permission | None


async def prepare_operation(
    *,
    request: ConversationRequest,
    auth: AuthHeaders,
    identity: IdentityPort,
    idempotency_key: str,
    payload_digest: str,
) -> PreparedOperation:
    """Check permissions and reserve quota; never trusts client plan data."""
    base = await identity.authorize(auth, Permission.CONVERSATION_USE)
    if not base.allowed:
        raise DomainError(
            ErrorCode.SUBSCRIPTION_REQUIRED,
            403,
            "Conversation is not enabled for this account",
            details={"reason": base.reason or "not_allowed"},
        )
    memory_permission = MODE_PERMISSION.get(request.mode)
    if memory_permission is not None:
        memory = await identity.authorize(auth, memory_permission)
        if not memory.allowed:
            raise DomainError(
                ErrorCode.SUBSCRIPTION_REQUIRED,
                403,
                "This plan does not allow the requested memory tool",
                details={"required_permission": memory_permission.value},
            )
    context_chars = sum(len(record.text) for record in request.context.records)
    estimated = min(8000, 1200 + (len(request.message) + context_chars) // 3)
    reserve = await identity.reserve(
        auth,
        ReserveRequest(
            operation_type=OperationType.AI_RESPONSE,
            permission=Permission.CONVERSATION_USE.value,
            idempotency_key=idempotency_key,
            payload_digest=payload_digest,
            metric=UsageMetric.AI_TOKENS,
            estimated_amount=estimated,
        ),
    )
    if not reserve.created:
        raise DomainError(
            ErrorCode.OPERATION_COMPLETED,
            409,
            "This idempotency key was already processed",
            details={
                "operation_id": str(reserve.operation_id),
                "state": reserve.state.value,
                "result_available": False,
            },
        )
    entitlement = base.entitlement
    return PreparedOperation(
        operation_id=reserve.operation_id,
        user_id=entitlement.user_id,
        session_id=entitlement.session_id,
        request=request,
        auth=auth,
        memory_permission=memory_permission,
    )
