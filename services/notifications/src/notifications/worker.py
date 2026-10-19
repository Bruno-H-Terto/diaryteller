"""Kafka consumer that delivers notifications without touching other databases."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal

from diary_messaging import EMAIL_EVENTS, SESSION_EVENTS
from diary_messaging.consumer import KafkaEventConsumer
from diary_messaging.kafka import KafkaEventPublisher
from diary_observability import MongoLogSink, configure_logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from notifications.adapters.email.client import EmailSender
from notifications.adapters.postgres.engine import build_engine, build_session_factory
from notifications.adapters.postgres.inbox import PostgresInbox
from notifications.adapters.push.client import build_push_client
from notifications.application.handlers.email_delivery import EmailDelivery
from notifications.application.handlers.router import EventRouter
from notifications.application.handlers.session_alerts import SessionAlerts
from notifications.settings import Settings, get_settings

_logger = logging.getLogger(__name__)


class SessionInbox:
    """Inbox adapter that opens one session per check."""

    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory

    async def seen(self, consumer: str, event_id) -> bool:  # type: ignore[no-untyped-def]
        async with self._factory() as session:
            return await PostgresInbox(session).seen(consumer, event_id)

    async def mark(self, consumer: str, event_id, topic: str) -> None:  # type: ignore[no-untyped-def]
        async with self._factory() as session:
            await PostgresInbox(session).mark(consumer, event_id, topic)


async def run(settings: Settings | None = None) -> None:
    """Consume until SIGTERM/SIGINT."""
    settings = settings or get_settings()
    configure_logging("notifications", settings.service_version)
    sink = MongoLogSink(
        url=settings.mongo_url,
        database=settings.mongo_db,
        service="notifications",
        environment=settings.app_env,
        buffer_size=settings.mongo_log_buffer,
    )
    engine = build_engine(
        settings.notifications_database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    factory = build_session_factory(engine)
    publisher = KafkaEventPublisher(settings.kafka_bootstrap_servers, "diary-notifications-dlq")
    handler = EventRouter(
        EmailDelivery(settings, EmailSender(settings)),
        SessionAlerts(settings, build_push_client(settings)),
    )
    consumer = KafkaEventConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        client_id=settings.kafka_client_id,
        topics=(SESSION_EVENTS, EMAIL_EVENTS),
        handler=handler,
        inbox=SessionInbox(factory),
        dlq=publisher,
        max_attempts=settings.kafka_retry_attempts,
        retry_base_seconds=settings.kafka_retry_base_seconds,
    )
    await sink.start()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(signal_name, stop.set)
    try:
        await consumer.run(stop)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        _logger.error(
            "consumer_error", extra={"event": "consumer_error", "error_code": type(exc).__name__}
        )
        raise
    finally:
        await publisher.close()
        await engine.dispose()
        await sink.close()


def main() -> None:
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
