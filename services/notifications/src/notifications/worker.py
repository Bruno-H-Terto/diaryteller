"""Outbox worker loop with leases, retries and graceful shutdown."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import uuid

from diary_observability import MongoLogSink, configure_logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from notifications.adapters.email.client import EmailSender
from notifications.adapters.postgres.outbox import OutboxRepository
from notifications.adapters.push.client import build_push_client
from notifications.application.dispatch import Dispatcher
from notifications.settings import Settings, get_settings

_logger = logging.getLogger(__name__)


async def dispatch_batch(
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    log_sink: MongoLogSink,
    stop: asyncio.Event,
) -> int:
    """Claim and deliver one batch with fresh sessions around network calls."""
    worker_id = f"notifications-{uuid.uuid4()}"
    push = build_push_client(settings)
    email = EmailSender(settings)
    async with factory() as session:
        events = await OutboxRepository(session).claim(
            settings.batch_size, settings.lease_seconds, worker_id
        )
    for event in events:
        if stop.is_set():
            break
        async with factory() as session:
            repo = OutboxRepository(session)
            dispatcher = Dispatcher(settings, email, push, repo)
            try:
                await dispatcher.dispatch(event)
            except Exception as exc:
                code = getattr(exc, "code", "delivery_failed")
                attempts = int(event["attempts"])
                if str(code).startswith("invalid_"):
                    attempts = settings.max_attempts
                await repo.retry(event["id"], attempts, settings.max_attempts, str(code))
                log_sink.emit(
                    {"event": "outbox_retry", "attempt": int(event["attempts"]), "error_code": code}
                )
            else:
                await repo.delivered(event["id"])
                log_sink.emit({"event": "outbox_delivered", "attempt": int(event["attempts"])})
    return len(events)


async def run(settings: Settings | None = None) -> None:
    """Run until SIGTERM/SIGINT, sleeping when the queue is idle."""
    settings = settings or get_settings()
    configure_logging("notifications", settings.service_version)
    sink = MongoLogSink(
        url=settings.mongo_url,
        database=settings.mongo_db,
        service="notifications",
        environment=settings.app_env,
        buffer_size=settings.mongo_log_buffer,
    )
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    await sink.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signal_name, stop.set)
    try:
        while not stop.is_set():
            try:
                count = await dispatch_batch(factory, settings, sink, stop)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.error(
                    "worker_error",
                    extra={"error_code": type(exc).__name__[:48], "event": "worker_error"},
                )
                count = 0
            if count == 0:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=settings.poll_seconds)
    finally:
        await engine.dispose()
        await sink.close()


def main() -> None:
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
