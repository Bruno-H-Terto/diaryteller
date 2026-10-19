"""Configuration for bounded speech transcription and synthesis."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed speech settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    mongo_url: str = "mongodb://diary:diary@localhost:27017"
    mongo_db: str = "diary_logs"
    mongo_log_buffer: int = Field(default=500, ge=50, le=10_000)

    identity_internal_url: str = "http://localhost:8001"
    speech_internal_token: str
    identity_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)

    speech_provider: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    stt_model: str = "gpt-4o-mini-transcribe"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voices: str = "alloy,verse,sage"
    tts_max_chars: int = Field(default=4000, ge=100, le=4000)
    provider_timeout_seconds: float = Field(default=60.0, ge=5.0, le=180.0)

    max_audio_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    max_audio_seconds: int = Field(default=120, ge=1, le=300)
    ffprobe_binary: str = "ffprobe"
    ffprobe_timeout_seconds: float = Field(default=5.0, ge=1.0, le=15.0)
    estimated_transcription_seconds: int = Field(default=120, ge=1, le=300)

    idempotency_hmac_key: str = Field(min_length=16)
    metrics_token: str = ""

    @property
    def voices(self) -> list[str]:
        """Allowed provider voices; cloning is not supported."""
        return [voice.strip() for voice in self.tts_voices.split(",") if voice.strip()]

    @model_validator(mode="after")
    def _provider(self) -> Settings:
        provider = self.speech_provider or ("openai" if self.openai_api_key else "fake")
        if provider not in {"openai", "fake"}:
            raise ValueError("speech provider must be openai or fake")
        if provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for openai speech")
        if self.app_env == "production" and provider != "openai":
            raise ValueError("fake speech is not allowed in production")
        if not self.voices:
            raise ValueError("at least one TTS voice is required")
        object.__setattr__(self, "speech_provider", provider)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings()  # type: ignore[call-arg]
