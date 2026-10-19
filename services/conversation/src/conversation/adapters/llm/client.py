"""OpenAI-compatible streaming chat adapter.

The provider receives only the current operation's messages. Requests disable
server-side storage when the provider supports it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from conversation.application.ports import (
    LlmEvent,
    LlmMessage,
    StreamFinished,
    TextDelta,
    ToolCall,
    ToolCallReady,
    Usage,
)


def _message(value: LlmMessage) -> dict[str, Any]:
    result: dict[str, Any] = {"role": value.role, "content": value.content}
    if value.tool_calls:
        result["tool_calls"] = value.tool_calls
        result["content"] = None
    if value.tool_call_id:
        result["tool_call_id"] = value.tool_call_id
    return result


class OpenAIChatClient:
    """Stream chat completions and accumulated tool calls."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_output_tokens: int = 4000,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=0,
        )
        self._model = model
        self._max_output = max_output_tokens

    async def stream(
        self, messages: list[LlmMessage], tools: list[dict[str, Any]] | None
    ) -> AsyncIterator[LlmEvent]:
        """Yield provider events, including tool calls and usage."""
        request: dict[str, Any] = {
            "model": self._model,
            "messages": [_message(message) for message in messages],
            "stream": True,
            "stream_options": {"include_usage": True},
            "max_completion_tokens": self._max_output,
            "store": False,
        }
        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"
        stream = await self._client.chat.completions.create(**request)
        calls: dict[int, dict[str, str]] = {}
        finish_reason: str | None = None
        async for chunk in stream:
            if chunk.usage is not None:
                yield Usage(
                    input_tokens=chunk.usage.prompt_tokens,
                    output_tokens=chunk.usage.completion_tokens,
                )
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            delta = choice.delta
            if delta.content:
                yield TextDelta(delta.content)
            for tool_delta in delta.tool_calls or []:
                entry = calls.setdefault(tool_delta.index, {"id": "", "name": "", "args": ""})
                if tool_delta.id:
                    entry["id"] = tool_delta.id
                if tool_delta.function and tool_delta.function.name:
                    entry["name"] += tool_delta.function.name
                if tool_delta.function and tool_delta.function.arguments:
                    entry["args"] += tool_delta.function.arguments
        for entry in calls.values():
            if entry["name"]:
                yield ToolCallReady(
                    ToolCall(
                        id=entry["id"] or f"call-{entry['name']}",
                        name=entry["name"],
                        arguments=entry["args"] or "{}",
                    )
                )
        yield StreamFinished(finish_reason)
