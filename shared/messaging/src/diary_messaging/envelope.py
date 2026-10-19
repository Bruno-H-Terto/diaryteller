"""The one envelope every service publishes and consumes."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventEnvelope(BaseModel):
    """Versioned, content-minimal event.

    `key` is the partition key (usually the owning user id) so events for one
    account stay ordered. `payload` carries IDs and, when delivery needs it,
    ciphertext produced by the owning service — never diary text.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    type: str = Field(pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$", max_length=120)
    version: int = Field(default=1, ge=1, le=100)
    producer: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    key: str = Field(min_length=1, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(default=None, max_length=64)

    @property
    def topic_type(self) -> str:
        """Type and version used to route consumers."""
        return f"{self.type}:v{self.version}"
