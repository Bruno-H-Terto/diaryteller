"""Typing aliases for the concrete persistence used by services."""

from .accounts import AccountRepository, DeviceConflict, DeviceRepository, ThrottleRepository
from .billing import BillingEventRepository, BillingProvider, StoreEvent, StoreEventType
from .federation import FederationRepository
from .notifications import (
    NotificationRepository,
    OutboxRepository,
    PushTokenRepository,
    SecurityRepository,
    VerificationTokenRepository,
)
from .operation import OperationControlRepository, OperationRepository
from .outbox import OutboxRelayRepository
from .sessions import RefreshRepository, SessionRepository
from .subscription import PlanRepository, SubscriptionRepository, UsageRepository
from .upload_quota import UploadQuotaGaugeRepository, UploadQuotaRepository

__all__ = [
    "AccountRepository",
    "BillingEventRepository",
    "BillingProvider",
    "DeviceConflict",
    "DeviceRepository",
    "FederationRepository",
    "NotificationRepository",
    "OperationControlRepository",
    "OperationRepository",
    "OutboxRelayRepository",
    "OutboxRepository",
    "PlanRepository",
    "PushTokenRepository",
    "RefreshRepository",
    "SecurityRepository",
    "SessionRepository",
    "StoreEvent",
    "StoreEventType",
    "SubscriptionRepository",
    "ThrottleRepository",
    "UploadQuotaGaugeRepository",
    "UploadQuotaRepository",
    "UsageRepository",
    "VerificationTokenRepository",
]
