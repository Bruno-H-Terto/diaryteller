"""FCM HTTP v1 adapter and an explicit development logger."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

_logger = logging.getLogger(__name__)


class FcmPushClient:
    """Send generic administrative notifications through FCM."""

    def __init__(self, project_id: str, service_account_json: str, timeout: float) -> None:
        self._project = project_id
        self._timeout = timeout
        self._credentials = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json),
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )

    def _send_sync(self, token: str, title: str, body: str) -> str:
        session = AuthorizedSession(self._credentials)
        try:
            response = session.post(
                f"https://fcm.googleapis.com/v1/projects/{self._project}/messages:send",
                json={
                    "message": {
                        "token": token,
                        "notification": {"title": title, "body": body},
                        "data": {"kind": "session_alert"},
                        "android": {"priority": "high"},
                    }
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            return str(response.json().get("name", ""))
        finally:
            session.close()

    async def send(self, token: str, title: str, body: str, data: dict[str, str]) -> str:
        """Send one message off the event loop."""
        return await asyncio.to_thread(self._send_sync, token, title, body)


class DevPushClient:
    """Log that a push would be sent, without token or diary content."""

    async def send(self, token: str, title: str, body: str, data: dict[str, str]) -> str:
        """Return a synthetic identifier."""
        _logger.info("push_dev", extra={"channel": "push", "event": "push_dev"})
        return "dev-message"


def build_push_client(settings) -> Any:
    """Select FCM or the development logger."""
    if settings.push_provider == "fcm":
        return FcmPushClient(
            settings.fcm_project_id,
            settings.fcm_service_account_json,
            settings.push_timeout_seconds,
        )
    return DevPushClient()
