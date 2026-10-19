"""Rotate a refresh credential inside a row-locked transaction.

Reuse of a consumed credential revokes the family and session. If the rotation
response is lost, the client may need to authenticate again; this is documented
and deliberately not masked with unlimited reuse.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from diary_contracts.authorization import AccountStatus
from diary_contracts.errors import DomainError, ErrorCode

from identity.adapters.security.access_tokens import AccessTokenIssuer
from identity.adapters.security.refresh_tokens import new_refresh_token, refresh_digest
from identity.adapters.security.source_tokens import SourceTokenCodec
from identity.application.ports.accounts import AccountRepository
from identity.application.ports.notifications import SecurityRepository
from identity.application.ports.sessions import RefreshRepository, SessionRepository
from identity.domain.session import RefreshCredential

from .common import IssuedSession, utcnow


class RefreshReuseDetected(Exception):
    """Raised after the revocation side effects have been staged."""


def _invalid(message: str = "Session is no longer valid") -> DomainError:
    return DomainError(ErrorCode.SESSION_REVOKED, 401, message)


async def refresh_session(
    *,
    accounts: AccountRepository,
    sessions: SessionRepository,
    refresh: RefreshRepository,
    security: SecurityRepository,
    access_tokens: AccessTokenIssuer,
    source_tokens: SourceTokenCodec,
    refresh_ttl_days: int,
    refresh_token: str,
    session_id: uuid.UUID,
    device_id: uuid.UUID,
    source_version: int,
    now: datetime | None = None,
) -> IssuedSession:
    """Consume the presented credential and return a replacement bundle."""
    moment = now or utcnow()
    credential = await refresh.lock_by_digest(refresh_digest(refresh_token))
    if credential is None:
        raise _invalid()
    if credential.consumed_at is not None:
        await refresh.revoke_family(credential.family_id, moment)
        await sessions.revoke(credential.session_id, "refresh_reuse", moment)
        await security.record(
            user_id=None,
            session_id=credential.session_id,
            event_type="refresh.reuse_detected",
            reference=None,
            now=moment,
        )
        raise RefreshReuseDetected()
    if not credential.is_reusable(moment):
        raise _invalid("Refresh credential expired")
    session = await sessions.by_id(credential.session_id)
    if session is None or session.id != session_id:
        raise _invalid()
    if session.device_id != device_id or session.source_version != source_version:
        raise _invalid("Session source mismatch")
    if not session.is_active(moment):
        raise _invalid()
    user = await accounts.by_id(session.user_id)
    if user is None or user.status is not AccountStatus.ACTIVE:
        raise DomainError(ErrorCode.ACCOUNT_DISABLED, 403, "Account is not active")
    if user.email_verified_at is None:
        raise DomainError(ErrorCode.EMAIL_NOT_VERIFIED, 403, "Email verification is required")
    token, digest = new_refresh_token()
    replacement = RefreshCredential(
        id=uuid.uuid4(),
        session_id=session.id,
        family_id=credential.family_id,
        digest=digest,
        issued_at=moment,
        expires_at=min(session.expires_at, moment + timedelta(days=refresh_ttl_days)),
        consumed_at=None,
        replacement_id=None,
    )
    await refresh.create(replacement)
    await refresh.consume(credential.id, replacement.id, moment)
    new_version = await sessions.bump_source_version(session.id)
    await sessions.touch(session.id, moment)
    await security.record(
        user_id=user.id,
        session_id=session.id,
        event_type="refresh.rotated",
        reference=None,
        now=moment,
    )
    return IssuedSession(
        access_token=access_tokens.issue(user.id, session.id, moment),
        refresh_token=token,
        source=source_tokens.issue(session.id, device_id, new_version, moment),
        session_id=session.id,
    )
