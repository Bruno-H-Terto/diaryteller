"""Notification, outbox and security persistence aliases."""

from __future__ import annotations

from ..notification_repository import (
    PostgresNotificationRepository,
    PostgresVerificationRepository,
)
from ..outbox_repository import PostgresOutboxRepository
from ..push_repository import PostgresPushRepository
from ..security_repository import PostgresSecurityRepository

NotificationRepository = PostgresNotificationRepository
VerificationTokenRepository = PostgresVerificationRepository
OutboxRepository = PostgresOutboxRepository
PushTokenRepository = PostgresPushRepository
SecurityRepository = PostgresSecurityRepository
