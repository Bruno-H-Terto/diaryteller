"""Direct and multipart upload contracts.

Bytes never pass through the API edge. The server reserves quota, issues short
lived signed URLs, then validates the real object before promoting it.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MAX_SIGNED_PARTS = 20
MAX_LIST_LIMIT = 100
MAX_PARTS = 10_000


class UploadMode(StrEnum):
    """Client-selected transfer strategy, bounded by server policy."""

    SINGLE = "SINGLE"
    MULTIPART = "MULTIPART"


class UploadState(StrEnum):
    """Upload and media lifecycle states."""

    CREATED = "CREATED"
    UPLOADING = "UPLOADING"
    COMPLETING = "COMPLETING"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    EXPIRED = "EXPIRED"
    DELETE_PENDING = "DELETE_PENDING"


class UploadCreate(BaseModel):
    """Request to reserve quota and create one media copy."""

    model_config = ConfigDict(extra="forbid")

    client_upload_id: UUID
    context_id: UUID
    local_media_id: UUID
    size_bytes: int = Field(ge=1)
    content_type: str = Field(min_length=1, max_length=100)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    mode: UploadMode


class UploadView(BaseModel):
    """Upload metadata; never carries an eternal URL."""

    model_config = ConfigDict(extra="forbid")

    upload_id: UUID
    media_id: UUID
    context_id: UUID
    local_media_id: UUID
    state: UploadState
    size_bytes: int = Field(ge=1)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")
    mode: UploadMode
    part_size_bytes: int | None
    max_parts: int = Field(ge=1, le=MAX_PARTS)
    expires_at: datetime
    reservation_expires_at: datetime
    failure_code: str | None


class SignedUrl(BaseModel):
    """One presigned URL with the exact headers the client must repeat."""

    model_config = ConfigDict(extra="forbid")

    part_number: int | None
    method: str = Field(pattern="^(PUT|GET)$")
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    expires_at: datetime


class SignedUrls(BaseModel):
    """Bounded batch of signed part URLs."""

    model_config = ConfigDict(extra="forbid")

    upload_id: UUID
    urls: list[SignedUrl] = Field(max_length=MAX_SIGNED_PARTS)


class PartSignRequest(BaseModel):
    """Requested part and its expected base64 checksum."""

    model_config = ConfigDict(extra="forbid")

    part_number: int = Field(ge=1, le=MAX_PARTS)
    checksum_sha256_base64: str = Field(min_length=44, max_length=44)


class SignUrlsRequest(BaseModel):
    """Parts requested for signing; empty means the whole SINGLE upload."""

    model_config = ConfigDict(extra="forbid")

    parts: list[PartSignRequest] = Field(default_factory=list, max_length=MAX_SIGNED_PARTS)


class CompletedPart(BaseModel):
    """Client-reported multipart part; verified against the provider."""

    model_config = ConfigDict(extra="forbid")

    part_number: int = Field(ge=1, le=MAX_PARTS)
    etag: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    checksum_sha256_base64: str = Field(min_length=44, max_length=44)


class UploadComplete(BaseModel):
    """Manifest submitted on completion; idempotent and asynchronous."""

    model_config = ConfigDict(extra="forbid")

    parts: list[CompletedPart] = Field(default_factory=list, max_length=MAX_PARTS)


class PartListing(BaseModel):
    """Part as reported by the provider, not by the phone's cache."""

    model_config = ConfigDict(extra="forbid")

    part_number: int = Field(ge=1)
    size_bytes: int = Field(ge=0)
    etag: str
    checksum_sha256_base64: str | None = None


class PartsPage(BaseModel):
    """Stable paginated provider listing."""

    model_config = ConfigDict(extra="forbid")

    upload_id: UUID
    items: list[PartListing]
    next_part_number: int | None = None


class MediaView(BaseModel):
    """Validated media metadata owned by the caller."""

    model_config = ConfigDict(extra="forbid")

    media_id: UUID
    context_id: UUID
    local_media_id: UUID
    state: UploadState
    size_bytes: int
    content_type: str
    sha256: str | None
    duration_seconds: float | None
    validated_at: datetime | None
    expires_at: datetime | None


class DownloadUrl(BaseModel):
    """Short-lived GET URL for a validated own media copy."""

    model_config = ConfigDict(extra="forbid")

    url: str
    expires_at: datetime


class MediaContent(BaseModel):
    """Internal bounded content descriptor for trusted services."""

    model_config = ConfigDict(extra="forbid")

    media_id: UUID
    context_id: UUID
    content_type: str
    size_bytes: int
    sha256: str
