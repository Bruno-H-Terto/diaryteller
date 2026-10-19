"""Explicitly assembled memory MCP dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from diary_observability import MongoLogSink

from memory_mcp.adapters.llm.client import OpenAIGenerator
from memory_mcp.adapters.llm.fake import FakeGenerator
from memory_mcp.application.ports import GenerativePort
from memory_mcp.domain.evidence import ContextVerifier
from memory_mcp.settings import Settings


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
