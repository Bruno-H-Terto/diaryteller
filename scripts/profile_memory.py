"""Memray profiling for a synthetic streaming scenario (no real diary data)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from conversation.config.settings import get_settings
from conversation.lib.llm.fake import FakeChatClient
from conversation.lib.ports import AuthHeaders, IdentityPort
from conversation.services.stream_response import stream_response
from diary_contracts.conversation import ConversationRequest


class NullIdentity:
    async def finish(self, *args, **kwargs):
        return None

    async def consume(self, *args, **kwargs):
        return None


class NullMcp:
    async def list_tools(self):
        return []

    async def call_tool(self, name, arguments):
        return {}


def prepared():
    from conversation.services.prepare import PreparedOperation

    records = [
        {
            "id": f"r{i}",
            "recorded_at": datetime.now(UTC).isoformat(),
            "text": "registro sintético " * 40,
        }
        for i in range(50)
    ]
    request = ConversationRequest.model_validate(
        {
            "client_message_id": str(uuid4()),
            "conversation_id": "profile",
            "mode": "conversation",
            "message": "cenário sintético",
            "timezone": "UTC",
            "context": {"records": records},
        }
    )
    return PreparedOperation(
        operation_id=uuid4(),
        user_id=uuid4(),
        session_id=uuid4(),
        request=request,
        auth=AuthHeaders("Bearer x", "x"),
        memory_permission=None,
    )


async def main() -> None:
    settings = get_settings()
    prompt = (Path(settings.prompts_dir) / "system_conversation.txt").read_text()
    for _ in range(50):
        async for _event in stream_response(
            prepared(),
            identity=cast(IdentityPort, NullIdentity()),
            llm=FakeChatClient(),
            mcp=NullMcp(),
            tools=[],
            system_prompt=prompt,
            settings=settings,
        ):
            pass


if __name__ == "__main__":
    try:
        import memray

        with memray.Tracker("memray-stream.bin", native_traces=True):
            asyncio.run(main())
        print("memray profile written to memray-stream.bin")
    except ImportError:
        asyncio.run(main())
        print("memray not installed; ran scenario without profiling")
