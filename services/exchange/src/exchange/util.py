"""Small shared helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(UTC)
