"""Idempotent reference-data seed for plans, permissions and roles."""

from __future__ import annotations

import asyncio

from diary_contracts.authorization import Permission, UsageMetric

from identity.adapters.postgres.engine import build_engine, build_session_factory
from identity.adapters.postgres.permission_repository import PostgresPlanRepository
from identity.domain.plans import FREE_UPLOAD_LIMITS, PAID_TEST_UPLOAD_LIMITS
from identity.domain.subscription import Plan
from identity.settings import get_settings

FREE = {
    Permission.CONVERSATION_USE,
    Permission.SPEECH_TRANSCRIBE,
    Permission.SPEECH_SYNTHESIZE,
    Permission.EXCHANGE_USE,
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
        upload_limits=FREE_UPLOAD_LIMITS,
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
        upload_limits=PAID_TEST_UPLOAD_LIMITS,
        is_default=False,
    ),
    Plan(
        code="paid_test",
        name="Paid test fixture",
        permissions=frozenset(permission.value for permission in FREE | MEMORY),
        quotas={
            UsageMetric.AI_TOKENS: 200_000,
            UsageMetric.SPEECH_SECONDS: 1_800,
            UsageMetric.MEMORY_CALLS: 100,
        },
        upload_limits=PAID_TEST_UPLOAD_LIMITS,
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
        upload_limits=PAID_TEST_UPLOAD_LIMITS,
        is_default=False,
    ),
]

TEST_ONLY_PLANS = {"paid_test"}


def plans_for(app_env: str) -> list[Plan]:
    """Never install engineering-only plans in production."""
    if app_env == "production":
        return [plan for plan in PLANS if plan.code not in TEST_ONLY_PLANS]
    return list(PLANS)


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
            await repository.upsert_seed(plans_for(settings.app_env), ROLE_PERMISSIONS)
            await session.commit()
    finally:
        await engine.dispose()


def main() -> None:
    """CLI entry point."""
    asyncio.run(seed())
    print("identity seeds applied")


if __name__ == "__main__":
    main()
