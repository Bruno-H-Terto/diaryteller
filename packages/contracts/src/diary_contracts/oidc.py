"""OIDC authorization-code + PKCE contracts for the mobile app.

Only the backend talks to the provider token endpoint. The app opens an external
browser and returns code, state and verifier.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OidcStartRequest(BaseModel):
    """Start a login transaction for a configured provider."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=64)
    redirect_uri: str = Field(min_length=1, max_length=500)
    device_id: UUID
    code_challenge: str = Field(pattern="^[A-Za-z0-9_-]{43}$")
    code_challenge_method: Literal["S256"] = "S256"


class OidcTransactionView(BaseModel):
    """Transaction id, URL, state and expiry; no token is returned."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: UUID
    authorization_url: str
    state: str
    expires_at: datetime


class OidcExchangeRequest(BaseModel):
    """Return the authorization code and PKCE verifier to the backend."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: UUID
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
    code_verifier: str = Field(min_length=43, max_length=128, pattern="^[A-Za-z0-9._~-]+$")


class OidcLinkRequest(BaseModel):
    """Link the provider identity to the currently authenticated account."""

    model_config = ConfigDict(extra="forbid")

    link_token: str = Field(min_length=20, max_length=4096)


class OidcConflictDetails(BaseModel):
    """Safe details when an unlinked identity matches an existing email."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    link_token: str
    requires_existing_account_login: bool = True
