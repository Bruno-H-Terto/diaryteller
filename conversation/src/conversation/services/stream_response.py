"""Streaming response orchestration with cancellation and evidence validation."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from diary_contracts.authorization import UsageMetric
from diary_contracts.errors import DomainError
from diary_contracts.mcp import MemoryTool
from diary_contracts.operation import OperationState
from diary_contracts.stream import StreamEventType

from conversation.config.settings import Settings
from conversation.lib.llm.messages import build_messages
from conversation.lib.ports import (
    IdentityPort,
    LlmMessage,
    LlmPort,
    McpPort,
    McpTool,
    TextDelta,
    ToolCall,
    ToolCallReady,
    Usage,
)
from conversation.models.evidence import (
    EvidenceError,
    parse_final_result,
    timeline_from_tool,
)
from conversation.models.response import MarkerFilter, ResponseEvent
from conversation.services.finish import (
    best_effort_finish,
    classify,
    finish,
    safe_message,
)
from conversation.services.monitor import monitor_control
from conversation.services.prepare import PreparedOperation
from conversation.services.stream_events import (
    OperationCancelled,
    ProviderTimeout,
    cancel_aware,
)
from conversation.services.tool_loop import execute, openai_tools

_logger = logging.getLogger(__name__)


def _tool_payload(call: ToolCall) -> dict[str, Any]:
    return {
        "id": call.id,
        "type": "function",
        "function": {"name": call.name, "arguments": call.arguments},
    }


async def stream_response(
    prepared: PreparedOperation,
    *,
    identity: IdentityPort,
    llm: LlmPort,
    mcp: McpPort,
    tools: list[McpTool],
    system_prompt: str,
    settings: Settings,
) -> AsyncGenerator[ResponseEvent, None]:
    """Yield started/text/tool/result/completed events for one operation."""
    request = prepared.request
    allowed_ids = request.context.ids()
    messages = build_messages(system_prompt, request)
    tool_defs = openai_tools(tools) if tools else None
    cancel = asyncio.Event()
    monitor = asyncio.create_task(monitor_control(identity, prepared, cancel, settings))
    loop = asyncio.get_running_loop()
    operation_deadline = loop.time() + settings.operation_timeout_seconds
    first_deadline = loop.time() + settings.first_token_timeout_seconds
    raw_text = ""
    marker = MarkerFilter()
    usage = Usage(reported=False)
    results: dict[str, dict[str, Any]] = {}
    tool_calls_used = 0
    terminal = False
    yield ResponseEvent(StreamEventType.STARTED, {"mode": request.mode.value})
    try:
        for _ in range(settings.mcp_max_tool_calls + 1):
            calls: list[ToolCall] = []
            async for event in cancel_aware(
                llm.stream(messages, tool_defs),
                cancel,
                first_deadline=first_deadline,
                operation_deadline=operation_deadline,
            ):
                if isinstance(event, TextDelta):
                    raw_text += event.text
                    visible = marker.feed(event.text)
                    if visible:
                        yield ResponseEvent(StreamEventType.TEXT_DELTA, {"text": visible})
                elif isinstance(event, ToolCallReady):
                    calls.append(event.call)
                elif isinstance(event, Usage):
                    usage = event
            if cancel.is_set():
                raise OperationCancelled()
            if not calls:
                break
            if tool_calls_used + len(calls) > settings.mcp_max_tool_calls:
                raise EvidenceError("tool call budget exceeded")
            messages.append(
                LlmMessage(role="assistant", tool_calls=[_tool_payload(call) for call in calls])
            )
            for call in calls:
                tool_calls_used += 1
                yield ResponseEvent(
                    StreamEventType.TOOL_STATUS, {"tool": call.name, "phase": "started"}
                )
                try:
                    await identity.consume(prepared.auth, UsageMetric.MEMORY_CALLS, 1)
                    result = await execute(mcp, call, allowed_ids)
                except DomainError:
                    yield ResponseEvent(
                        StreamEventType.TOOL_STATUS, {"tool": call.name, "phase": "failed"}
                    )
                    raise
                results[call.name] = result
                messages.append(
                    LlmMessage(
                        role="tool",
                        tool_call_id=call.id,
                        content=json.dumps(result, ensure_ascii=False),
                    )
                )
                yield ResponseEvent(
                    StreamEventType.TOOL_STATUS, {"tool": call.name, "phase": "completed"}
                )
        if not marker.marker_seen:
            raise EvidenceError("structured result marker missing")
        visible_tail = marker.flush()
        if visible_tail:
            yield ResponseEvent(StreamEventType.TEXT_DELTA, {"text": visible_tail})
        timeline_override = None
        if MemoryTool.TIMELINE.value in results:
            timeline_override = timeline_from_tool(results[MemoryTool.TIMELINE.value], allowed_ids)
        result = parse_final_result(
            raw_text,
            snapshot=request.diary,
            operation_id=prepared.operation_id,
            allowed_ids=allowed_ids,
            timezone=request.timezone,
            timeline_override=timeline_override,
        )
        actual = usage.input_tokens + usage.output_tokens if usage.reported else None
        await finish(identity, prepared, OperationState.SUCCEEDED, actual, None)
        terminal = True
        yield ResponseEvent(StreamEventType.RESULT, result.model_dump(mode="json"))
        yield ResponseEvent(StreamEventType.COMPLETED, {"state": "succeeded"})
    except (OperationCancelled, ProviderTimeout, EvidenceError, DomainError) as exc:
        state, code, retryable = classify(exc)
        with contextlib.suppress(Exception):
            await finish(identity, prepared, state, None, code)
        terminal = True
        yield ResponseEvent(
            StreamEventType.ERROR,
            {"code": code, "message": safe_message(exc), "retryable": retryable},
        )
    except asyncio.CancelledError:
        if not terminal:
            best_effort_finish(
                identity, prepared, OperationState.INTERRUPTED, None, "client_disconnected"
            )
        terminal = True
        raise
    except Exception as exc:
        _logger.error(
            "stream_failed",
            extra={
                "operation_id": str(prepared.operation_id),
                "error_code": type(exc).__name__[:48],
            },
        )
        with contextlib.suppress(Exception):
            await finish(identity, prepared, OperationState.FAILED, None, "internal_error")
        terminal = True
        yield ResponseEvent(
            StreamEventType.ERROR,
            {"code": "internal_error", "message": "Response failed", "retryable": True},
        )
    finally:
        monitor.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await monitor
        if not terminal:
            best_effort_finish(identity, prepared, OperationState.INTERRUPTED, None, "interrupted")
