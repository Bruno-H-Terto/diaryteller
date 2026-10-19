"""Idempotent reference-data seed for plans, permissions and roles."""

from __future__ import annotations

import asyncio

from diary_contracts.authorization import Permission, UsageMetric

from identity.adapters.postgres.engine import build_engine, build_session_factory
from identity.adapters.postgres.permission_repository import PostgresPlanRepository
from identity.domain.subscription import Plan
from identity.settings import get_settings

FREE = {
    Permission.CONVERSATION_USE,
    Permission.SPEECH_TRANSCRIBE,
    Permission.SPEECH_SYNTHESIZE,
}
MEMORY = {
    Permission.MEMORY_SEARCH,
    Permission.MEMORY_TIMELINE,
    Permission.MEMORY_SUMMARIZE,
}

PLANS = [
    Plan(
        code="free",
        name="Free",
        permissions=frozenset(permission.value for permission in FREE),
        quotas={
            UsageMetric.AI_TOKENS: 20_000,
            UsageMetric.SPEECH_SECONDS: 300,
            UsageMetric.MEMORY_CALLS: 0,
        },
        is_default=True,
    ),
    Plan(
        code="plus",
        name="Plus",
        permissions=frozenset(permission.value for permission in FREE | MEMORY),
        quotas={
            UsageMetric.AI_TOKENS: 200_000,
            UsageMetric.SPEECH_SECONDS: 1_800,
            UsageMetric.MEMORY_CALLS: 100,
        },
        is_default=False,
    ),
    Plan(
        code="pro",
        name="Pro",
        permissions=frozenset(
            permission.value for permission in FREE | MEMORY | {Permission.MEMORY_ORGANIZE}
        ),
        quotas={
            UsageMetric.AI_TOKENS: 1_000_000,
            UsageMetric.SPEECH_SECONDS: 3_600,
            UsageMetric.MEMORY_CALLS: 500,
        },
        is_default=False,
    ),
]

ROLE_PERMISSIONS = {
    "user": {Permission.SESSIONS_MANAGE.value},
    "admin": {permission.value for permission in Permission},
}


async def seed() -> None:
    """Install catalogs without touching production user data."""
    settings = get_settings()
    engine = build_engine(
        settings.database_url,
        pool_size=1,
        max_overflow=0,
    )
    factory = build_session_factory(engine)
    try:
        async with factory() as session:
            repository = PostgresPlanRepository(session)
            await repository.upsert_seed(PLANS, ROLE_PERMISSIONS)
            await session.commit()
    finally:
        await engine.dispose()


def main() -> None:
    """CLI entry point."""
    asyncio.run(seed())
    print("identity seeds applied")


if __name__ == "__main__":
    main()
