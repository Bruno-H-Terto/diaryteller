"""Configuration for the outbox notification worker."""

from __future__ import annotations

import base64
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed worker settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://diary:diary@localhost:5432/diary"
    db_pool_size: int = Field(default=2, ge=1, le=20)
    db_max_overflow: int = Field(default=1, ge=0, le=20)

    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=500, ge=50, le=10_000)

    poll_seconds: float = Field(default=2.0, ge=0.2, le=30.0)
    batch_size: int = Field(default=10, ge=1, le=50)
    lease_seconds: int = Field(default=60, ge=10, le=300)
    max_attempts: int = Field(default=8, ge=1, le=20)

    email_token_key: str
    push_token_key: str
    email_link_base_url: str = "http://localhost:3000"
    verify_path: str = "/verify-email?token="
    reset_path: str = "/reset-password?token="
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@diary.local"
    smtp_starttls: bool = False
    smtp_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)

    push_provider: str = ""
    fcm_project_id: str = ""
    fcm_service_account_json: str = ""
    push_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)

    @field_validator("email_token_key", "push_token_key")
    @classmethod
    def _decode_key(cls, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception as exc:
            raise ValueError("token key must be base64url") from exc
        if len(decoded) != 32:
            raise ValueError("token key must decode to 32 bytes")
        return value

    @model_validator(mode="after")
    def _push(self) -> Settings:
        provider = self.push_provider or ("fcm" if self.fcm_service_account_json else "dev")
        if provider not in {"fcm", "dev"}:
            raise ValueError("push provider must be fcm or dev")
        if provider == "fcm" and not self.fcm_service_account_json:
            raise ValueError("FCM credentials are required")
        if self.app_env == "production" and provider != "fcm":
            raise ValueError("development push adapter is not allowed in production")
        object.__setattr__(self, "push_provider", provider)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
