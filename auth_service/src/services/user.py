from functools import lru_cache
from http import HTTPStatus
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.entity import User, UserProfile
from src.schemas.user import UserRegister, UserUpdateCredentials
from src.repositories.user_repository import PgUserRepository, UserRepository
from src.db.postgres import get_session


class UserService:
    def __init__(self, session: AsyncSession, user_repo: UserRepository) -> None:
        self.session = session
        self.user_repo = user_repo

    async def create_user(self, user_data: UserRegister):
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
            user = await self.user_repo.create(user=user)
            await self.session.commit()
            return user
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while create user",
            )

    async def get_user_by_login(self, login: str):
        try:
            user = await self.user_repo.get_user_by_login(login=login)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

    async def get_user(self, user_id: UUID):
        try:
            user = await self.user_repo.get(user_id=user_id)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while get user",
            )

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

    async def get_login_history_from_db(self):
        pass


@lru_cache()
def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    user_repo = PgUserRepository(session=session)
    return UserService(session=session, user_repo=user_repo)
