"""Shared identity use-case helpers (no framework or database imports)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from diary_contracts.errors import DomainError, ErrorCode


def utcnow() -> datetime:
    """Current UTC timestamp."""
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    """Normalize for uniqueness and storage."""
    return email.strip().lower()


def invalid_credentials() -> DomainError:
    """Uniform response for unknown email and wrong password."""
    return DomainError(ErrorCode.AUTH_INVALID, 401, "Invalid email or password")


def locked_out() -> DomainError:
    """Throttle response with a retry hint."""
    return DomainError(
        ErrorCode.RATE_LIMITED,
        429,
        "Too many attempts; try again later",
        retryable=True,
        details={"retry_after_seconds": 900},
    )


@dataclass(frozen=True, slots=True)
class IssuedSession:
    """Credential response returned once at login/refresh."""

    access_token: str
    refresh_token: str
    source: str
    session_id: UUID
