"""Ports the API and neighbors depend on, independent of Kafka."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .envelope import EventEnvelope


class EventPublisher(Protocol):
    """Publish an envelope to a topic."""

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        """Publish and wait for the broker acknowledgement."""
        ...

    async def close(self) -> None:
        """Flush and release the producer."""
        ...


class EventHandler(Protocol):
    """Handle one event; raising schedules a retry."""

    async def handle(self, event: EventEnvelope) -> None:
        """Process an event idempotently."""
        ...


class ProcessedEventStore(Protocol):
    """Inbox used to make at-least-once delivery safe."""

    async def seen(self, consumer: str, event_id: UUID) -> bool:
        """Whether this consumer already processed the event."""
        ...

    async def mark(self, consumer: str, event_id: UUID, topic: str) -> None:
        """Record the event as processed."""
        ...
