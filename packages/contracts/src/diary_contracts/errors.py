"""Transport error envelope shared by every public endpoint.

The envelope never carries provider messages, stack traces or user content.
`details` is for safe, documented fields only.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(StrEnum):
    """Stable machine-readable codes documented for mobile clients."""

    AUTH_INVALID = "auth_invalid"
    SESSION_REVOKED = "session_revoked"
    SESSION_SOURCE_INVALID = "session_source_invalid"
    ACCOUNT_DISABLED = "account_disabled"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    TOKEN_INVALID = "token_invalid"
    RECENT_AUTH_REQUIRED = "recent_auth_required"
    OPERATION_COMPLETED = "operation_completed"
    DAILY_UPLOAD_COUNT_EXCEEDED = "daily_upload_count_exceeded"
    DAILY_UPLOAD_BYTES_EXCEEDED = "daily_upload_bytes_exceeded"
    FILE_TOO_LARGE = "file_too_large"
    CONTEXT_TOO_LARGE = "context_too_large"
    STORAGE_QUOTA_EXCEEDED = "storage_quota_exceeded"
    UPLOAD_CONCURRENCY_EXCEEDED = "upload_concurrency_exceeded"
    UPLOAD_STATE_INVALID = "upload_state_invalid"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    CURSOR_EXPIRED = "cursor_expired"
    RESULT_EXPIRED = "result_expired"
    MEDIA_EXPIRED = "media_expired"
    CONTEXT_NOT_READY = "context_not_ready"
    PRECONDITION_REQUIRED = "precondition_required"
    PRECONDITION_FAILED = "precondition_failed"
    OIDC_TRANSACTION_INVALID = "oidc_transaction_invalid"
    OIDC_PROVIDER_UNAVAILABLE = "oidc_provider_unavailable"
    ACCOUNT_LINK_REQUIRED = "account_link_required"
    FEATURE_DISABLED = "feature_disabled"
    OPERATION_IN_PROGRESS = "operation_in_progress"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    SUBSCRIPTION_REQUIRED = "subscription_required"
    QUOTA_EXCEEDED = "quota_exceeded"
    CONTEXT_REQUIRED = "context_required"
    CONTEXT_INVALID = "context_invalid"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    OPERATION_NOT_FOUND = "operation_not_found"
    OPERATION_INTERRUPTED = "operation_interrupted"
    OPERATION_CANCELLED = "operation_cancelled"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_TIMEOUT = "provider_timeout"
    MEDIA_INVALID = "media_invalid"
    MEDIA_TOO_LARGE = "media_too_large"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"


class ErrorEnvelope(BaseModel):
    """Consistent JSON error body returned by every service."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(description="Stable URI-like category, e.g. https://diary/errors/session")
    title: str
    message: str = Field(default="", description="Android-facing copy of the safe title")
    status: int = Field(ge=400, le=599)
    code: ErrorCode
    request_id: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class DomainError(Exception):
    """Application error translated by the HTTP layer into `ErrorEnvelope`."""

    def __init__(
        self,
        code: ErrorCode,
        status: int,
        title: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(title)
        self.code = code
        self.status = status
        self.title = title
        self.retryable = retryable
        self.details = details or {}


def error_type(code: ErrorCode) -> str:
    """Return a stable category URI for an error code."""
    return f"https://diary.local/errors/{code.value}"
