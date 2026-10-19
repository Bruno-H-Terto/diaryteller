"""Publish transactional outbox rows to Kafka until shutdown."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal

from diary_messaging.kafka import KafkaEventPublisher
from diary_observability import MongoLogSink, configure_logging
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from identity.adapters.postgres.outbox_relay_repository import PostgresOutboxRelayRepository
from identity.application.use_cases.common import utcnow
from identity.application.use_cases.relay_outbox import relay_batch, worker_name
from identity.settings import Settings, get_settings

_logger = logging.getLogger(__name__)


async def run(settings: Settings | None = None) -> None:
    """Relay until SIGTERM/SIGINT."""
    settings = settings or get_settings()
    configure_logging("identity-relay", settings.service_version)
    sink = MongoLogSink(
        url=settings.mongo_url,
        database=settings.mongo_db,
        service="identity-relay",
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
    publisher = KafkaEventPublisher(settings.kafka_bootstrap_servers, settings.kafka_client_id)
    await sink.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signal_name, stop.set)
    worker = worker_name()
    try:
        while not stop.is_set():
            try:
                async with factory() as session:
                    count = await relay_batch(
                        repo=PostgresOutboxRelayRepository(session),
                        publisher=publisher,
                        worker_id=worker,
                        batch_size=settings.relay_batch_size,
                        lease_seconds=settings.relay_lease_seconds,
                        max_attempts=settings.relay_max_attempts,
                        now=utcnow(),
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.error(
                    "relay_error",
                    extra={"event": "relay_error", "error_code": type(exc).__name__[:48]},
                )
                count = 0
            sink.emit({"event": "outbox_relayed", "count": count})
            if count == 0:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=settings.relay_poll_seconds)
    finally:
        await publisher.close()
        await engine.dispose()
        await sink.close()


def main() -> None:
    """Entry point for the compose relay service."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
