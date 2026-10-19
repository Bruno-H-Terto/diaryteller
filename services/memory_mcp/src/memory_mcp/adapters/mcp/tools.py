"""The five MCP tools operating only on authenticated context."""

from __future__ import annotations

import logging
from datetime import date

from diary_contracts.authorization import Permission
from diary_contracts.context import ContextRecord
from diary_contracts.mcp import (
    MemoryItem,
    MemorySearchResult,
    OrganizedIdeas,
    SummaryToolResult,
    TimelineToolResult,
)
from mcp.server.mcpserver.exceptions import ToolError

from memory_mcp.application.ports import GenerativePort
from memory_mcp.application.search import search_records
from memory_mcp.application.timeline import build_timeline
from memory_mcp.domain.evidence import ContextRejected, ContextVerifier

_logger = logging.getLogger(__name__)


class MemoryTools:
    """Stateless tool implementations; no content survives the call."""

    def __init__(self, verifier: ContextVerifier, generator: GenerativePort) -> None:
        self._verifier = verifier
        self._generator = generator

    def _claims(self, token: str, permission: Permission):
        try:
            return self._verifier.verify(token, permission.value)
        except ContextRejected as exc:
            _logger.info("context_rejected", extra={"error_code": "context_rejected"})
            raise ToolError("context is not authorized for this tool") from exc

    def search(self, context_token: str, query: str, limit: int = 10) -> MemorySearchResult:
        """Lexical search inside the provided records."""
        claims = self._claims(context_token, Permission.MEMORY_SEARCH)
        return search_records(claims.records, query, limit)

    def get(self, context_token: str, memory_id: str) -> MemoryItem:
        """Return one record only when its ID is in the provided set."""
        claims = self._claims(context_token, Permission.MEMORY_SEARCH)
        for record in claims.records:
            if record.id == memory_id:
                return MemoryItem(
                    id=record.id,
                    text=record.text,
                    recorded_at=record.recorded_at,
                    event_at=record.event_at,
                    source_type=record.source_type.value,
                )
        raise ToolError("memory id is outside the provided context")

    async def organize(self, context_token: str) -> OrganizedIdeas:
        """Group ideas with validated sources."""
        claims = self._claims(context_token, Permission.MEMORY_ORGANIZE)
        return await self._generator.organize(claims.records)

    def timeline(self, context_token: str) -> TimelineToolResult:
        """Build a deterministic timeline from explicit event dates."""
        claims = self._claims(context_token, Permission.MEMORY_TIMELINE)
        return build_timeline(claims.records)

    async def summarize(
        self, context_token: str, start: str | None = None, end: str | None = None
    ) -> SummaryToolResult:
        """Summarize records whose effective date falls in the period."""
        claims = self._claims(context_token, Permission.MEMORY_SUMMARIZE)
        try:
            start_date = date.fromisoformat(start) if start else None
            end_date = date.fromisoformat(end) if end else None
        except ValueError as exc:
            raise ToolError("dates must be ISO 8601 dates") from exc
        if start_date and end_date and start_date > end_date:
            raise ToolError("start date is after end date")
        selected = [record for record in claims.records if _in_period(record, start_date, end_date)]
        if not selected:
            return SummaryToolResult(
                summary="Nenhum registro foi enviado para o período solicitado.",
                period_start=start,
                period_end=end,
                source_ids=[],
            )
        return await self._generator.summarize(selected, start, end)


def _in_period(record: ContextRecord, start: date | None, end: date | None) -> bool:
    effective = record.event_at.date() if record.event_at else record.recorded_at.date()
    if start and effective < start:
        return False
    return not (end and effective > end)
