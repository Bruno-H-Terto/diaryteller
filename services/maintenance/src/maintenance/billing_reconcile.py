"""Re-verify stored subscriptions with the store provider."""

from __future__ import annotations

from datetime import UTC, datetime

from diary_security import decrypt_json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from maintenance.settings import MaintenanceSettings


def _provider(settings: MaintenanceSettings):
    if settings.billing_provider == "google_play":
        from identity.adapters.billing.store_client import GooglePlayBillingProvider

        return GooglePlayBillingProvider(
            package_name=settings.google_play_package_name,
            service_account_json=settings.google_play_service_account_json,
            products=settings.google_play_products,
            pubsub_audience="",
            pubsub_service_account="",
            account_link_salt=settings.source_encryption_key or settings.billing_token_key,
        )
    from identity.adapters.billing.fake import FakeBillingProvider

    return FakeBillingProvider(settings.source_encryption_key or settings.billing_token_key)


async def reconcile(settings: MaintenanceSettings) -> dict[str, int]:
    """Update status and period end from authoritative provider state."""
    provider = _provider(settings)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    counts = {"checked": 0, "updated": 0, "failed": 0}
    now = datetime.now(UTC)
    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text("""
                        SELECT id, purchase_token_ciphertext
                        FROM subscriptions
                        WHERE current_period_end <= now() + interval '1 day'
                          AND purchase_token_ciphertext <> ''
                        ORDER BY current_period_end
                        LIMIT :limit
                        """),
                        {"limit": settings.billing_reconcile_limit},
                    )
                )
                .mappings()
                .all()
            )
            for row in rows:
                counts["checked"] += 1
                try:
                    token = decrypt_json(
                        row["purchase_token_ciphertext"], settings.billing_token_key
                    )["token"]
                    verified = await provider.lookup_subscription(str(token))
                except Exception:
                    counts["failed"] += 1
                    continue
                status = "active" if verified.is_active else "expired"
                await conn.execute(
                    text("""
                        UPDATE subscriptions
                        SET status = :status, current_period_end = :expires,
                            updated_at = :now
                        WHERE id = :id
                        """),
                    {
                        "status": status,
                        "expires": verified.expires_at,
                        "now": now,
                        "id": row["id"],
                    },
                )
                counts["updated"] += 1
    finally:
        await engine.dispose()
    return counts
