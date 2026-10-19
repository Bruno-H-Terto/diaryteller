"""Outbox relay builds envelopes and settles rows exactly once."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from diary_messaging import EventEnvelope
from diary_messaging.kafka import BrokerUnavailable
from identity.application.use_cases.relay_outbox import envelope_for, relay_batch


class FakeRepo:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.published_ids: list[uuid.UUID] = []
        self.retried: list[tuple[uuid.UUID, str]] = []

    async def claim(self, batch: int, lease_seconds: int, worker: str) -> list[dict[str, Any]]:
        return self.rows

    async def published(self, event_id: uuid.UUID, now: datetime | None = None) -> None:
        self.published_ids.append(event_id)

    async def retry(self, event_id: uuid.UUID, attempts: int, max_attempts: int, code: str) -> None:
        self.retried.append((event_id, code))


class FakePublisher:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, EventEnvelope]] = []

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        if self.fail:
            raise BrokerUnavailable("down")
        self.sent.append((topic, event))

    async def close(self) -> None:
        return None


def _row(**overrides: Any) -> dict[str, Any]:
    row = {
        "id": uuid.uuid4(),
        "event_type": "session.created",
        "payload": {"user_id": "user-1", "session_id": "s-1"},
        "attempts": 1,
        "created_at": datetime.now(UTC),
        "topic": "diary.identity.sessions.v1",
    }
    row.update(overrides)
    return row


def test_envelope_keeps_event_id_and_partitions_by_user() -> None:
    row = _row()
    event = envelope_for(row)
    assert event.event_id == row["id"]
    assert event.key == "user-1"
    assert event.producer == "api"
    assert event.type == "session.created"


async def test_batch_marks_published_rows() -> None:
    row = _row()
    repo = FakeRepo([row])
    publisher = FakePublisher()
    count = await relay_batch(
        repo=repo,
        publisher=publisher,
        worker_id="relay-1",
        batch_size=10,
        lease_seconds=30,
        max_attempts=5,
        now=datetime.now(UTC),
    )
    assert count == 1
    assert repo.published_ids == [row["id"]]
    assert publisher.sent[0][0] == row["topic"]


async def test_broker_failure_reschedules_instead_of_losing() -> None:
    row = _row(attempts=3)
    repo = FakeRepo([row])
    count = await relay_batch(
        repo=repo,
        publisher=FakePublisher(fail=True),
        worker_id="relay-1",
        batch_size=10,
        lease_seconds=30,
        max_attempts=5,
        now=datetime.now(UTC),
    )
    assert count == 0
    assert repo.published_ids == []
    assert repo.retried == [(row["id"], "BrokerUnavailable")]
