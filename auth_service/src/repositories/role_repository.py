from typing import Protocol
from uuid import UUID

import backoff
from sqlalchemy import delete, select, update
from src.models.entity import Role
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class RoleRepository(Protocol):

    async def get_all(self) -> list[Role]: ...

    async def get(self, role_id: UUID) -> Role | None: ...

    async def get_by_name(self, role_name: str) -> Role | None: ...

    async def create(self, role: Role) -> Role: ...

    async def update(self, role_id: UUID, new_role: Role) -> None: ...

    async def delete(self, role_id: UUID) -> bool: ...


class PgRoleRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @backoff.on_exception(backoff.expo, (SQLAlchemyError), max_time=30)
    async def get_all(self) -> list[Role]:
        result = await self.session.execute(select(Role))
        return result.scalars().all()

    async def get(self, role_id: UUID) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, role_name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == role_name))
        return result.scalar_one_or_none()

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        return role

    async def update(self, role_id: UUID, new_role: Role) -> Role | None:
        result = await self.session.execute(
            update(Role)
            .where(Role.id == role_id)
            .values(name=new_role.name)
            .returning(Role)
        )
        return result.scalar_one_or_none()

    async def delete(self, role_id: UUID) -> bool:
        role = await self.session.get(Role, role_id)
        if not role:
            return False
        await self.session.delete(role)
        await self.session.flush()
        return True
