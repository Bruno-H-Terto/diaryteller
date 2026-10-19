"""Authorization and entitlement contracts exchanged with identity.

These models are transport contracts, not ORM entities. Identity computes every
field; callers must treat them as authoritative decisions.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Permission(StrEnum):
    """Permissions granted by roles and plans."""

    CONVERSATION_USE = "conversation:use"
    MEMORY_SEARCH = "memory:search"
    MEMORY_ORGANIZE = "memory:organize"
    MEMORY_TIMELINE = "memory:timeline"
    MEMORY_SUMMARIZE = "memory:summarize"
    SESSIONS_MANAGE = "sessions:manage"
    EXCHANGE_USE = "exchange:use"


class AccountStatus(StrEnum):
    """Account lifecycle states relevant to authorization."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_DELETION = "pending_deletion"


class UsageMetric(StrEnum):
    """Metered resources reserved before an external provider call."""

    AI_TOKENS = "ai_tokens"
    MEMORY_CALLS = "memory_calls"


class EntitlementView(BaseModel):
    """Materialized view returned by `/me/entitlements` and internal authorize."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    session_id: UUID
    account_status: AccountStatus
    plan_code: str
    plan_expires_at: datetime | None
    permissions: list[Permission]
    quotas: dict[UsageMetric, int]
    quota_remaining: dict[UsageMetric, int]
    source_version: int
    evaluated_at: datetime


class AuthorizeRequest(BaseModel):
    """Internal request: never trusted from the public edge."""

    model_config = ConfigDict(extra="forbid")

    permission: Permission
    operation_type: str | None = None


class AuthorizeDecision(BaseModel):
    """Internal authorization result with the current persisted state."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reason: str | None = None
    entitlement: EntitlementView
    request_id: str = Field(default="")
