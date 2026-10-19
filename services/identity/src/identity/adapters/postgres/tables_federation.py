"""Federated identities and one-time OIDC transactions.

Only hashes of state/nonce are stored. Provider tokens and authorization codes
are never persisted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .engine import Base


class FederatedIdentityTable(Base):
    """External identity linked to one account, unique per issuer and subject."""

    __tablename__ = "federated_identities"
    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_federation_issuer_subject"),
        Index("ix_federation_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    issuer: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(64))
    email_at_link: Mapped[str | None] = mapped_column(String(320))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OidcTransactionTable(Base):
    """Short-lived authorization-code transaction; state/nonce stored as hashes."""

    __tablename__ = "oidc_transactions"
    __table_args__ = (Index("ix_oidc_transactions_expiry", "expires_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    state_hash: Mapped[str] = mapped_column(String(64), unique=True)
    nonce_hash: Mapped[str] = mapped_column(String(64))
    redirect_uri: Mapped[str] = mapped_column(String(500))
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    code_challenge: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
