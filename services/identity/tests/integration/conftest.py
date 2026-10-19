"""Real PostgreSQL fixtures for identity integration tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import asyncpg
import httpx
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.integration


async def _ensure_database() -> None:
    url = make_url(__import__("os").environ["DATABASE_URL"])
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
    """Create a clean schema once per integration session."""
    await _ensure_database()
    from identity.adapters.postgres import (
        tables_access,
        tables_billing,
        tables_federation,
        tables_identity,
        tables_operation,
        tables_outbox,
        tables_session,
        tables_upload_quota,
    )
    from identity.adapters.postgres.engine import Base
    from identity.adapters.postgres.permission_repository import PostgresPlanRepository
    from identity.seed import PLANS, ROLE_PERMISSIONS

    _registered = (
        tables_access,
        tables_billing,
        tables_federation,
        tables_identity,
        tables_operation,
        tables_outbox,
        tables_session,
        tables_upload_quota,
    )

    url = __import__("os").environ["DATABASE_URL"]
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await PostgresPlanRepository(session).upsert_seed(PLANS, ROLE_PERMISSIONS)
        await session.commit()
    yield url
    await engine.dispose()


@pytest.fixture()
async def client(database: str) -> AsyncIterator[httpx.AsyncClient]:
    """In-process identity app against the test database."""
    from identity.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://identity") as value:
        yield value


@pytest.fixture()
async def db_engine(database: str):
    engine = create_async_engine(database)
    yield engine
    await engine.dispose()
