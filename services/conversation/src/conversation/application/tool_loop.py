"""MCP tool allowlist, schema conversion and argument validation."""

from __future__ import annotations

import json
from typing import Any

from diary_contracts.conversation import ResponseMode
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.mcp import MemoryTool

from conversation.application.ports import McpPort, McpTool, ToolCall

ALLOWLIST: dict[ResponseMode, set[MemoryTool]] = {
    ResponseMode.CONVERSATION: set(),
    ResponseMode.RECALL: {MemoryTool.SEARCH, MemoryTool.GET},
    ResponseMode.ORGANIZE: {MemoryTool.ORGANIZE, MemoryTool.SEARCH},
    ResponseMode.TIMELINE: {MemoryTool.TIMELINE},
    ResponseMode.SUMMARIZE: {MemoryTool.SUMMARIZE},
}


def public_tools(mode: ResponseMode, discovered: list[McpTool]) -> list[McpTool]:
    """Return only tools allowed for the mode; discovery is not authorization."""
    allowed = {tool.value for tool in ALLOWLIST[mode]}
    return [tool for tool in discovered if tool.name in allowed]


async def discover(mcp: McpPort, mode: ResponseMode) -> list[McpTool]:
    """Discover and filter from the real MCP server."""
    if not ALLOWLIST[mode]:
        return []
    return public_tools(mode, await mcp.list_tools())


def openai_tools(tools: list[McpTool]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to chat-completion function schemas."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def parse_arguments(call: ToolCall) -> dict[str, Any]:
    """Reject malformed tool arguments before they reach the MCP server."""
    try:
        value = json.loads(call.arguments or "{}")
    except ValueError as exc:
        raise DomainError(
            ErrorCode.CONTEXT_INVALID, 422, "Tool arguments are not valid JSON"
        ) from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Tool arguments must be an object")
    return value


async def execute(mcp: McpPort, call: ToolCall, allowed_ids: set[str]) -> dict[str, Any]:
    """Validate local references and call the tool with injected context."""
    arguments = parse_arguments(call)
    if call.name == MemoryTool.GET.value:
        memory_id = str(arguments.get("memory_id", ""))
        if memory_id not in allowed_ids:
            raise DomainError(
                ErrorCode.CONTEXT_INVALID, 422, "Requested memory is outside the context"
            )
    return await mcp.call_tool(call.name, arguments)
