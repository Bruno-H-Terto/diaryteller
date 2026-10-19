"""Minimal in-process Prometheus counters and gauges.

The registry exposes no user data: names and bounded labels are chosen by code.
Multi-process deployments aggregate per process; the endpoint is internal.
"""

from __future__ import annotations

from collections import Counter
from threading import Lock

_COUNTERS: Counter[tuple[str, tuple[tuple[str, str], ...]]] = Counter()
_GAUGES: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
_LOCK = Lock()


def increment(name: str, labels: dict[str, str] | None = None, value: int = 1) -> None:
    """Increase a counter."""
    key = (name, tuple(sorted((labels or {}).items())))
    with _LOCK:
        _COUNTERS[key] += value


def set_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Set a gauge to the current value."""
    key = (name, tuple(sorted((labels or {}).items())))
    with _LOCK:
        _GAUGES[key] = value


def _format_key(name: str, labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return name
    rendered = ",".join(f'{key}="{value}"' for key, value in labels)
    return f"{name}{{{rendered}}}"


def render() -> str:
    """Render the current registry in Prometheus text format."""
    lines: list[str] = []
    with _LOCK:
        for (name, labels), value in sorted(_COUNTERS.items()):
            lines.append(f"{_format_key(name, labels)} {value}")
        for (name, labels), value in sorted(_GAUGES.items()):
            lines.append(f"{_format_key(name, labels)} {value}")
    return "\n".join(lines) + "\n"
