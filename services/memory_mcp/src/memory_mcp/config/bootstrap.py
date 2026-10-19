"""Construction of memory MCP runtime dependencies."""

from __future__ import annotations

from diary_observability import MongoLogSink

from memory_mcp.config.container import Container, build_generator
from memory_mcp.config.settings import Settings
from memory_mcp.models.evidence import ContextVerifier


def build_container(settings: Settings) -> Container:
    """Create verifier, generator and bounded log sink."""
    return Container(
        settings=settings,
        verifier=ContextVerifier(settings.mcp_context_key, settings.max_context_ttl_seconds),
        generator=build_generator(settings),
        sink=MongoLogSink(
            url=settings.mongo_url,
            database=settings.mongo_db,
            service="memory_mcp",
            environment=settings.app_env,
            buffer_size=settings.mongo_log_buffer,
        ),
    )
