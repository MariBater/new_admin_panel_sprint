from src.core.config import settings
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()

dsn = f'postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}'
engine = create_async_engine(dsn, echo=True, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def create_database() -> None:
    from src.models.entity import User, UsersRoles, Role, UserAuthHistory, UserProfile

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
