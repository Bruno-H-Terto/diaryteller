"""Configuration for the exchange service."""

from __future__ import annotations

import base64
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings; secrets are never committed."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="EXCHANGE_", extra="ignore", case_sensitive=False
    )

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://diary:diary@localhost:5432/exchange"
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=2, ge=0, le=50)
    db_echo: bool = False

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=1000, ge=50, le=100_000)

    identity_internal_url: str = "http://localhost:8001"
    identity_internal_service: str = "exchange"
    identity_internal_token: str = "dev-exchange-secret"
    identity_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    internal_secrets: dict[str, str] = Field(default_factory=dict)

    context_encryption_key: str
    context_max_bytes: int = Field(default=262_144, ge=1024)
    context_max_records: int = Field(default=50, ge=1, le=50)
    context_purge_deadline_seconds: int = Field(default=86_400, ge=60)

    storage_backend: Literal["s3", "file"] = "s3"
    storage_dir: str = "/tmp/diary-exchange"
    storage_endpoint: str = "http://localhost:9000"
    storage_public_endpoint: str = "http://localhost:9000"
    storage_region: str = "us-east-1"
    storage_bucket: str = "diary-exchange"
    storage_access_key: str = "diary"
    storage_secret_key: str = "diary-secret"
    storage_use_ssl: bool = False
    storage_url_ttl_seconds: int = Field(default=900, ge=60, le=3600)

    metrics_token: str = ""

    @field_validator("context_encryption_key")
    @classmethod
    def _decode_key(cls, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception as exc:
            raise ValueError("context key must be base64url encoded") from exc
        if len(decoded) != 32:
            raise ValueError("context key must decode to 32 bytes")
        return value

    @model_validator(mode="after")
    def _protect_production(self) -> Settings:
        if self.app_env == "production" and self.storage_backend != "s3":
            raise ValueError("only the s3 backend is allowed in production")
        if self.app_env == "production" and not self.storage_use_ssl:
            raise ValueError("storage must use TLS in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
