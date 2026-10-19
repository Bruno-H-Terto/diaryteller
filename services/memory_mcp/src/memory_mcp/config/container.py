"""Explicitly assembled memory MCP dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from diary_observability import MongoLogSink

from memory_mcp.config.settings import Settings
from memory_mcp.lib.llm.client import OpenAIGenerator
from memory_mcp.lib.llm.fake import FakeGenerator
from memory_mcp.lib.ports import GenerativePort
from memory_mcp.models.evidence import ContextVerifier


@dataclass(slots=True)
class Container:
    """Runtime dependencies for tool execution."""

    settings: Settings
    verifier: ContextVerifier
    generator: GenerativePort
    sink: MongoLogSink


def build_generator(settings: Settings) -> GenerativePort:
    """Select the provider or the explicit local fake."""
    if settings.llm_provider == "openai":
        return OpenAIGenerator(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.llm_model,
            settings.llm_timeout_seconds,
            settings.llm_max_output_tokens,
        )
    return FakeGenerator()
