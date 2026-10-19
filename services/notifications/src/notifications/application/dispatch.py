"""Dispatch outbox events to email and push without diary content."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote
from uuid import UUID

from diary_security import TokenError, decrypt_json, sha256_digest

from notifications.adapters.email.templates import reset_email, verification_email
from notifications.settings import Settings

_logger = logging.getLogger(__name__)


class DispatchError(Exception):
    """Delivery failed and may be retried safely."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class Dispatcher:
    """Event-type-specific delivery with sanitized logs."""

    def __init__(self, settings: Settings, email_sender, push_client, repo) -> None:
        self._settings = settings
        self._email = email_sender
        self._push = push_client
        self._repo = repo

    async def dispatch(self, event: dict[str, Any]) -> None:
        """Deliver one claimed event."""
        kind = str(event["event_type"])
        payload = event["payload"]
        if kind in {"email.verification", "email.password_reset"}:
            await self._send_email(kind, payload)
        elif kind == "session.new":
            await self._send_session_alert(payload)
        else:
            _logger.info("outbox_ignored", extra={"event": "outbox_ignored"})

    async def _send_email(self, kind: str, payload: dict[str, Any]) -> None:
        try:
            user_id = UUID(str(payload["user_id"]))
            token = decrypt_json(str(payload["token_ciphertext"]), self._settings.email_token_key)[
                "token"
            ]
        except (TokenError, KeyError, ValueError) as exc:
            raise DispatchError("invalid_email_payload") from exc
        recipient = await self._repo.user_email(user_id)
        if not recipient or recipient.startswith("deleted-"):
            _logger.info("email_skipped", extra={"channel": "email", "event": "email_skipped"})
            return
        if kind == "email.verification":
            link = f"{self._settings.email_link_base_url}{self._settings.verify_path}{quote(token)}"
            subject, body = verification_email(link)
        else:
            link = f"{self._settings.email_link_base_url}{self._settings.reset_path}{quote(token)}"
            subject, body = reset_email(link)
        await self._email.send(recipient, subject, body)
        await self._repo.clear_email_secret(sha256_digest(token))

    async def _send_session_alert(self, payload: dict[str, Any]) -> None:
        try:
            user_id = UUID(str(payload["user_id"]))
            current_device = str(payload["device_id"])
        except (KeyError, ValueError) as exc:
            raise DispatchError("invalid_session_payload") from exc
        tokens = await self._repo.push_tokens(user_id)
        for row in tokens:
            if str(row["device_id"]) == current_device:
                continue
            try:
                token = decrypt_json(str(row["token_ciphertext"]), self._settings.push_token_key)[
                    "token"
                ]
            except (TokenError, KeyError, TypeError):
                continue
            try:
                await self._push.send(
                    str(token),
                    "Novo acesso",
                    "Uma nova sessão foi iniciada. Se não foi você, revogue-a no aplicativo.",
                    {"kind": "session_alert"},
                )
            except Exception as exc:
                _logger.warning(
                    "push_failed",
                    extra={
                        "channel": "push",
                        "event": "push_failed",
                        "error_code": str(exc)[:32],
                    },
                )
        _logger.info(
            "session_alert_dispatched",
            extra={"channel": "push", "event": "session_alert"},
        )
