"""Versioned event envelopes and Kafka adapters."""

from .envelope import EventEnvelope
from .ports import EventHandler, EventPublisher, ProcessedEventStore
from .topics import DLQ_SUFFIX, EMAIL_EVENTS, SESSION_EVENTS, dlq_topic

__all__ = [
    "DLQ_SUFFIX",
    "EMAIL_EVENTS",
    "SESSION_EVENTS",
    "EventEnvelope",
    "EventHandler",
    "EventPublisher",
    "ProcessedEventStore",
    "dlq_topic",
]
