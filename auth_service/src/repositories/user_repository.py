from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from auth_service.src.models.entity import User, UserAuthHistory
from typing import List, Protocol, Tuple

from werkzeug.security import generate_password_hash


class UserRepository(Protocol):

    async def get(self, user_id: UUID) -> User | None: ...
    async def get_user_by_login(self, login: str) -> User | None: ...
    async def create(self, user: User) -> User: ...
    async def update_credentials(self, user_id, login: str, password: str): ...
    async def get_login_history_paginated(
        self, user_id: UUID, page: int, size: int
    ) -> List[UserAuthHistory]: ...


class PgUserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_login(self, login: str) -> User | None:
        result = await self.session.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_credentials(self, user_id, login: str, password: str):
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(login=login, password=generate_password_hash(password))
            .returning(User)
        )
        return result.scalar_one_or_none()

    async def get_login_history_paginated(
        self, user_id: UUID, page: int, size: int
    ) -> List[UserAuthHistory]:
        offset = (page - 1) * size
        result = await self.session.execute(
            select(UserAuthHistory)
            .where(UserAuthHistory.user_id == user_id)
            .order_by(UserAuthHistory.auth_date.desc())
            .limit(size)
            .offset(offset)
        )
        return result.scalars().all()
