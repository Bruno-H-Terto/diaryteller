"""aiokafka publisher used by the API outbox relay."""

from __future__ import annotations

import asyncio

from aiokafka import AIOKafkaProducer

from .codec import encode
from .envelope import EventEnvelope


class BrokerUnavailable(Exception):
    """The broker did not acknowledge the event."""


class KafkaEventPublisher:
    """Lazily started producer with per-message acknowledgement."""

    def __init__(self, bootstrap_servers: str, client_id: str) -> None:
        self._bootstrap = bootstrap_servers
        self._client_id = client_id
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Connect once; safe to call from every publish."""
        async with self._lock:
            if self._producer is not None:
                return
            producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap,
                client_id=self._client_id,
                acks="all",
                enable_idempotence=True,
            )
            await producer.start()
            self._producer = producer

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        """Publish and wait for the broker acknowledgement."""
        await self.start()
        assert self._producer is not None
        try:
            await self._producer.send_and_wait(
                topic,
                encode(event),
                key=event.key.encode(),
                headers=[("type", event.type.encode())],
            )
        except Exception as exc:
            raise BrokerUnavailable("broker did not acknowledge the event") from exc

    async def close(self) -> None:
        """Flush and release the producer."""
        async with self._lock:
            if self._producer is None:
                return
            await self._producer.stop()
            self._producer = None
