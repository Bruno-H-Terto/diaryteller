"""JSON codec with strict envelope validation."""

from __future__ import annotations

import json

from .envelope import EventEnvelope


class EventInvalid(Exception):
    """The message is not a valid envelope; it must go to the DLQ."""


def encode(event: EventEnvelope) -> bytes:
    """Serialize deterministically for tests and brokers."""
    return event.model_dump_json().encode()


def decode(value: bytes) -> EventEnvelope:
    """Validate bytes into an envelope or raise `EventInvalid`."""
    try:
        payload = json.loads(value)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EventInvalid("event is not JSON") from exc
    if not isinstance(payload, dict):
        raise EventInvalid("event is not an object")
    try:
        return EventEnvelope.model_validate(payload)
    except ValueError as exc:
        raise EventInvalid("event does not match the envelope") from exc
