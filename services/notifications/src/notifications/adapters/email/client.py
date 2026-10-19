"""SMTP delivery for transactional email without logging secrets."""

from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from notifications.settings import Settings


class EmailSender:
    """Send UTF-8 plain-text transactional email through configured SMTP."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(self, recipient: str, subject: str, body: str) -> None:
        """Send one message; raises on transport failure for retry."""
        message = EmailMessage()
        message["From"] = self._settings.smtp_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body, charset="utf-8")
        await aiosmtplib.send(
            message,
            sender=self._settings.smtp_from,
            recipients=[recipient],
            hostname=self._settings.smtp_host,
            port=self._settings.smtp_port,
            username=self._settings.smtp_user or None,
            password=self._settings.smtp_password or None,
            start_tls=self._settings.smtp_starttls,
            timeout=self._settings.smtp_timeout_seconds,
        )
