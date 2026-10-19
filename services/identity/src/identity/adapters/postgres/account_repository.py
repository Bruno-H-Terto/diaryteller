"""PostgreSQL implementation of account and profile persistence."""

from __future__ import annotations

import uuid
from datetime import datetime

from diary_contracts.authorization import AccountStatus
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.profile import Profile, User

from .tables_access import UserRoleTable
from .tables_identity import (
    ProfileTable,
    UserTable,
)


def _user(row: UserTable) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        status=AccountStatus(row.status),
        email_verified_at=row.email_verified_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _profile(row: ProfileTable) -> Profile:
    return Profile(
        id=row.id,
        display_name=row.display_name,
        locale=row.locale,
        timezone=row.timezone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class PostgresAccountRepository:
    """Account persistence bound to one request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_email(self, email: str) -> User | None:
        """Find by normalized email."""
        row = await self._session.scalar(select(UserTable).where(UserTable.email == email))
        return _user(row) if row else None

    async def by_id(self, user_id: uuid.UUID) -> User | None:
        """Find by id."""
        row = await self._session.get(UserTable, user_id)
        return _user(row) if row else None

    async def profile(self, user_id: uuid.UUID) -> Profile | None:
        """Load profile."""
        row = await self._session.get(ProfileTable, user_id)
        return _profile(row) if row else None

    async def create(
        self, email: str, password_hash: str, locale: str, timezone: str, now: datetime
    ) -> User:
        """Insert profile and user with an explicit default role."""
        user_id = uuid.uuid4()
        self._session.add(
            ProfileTable(
                id=user_id,
                locale=locale,
                timezone=timezone,
                created_at=now,
                updated_at=now,
            )
        )
        row = UserTable(
            id=user_id,
            email=email,
            password_hash=password_hash,
            status=AccountStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        self._session.add(UserRoleTable(user_id=user_id, role_code="user"))
        await self._session.flush()
        return _user(row)

    async def assign_role(self, user_id: uuid.UUID, role_code: str) -> None:
        """Grant a role idempotently."""
        self._session.add(UserRoleTable(user_id=user_id, role_code=role_code))
        await self._session.flush()

    async def update_profile(
        self,
        user_id: uuid.UUID,
        *,
        display_name: str | None,
        locale: str | None,
        timezone: str | None,
        now: datetime,
    ) -> Profile:
        """Update only provided fields."""
        values: dict[str, object] = {"updated_at": now}
        if display_name is not None:
            values["display_name"] = display_name
        if locale is not None:
            values["locale"] = locale
        if timezone is not None:
            values["timezone"] = timezone
        await self._session.execute(
            update(ProfileTable).where(ProfileTable.id == user_id).values(**values)
        )
        row = await self._session.get(ProfileTable, user_id)
        if row is None:
            raise LookupError("profile not found")
        return _profile(row)

    async def mark_email_verified(self, user_id: uuid.UUID, now: datetime) -> None:
        """Set verification once."""
        await self._session.execute(
            update(UserTable)
            .where(UserTable.id == user_id, UserTable.email_verified_at.is_(None))
            .values(email_verified_at=now, updated_at=now)
        )

    async def update_password(self, user_id: uuid.UUID, password_hash: str, now: datetime) -> None:
        """Replace the password hash."""
        await self._session.execute(
            update(UserTable)
            .where(UserTable.id == user_id)
            .values(password_hash=password_hash, updated_at=now)
        )

    async def schedule_deletion(self, user_id: uuid.UUID, now: datetime, due_at: datetime) -> None:
        """Mark pending deletion after the caller revoked all sessions."""
        await self._session.execute(
            update(UserTable)
            .where(UserTable.id == user_id)
            .values(
                status=AccountStatus.PENDING_DELETION.value,
                deletion_due_at=due_at,
                updated_at=now,
            )
        )
