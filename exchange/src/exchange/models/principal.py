"""Validated caller identity shared by controllers and services."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from diary_contracts.authorization import AccountStatus


@dataclass(frozen=True, slots=True)
class Principal:
    """Validated caller identity and effective plan."""

    user_id: UUID
    session_id: UUID
    account_status: AccountStatus
    plan_code: str
