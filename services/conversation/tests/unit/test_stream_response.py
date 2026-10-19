"""Streaming orchestration tests with deterministic adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from conversation.adapters.llm.fake import FakeChatClient
from conversation.adapters.llm.messages import load_system_prompt
from conversation.application.ports import AuthHeaders, IdentityPort, McpTool
from conversation.application.prepare import PreparedOperation
from conversation.application.stream_response import stream_response
from conversation.application.tool_loop import discover
from conversation.settings import get_settings
from diary_contracts.conversation import ConversationRequest
from diary_contracts.stream import StreamEventType


class FakeMcp:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def list_tools(self):
        return [
            McpTool(
                name="build_timeline",
                description="timeline",
                input_schema={"type": "object", "properties": {}, "required": []},
            )
        ]

    async def call_tool(self, name, arguments):
        self.calls.append(name)
        return {
            "events": [
                {
                    "event": "Conversa",
                    "event_date": "2026-10-17",
                    "recorded_at": "2026-10-18T20:00:00+00:00",
                    "source_ids": ["r1"],
                    "uncertainty": None,
                }
            ],
            "undated": [
                {
                    "event": "Ligar",
                    "event_date": None,
                    "recorded_at": "2026-10-19T08:00:00+00:00",
                    "source_ids": ["r2"],
                    "uncertainty": "sem data",
                }
            ],
            "source_ids": ["r1", "r2"],
            "coverage": "provided_context",
        }


class FakeIdentity:
    def __init__(self) -> None:
        self.finished: list[tuple[str, int | None]] = []

    async def finish(self, headers, operation_id, request):
        self.finished.append((request.state.value, request.actual_amount))
        return None

    async def consume(self, headers, metric, amount):
        return None


def prepared() -> PreparedOperation:
    request = ConversationRequest.model_validate(
        {
            "client_message_id": str(uuid4()),
            "conversation_id": "c1",
            "mode": "timeline",
            "message": "Organize",
            "timezone": "UTC",
            "context": {
                "records": [
                    {
                        "id": "r1",
                        "recorded_at": datetime(2026, 10, 18, 20, tzinfo=UTC).isoformat(),
                        "event_at": datetime(2026, 10, 17, 10, tzinfo=UTC).isoformat(),
                        "text": "Conversa",
                    },
                    {
                        "id": "r2",
                        "recorded_at": datetime(2026, 10, 19, 8, tzinfo=UTC).isoformat(),
                        "text": "Ligar",
                    },
                ]
            },
        }
    )
    return PreparedOperation(
        operation_id=uuid4(),
        user_id=uuid4(),
        session_id=uuid4(),
        request=request,
        auth=AuthHeaders("Bearer x", "source"),
        memory_permission=None,
    )


async def test_timeline_uses_mcp_sources_and_finishes() -> None:
    settings = get_settings()
    mcp = FakeMcp()
    identity = FakeIdentity()
    tools = await discover(mcp, prepared().request.mode)
    events = [
        event
        async for event in stream_response(
            prepared(),
            identity=cast(IdentityPort, identity),
            llm=FakeChatClient(),
            mcp=mcp,
            tools=tools,
            system_prompt=load_system_prompt(settings.prompts_dir),
            settings=settings,
        )
    ]
    types = [event.type for event in events]
    assert StreamEventType.TOOL_STATUS in types
    assert StreamEventType.RESULT in types and StreamEventType.COMPLETED in types
    result = next(event.data for event in events if event.type is StreamEventType.RESULT)
    assert result["source_ids"] == ["r1", "r2"]
    assert len(result["timeline"]) == 2
    assert identity.finished[0][0] == "succeeded"
