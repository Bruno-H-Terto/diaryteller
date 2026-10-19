"""Explicitly assembled identity dependencies for the application process."""

from __future__ import annotations

from dataclasses import dataclass

from diary_observability import MongoLogSink
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from identity.adapters.billing.store_client import GooglePlayBillingProvider
from identity.adapters.security.access_tokens import AccessTokenIssuer
from identity.adapters.security.passwords import PasswordHasher
from identity.adapters.security.source_tokens import SourceTokenCodec
from identity.application.ports.billing import BillingProvider
from identity.settings import Settings


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
    from identity.adapters.billing.fake import FakeBillingProvider

    return FakeBillingProvider(settings.source_encryption_key), "fake"
