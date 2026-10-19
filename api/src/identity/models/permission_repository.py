"""Plans, permissions, roles and entitlement materialization."""

from __future__ import annotations

import uuid
from typing import Any

from diary_contracts.authorization import Permission, UsageMetric
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from identity.models.plans import upload_limits_for
from identity.models.subscription import Plan

from .tables_access import (
    PermissionTable,
    PlanPermissionTable,
    PlanTable,
    RolePermissionTable,
    RoleTable,
    UserRoleTable,
)


class PostgresPlanRepository:
    """Role/plan permission reads and idempotent reference-data seeding."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _plan_row(self, code: str) -> PlanTable | None:
        return await self._session.scalar(select(PlanTable).where(PlanTable.code == code))

    async def _permissions(self, plan_code: str) -> frozenset[str]:
        values = await self._session.scalars(
            select(PlanPermissionTable.permission_code).where(
                PlanPermissionTable.plan_code == plan_code
            )
        )
        return frozenset(values)

    async def default_plan(self) -> Plan:
        """Return the seeded default plan."""
        row = await self._session.scalar(select(PlanTable).where(PlanTable.is_default.is_(True)))
        if row is None:
            raise LookupError("default plan missing; run seeds")
        return await self._to_plan(row)

    async def plan(self, code: str) -> Plan | None:
        """Return a plan by code."""
        row = await self._plan_row(code)
        return await self._to_plan(row) if row else None

    async def plans(self) -> list[Plan]:
        """List plans."""
        rows = await self._session.scalars(select(PlanTable).order_by(PlanTable.code))
        return [await self._to_plan(row) for row in rows]

    async def _to_plan(self, row: PlanTable) -> Plan:
        quotas: dict[UsageMetric, int] = {}
        for key, value in (row.quotas or {}).items():
            try:
                quotas[UsageMetric(key)] = int(value)
            except ValueError:
                continue
        limits = {str(key): int(value) for key, value in (row.upload_limits or {}).items()}
        return Plan(
            code=row.code,
            name=row.name,
            permissions=await self._permissions(row.code),
            quotas=quotas,
            upload_limits=limits or upload_limits_for(row.code),
            is_default=row.is_default,
        )

    async def user_permissions(self, user_id: uuid.UUID) -> set[str]:
        """Permissions granted through roles only."""
        values = await self._session.scalars(
            select(RolePermissionTable.permission_code)
            .join(UserRoleTable, UserRoleTable.role_code == RolePermissionTable.role_code)
            .where(UserRoleTable.user_id == user_id)
        )
        return set(values)

    async def upsert_seed(self, plans: list[Plan], role_permissions: dict[str, set[str]]) -> None:
        """Install catalogs and grants without touching user data."""
        for permission in Permission:
            await self._session.execute(
                insert(PermissionTable)
                .values(code=permission.value, description=permission.value)
                .on_conflict_do_nothing()
            )
        roles = {"user": "Standard account", "admin": "Administrative operator"}
        for code, description in roles.items():
            await self._session.execute(
                insert(RoleTable)
                .values(code=code, description=description)
                .on_conflict_do_update(
                    index_elements=[RoleTable.code], set_={"description": description}
                )
            )
        for role_code, permissions in role_permissions.items():
            for permission in sorted(permissions):
                await self._session.execute(
                    insert(RolePermissionTable)
                    .values(role_code=role_code, permission_code=permission)
                    .on_conflict_do_nothing()
                )
        for plan in plans:
            await self._session.execute(
                insert(PlanTable)
                .values(
                    code=plan.code,
                    name=plan.name,
                    quotas={metric.value: limit for metric, limit in plan.quotas.items()},
                    upload_limits=dict(plan.upload_limits),
                    is_default=plan.is_default,
                )
                .on_conflict_do_update(
                    index_elements=[PlanTable.code],
                    set_={
                        "name": plan.name,
                        "quotas": {metric.value: limit for metric, limit in plan.quotas.items()},
                        "upload_limits": dict(plan.upload_limits),
                        "is_default": plan.is_default,
                    },
                )
            )
            for permission in sorted(plan.permissions):
                await self._session.execute(
                    insert(PlanPermissionTable)
                    .values(plan_code=plan.code, permission_code=permission)
                    .on_conflict_do_nothing()
                )

    async def quota_payload(self, plan: Plan) -> dict[str, Any]:
        """Serialize quotas for logs/administration (no personal data)."""
        return {metric.value: limit for metric, limit in plan.quotas.items()}
