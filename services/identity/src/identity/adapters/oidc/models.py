"""Provider metadata and validated identity value objects."""

from __future__ import annotations

from dataclasses import dataclass


class OidcUnavailable(Exception):
    """Discovery, JWKS or token exchange could not be completed safely."""


class OidcInvalidToken(Exception):
    """The provider returned a token that failed validation."""


@dataclass(frozen=True, slots=True)
class OidcDiscovery:
    """Endpoints resolved from `/.well-known/openid-configuration`."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str


@dataclass(frozen=True, slots=True)
class OidcIdentity:
    """Validated claims that identify one external subject."""

    issuer: str
    subject: str
    provider: str
    email: str | None
    email_verified: bool
    name: str | None


def truthy(value: object) -> bool:
    """Providers disagree on boolean encoding for `email_verified`."""
    return value is True or (isinstance(value, str) and value.lower() == "true")
