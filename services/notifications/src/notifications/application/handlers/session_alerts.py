"""Send session alerts to the user's other devices from a Kafka event."""

from __future__ import annotations

import logging
from typing import Protocol

from diary_messaging import EventEnvelope
from diary_security import TokenError, decrypt_json
from notifications.settings import Settings

_logger = logging.getLogger(__name__)


class PushSender(Protocol):
    """Minimal push contract used by the handler."""

    async def send(self, token: str, title: str, body: str, data: dict[str, str]) -> None:
        """Send one administrative notification."""
        ...


class SessionAlerts:
    """Fan out one alert to every registered device except the current one."""

    def __init__(self, settings: Settings, push: PushSender) -> None:
        self._settings = settings
        self._push = push

    async def send(self, event: EventEnvelope) -> None:
        """Deliver alerts; a broken token never blocks the others."""
        current = str(event.payload.get("device_id") or "")
        recipients = event.payload.get("recipients") or []
        sent = 0
        for recipient in recipients:
            if not isinstance(recipient, dict):
                continue
            if str(recipient.get("device_id") or "") == current:
                continue
            try:
                token = str(
                    decrypt_json(str(recipient["token_ciphertext"]), self._settings.push_token_key)[
                        "token"
                    ]
                )
            except (TokenError, KeyError, TypeError, ValueError):
                continue
            try:
                await self._push.send(
                    token,
                    "Novo acesso",
                    "Uma nova sessão foi iniciada. Se não foi você, revogue-a no aplicativo.",
                    {"kind": "session_alert"},
                )
            except Exception as exc:
                _logger.warning(
                    "push_failed",
                    extra={"event": "push_failed", "error_code": type(exc).__name__[:32]},
                )
            else:
                sent += 1
        _logger.info("session_alert_dispatched", extra={"event": "session_alert", "sent": sent})
