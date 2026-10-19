"""Exchange fixtures: isolated database, deterministic identity and storage."""

from __future__ import annotations

import base64
import os
from collections.abc import AsyncIterator

import asyncpg
import httpx
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from support import FakeAuthorizer, MemoryBlobStore

os.environ.setdefault(
    "EXCHANGE_DATABASE_URL",
    os.environ.get(
        "TEST_EXCHANGE_DATABASE_URL",
        "postgresql+asyncpg://diary:diary@localhost:5432/exchange_test",
    ),
)
os.environ.setdefault(
    "EXCHANGE_CONTEXT_ENCRYPTION_KEY", base64.urlsafe_b64encode(b"x" * 32).decode()
)
os.environ.setdefault(
    "EXCHANGE_INTERNAL_SECRETS",
    '{"conversation":"test-conversation","speech":"test-speech"}',
)

pytestmark = pytest.mark.integration


async def _ensure_database() -> None:
    url = make_url(os.environ["EXCHANGE_DATABASE_URL"])
    try:
        connection = await asyncpg.connect(
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port or 5432,
            database="postgres",
            timeout=3,
        )
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"PostgreSQL unavailable: {type(exc).__name__}")
    try:
        await connection.execute(f'CREATE DATABASE "{url.database}"')
    except asyncpg.DuplicateDatabaseError:
        pass
    finally:
        await connection.close()


@pytest.fixture()
async def database() -> AsyncIterator[str]:
    """Create a clean exchange schema."""
    await _ensure_database()
    from exchange.adapters.postgres import tables  # noqa: F401 - register tables
    from exchange.adapters.postgres.engine import Base

    url = os.environ["EXCHANGE_DATABASE_URL"]
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield url
    await engine.dispose()


@pytest.fixture()
def authorizer() -> FakeAuthorizer:
    """Return a mutable fake identity client."""
    return FakeAuthorizer()


@pytest.fixture()
def blobs() -> MemoryBlobStore:
    """Return a mutable in-memory blob store."""
    return MemoryBlobStore()


@pytest.fixture()
async def client(
    database: str, authorizer: FakeAuthorizer, blobs: MemoryBlobStore
) -> AsyncIterator[httpx.AsyncClient]:
    """In-process exchange app with deterministic collaborators."""
    from exchange.main import app

    container = app.state.container
    container.identity = authorizer  # type: ignore[assignment]
    container.blobs = blobs  # type: ignore[assignment]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://exchange") as value:
        yield value
