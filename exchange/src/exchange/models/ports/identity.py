"""Identity authorizer alias and principal re-export."""

from __future__ import annotations

from ...lib.identity.authorizer import IdentityHttpAuthorizer
from ..principal import Principal

IdentityAuthorizer = IdentityHttpAuthorizer

__all__ = ["IdentityAuthorizer", "Principal"]
