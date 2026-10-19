"""Simple single-process scheduler with advisory locks.

Production can replace this loop by an external scheduler invoking the same CLI
commands; both paths share the lock semantics.
"""

from __future__ import annotations

import asyncio
import contextlib

from diary_observability import MongoLogSink
from sqlalchemy.ext.asyncio import create_async_engine

from maintenance.backup_mongo import backup_mongo
from maintenance.backup_postgres import backup_postgres
from maintenance.billing_reconcile import reconcile
from maintenance.leases import job_lock
from maintenance.restore_check import verify_latest
from maintenance.retention import run_retention
from maintenance.settings import MaintenanceSettings


async def _guarded(engine, settings: MaintenanceSettings, name: str, job, sink) -> None:
    async with job_lock(engine, f"maintenance:{name}") as acquired:
        if not acquired:
            return
        try:
            await job(settings)
        except Exception as exc:
            sink.emit({"event": "job_failed", "error_code": type(exc).__name__[:48]})


async def run_scheduler(settings: MaintenanceSettings) -> str:
    """Run retention, reconciliation and backups on a fixed interval."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sink = MongoLogSink(
        url=settings.mongo_url,
        database=settings.mongo_db,
        service="maintenance",
        environment=settings.app_env,
        buffer_size=200,
    )
    await sink.start()
    cycle = 0
    try:
        while True:
            await _guarded(engine, settings, "retention", run_retention, sink)
            await _guarded(engine, settings, "reconcile", reconcile, sink)
            await _guarded(engine, settings, "backup-postgres", backup_postgres, sink)
            await _guarded(engine, settings, "backup-mongo", backup_mongo, sink)
            if cycle % 7 == 0:
                await _guarded(engine, settings, "restore-check", verify_latest, sink)
            cycle += 1
            sink.emit({"event": "scheduler_cycle", "value": cycle})
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.sleep(settings.scheduler_interval_seconds)
    finally:
        await engine.dispose()
        await sink.close()
