"""Public streaming endpoint `/v1/ai/responses`."""

from __future__ import annotations

import contextlib

from diary_contracts.conversation import ConversationRequest
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.operation import OperationState
from diary_security import hmac_digest
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from conversation.adapters.http.sse import event_stream
from conversation.adapters.mcp.context_binding import ContextBinder
from conversation.application.finish import finish
from conversation.application.ports import AuthHeaders
from conversation.application.prepare import prepare_operation
from conversation.application.stream_response import stream_response
from conversation.application.tool_loop import discover
from conversation.container import Container

router = APIRouter(prefix="/ai", tags=["ai"])


def _container(request: Request) -> Container:
    return request.app.state.container


def _validate_limits(body: ConversationRequest, container: Container) -> None:
    settings = container.settings
    records = body.context.records
    if len(records) > settings.max_context_records:
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Too many context records")
    if sum(len(record.text) for record in records) > settings.max_context_chars:
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Context is too large")
    if len(body.message) > settings.max_message_chars:
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Message is too large")


@router.post("/responses")
async def respond(
    body: ConversationRequest,
    request: Request,
    authorization: str = Header(default=""),
    x_session_source: str = Header(default="", alias="X-Session-Source"),
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
) -> StreamingResponse:
    """Authorize, reserve, then stream a validated AI response."""
    container = _container(request)
    if not authorization.lower().startswith("bearer ") or not x_session_source:
        raise DomainError(ErrorCode.AUTH_INVALID, 401, "Authentication required")
    if not 8 <= len(idempotency_key) <= 128:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, 422, "A valid Idempotency-Key header is required"
        )
    _validate_limits(body, container)
    content_length = int(request.headers.get("content-length", "0") or 0)
    if content_length > container.settings.max_context_bytes:
        raise DomainError(ErrorCode.MEDIA_TOO_LARGE, 413, "Request body is too large")
    auth = AuthHeaders(authorization=authorization, source=x_session_source)
    payload_digest = hmac_digest(
        container.settings.idempotency_hmac_key, body.model_dump(mode="json")
    )
    prepared = await prepare_operation(
        request=body,
        auth=auth,
        identity=container.identity,
        idempotency_key=idempotency_key,
        payload_digest=payload_digest,
    )
    mcp = container.new_mcp()
    try:
        tools = await discover(mcp, body.mode)
        if prepared.memory_permission is not None and tools:
            binder = ContextBinder(
                container.settings.mcp_context_key,
                container.settings.mcp_context_ttl_seconds,
            )
            mcp.context_token = binder.create(
                context=body.context,
                operation_id=prepared.operation_id,
                user_id=prepared.user_id,
                session_id=prepared.session_id,
                permission=prepared.memory_permission,
            )
    except Exception as exc:
        with contextlib.suppress(Exception):
            await finish(container.identity, prepared, OperationState.FAILED, None, "setup_failed")
        raise DomainError(
            ErrorCode.PROVIDER_UNAVAILABLE, 502, "Memory service unavailable", retryable=True
        ) from exc
    events = stream_response(
        prepared,
        identity=container.identity,
        llm=container.llm,
        mcp=mcp,
        tools=tools,
        system_prompt=container.system_prompt,
        settings=container.settings,
    )
    return StreamingResponse(
        event_stream(prepared.operation_id, events, container.settings.heartbeat_seconds),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
