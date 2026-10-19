"""Route one event to the notification channel that owns it."""

from __future__ import annotations

import logging

from diary_messaging import EventEnvelope

from .email_delivery import EMAIL_TYPES, EmailDelivery
from .session_alerts import SessionAlerts

_logger = logging.getLogger(__name__)


class EventRouter:
    """Only known event types are delivered; the rest are ignored."""

    def __init__(self, email: EmailDelivery, sessions: SessionAlerts) -> None:
        self._email = email
        self._sessions = sessions

    async def handle(self, event: EventEnvelope) -> None:
        """Dispatch by event type."""
        if event.type == "session.created":
            await self._sessions.send(event)
            return
        if event.type in EMAIL_TYPES:
            await self._email.send(event)
            return
        _logger.info("event_ignored", extra={"event": "event_ignored"})
