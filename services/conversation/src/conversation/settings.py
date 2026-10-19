"""Configuration for the streaming conversation service."""

from __future__ import annotations

import base64
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed conversation settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=1000, ge=50, le=100_000)

    identity_internal_url: str = "http://localhost:8001"
    conversation_internal_token: str
    identity_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)

    mcp_url: str = "http://localhost:8082/mcp"
    mcp_service_token: str
    mcp_context_key: str
    mcp_timeout_seconds: float = Field(default=20.0, ge=1.0, le=60.0)
    mcp_max_tool_calls: int = Field(default=4, ge=1, le=4)
    mcp_context_ttl_seconds: int = Field(default=180, ge=30, le=600)

    llm_provider: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = Field(default=60.0, ge=5.0, le=180.0)
    first_token_timeout_seconds: float = Field(default=20.0, ge=5.0, le=60.0)
    operation_timeout_seconds: float = Field(default=90.0, ge=10.0, le=180.0)
    estimated_ai_tokens: int = Field(default=4000, ge=100, le=16_000)

    idempotency_hmac_key: str = Field(min_length=16)
    max_context_bytes: int = Field(default=262_144, ge=1024, le=1_048_576)
    max_context_records: int = Field(default=50, ge=1, le=50)
    max_context_chars: int = Field(default=50_000, ge=1000, le=100_000)
    max_message_chars: int = Field(default=8000, ge=100, le=20_000)

    prompts_dir: str = "services/conversation/prompts"
    heartbeat_seconds: int = Field(default=15, ge=5, le=30)
    revalidate_seconds: int = Field(default=15, ge=5, le=15)
    metrics_token: str = ""

    @field_validator("mcp_context_key")
    @classmethod
    def _decode_key(cls, value: str) -> str:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        except Exception as exc:
            raise ValueError("mcp context key must be base64url") from exc
        if len(decoded) != 32:
            raise ValueError("mcp context key must decode to 32 bytes")
        return value

    @model_validator(mode="after")
    def _provider(self) -> Settings:
        provider = self.llm_provider or ("openai" if self.openai_api_key else "fake")
        if provider not in {"openai", "fake"}:
            raise ValueError("llm provider must be openai or fake")
        if provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai provider")
        if self.app_env == "production" and provider != "openai":
            raise ValueError("fake LLM is not allowed in production")
        object.__setattr__(self, "llm_provider", provider)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
