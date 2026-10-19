"""MCP server exposing the five memory tools over Streamable HTTP."""

from __future__ import annotations

from diary_contracts.mcp import (
    MemoryItem,
    MemorySearchResult,
    OrganizedIdeas,
    SummaryToolResult,
    TimelineToolResult,
)
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from memory_mcp.config.container import Container
from memory_mcp.lib.mcp.tools import MemoryTools


def build_server(container: Container) -> MCPServer:
    """Register tools; every handler requires the encrypted context argument."""
    mcp = MCPServer(
        "diary-memory",
        instructions=(
            "Tools operate only on the records in the provided context token. "
            "Never assume access to records that were not provided."
        ),
    )
    tools = MemoryTools(container.verifier, container.generator)

    @mcp.tool(title="Search memories")
    def search_memories(context_token: str, query: str, limit: int = 10) -> MemorySearchResult:
        """Lexically search only the provided records and report coverage."""
        return tools.search(context_token, query, limit)

    @mcp.tool(title="Get memory")
    def get_memory(context_token: str, memory_id: str) -> MemoryItem:
        """Return one record only if its ID belongs to the provided context."""
        return tools.get(context_token, memory_id)

    @mcp.tool(title="Organize ideas")
    async def organize_ideas(context_token: str) -> OrganizedIdeas:
        """Group reports, open questions and suggestions without adding facts."""
        return await tools.organize(context_token)

    @mcp.tool(title="Build timeline")
    def build_timeline(context_token: str) -> TimelineToolResult:
        """Order dated events and keep records without an event date separate."""
        return tools.timeline(context_token)

    @mcp.tool(title="Summarize period")
    async def summarize_period(
        context_token: str, start: str | None = None, end: str | None = None
    ) -> SummaryToolResult:
        """Summarize only records in the period; never claim missing records."""
        return await tools.summarize(context_token, start, end)

    return mcp


TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
    allowed_hosts=["*"],
    allowed_origins=["*"],
)
