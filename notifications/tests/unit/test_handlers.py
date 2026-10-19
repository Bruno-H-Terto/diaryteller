"""Notification handlers are event-driven and never read another database."""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from diary_messaging import EventEnvelope
from diary_security import encrypt_json
from notifications.config.settings import Settings
from notifications.services.email_delivery import (
    EmailDelivery,
    EmailDeliveryError,
)
from notifications.services.session_alerts import SessionAlerts

KEY = base64.urlsafe_b64encode(b"n" * 32).decode()


class FakeEmail:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, recipient: str, subject: str, body: str) -> None:
        self.sent.append((recipient, subject, body))


class FakePush:
    def __init__(self) -> None:
        self.tokens: list[str] = []

    async def send(self, token: str, title: str, body: str, data: dict[str, str]) -> None:
        self.tokens.append(token)


def _settings() -> Settings:
    return Settings(email_token_key=KEY, push_token_key=KEY)


def _event(event_type: str, payload: dict[str, Any]) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid.uuid4(),
        type=event_type,
        producer="api",
        occurred_at=datetime.now(UTC),
        key="user-1",
        payload=payload,
    )


async def test_verification_email_is_built_from_encrypted_payload() -> None:
    sender = FakeEmail()
    handler = EmailDelivery(_settings(), sender)  # type: ignore[arg-type]
    event = _event(
        "email.verification",
        {
            "recipient_ciphertext": encrypt_json({"email": "user@example.com"}, KEY),
            "token_ciphertext": encrypt_json({"token": "tok-123"}, KEY),
            "link_base": "https://app.example",
        },
    )
    await handler.send(event)
    recipient, _subject, body = sender.sent[0]
    assert recipient == "user@example.com"
    assert "verify-email" in body or "confirmar" in body
    assert "tok-123" in body


async def test_reset_email_uses_the_reset_path() -> None:
    sender = FakeEmail()
    handler = EmailDelivery(_settings(), sender)  # type: ignore[arg-type]
    event = _event(
        "email.password_reset",
        {
            "recipient_ciphertext": encrypt_json({"email": "user@example.com"}, KEY),
            "token_ciphertext": encrypt_json({"token": "reset-1"}, KEY),
            "link_base": "https://app.example",
        },
    )
    await handler.send(event)
    assert "reset-password?token=reset-1" in sender.sent[0][2]


async def test_invalid_payload_is_rejected() -> None:
    handler = EmailDelivery(_settings(), FakeEmail())  # type: ignore[arg-type]
    with pytest.raises(EmailDeliveryError):
        await handler.send(_event("email.verification", {"token_ciphertext": "x"}))


async def test_session_alert_skips_current_device_and_broken_tokens() -> None:
    push = FakePush()
    handler = SessionAlerts(_settings(), push)
    event = _event(
        "session.created",
        {
            "device_id": "device-1",
            "recipients": [
                {"device_id": "device-1", "token_ciphertext": encrypt_json({"token": "own"}, KEY)},
                {
                    "device_id": "device-2",
                    "token_ciphertext": encrypt_json({"token": "other"}, KEY),
                },
                {"device_id": "device-3", "token_ciphertext": "broken"},
            ],
        },
    )
    await handler.send(event)
    assert push.tokens == ["other"]
