"""Idempotent retention and reservation reconciliation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from maintenance.settings import MaintenanceSettings

TERMINAL = ("succeeded", "failed", "cancelled", "interrupted")


async def _reservations(conn, now: datetime) -> int:
    rows = (
        await conn.execute(
            text("""
                SELECT operation_id, user_id, metric, amount, period_start
                FROM usage_reservations
                WHERE state = 'reserved' AND expires_at < :now
                """),
            {"now": now},
        )
    ).mappings()
    count = 0
    for row in rows:
        await conn.execute(
            text("""
                UPDATE usage_buckets
                SET used = GREATEST(0, used - :amount)
                WHERE user_id = :user_id AND metric = :metric AND period_start = :period
                """),
            {
                "amount": row["amount"],
                "user_id": row["user_id"],
                "metric": row["metric"],
                "period": row["period_start"],
            },
        )
        await conn.execute(
            text("""
                UPDATE usage_reservations
                SET state = 'abandoned', finished_at = :now
                WHERE operation_id = :operation_id
                """),
            {"now": now, "operation_id": row["operation_id"]},
        )
        await conn.execute(
            text("""
                UPDATE operation_receipts
                SET state = 'interrupted', finished_at = :now, updated_at = :now,
                    error_code = 'reservation_expired'
                WHERE id = :operation_id AND state IN ('accepted', 'running')
                """),
            {"now": now, "operation_id": row["operation_id"]},
        )
        count += 1
    return count


async def _purge_accounts(conn, now: datetime) -> int:
    ids = list(
        await conn.scalars(
            text("""
                SELECT id FROM users
                WHERE status = 'pending_deletion' AND deletion_due_at <= :now
                """),
            {"now": now},
        )
    )
    for user_id in ids:
        for statement in (
            "DELETE FROM verification_tokens WHERE user_id = :id",
            "DELETE FROM push_tokens WHERE user_id = :id",
            "DELETE FROM notifications WHERE user_id = :id",
            "DELETE FROM devices WHERE user_id = :id",
            "DELETE FROM sessions WHERE user_id = :id",
            "DELETE FROM user_roles WHERE user_id = :id",
        ):
            await conn.execute(text(statement), {"id": user_id})
        await conn.execute(
            text("UPDATE profiles SET display_name = NULL, updated_at = :now WHERE id = :id"),
            {"id": user_id, "now": now},
        )
        await conn.execute(
            text("""
                UPDATE users SET email = :email, password_hash = '!', status = 'deleted',
                    email_verified_at = NULL, updated_at = :now WHERE id = :id
                """),
            {"email": f"deleted-{user_id}@invalid", "id": user_id, "now": now},
        )
    return len(ids)


async def run_retention(settings: MaintenanceSettings) -> dict[str, int]:
    """Delete expired administrative data and reconcile abandoned quotas."""
    engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
    now = datetime.now(UTC)
    counts: dict[str, int] = {}
    receipts_cutoff = now - timedelta(hours=settings.receipt_retention_hours)
    notifications_cutoff = now - timedelta(days=settings.notification_retention_days)
    security_cutoff = now - timedelta(days=settings.security_retention_days)
    session_cutoff = now - timedelta(days=settings.session_retention_days)
    token_cutoff = now - timedelta(days=settings.token_retention_days)
    outbox_cutoff = now - timedelta(days=settings.outbox_retention_days)
    try:
        async with engine.begin() as conn:
            statements = {
                "receipts": (
                    "DELETE FROM operation_receipts WHERE created_at < :cutoff AND state = ANY(:states)",
                    {"cutoff": receipts_cutoff, "states": list(TERMINAL)},
                ),
                "reservations": (
                    "DELETE FROM usage_reservations WHERE finished_at < :cutoff",
                    {"cutoff": receipts_cutoff},
                ),
                "notifications": (
                    "DELETE FROM notifications WHERE created_at < :cutoff",
                    {"cutoff": notifications_cutoff},
                ),
                "security_events": (
                    "DELETE FROM security_events WHERE created_at < :cutoff",
                    {"cutoff": security_cutoff},
                ),
                "sessions": (
                    "DELETE FROM sessions WHERE revoked_at IS NOT NULL AND revoked_at < :cutoff",
                    {"cutoff": session_cutoff},
                ),
                "tokens": (
                    "DELETE FROM verification_tokens WHERE expires_at < :cutoff OR used_at < :cutoff",
                    {"cutoff": token_cutoff},
                ),
                "outbox": (
                    "DELETE FROM outbox_events WHERE state IN ('delivered', 'failed') AND created_at < :cutoff",
                    {"cutoff": outbox_cutoff},
                ),
            }
            for name, (statement, params) in statements.items():
                result = await conn.execute(text(statement), params)
                counts[name] = int(getattr(result, "rowcount", 0) or 0)
            counts["reservations_reconciled"] = await _reservations(conn, now)
            counts["accounts_purged"] = await _purge_accounts(conn, now)
    finally:
        await engine.dispose()
    return counts
