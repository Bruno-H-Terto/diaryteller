"""Real MCP client over Streamable HTTP with context-token injection."""

from __future__ import annotations

import json
from typing import Any

import httpx2
from diary_contracts.errors import DomainError, ErrorCode
from diary_contracts.mcp import CONTEXT_TOKEN_FIELD
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

from conversation.application.ports import McpTool


class McpHttpClient:
    """One MCP session per call; no persistent content or affinity."""

    def __init__(self, url: str, service_token: str, timeout_seconds: float) -> None:
        self._url = url
        self._token = service_token
        self._timeout = timeout_seconds
        self.context_token: str | None = None

    async def _session(self):
        http = httpx2.AsyncClient(
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=httpx2.Timeout(self._timeout, read=self._timeout),
        )
        transport = streamable_http_client(
            self._url,
            http_client=http,
            max_sse_event_size=2 * 1024 * 1024,
        )
        return http, Client(transport)

    @staticmethod
    def _public_schema(schema: dict[str, Any]) -> dict[str, Any]:
        clean = json.loads(json.dumps(schema))
        properties = clean.get("properties", {})
        properties.pop(CONTEXT_TOKEN_FIELD, None)
        required = clean.get("required")
        if isinstance(required, list):
            clean["required"] = [name for name in required if name != CONTEXT_TOKEN_FIELD]
        return clean

    async def list_tools(self) -> list[McpTool]:
        """Discover tools and hide the internal context argument from the model."""
        http, client = await self._session()
        try:
            async with http, client:
                result = await client.list_tools()
                return [
                    McpTool(
                        name=tool.name,
                        description=tool.description or tool.name,
                        input_schema=self._public_schema(tool.input_schema),
                    )
                    for tool in result.tools
                ]
        except Exception as exc:
            raise DomainError(
                ErrorCode.PROVIDER_UNAVAILABLE, 502, "Memory service unavailable", retryable=True
            ) from exc

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one tool with the injected encrypted context."""
        if not self.context_token:
            raise RuntimeError("context token not bound")
        payload = {**arguments, CONTEXT_TOKEN_FIELD: self.context_token}
        http, client = await self._session()
        try:
            async with http, client:
                result = await client.call_tool(name, payload)
        except Exception as exc:
            raise DomainError(
                ErrorCode.PROVIDER_UNAVAILABLE, 502, "Memory service unavailable", retryable=True
            ) from exc
        if result.is_error:
            raise DomainError(ErrorCode.CONTEXT_INVALID, 422, "Memory tool rejected the request")
        if isinstance(result.structured_content, dict):
            return result.structured_content
        for block in result.content:
            if isinstance(block, TextContent):
                try:
                    value = json.loads(block.text)
                except ValueError:
                    continue
                if isinstance(value, dict):
                    return value
        raise DomainError(ErrorCode.PROVIDER_UNAVAILABLE, 502, "Invalid memory response")
