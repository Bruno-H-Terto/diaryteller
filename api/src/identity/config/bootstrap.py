"""Explicit construction of identity runtime dependencies."""

from __future__ import annotations

from diary_observability import MongoLogSink

from identity.config.container import Container, build_billing, build_oidc
from identity.config.database import build_engine, build_session_factory
from identity.config.settings import Settings
from identity.lib.security.access_tokens import AccessTokenIssuer
from identity.lib.security.passwords import PasswordHasher
from identity.lib.security.source_tokens import SourceTokenCodec


def build_container(settings: Settings) -> Container:
    """Create engines, crypto helpers, billing and the log sink."""
    engine = build_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.db_echo,
    )
    billing, billing_name = build_billing(settings)
    oidc_http, oidc_providers, oidc_link_tokens = build_oidc(settings)
    return Container(
        settings=settings,
        engine=engine,
        session_factory=build_session_factory(engine),
        hasher=PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_kib=settings.argon2_memory_kib,
            parallelism=settings.argon2_parallelism,
            concurrency=settings.argon2_concurrency,
        ),
        access_tokens=AccessTokenIssuer(
            settings.keys_path,
            settings.jwt_active_kid,
            settings.jwt_issuer,
            settings.jwt_audience,
            settings.access_token_ttl_seconds,
            settings.jwt_leeway_seconds,
        ),
        source_tokens=SourceTokenCodec(
            settings.source_encryption_key,
            issuer=settings.source_issuer,
            audience=settings.source_audience,
            ttl_seconds=settings.source_ttl_seconds,
            leeway_seconds=settings.jwt_leeway_seconds,
        ),
        billing=billing,
        billing_name=billing_name,
        sink=MongoLogSink(
            url=settings.mongo_url,
            database=settings.mongo_db,
            service="identity",
            environment=settings.app_env,
            buffer_size=settings.mongo_log_buffer,
        ),
        oidc_http=oidc_http,
        oidc_providers=oidc_providers,
        oidc_link_tokens=oidc_link_tokens,
    )
