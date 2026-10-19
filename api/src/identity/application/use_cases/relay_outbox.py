"""Publish transactional outbox rows as Kafka events."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from diary_messaging import EventEnvelope, EventPublisher
from diary_messaging.kafka import BrokerUnavailable

from identity.application.ports.outbox import OutboxRelayRepository


def envelope_for(row: dict[str, Any]) -> EventEnvelope:
    """Build the envelope from the stored row without exposing diary content."""
    payload = row.get("payload") or {}
    key = str(payload.get("user_id") or row["id"])
    return EventEnvelope(
        event_id=row["id"],
        type=str(row["event_type"]),
        producer="api",
        occurred_at=row["created_at"],
        key=key,
        payload=payload,
    )


async def relay_batch(
    *,
    repo: OutboxRelayRepository,
    publisher: EventPublisher,
    worker_id: str,
    batch_size: int,
    lease_seconds: int,
    max_attempts: int,
    now: datetime,
) -> int:
    """Publish one claimed batch, acknowledging or rescheduling each row."""
    rows = await repo.claim(batch_size, lease_seconds, worker_id)
    published = 0
    for row in rows:
        topic = str(row["topic"])
        try:
            event = envelope_for(row)
            await publisher.publish(topic, event)
        except (BrokerUnavailable, ValueError) as exc:
            await repo.retry(row["id"], int(row["attempts"]), max_attempts, type(exc).__name__)
        else:
            await repo.published(row["id"], now)
            published += 1
    return published


def worker_name(prefix: str = "outbox-relay") -> str:
    """Unique lease owner for one relay process."""
    return f"{prefix}-{uuid.uuid4()}"
