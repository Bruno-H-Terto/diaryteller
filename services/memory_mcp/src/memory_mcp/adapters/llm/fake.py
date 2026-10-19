"""Deterministic generative tools for test and explicit local development."""

from __future__ import annotations

from collections import defaultdict

from diary_contracts.context import ContextRecord
from diary_contracts.mcp import OrganizedGroup, OrganizedIdeas, SummaryToolResult


class FakeGenerator:
    """Produce deterministic, source-bound organization and summaries."""

    async def organize(self, records: list[ContextRecord]) -> OrganizedIdeas:
        """Group records by source type without adding facts."""
        groups: dict[str, list[ContextRecord]] = defaultdict(list)
        for record in records:
            groups[record.source_type.value].append(record)
        return OrganizedIdeas(
            reports=[record.text[:300] for record in records[:10]],
            open_questions=[],
            next_steps=[],
            groups=[
                OrganizedGroup(
                    label=label,
                    items=[record.text[:300] for record in items],
                    source_ids=[record.id for record in items],
                )
                for label, items in groups.items()
            ],
            source_ids=[record.id for record in records],
        )

    async def summarize(
        self, records: list[ContextRecord], start: str | None, end: str | None
    ) -> SummaryToolResult:
        """Join a short excerpt of each provided record."""
        text = " ".join(record.text[:200] for record in records[:5])
        return SummaryToolResult(
            summary=(text or "Nenhum registro foi enviado no período.")[:4000],
            period_start=start,
            period_end=end,
            source_ids=[record.id for record in records],
        )
