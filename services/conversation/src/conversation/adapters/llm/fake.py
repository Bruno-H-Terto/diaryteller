"""Deterministic LLM adapter for tests and explicit local development."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from conversation.application.ports import (
    LlmEvent,
    LlmMessage,
    StreamFinished,
    TextDelta,
    ToolCall,
    ToolCallReady,
    Usage,
)

MARKER = "<<<RESULT>>>"


def _tools_in(messages: list[LlmMessage]) -> list[dict[str, Any]]:
    return []


class FakeChatClient:
    """Emit a tool call on the first round and a structured answer afterwards."""

    def __init__(self, delay_seconds: float = 0.0) -> None:
        self._delay = delay_seconds

    async def stream(
        self, messages: list[LlmMessage], tools: list[dict[str, Any]] | None
    ) -> AsyncIterator[LlmEvent]:
        """Simulate streaming with optional tool use driven by tool availability."""
        await asyncio.sleep(self._delay)
        tool_results = [message for message in messages if message.role == "tool"]
        if tools and not tool_results:
            tool = tools[0]["function"]["name"]
            arguments: dict[str, Any] = {}
            schema = tools[0]["function"].get("parameters", {})
            for name in schema.get("required", []):
                if name == "query":
                    arguments["query"] = "registros"
                elif name == "memory_id":
                    arguments["memory_id"] = "unknown"
            yield ToolCallReady(
                ToolCall(id="fake-call-1", name=tool, arguments=json.dumps(arguments))
            )
            yield StreamFinished("tool_calls")
            return
        source_ids: list[str] = []
        extra: dict[str, Any] = {
            "source_ids": [],
            "follow_up_questions": ["Quer me contar um pouco mais sobre isso?"],
            "suggested_replies": [],
            "proposals": [],
            "timeline": [],
            "warnings": [],
        }
        if tool_results:
            try:
                data = json.loads(tool_results[-1].content or "{}")
            except ValueError:
                data = {}
            source_ids = list(data.get("source_ids") or [])
            for key in ("hits", "events", "undated"):
                for item in data.get(key, []) if isinstance(data.get(key), list) else []:
                    if isinstance(item, dict) and item.get("id") and item["id"] not in source_ids:
                        source_ids.append(item["id"])
            extra["source_ids"] = source_ids
            answer = data.get("summary") or data.get("answer") or "Organizei os registros enviados."
        else:
            answer = "Entendi. Quer me contar o que aconteceu?"
        text = answer + "\n" + MARKER + json.dumps(extra, ensure_ascii=False)
        for start in range(0, len(text), 24):
            yield TextDelta(text[start : start + 24])
            await asyncio.sleep(0)
        yield Usage(input_tokens=100, output_tokens=50, reported=True)
        yield StreamFinished("stop")
