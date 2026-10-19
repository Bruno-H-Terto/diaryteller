"""Upload and retained-storage quota contracts.

Reservations happen before signing or accepting text. Daily metrics reset at UTC
midnight; capacity metrics do not. Only numbers and IDs are stored.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UploadMetric(StrEnum):
    """Metered upload resources."""

    DAILY_UPLOAD_COUNT = "daily_upload_count"
    DAILY_UPLOAD_BYTES = "daily_upload_bytes"
    RETAINED_STORAGE_BYTES = "retained_storage_bytes"
    CONCURRENT_UPLOADS = "concurrent_uploads"


class QuotaPeriod(StrEnum):
    """Daily bucket or long-lived capacity."""

    DAILY = "daily"
    CAPACITY = "capacity"


class QuotaAmount(BaseModel):
    """Used, reserved, limit and remaining for one metric."""

    model_config = ConfigDict(extra="forbid")

    used: int = Field(ge=0)
    reserved: int = Field(ge=0)
    limit: int = Field(ge=0)
    remaining: int = Field(ge=0)


class UploadLimits(BaseModel):
    """Limits that are not counters, derived from the effective plan."""

    model_config = ConfigDict(extra="forbid")

    max_file_bytes: int = Field(ge=1)
    max_context_bytes: int = Field(ge=1)
    max_context_records: int = Field(ge=1, le=50)
    max_audio_seconds: int = Field(ge=1)
    max_concurrent_uploads: int = Field(ge=1)


class UploadQuota(BaseModel):
    """Public view for `/v1/me/upload-quota`."""

    model_config = ConfigDict(extra="forbid")

    tier: str
    window_start: datetime
    reset_at: datetime
    daily_upload_count: QuotaAmount
    daily_upload_bytes: QuotaAmount
    retained_storage_bytes: QuotaAmount
    max_file_bytes: int = Field(ge=1)
    max_context_bytes: int = Field(ge=1)
    max_context_records: int = Field(ge=1, le=50)
    max_audio_seconds: int = Field(ge=1)
    max_concurrent_uploads: int = Field(ge=1)


class QuotaReserveRequest(BaseModel):
    """Internal reservation; `reference` deduplicates retries."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    metric: UploadMetric
    amount: int = Field(ge=1)
    reference: str = Field(min_length=8, max_length=128)
    ttl_seconds: int = Field(default=3600, ge=60, le=172_800)


class QuotaReservationView(BaseModel):
    """Result of a reservation, including the current window."""

    model_config = ConfigDict(extra="forbid")

    reservation_id: UUID
    metric: UploadMetric
    bucket_date: date | None
    used: int = Field(ge=0)
    reserved: int = Field(ge=0)
    limit: int = Field(ge=0)
    remaining: int = Field(ge=0)
    reset_at: datetime


class QuotaSettlementRequest(BaseModel):
    """Commit or release one reservation exactly once."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    reservation_id: UUID


class QuotaErrorDetails(BaseModel):
    """Safe details for 429/413/409 quota responses."""

    model_config = ConfigDict(extra="forbid")

    metric: UploadMetric
    limit: int = Field(ge=0)
    used: int = Field(ge=0)
    reserved: int = Field(ge=0)
    requested: int = Field(ge=0)
    reset_at: datetime


class QuotaGaugeRequest(BaseModel):
    """Internal idempotent adjustment for a capacity gauge."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    metric: UploadMetric
    amount: int = Field(ge=1)
    reference: str = Field(min_length=8, max_length=128)


class QuotaResetRequest(BaseModel):
    """Internal request used by account deletion."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
