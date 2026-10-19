"""Configuration for retention, reconciliation and backup jobs."""

from __future__ import annotations

import base64
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MaintenanceSettings(BaseSettings):
    """Environment-backed job settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://diary:diary@localhost:5432/diary"
    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"

    receipt_retention_hours: int = Field(default=24, ge=1, le=720)
    notification_retention_days: int = Field(default=30, ge=1, le=365)
    security_retention_days: int = Field(default=30, ge=1, le=365)
    session_retention_days: int = Field(default=30, ge=1, le=365)
    token_retention_days: int = Field(default=7, ge=1, le=90)
    outbox_retention_days: int = Field(default=7, ge=1, le=90)
    account_deletion_grace_days: int = Field(default=30, ge=1, le=365)

    backup_dir: str = "backups"
    backup_encryption_key: str
    backup_retention_days: int = Field(default=7, ge=1, le=90)
    pg_dump_binary: str = "pg_dump"
    pg_restore_binary: str = "pg_restore"
    mongodump_binary: str = "mongodump"
    mongorestore_binary: str = "mongorestore"
    backup_timeout_seconds: int = Field(default=600, ge=30, le=3600)
    restore_target_database_url: str = ""

    billing_provider: str = "fake"
    google_play_package_name: str = ""
    google_play_service_account_json: str = ""
    google_play_products: dict[str, str] = Field(default_factory=dict)
    billing_token_key: str = ""
    source_encryption_key: str = ""
    billing_reconcile_limit: int = Field(default=50, ge=1, le=500)

    scheduler_interval_seconds: int = Field(default=3600, ge=60, le=86_400)
    metrics_token: str = ""

    @field_validator("backup_encryption_key")
    @classmethod
    def _decode_key(cls, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception as exc:
            raise ValueError("backup key must be base64url") from exc
        if len(decoded) != 32:
            raise ValueError("backup key must decode to 32 bytes")
        return value


@lru_cache
def get_settings() -> MaintenanceSettings:
    """Load settings once per process."""
    return MaintenanceSettings()  # type: ignore[call-arg]
