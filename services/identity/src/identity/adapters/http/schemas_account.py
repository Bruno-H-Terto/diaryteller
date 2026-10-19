"""HTTP schemas for profile, usage and notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from diary_contracts.authorization import UsageMetric
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileUpdate(BaseModel):
    """Editable profile fields; omitted fields are unchanged."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=120)
    locale: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _at_least_one(self) -> ProfileUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class UsageResponse(BaseModel):
    """Per-metric limits and remaining units for the current UTC day."""

    model_config = ConfigDict(extra="forbid")

    plan_code: str
    quotas: dict[UsageMetric, int]
    remaining: dict[UsageMetric, int]
    period: str = "utc_day"


class NotificationListResponse(BaseModel):
    """Cursor-paginated administrative notifications."""

    model_config = ConfigDict(extra="forbid")

    items: list[dict[str, Any]]
    next_before: datetime | None = None


class NotificationId(BaseModel):
    """Path-free notification identifier for responses."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
