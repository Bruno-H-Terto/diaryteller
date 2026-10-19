"""Envelope validation, codec strictness and topic naming."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from diary_messaging import EventEnvelope, dlq_topic
from diary_messaging.codec import EventInvalid, decode, encode
from diary_messaging.topics import SESSION_EVENTS


def _envelope(**overrides) -> EventEnvelope:
    values = {
        "event_id": uuid.uuid4(),
        "type": "session.created",
        "producer": "api",
        "occurred_at": datetime.now(UTC),
        "key": "user-1",
        "payload": {"user_id": "user-1"},
    }
    values.update(overrides)
    return EventEnvelope(**values)


def test_round_trip_preserves_the_envelope() -> None:
    event = _envelope()
    assert decode(encode(event)) == event


@pytest.mark.parametrize("event_type", ["Session.Created", "session", "session..created", "-bad"])
def test_invalid_event_types_are_rejected(event_type: str) -> None:
    with pytest.raises(ValueError):
        _envelope(type=event_type)


@pytest.mark.parametrize("payload", [b"not-json", b"[]", b'{"event_id":"x"}'])
def test_invalid_messages_raise_event_invalid(payload: bytes) -> None:
    with pytest.raises(EventInvalid):
        decode(payload)


def test_extra_fields_are_rejected() -> None:
    body = encode(_envelope())
    with pytest.raises(EventInvalid):
        decode(body.replace(b'"producer"', b'"unknown":1,"producer"'))


def test_dlq_topic_is_derived() -> None:
    assert dlq_topic(SESSION_EVENTS) == f"{SESSION_EVENTS}.dlq"
