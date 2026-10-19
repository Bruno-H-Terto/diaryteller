"""Configuration for the internal MCP memory server."""

from __future__ import annotations

import base64
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed memory server settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8080

    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=500, ge=50, le=10_000)

    mcp_service_token: str
    mcp_context_key: str
    max_context_ttl_seconds: int = Field(default=300, ge=30, le=600)

    llm_provider: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = Field(default=20.0, ge=5.0, le=60.0)
    llm_max_output_tokens: int = Field(default=900, ge=100, le=2000)
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
            raise ValueError("OPENAI_API_KEY is required for openai")
        if self.app_env == "production" and provider != "openai":
            raise ValueError("fake LLM is not allowed in production")
        object.__setattr__(self, "llm_provider", provider)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
