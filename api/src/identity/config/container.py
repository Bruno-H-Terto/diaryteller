"""Explicitly assembled identity dependencies for the application process."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from diary_observability import MongoLogSink
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from identity.config.settings import Settings
from identity.lib.billing.store_client import GooglePlayBillingProvider
from identity.lib.oidc import OidcProviderClient
from identity.lib.security.access_tokens import AccessTokenIssuer
from identity.lib.security.oidc_link_tokens import OidcLinkTokenCodec
from identity.lib.security.passwords import PasswordHasher
from identity.lib.security.source_tokens import SourceTokenCodec
from identity.models.ports.billing import BillingProvider


@dataclass(slots=True)
class Container:
    """Runtime objects shared by request-scoped dependencies."""

    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    hasher: PasswordHasher
    access_tokens: AccessTokenIssuer
    source_tokens: SourceTokenCodec
    billing: BillingProvider
    billing_name: str
    sink: MongoLogSink
    oidc_http: httpx.AsyncClient | None = None
    oidc_providers: dict[str, OidcProviderClient] = field(default_factory=dict)
    oidc_link_tokens: OidcLinkTokenCodec | None = None


def build_billing(settings: Settings) -> tuple[BillingProvider, str]:
    """Select the real store or the explicitly local test adapter."""
    if settings.billing_provider == "google_play":
        return (
            GooglePlayBillingProvider(
                package_name=settings.google_play_package_name,
                service_account_json=settings.google_play_service_account_json,
                products=settings.google_play_products,
                pubsub_audience=settings.google_pubsub_audience,
                pubsub_service_account=settings.google_pubsub_service_account_email,
                account_link_salt=settings.source_encryption_key,
            ),
            "google_play",
        )
    if not settings.is_test:
        raise RuntimeError("fake billing is only available in test/development")
    from identity.lib.billing.fake import FakeBillingProvider

    return FakeBillingProvider(settings.source_encryption_key), "fake"


def build_oidc(
    settings: Settings,
) -> tuple[httpx.AsyncClient | None, dict[str, OidcProviderClient], OidcLinkTokenCodec | None]:
    """Build provider clients only when the flag is enabled."""
    if not settings.oidc_enabled:
        return None, {}, None
    http = httpx.AsyncClient(timeout=settings.oidc_http_timeout_seconds)
    providers = {
        name: OidcProviderClient(name, config, http)
        for name, config in settings.oidc_providers.items()
    }
    codec = OidcLinkTokenCodec(
        settings.oidc_link_encryption_key,
        issuer=settings.jwt_issuer,
        audience=f"{settings.jwt_audience}-link",
        ttl_seconds=settings.oidc_link_token_ttl_seconds,
        leeway_seconds=settings.jwt_leeway_seconds,
    )
    return http, providers, codec
