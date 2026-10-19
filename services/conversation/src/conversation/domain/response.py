"""Streaming response types and the marker filter.

Text after `<<<RESULT>>>` is structured metadata and is never shown to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from diary_contracts.stream import StreamEventType

MARKER = "<<<RESULT>>>"


@dataclass(frozen=True, slots=True)
class ResponseEvent:
    """One application-level SSE event before encoding."""

    type: StreamEventType
    data: dict[str, Any] = field(default_factory=dict)


class MarkerFilter:
    """Incrementally withhold a possible result marker from visible deltas."""

    def __init__(self, marker: str = MARKER) -> None:
        self._marker = marker
        self._buffer = ""
        self._stopped = False

    def feed(self, delta: str) -> str:
        """Return safe visible text for this delta."""
        if self._stopped:
            return ""
        self._buffer += delta
        index = self._buffer.find(self._marker)
        if index >= 0:
            visible = self._buffer[:index]
            self._buffer = ""
            self._stopped = True
            return visible
        keep = len(self._marker) - 1
        if len(self._buffer) <= keep:
            return ""
        visible = self._buffer[:-keep]
        self._buffer = self._buffer[-keep:]
        return visible

    def flush(self) -> str:
        """Release any remaining safe text at the end of the stream."""
        if self._stopped:
            return ""
        visible, self._buffer = self._buffer, ""
        return visible

    @property
    def marker_seen(self) -> bool:
        """Whether the structured result marker was observed."""
        return self._stopped
