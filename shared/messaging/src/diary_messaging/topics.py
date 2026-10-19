"""Topic names owned by the public API and consumed by neighbors."""

from __future__ import annotations

SESSION_EVENTS = "diary.identity.sessions.v1"
EMAIL_EVENTS = "diary.identity.emails.v1"
ACCOUNT_EVENTS = "diary.identity.accounts.v1"
MAINTENANCE_EVENTS = "diary.maintenance.lifecycle.v1"

DLQ_SUFFIX = ".dlq"

PUBLISHED_TOPICS = (
    SESSION_EVENTS,
    EMAIL_EVENTS,
    ACCOUNT_EVENTS,
    MAINTENANCE_EVENTS,
)


def dlq_topic(topic: str) -> str:
    """Dead-letter topic for one source topic."""
    return f"{topic}{DLQ_SUFFIX}"
