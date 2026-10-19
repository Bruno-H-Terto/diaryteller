"""Deliver verification and reset emails from Kafka events.

The recipient and the single-use token arrive encrypted with the shared email
key; this worker never reads another service's database.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from diary_messaging import EventEnvelope
from diary_security import TokenError, decrypt_json

from notifications.config.settings import Settings
from notifications.lib.email.client import EmailSender
from notifications.lib.email.templates import reset_email, verification_email

_logger = logging.getLogger(__name__)

EMAIL_TYPES = {"email.verification", "email.password_reset"}


class EmailDeliveryError(Exception):
    """The payload cannot produce a safe email."""


class EmailDelivery:
    """Decrypt and send one email event."""

    def __init__(self, settings: Settings, sender: EmailSender) -> None:
        self._settings = settings
        self._sender = sender

    async def send(self, event: EventEnvelope) -> None:
        """Send the email or raise so the consumer retries."""
        payload = event.payload
        try:
            recipient = str(
                decrypt_json(str(payload["recipient_ciphertext"]), self._settings.email_token_key)[
                    "email"
                ]
            )
            token = str(
                decrypt_json(str(payload["token_ciphertext"]), self._settings.email_token_key)[
                    "token"
                ]
            )
        except (TokenError, KeyError, TypeError, ValueError) as exc:
            raise EmailDeliveryError("invalid email payload") from exc
        if "@" not in recipient:
            raise EmailDeliveryError("invalid recipient")
        base = str(payload.get("link_base") or self._settings.email_link_base_url)
        if event.type == "email.verification":
            subject, body = verification_email(f"{base}{self._settings.verify_path}{quote(token)}")
        elif event.type == "email.password_reset":
            subject, body = reset_email(f"{base}{self._settings.reset_path}{quote(token)}")
        else:
            _logger.info("email_ignored", extra={"event": "email_ignored"})
            return
        await self._sender.send(recipient, subject, body)
        _logger.info("email_sent", extra={"event": "email_sent"})
