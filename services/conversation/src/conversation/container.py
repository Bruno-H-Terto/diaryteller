"""Explicitly assembled conversation dependencies."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from diary_observability import MongoLogSink

from conversation.adapters.identity.client import IdentityClient
from conversation.adapters.llm.client import OpenAIChatClient
from conversation.adapters.llm.fake import FakeChatClient
from conversation.adapters.mcp.client import McpHttpClient
from conversation.application.ports import LlmPort
from conversation.settings import Settings


@dataclass(slots=True)
class Container:
    """Objects shared across requests; MCP clients are request-scoped."""

    settings: Settings
    identity_http: httpx.AsyncClient
    identity: IdentityClient
    llm: LlmPort
    system_prompt: str
    sink: MongoLogSink

    def new_mcp(self) -> McpHttpClient:
        """Create a request-scoped MCP client with its own context token."""
        return McpHttpClient(
            self.settings.mcp_url,
            self.settings.mcp_service_token,
            self.settings.mcp_timeout_seconds,
        )


def build_llm(settings: Settings) -> LlmPort:
    """Select OpenAI or the explicit local fake."""
    if settings.llm_provider == "openai":
        return OpenAIChatClient(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.llm_model,
            settings.llm_timeout_seconds,
        )
    return FakeChatClient()
