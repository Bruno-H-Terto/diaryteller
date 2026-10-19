"""Allowlist-based log sanitization shared by every service.

Only operational metadata may be logged. Anything else, including request and
response bodies, headers, prompts, transcripts and provider errors, is dropped
before it reaches stdout or MongoDB.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

ALLOWED_FIELDS = frozenset(
    {
        "timestamp",
        "level",
        "service",
        "version",
        "environment",
        "request_id",
        "operation_id",
        "event",
        "status",
        "duration_ms",
        "error_code",
        "method",
        "path",
        "state",
        "attempt",
        "channel",
        "dropped_logs",
        "provider",
        "metric",
        "value",
    }
)
MAX_STRING = 256


def _safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:MAX_STRING]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return None


def sanitize(fields: dict[str, Any]) -> dict[str, Any]:
    """Return only allowlisted, length-bounded scalar fields."""
    clean: dict[str, Any] = {}
    for key, value in fields.items():
        if key in ALLOWED_FIELDS:
            safe = _safe_value(value)
            if safe is not None:
                clean[key] = safe
    return clean


class JsonFormatter(logging.Formatter):
    """Render log records as one sanitized JSON object per line."""

    def __init__(self, service: str, version: str, environment: str) -> None:
        super().__init__()
        self.service = service
        self.version = version
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        fields = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "version": self.version,
            "environment": self.environment,
            "event": record.getMessage(),
        }
        for key in ALLOWED_FIELDS:
            if hasattr(record, key):
                fields[key] = getattr(record, key)
        return json.dumps(sanitize(fields), ensure_ascii=False, separators=(",", ":"))


def configure_logging(service: str, version: str = "0.1.0") -> None:
    """Install the JSON formatter without duplicating handlers."""
    environment = os.environ.get("APP_ENV", "development")
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service, version, environment))
    root.addHandler(handler)
    for name in ("uvicorn.access", "httpx", "httpcore", "openai", "mcp", "pymongo"):
        logging.getLogger(name).setLevel(logging.WARNING)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a sanitized event; unknown fields are silently discarded."""
    logger.log(level, event, extra=sanitize(fields))
