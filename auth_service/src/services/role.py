from functools import lru_cache
from uuid import UUID
import asyncpg
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_session
from src.models.entity import Role
from src.repositories.role_repository import PgRoleRepository, RoleRepository
from http import HTTPStatus
from src.core.logger import app_logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class RoleService:

    def __init__(self, session: AsyncSession, roles_repo: RoleRepository) -> None:
        self.session = session
        self.roles_repo = roles_repo

    async def get_all(self):
        try:
            return await self.roles_repo.get_all()
        except SQLAlchemyError:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Failed to fetch roles",
            )

    async def create(self, name: str):
        try:
            new_role = Role(name=name)
            role = await self.roles_repo.create(new_role)
            await self._commit()
            return role

        except IntegrityError as e:
            await self._handle_integrity_error(e, name)

    async def update(self, role_id: UUID, name: str):
        try:
            updated_role = await self.roles_repo.update(role_id, Role(name=name))

            if not updated_role:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Role not found"
                )

            await self._commit()
            return updated_role

        except IntegrityError as e:
            await self._handle_integrity_error(e, name)

    async def delete(self, role_id: UUID):
        try:
            deleted = await self.roles_repo.delete(role_id)

            if not deleted:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Role not found"
                )

            await self._commit()
            return True

        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Database error while deleting role",
            )

    async def _commit(self):
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    async def _handle_integrity_error(self, e: IntegrityError, name: str | None = None):
        await self.session.rollback()

        if isinstance(e.orig, asyncpg.UniqueViolationError):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Role '{name}' already exists" if name else "Duplicate value",
            )

        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


@lru_cache()
def get_role_service(
    session: AsyncSession = Depends(get_session),
) -> RoleService:
    roles_repo = PgRoleRepository(session=session)
    return RoleService(session=session, roles_repo=roles_repo)
