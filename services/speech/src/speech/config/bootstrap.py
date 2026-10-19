"""Construction of speech runtime dependencies."""

from __future__ import annotations

import httpx
from diary_observability import MongoLogSink

from speech.config.container import Container, build_provider
from speech.config.settings import Settings
from speech.lib.identity.client import IdentityClient


def build_container(settings: Settings) -> Container:
    """Create HTTP client, provider and bounded log sink."""
    identity_http = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.identity_timeout_seconds),
        limits=httpx.Limits(max_connections=30, max_keepalive_connections=10),
    )
    return Container(
        settings=settings,
        identity_http=identity_http,
        identity=IdentityClient(
            identity_http,
            settings.identity_internal_url,
            settings.speech_internal_token,
        ),
        provider=build_provider(settings),
        sink=MongoLogSink(
            url=settings.mongo_url,
            database=settings.mongo_db,
            service="speech",
            environment=settings.app_env,
            buffer_size=settings.mongo_log_buffer,
        ),
    )
