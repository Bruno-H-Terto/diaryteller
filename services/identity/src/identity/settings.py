"""Validated configuration for the identity service.

Missing or malformed security configuration aborts startup with a sanitized
message. Secrets are read from the environment, never from the repository.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OidcProviderSettings(BaseModel):
    """One conference/identity provider reachable over OIDC discovery."""

    discovery_url: str = Field(pattern=r"^https?://")
    client_id: str = Field(min_length=1, max_length=200)
    client_secret: str = Field(default="", max_length=500)
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    algorithms: list[str] = Field(default_factory=lambda: ["RS256", "ES256"])


class Settings(BaseSettings):
    """Environment-backed settings for identity."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://diary:diary@localhost:5432/diary"
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=2, ge=0, le=50)
    db_echo: bool = False

    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=1000, ge=50, le=100_000)

    jwt_issuer: str = "diary-api"
    jwt_audience: str = "diary-mobile"
    jwt_keys_dir: str = "keys/jwt"
    jwt_active_kid: str = "dev-1"
    jwt_leeway_seconds: int = Field(default=10, ge=0, le=60)
    access_token_ttl_seconds: int = Field(default=600, ge=60, le=3600)
    session_max_days: int = Field(default=30, ge=1, le=365)
    refresh_ttl_days: int = Field(default=30, ge=1, le=365)

    source_issuer: str = "diary-api"
    source_audience: str = "diary-mobile-source"
    source_encryption_key: str
    source_ttl_seconds: int = Field(default=900, ge=60, le=3600)

    email_token_key: str
    push_token_key: str = ""
    billing_token_key: str = ""
    email_link_base_url: str = "http://localhost:3000"
    verification_ttl_hours: int = Field(default=24, ge=1, le=72)
    reset_ttl_minutes: int = Field(default=30, ge=5, le=120)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@diary.local"
    smtp_starttls: bool = False

    identity_internal_secrets: dict[str, str] = Field(default_factory=dict)
    metrics_token: str = ""

    password_min_length: int = Field(default=10, ge=8, le=64)
    argon2_time_cost: int = Field(default=3, ge=1, le=10)
    argon2_memory_kib: int = Field(default=65_536, ge=8192, le=262_144)
    argon2_parallelism: int = Field(default=4, ge=1, le=8)
    argon2_concurrency: int = Field(default=4, ge=1, le=16)
    login_max_attempts: int = Field(default=5, ge=3, le=20)
    login_window_seconds: int = Field(default=900, ge=60, le=3600)

    oidc_enabled: bool = False
    oidc_providers: dict[str, OidcProviderSettings] = Field(default_factory=dict)
    oidc_transaction_ttl_seconds: int = Field(default=300, ge=60, le=600)
    oidc_http_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    oidc_allowed_redirect_uris: list[str] = Field(default_factory=list)
    oidc_link_key: str = ""
    oidc_link_token_ttl_seconds: int = Field(default=300, ge=60, le=900)
    ads_enabled: bool = False
    rewarded_ads_enabled: bool = False
    ad_policy_version: str = "local-fixture-1"

    billing_provider: str = "fake"
    google_play_package_name: str = ""
    google_play_service_account_json: str = ""
    google_play_products: dict[str, str] = Field(
        default_factory=lambda: {"diary_plus_monthly": "plus", "diary_pro_monthly": "pro"}
    )
    google_pubsub_audience: str = ""
    google_pubsub_service_account_email: str = ""
    billing_grace_hours: int = Field(default=72, ge=0, le=720)

    account_deletion_grace_days: int = Field(default=30, ge=1, le=365)
    receipt_retention_hours: int = Field(default=24, ge=1, le=720)

    @field_validator(
        "source_encryption_key",
        "email_token_key",
        "push_token_key",
        "billing_token_key",
        "oidc_link_key",
    )
    @classmethod
    def _decode_key(cls, value: str) -> str:
        if not value:
            return value
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception as exc:
            raise ValueError("key must be base64url encoded") from exc
        if len(decoded) != 32:
            raise ValueError("key must decode to 32 bytes")
        return value

    @field_validator("billing_provider")
    @classmethod
    def _billing_provider(cls, value: str) -> str:
        if value not in {"fake", "google_play"}:
            raise ValueError("billing provider must be fake or google_play")
        return value

    @model_validator(mode="after")
    def _protect_flags(self) -> Settings:
        if self.rewarded_ads_enabled and not self.ads_enabled:
            raise ValueError("rewarded ads require ads_enabled")
        if self.app_env == "production" and self.rewarded_ads_enabled:
            raise ValueError("rewarded ads are disabled until a provider is chosen")
        if self.oidc_enabled and not self.oidc_providers:
            raise ValueError("oidc_enabled requires at least one provider")
        if self.oidc_enabled and not self.oidc_allowed_redirect_uris:
            raise ValueError("oidc_enabled requires oidc_allowed_redirect_uris")
        return self

    @model_validator(mode="after")
    def _protect_production(self) -> Settings:
        if self.app_env == "production" and self.billing_provider == "fake":
            raise ValueError("fake billing is not allowed in production")
        if self.app_env == "production" and not self.google_play_service_account_json:
            raise ValueError("google play credentials are required in production")
        return self

    @property
    def is_test(self) -> bool:
        """Whether deterministic adapters are allowed."""
        return self.app_env in {"test", "development"}

    @property
    def oidc_link_encryption_key(self) -> str:
        """Key used to encrypt short-lived OIDC link tokens."""
        return self.oidc_link_key or self.email_token_key

    @property
    def keys_path(self) -> Path:
        """Directory containing `{kid}.private.pem` and `{kid}.public.pem`."""
        return Path(self.jwt_keys_dir)

    @property
    def auth_concurrency(self) -> int:
        """Bounded worker count for password hashing/verification."""
        return self.argon2_concurrency


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
