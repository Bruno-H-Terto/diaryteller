"""Explicitly assembled exchange dependencies."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from diary_observability import MongoLogSink
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from exchange.adapters.identity.authorizer import IdentityHttpAuthorizer
from exchange.application.ports.storage import BlobStore
from exchange.settings import Settings


@dataclass(slots=True)
class Container:
    """Runtime objects shared by request-scoped dependencies."""

    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    http: httpx.AsyncClient
    identity: IdentityHttpAuthorizer
    blobs: BlobStore
    sink: MongoLogSink
