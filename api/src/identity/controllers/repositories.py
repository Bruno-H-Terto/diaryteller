"""Construct all request-scoped repositories over one AsyncSession."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.account_repository import PostgresAccountRepository
from identity.models.billing_event_repository import PostgresBillingEventRepository
from identity.models.device_repository import PostgresDeviceRepository
from identity.models.federation_repository import PostgresFederationRepository
from identity.models.notification_repository import (
    PostgresNotificationRepository,
    PostgresVerificationRepository,
)
from identity.models.operation_control_repository import (
    PostgresOperationControlRepository,
)
from identity.models.operation_repository import PostgresOperationRepository
from identity.models.outbox_repository import PostgresOutboxRepository
from identity.models.permission_repository import PostgresPlanRepository
from identity.models.push_repository import PostgresPushRepository
from identity.models.refresh_repository import PostgresRefreshRepository
from identity.models.security_repository import PostgresSecurityRepository
from identity.models.session_repository import PostgresSessionRepository
from identity.models.subscription_repository import (
    PostgresSubscriptionRepository,
)
from identity.models.throttle_repository import PostgresThrottleRepository
from identity.models.upload_quota_gauge_repository import (
    PostgresUploadQuotaGaugeRepository,
)
from identity.models.upload_quota_repository import PostgresUploadQuotaRepository
from identity.models.usage_repository import PostgresUsageRepository


@dataclass(slots=True)
class Repositories:
    """Bundle of repositories sharing the request transaction."""

    accounts: PostgresAccountRepository
    devices: PostgresDeviceRepository
    sessions: PostgresSessionRepository
    refresh: PostgresRefreshRepository
    plans: PostgresPlanRepository
    subscriptions: PostgresSubscriptionRepository
    usage: PostgresUsageRepository
    operations: PostgresOperationRepository
    control: PostgresOperationControlRepository
    outbox: PostgresOutboxRepository
    notifications: PostgresNotificationRepository
    verifications: PostgresVerificationRepository
    push: PostgresPushRepository
    security: PostgresSecurityRepository
    billing_events: PostgresBillingEventRepository
    throttles: PostgresThrottleRepository
    federation: PostgresFederationRepository
    upload_quota: PostgresUploadQuotaRepository
    upload_gauges: PostgresUploadQuotaGaugeRepository


def build_repositories(session: AsyncSession) -> Repositories:
    """Create the bundle; no I/O happens here."""
    return Repositories(
        accounts=PostgresAccountRepository(session),
        devices=PostgresDeviceRepository(session),
        sessions=PostgresSessionRepository(session),
        refresh=PostgresRefreshRepository(session),
        plans=PostgresPlanRepository(session),
        subscriptions=PostgresSubscriptionRepository(session),
        usage=PostgresUsageRepository(session),
        operations=PostgresOperationRepository(session),
        control=PostgresOperationControlRepository(session),
        outbox=PostgresOutboxRepository(session),
        notifications=PostgresNotificationRepository(session),
        verifications=PostgresVerificationRepository(session),
        push=PostgresPushRepository(session),
        security=PostgresSecurityRepository(session),
        billing_events=PostgresBillingEventRepository(session),
        throttles=PostgresThrottleRepository(session),
        federation=PostgresFederationRepository(session),
        upload_quota=PostgresUploadQuotaRepository(session),
        upload_gauges=PostgresUploadQuotaGaugeRepository(session),
    )
