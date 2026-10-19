"""Concrete account, device and throttle persistence types."""

from __future__ import annotations

from ..account_repository import PostgresAccountRepository
from ..device_repository import PostgresDeviceRepository
from ..errors import DeviceConflict
from ..throttle_repository import PostgresThrottleRepository

AccountRepository = PostgresAccountRepository
DeviceRepository = PostgresDeviceRepository
ThrottleRepository = PostgresThrottleRepository

__all__ = [
    "AccountRepository",
    "DeviceConflict",
    "DeviceRepository",
    "ThrottleRepository",
]
