"""Construct engines, storage and clients for exchange."""

from __future__ import annotations

import httpx
from diary_observability import MongoLogSink

from exchange.adapters.identity.authorizer import IdentityHttpAuthorizer
from exchange.adapters.postgres.engine import build_engine, build_session_factory
from exchange.adapters.storage.filesystem import FilesystemBlobStore
from exchange.adapters.storage.s3 import S3BlobStore
from exchange.application.ports.storage import BlobStore
from exchange.container import Container
from exchange.settings import Settings


def build_container(settings: Settings) -> Container:
    """Create the runtime graph without performing network calls."""
    engine = build_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.db_echo,
    )
    http = httpx.AsyncClient(timeout=settings.identity_timeout_seconds)
    return Container(
        settings=settings,
        engine=engine,
        session_factory=build_session_factory(engine),
        http=http,
        identity=IdentityHttpAuthorizer(
            base_url=settings.identity_internal_url,
            service=settings.identity_internal_service,
            token=settings.identity_internal_token,
            http=http,
        ),
        blobs=build_blobs(settings),
        sink=MongoLogSink(
            url=settings.mongo_url,
            database=settings.mongo_db,
            service="exchange",
            environment=settings.app_env,
            buffer_size=settings.mongo_log_buffer,
        ),
    )


def build_blobs(settings: Settings) -> BlobStore:
    """Select the object store; the filesystem backend is dev-only."""
    if settings.storage_backend == "file":
        return FilesystemBlobStore(settings.storage_dir)
    return S3BlobStore(
        endpoint=settings.storage_endpoint,
        public_endpoint=settings.storage_public_endpoint,
        region=settings.storage_region,
        bucket=settings.storage_bucket,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        use_ssl=settings.storage_use_ssl,
    )
