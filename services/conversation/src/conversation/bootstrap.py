"""Construction of conversation runtime dependencies."""

from __future__ import annotations

from pathlib import Path

import httpx
from diary_observability import MongoLogSink

from conversation.adapters.identity.client import IdentityClient
from conversation.container import Container, build_llm
from conversation.settings import Settings


def build_container(settings: Settings) -> Container:
    """Create the shared HTTP client, LLM adapter and log sink."""
    identity_http = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.identity_timeout_seconds),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
    )
    prompt_path = Path(settings.prompts_dir) / "system_conversation.txt"
    return Container(
        settings=settings,
        identity_http=identity_http,
        identity=IdentityClient(
            identity_http,
            settings.identity_internal_url,
            settings.conversation_internal_token,
        ),
        llm=build_llm(settings),
        system_prompt=prompt_path.read_text(encoding="utf-8"),
        sink=MongoLogSink(
            url=settings.mongo_url,
            database=settings.mongo_db,
            service="conversation",
            environment=settings.app_env,
            buffer_size=settings.mongo_log_buffer,
        ),
    )
