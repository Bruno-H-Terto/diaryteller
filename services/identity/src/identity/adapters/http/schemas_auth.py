"""HTTP request/response schemas for authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from identity.application.use_cases.common import IssuedSession
from identity.settings import Settings


class RegisterRequest(BaseModel):
    """Account registration payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    locale: str = Field(default="pt-BR", max_length=16)
    timezone: str = Field(default="UTC", max_length=64)


class VerifyEmailRequest(BaseModel):
    """Single-use verification token."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=200)


class EmailRequest(BaseModel):
    """Email used by resend and reset request flows."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Reset token and new password."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    """Password login bound to a client-generated device id."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    device_id: UUID
    device_label: str | None = Field(default=None, max_length=80)
    platform: Literal["android", "ios"]


class RefreshRequest(BaseModel):
    """Refresh rotation payload; device id must match the session."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=20, max_length=200)
    device_id: UUID


class TokenResponse(BaseModel):
    """Credential bundle returned once; never logged."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    source: str
    session_id: UUID
    token_type: str = "Bearer"
    expires_in: int
    source_expires_in: int


def tokens_response(bundle: IssuedSession, settings: Settings) -> TokenResponse:
    """Build the documented token payload from an issued credential bundle."""
    return TokenResponse(
        access_token=bundle.access_token,
        refresh_token=bundle.refresh_token,
        source=bundle.source,
        session_id=bundle.session_id,
        expires_in=settings.access_token_ttl_seconds,
        source_expires_in=settings.source_ttl_seconds,
    )


class ProfileResponse(BaseModel):
    """Editable profile and account state."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    display_name: str | None
    locale: str
    timezone: str
    status: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class DeviceInfo(BaseModel):
    """Device metadata attached to a session."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    label: str | None
    platform: str


class SessionResponse(BaseModel):
    """Session view without credentials."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    device_id: UUID
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    is_current: bool
    is_active: bool


class NotificationResponse(BaseModel):
    """Administrative notification."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    kind: str
    title: str
    body: str
    read: bool
    created_at: datetime


class PushTokenRequest(BaseModel):
    """Push registration for one device."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=4096)
    platform: Literal["android", "ios"]


class VerifyPurchaseRequest(BaseModel):
    """Store purchase token to verify server-side."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1, max_length=190)
    purchase_token: str = Field(min_length=8, max_length=4096)

    @field_validator("product_id")
    @classmethod
    def _safe_product(cls, value: str) -> str:
        if any(char.isspace() for char in value):
            raise ValueError("product id must not contain spaces")
        return value
