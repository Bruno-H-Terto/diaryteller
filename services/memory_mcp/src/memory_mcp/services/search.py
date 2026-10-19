"""Deterministic lexical search over only the provided records."""

from __future__ import annotations

import re

from diary_contracts.context import ContextRecord
from diary_contracts.mcp import MemoryHit, MemorySearchResult

_WORD = re.compile(r"\w{2,}", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _WORD.findall(text)]


def search_records(records: list[ContextRecord], query: str, limit: int = 10) -> MemorySearchResult:
    """Rank records by term frequency; never search outside the context."""
    terms = _tokens(query)
    hits: list[MemoryHit] = []
    for record in records:
        text_terms = _tokens(record.text)
        score = sum(text_terms.count(term) for term in terms)
        if score > 0:
            hits.append(
                MemoryHit(
                    id=record.id,
                    text=record.text,
                    recorded_at=record.recorded_at,
                    event_at=record.event_at,
                    score=float(score),
                )
            )
    hits.sort(key=lambda hit: (-hit.score, -hit.recorded_at.timestamp()))
    return MemorySearchResult(
        query=query,
        hits=hits[: max(1, min(limit, 20))],
        searched_records=len(records),
    )
