"""Generic OIDC discovery, PKCE authorization and ID token validation.

Only `issuer`, `subject`, `email` and `email_verified` leave this adapter. The
nonce is compared against the server-side hash, never returned to the app.
"""

from __future__ import annotations

import asyncio
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from diary_security import sha256_digest

from identity.settings import OidcProviderSettings

from .models import OidcDiscovery, OidcIdentity, OidcInvalidToken, OidcUnavailable, truthy


class OidcProviderClient:
    """One configured provider, with discovery and JWKS caches."""

    def __init__(
        self,
        name: str,
        config: OidcProviderSettings,
        http: httpx.AsyncClient,
    ) -> None:
        self.name = name
        self._config = config
        self._http = http
        self._discovery: OidcDiscovery | None = None
        self._keys: dict[str, Any] = {}
        self._keys_at = 0.0
        self._lock = asyncio.Lock()

    async def discover(self) -> OidcDiscovery:
        """Fetch and cache provider metadata."""
        async with self._lock:
            if self._discovery is not None:
                return self._discovery
            payload = await self._get_json(self._config.discovery_url)
            try:
                discovery = OidcDiscovery(
                    issuer=str(payload["issuer"]),
                    authorization_endpoint=str(payload["authorization_endpoint"]),
                    token_endpoint=str(payload["token_endpoint"]),
                    jwks_uri=str(payload["jwks_uri"]),
                )
            except KeyError as exc:
                raise OidcUnavailable("discovery document is incomplete") from exc
            self._discovery = discovery
            return discovery

    async def authorization_url(
        self, *, redirect_uri: str, state: str, nonce: str, code_challenge: str
    ) -> str:
        """Build the external-browser URL for the authorization code flow."""
        discovery = await self.discover()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._config.client_id,
                "redirect_uri": redirect_uri,
                "scope": " ".join(self._config.scopes),
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{discovery.authorization_endpoint}?{query}"

    async def exchange(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: str,
        nonce_hash: str,
    ) -> OidcIdentity:
        """Exchange the code server-side and validate the returned ID token."""
        discovery = await self.discover()
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._config.client_id,
            "code_verifier": code_verifier,
        }
        if self._config.client_secret:
            form["client_secret"] = self._config.client_secret
        try:
            response = await self._http.post(
                discovery.token_endpoint,
                data=form,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcUnavailable("token endpoint rejected the exchange") from exc
        id_token = payload.get("id_token")
        if not isinstance(id_token, str):
            raise OidcInvalidToken("id_token missing")
        claims = await self._verify(id_token, discovery)
        nonce = claims.get("nonce")
        if not isinstance(nonce, str) or not hmac.compare_digest(sha256_digest(nonce), nonce_hash):
            raise OidcInvalidToken("nonce mismatch")
        subject = claims.get("sub")
        issuer = claims.get("iss")
        if not isinstance(subject, str) or not isinstance(issuer, str):
            raise OidcInvalidToken("subject or issuer invalid")
        if issuer != discovery.issuer:
            raise OidcInvalidToken("subject or issuer invalid")
        email = claims.get("email")
        return OidcIdentity(
            issuer=issuer,
            subject=subject,
            provider=self.name,
            email=email.lower() if isinstance(email, str) else None,
            email_verified=truthy(claims.get("email_verified")),
            name=claims.get("name") if isinstance(claims.get("name"), str) else None,
        )

    async def _verify(self, token: str, discovery: OidcDiscovery) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise OidcInvalidToken("malformed id_token") from exc
        kid = header.get("kid")
        key = await self._key(str(kid) if kid else None, discovery)
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key,
                algorithms=self._config.algorithms,
                audience=self._config.client_id,
                issuer=discovery.issuer,
                leeway=30,
                options={"require": ["exp", "iat", "aud", "iss", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise OidcInvalidToken("id_token rejected") from exc
        authorized_party = claims.get("azp")
        if authorized_party is not None and authorized_party != self._config.client_id:
            raise OidcInvalidToken("azp mismatch")
        return claims

    async def _key(self, kid: str | None, discovery: OidcDiscovery) -> Any:
        if kid and kid in self._keys and time.monotonic() - self._keys_at < 600:
            return self._keys[kid]
        async with self._lock:
            if kid and kid in self._keys and time.monotonic() - self._keys_at < 600:
                return self._keys[kid]
            payload = await self._get_json(discovery.jwks_uri)
            keys: dict[str, Any] = {}
            for jwk in payload.get("keys", []):
                if not isinstance(jwk, dict):
                    continue
                try:
                    public = jwt.PyJWK(jwk, algorithm=jwk.get("alg"))
                except jwt.PyJWTError:
                    continue
                keys[str(jwk.get("kid", ""))] = public.key
            if not keys:
                raise OidcUnavailable("no usable signing key")
            self._keys = keys
            self._keys_at = time.monotonic()
        chosen = self._keys.get(kid or "") or next(iter(self._keys.values()))
        return chosen

    async def _get_json(self, url: str) -> dict[str, Any]:
        try:
            response = await self._http.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcUnavailable("provider metadata unavailable") from exc
        if not isinstance(payload, dict):
            raise OidcUnavailable("provider metadata is not an object")
        return payload
