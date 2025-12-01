from functools import lru_cache
from uuid import UUID
import asyncpg
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import PgUserRepository, UserRepository
from src.db.postgres import get_session
from src.models.entity import Role
from src.repositories.role_repository import PgRoleRepository, RoleRepository
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from src.schemas.role import RoleUserSchema


class RoleService:

    def __init__(
        self,
        session: AsyncSession,
        roles_repo: RoleRepository,
        user_repo: UserRepository,
    ) -> None:
        self.session = session
        self.roles_repo = roles_repo
        self.user_repo = user_repo

    async def get_all(self):
        try:
            return await self.roles_repo.get_all()
        except SQLAlchemyError:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Failed to fetch roles",
            )

    async def create(self, name: str):
        new_role = Role(name=name)
        return await self.roles_repo.create(new_role)

    async def update(self, role_id: UUID, name: str):
        updated_role = await self.roles_repo.update(role_id, Role(name=name))
        return updated_role

    async def delete(self, role_id: UUID):
        return await self.roles_repo.delete(role_id)

    async def set_role(self, role_user: RoleUserSchema) -> bool:
        role = await self.roles_repo.get(role_user.role_id)
        user = await self.user_repo.get(role_user.user_id)

        if not role or not user:
            return False  # Указываем на неудачу, обработка будет в API

        if role in user.roles:
            # Роль уже есть, это не ошибка, а состояние. Возвращаем True.
            return True

        user.roles.append(role)
        return True

    async def revoke_role(self, role_user: RoleUserSchema) -> bool:
        role = await self.roles_repo.get(role_user.role_id)
        user = await self.user_repo.get(role_user.user_id)

        if not role or not user or role not in user.roles:
            return False  # Нечего отзывать

        user.roles.remove(role)
        return True

    async def check_role(self, role_user: RoleUserSchema) -> bool:
        role = await self.roles_repo.get(role_user.role_id)
        user = await self.user_repo.get(role_user.user_id)

        if not role or not user:
            return False

        return role in user.roles


@lru_cache()
def get_role_service(
    session: AsyncSession = Depends(get_session),
) -> RoleService:
    roles_repo = PgRoleRepository(session=session)
    user_repo = PgUserRepository(session=session)
    return RoleService(session=session, roles_repo=roles_repo, user_repo=user_repo)
