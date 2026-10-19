"""Argon2id hashing with bounded concurrency outside the event loop.

Parameters are configurable and calibrated at deployment. Verification of an
unknown email uses the same hasher so response timing does not reveal accounts.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


@dataclass(frozen=True, slots=True)
class Verification:
    """Outcome of a password verification."""

    valid: bool
    needs_rehash: bool


class PasswordHasher:
    """Async facade around Argon2id with a semaphore and dummy hash."""

    def __init__(
        self,
        *,
        time_cost: int,
        memory_kib: int,
        parallelism: int,
        concurrency: int,
    ) -> None:
        self._hasher = Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_kib,
            parallelism=parallelism,
            hash_len=32,
            salt_len=16,
        )
        self._semaphore = asyncio.Semaphore(concurrency)
        self._dummy_hash = self._hasher.hash("dummy-password-not-a-user")

    async def hash(self, password: str) -> str:
        """Hash a password in a worker thread with bounded concurrency."""
        async with self._semaphore:
            return await asyncio.to_thread(self._hasher.hash, password)

    async def verify(self, password: str, encoded: str) -> Verification:
        """Verify a password; malformed hashes count as a mismatch."""
        async with self._semaphore:
            try:
                valid = await asyncio.to_thread(self._hasher.verify, encoded, password)
                needs_rehash = self._hasher.check_needs_rehash(encoded)
            except (VerifyMismatchError, InvalidHashError):
                valid, needs_rehash = False, False
        return Verification(valid=valid, needs_rehash=needs_rehash)

    async def dummy_verify(self, password: str) -> None:
        """Burn comparable CPU when the account does not exist."""
        await self.verify(password, self._dummy_hash)
