"""At-least-once consumer loop with inbox dedupe and a dead-letter topic."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord, OffsetAndMetadata

from .codec import EventInvalid, decode
from .envelope import EventEnvelope
from .ports import EventHandler, EventPublisher, ProcessedEventStore
from .topics import dlq_topic

_logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    """Consume topics in one group, commit after handling, DLQ poison events."""

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        group_id: str,
        client_id: str,
        topics: Sequence[str],
        handler: EventHandler,
        inbox: ProcessedEventStore | None = None,
        dlq: EventPublisher | None = None,
        max_attempts: int = 5,
        retry_base_seconds: float = 0.5,
    ) -> None:
        self._bootstrap = bootstrap_servers
        self._group_id = group_id
        self._client_id = client_id
        self._topics = list(topics)
        self._handler = handler
        self._inbox = inbox
        self._dlq = dlq
        self._max_attempts = max_attempts
        self._retry_base = retry_base_seconds

    async def run(self, stop: asyncio.Event) -> None:
        """Consume until `stop` is set, then commit and close."""
        consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap,
            group_id=self._group_id,
            client_id=self._client_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await consumer.start()
        try:
            while not stop.is_set():
                batches = await consumer.getmany(timeout_ms=1000)
                for partition, records in batches.items():
                    if not records:
                        continue
                    for record in records:
                        await self._process(record)
                    await consumer.commit(
                        {partition: OffsetAndMetadata(records[-1].offset + 1, "")}
                    )
        finally:
            await consumer.stop()

    async def _process(self, record: ConsumerRecord) -> None:
        if record.value is None:
            await self._to_dlq(record.topic, record, "empty_event")
            return
        try:
            event = decode(record.value)
        except EventInvalid:
            await self._to_dlq(record.topic, record, "invalid_envelope")
            return
        if self._inbox is not None and await self._inbox.seen(self._group_id, event.event_id):
            _logger.info("event_duplicate", extra={"event": "event_duplicate"})
            return
        for attempt in range(1, self._max_attempts + 1):
            try:
                await self._handler.handle(event)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _logger.warning(
                    "event_failed",
                    extra={
                        "event": "event_failed",
                        "attempt": attempt,
                        "error_code": type(exc).__name__[:48],
                    },
                )
                if attempt == self._max_attempts:
                    await self._to_dlq(record.topic, record, "handler_failed")
                    return
                await asyncio.sleep(min(30.0, self._retry_base * 2 ** (attempt - 1)))
            else:
                if self._inbox is not None:
                    await self._inbox.mark(self._group_id, event.event_id, record.topic)
                return

    async def _to_dlq(self, topic: str, record: ConsumerRecord, reason: str) -> None:
        _logger.error("event_dead_letter", extra={"event": "event_dead_letter", "reason": reason})
        if self._dlq is None:
            return
        envelope = _envelope_or_placeholder(record, reason)
        await self._dlq.publish(dlq_topic(topic), envelope)


def _envelope_or_placeholder(record: ConsumerRecord, reason: str) -> EventEnvelope:
    from datetime import UTC, datetime
    from uuid import uuid4

    try:
        if record.value is None:
            raise EventInvalid("empty event")
        return decode(record.value)
    except EventInvalid:
        return EventEnvelope(
            event_id=uuid4(),
            type="dead_letter.invalid",
            producer="broker",
            occurred_at=datetime.now(UTC),
            key=str(record.key or "unknown"),
            payload={"reason": reason, "topic": record.topic, "offset": record.offset},
        )
