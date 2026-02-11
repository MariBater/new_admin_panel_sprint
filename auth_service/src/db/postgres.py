from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from auth_service.src.core.config import settings # Этот импорт уже должен работать с правильным pythonpath


dsn = str(settings.POSTGRES_DSN)

engine = create_async_engine(dsn, echo=False)

async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

async def get_session():
    async with async_session() as session:
        yield session
