"""Generative ports for organization and summary tools."""

from __future__ import annotations

from typing import Protocol

from diary_contracts.context import ContextRecord
from diary_contracts.mcp import OrganizedIdeas, SummaryToolResult


class GenerativePort(Protocol):
    """Provider-backed tool generation with validated output."""

    async def organize(self, records: list[ContextRecord]) -> OrganizedIdeas:
        """Group ideas without adding facts."""
        ...

    async def summarize(
        self, records: list[ContextRecord], start: str | None, end: str | None
    ) -> SummaryToolResult:
        """Summarize only the provided records."""
        ...
