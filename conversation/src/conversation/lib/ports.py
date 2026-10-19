"""Ports and streamed LLM event types for the conversation use case."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from diary_contracts.authorization import AuthorizeDecision, Permission, UsageMetric
from diary_contracts.operation import (
    FinishRequest,
    OperationControl,
    OperationView,
    ReserveRequest,
    ReserveResult,
)


@dataclass(frozen=True, slots=True)
class AuthHeaders:
    """Inbound user credentials forwarded to identity (never logged)."""

    authorization: str
    source: str


@dataclass(frozen=True, slots=True)
class McpTool:
    """Discovered MCP tool definition without internal fields."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A model-requested tool invocation."""

    id: str
    name: str
    arguments: str


@dataclass(frozen=True, slots=True)
class TextDelta:
    """Incremental visible text."""

    text: str


@dataclass(frozen=True, slots=True)
class ToolCallReady:
    """A complete tool call accumulated across deltas."""

    call: ToolCall


@dataclass(frozen=True, slots=True)
class Usage:
    """Provider-reported token usage when available."""

    input_tokens: int = 0
    output_tokens: int = 0
    reported: bool = True


@dataclass(frozen=True, slots=True)
class StreamFinished:
    """Provider stream ended cleanly."""

    finish_reason: str | None = None


LlmEvent = TextDelta | ToolCallReady | Usage | StreamFinished


@dataclass(slots=True)
class LlmMessage:
    """Chat message passed to the provider, including tool results."""

    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str | None = None


class LlmPort(Protocol):
    """Streaming chat completion port."""

    def stream(
        self, messages: list[LlmMessage], tools: list[dict[str, Any]] | None
    ) -> AsyncIterator[LlmEvent]:
        """Yield text, tool calls, usage and completion events."""
        ...


class IdentityPort(Protocol):
    """Internal identity operations."""

    async def authorize(self, headers: AuthHeaders, permission: Permission) -> AuthorizeDecision:
        """Return the current authorization decision."""
        ...

    async def reserve(self, headers: AuthHeaders, request: ReserveRequest) -> ReserveResult:
        """Create/reuse an operation and reserve quota."""
        ...

    async def finish(
        self, headers: AuthHeaders, operation_id: UUID, request: FinishRequest
    ) -> OperationView:
        """Finalize an operation."""
        ...

    async def control(self, headers: AuthHeaders, operation_id: UUID) -> OperationControl:
        """Check cancellation and session state."""
        ...

    async def consume(self, headers: AuthHeaders, metric: UsageMetric, amount: int) -> None:
        """Consume incremental metered usage (memory calls)."""
        ...


class McpPort(Protocol):
    """MCP client boundary."""

    async def list_tools(self) -> list[McpTool]:
        """Discover tools exposed by the internal server."""
        ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one allowlisted tool and return structured content."""
        ...
