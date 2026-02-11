from functools import lru_cache
from http import HTTPStatus
from opentelemetry import trace
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from auth_service.src.core.tracing import traced
from auth_service.src.models.entity import Role, User, UserAuthHistory, UserProfile
from auth_service.src.schemas.user import UserRegister, UserUpdateCredentials
from auth_service.src.repositories.user_repository import PgUserRepository, UserRepository
from auth_service.src.db.postgres import get_session


class UserService:
    def __init__(self, session: AsyncSession, user_repo: UserRepository) -> None:
        self.session = session
        self.user_repo = user_repo

    @traced("service_create_user")
    async def create_user(self, user_data: UserRegister, role: Role):
        try:
            user = User(
                login=user_data.login,
                email=user_data.email,
                password=user_data.password,
            )
            user_profile = UserProfile(
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                avatar=user_data.avatar,
                phone=user_data.phone,
                city=user_data.city,
            )
            user.user_profile = user_profile
            user.roles.append(role)
            user = await self.user_repo.create(user=user)
            await self.session.commit()
            return user
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while create user",
            )

    @traced("service_get_user_by_login")
    async def get_user_by_login(self, login: str):
        try:
            user = await self.user_repo.get_user_by_login(login=login)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

    @traced("service_get_user")
    async def get_user(self, user_id: UUID):
        try:
            user = await self.user_repo.get(user_id=user_id)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

    @traced("service_update_user_credentials")
    async def update_user_credentials(
        self, user_id: UUID, update_data: UserUpdateCredentials
    ):
        try:
            updated_user = await self.user_repo.update_credentials(
                user_id=user_id, login=update_data.login, password=update_data.password
            )

            if not updated_user:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Role not found"
                )

            await self.session.commit()
            return updated_user
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

    @traced("service_login")
    async def login(self, user_id: UUID, user_agent: str):
        try:
            user = await self.user_repo.get(user_id=user_id)
            if user:
                user_auth = UserAuthHistory(user_agent=user_agent, user_id=user_id)
                user.auth_histories.append(user_auth)

                await self.session.commit()
            return user
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

    @traced("service_get_login_history_paginated")
    async def get_login_history_paginated(
        self, user_id: UUID, page: int, size: int
    ) -> list[UserAuthHistory]:
        try:
            user = await self.user_repo.get(user_id=user_id)
            if not user:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="User not found",
                )

            return await self.user_repo.get_login_history_paginated(
                user_id=user_id, page=page, size=size
            )
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )


@lru_cache()
def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    user_repo = PgUserRepository(session=session)
    return UserService(session=session, user_repo=user_repo)
