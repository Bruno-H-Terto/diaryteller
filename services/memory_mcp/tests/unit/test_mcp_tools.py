"""In-memory MCP client tests against the real SDK server."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

from diary_contracts.authorization import Permission
from diary_contracts.context import ContextRecord
from diary_contracts.mcp import ContextTokenClaims
from diary_security import context_digest, encrypt_json
from mcp import Client
from memory_mcp.adapters.llm.fake import FakeGenerator
from memory_mcp.adapters.mcp.server import build_server
from memory_mcp.container import Container
from memory_mcp.domain.evidence import ContextVerifier

KEY = base64.urlsafe_b64encode(b"m" * 32).decode()


def token(permission: Permission = Permission.MEMORY_SEARCH) -> str:
    records = [
        ContextRecord(
            id="r1",
            recorded_at=datetime(2026, 10, 18, 20, tzinfo=UTC),
            event_at=datetime(2026, 10, 17, 10, tzinfo=UTC),
            text="Conversa com minha mãe.",
        ),
        ContextRecord(
            id="r2",
            recorded_at=datetime(2026, 10, 19, 8, tzinfo=UTC),
            text="Pensei em ligar.",
        ),
    ]
    now = datetime.now(UTC)
    digest = context_digest([record.model_dump(mode="json") for record in records])
    claims = ContextTokenClaims(
        operation_id=uuid4(),
        user_id=uuid4(),
        session_id=uuid4(),
        permission=permission.value,
        records=records,
        issued_at=now,
        expires_at=now + timedelta(minutes=2),
        context_digest=digest,
    )
    return encrypt_json(claims.model_dump(mode="json"), KEY)


def server():
    settings = SimpleNamespace(mcp_context_key=KEY, max_context_ttl_seconds=300)
    container = SimpleNamespace(
        verifier=ContextVerifier(KEY, 300), generator=FakeGenerator(), settings=settings
    )
    return build_server(cast(Container, container))


async def test_discovery_exposes_five_tools() -> None:
    async with Client(server()) as client:
        result = await client.list_tools()
        names = {tool.name for tool in result.tools}
    assert names == {
        "search_memories",
        "get_memory",
        "organize_ideas",
        "build_timeline",
        "summarize_period",
    }


async def test_search_only_returns_provided_ids() -> None:
    async with Client(server()) as client:
        result = await client.call_tool(
            "search_memories", {"context_token": token(), "query": "mãe"}
        )
    assert result.is_error is False
    assert result.structured_content["hits"][0]["id"] == "r1"


async def test_get_outside_context_is_error() -> None:
    async with Client(server()) as client:
        result = await client.call_tool(
            "get_memory", {"context_token": token(), "memory_id": "invented"}
        )
    assert result.is_error is True


async def test_wrong_permission_is_rejected() -> None:
    async with Client(server()) as client:
        result = await client.call_tool(
            "build_timeline", {"context_token": token(Permission.MEMORY_SEARCH)}
        )
    assert result.is_error is True


async def test_timeline_keeps_undated_separate() -> None:
    async with Client(server()) as client:
        result = await client.call_tool(
            "build_timeline", {"context_token": token(Permission.MEMORY_TIMELINE)}
        )
    content = result.structured_content
    assert content["events"][0]["event_date"] == "2026-10-17"
    assert content["undated"][0]["event_date"] is None
    assert content["undated"][0]["uncertainty"]
