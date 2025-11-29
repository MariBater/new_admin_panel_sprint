from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.entity import User
from typing import Protocol


class UserRepository(Protocol):

    async def get(self, user_id: UUID) -> User | None: ...


class PgUserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
