import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import redis.asyncio as aioredis

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.models.entity import User
from src.core.dependencies import get_current_user, require_superuser
from src.db.postgres import get_session, Base

from src.repositories.role_repository import PgRoleRepository
from src.repositories.user_repository import PgUserRepository

from src.services.role import RoleService, get_role_service
from src.services.user import get_user_service
from src.services.auth import get_auth_service

from src.api.v1.roles import router as role_router
from src.api.v1.users import router as users_router
from src.api.v1.auth import router as auth_router

from tests.functional.settings import settings

TEST_DSN = (
    f"postgresql+asyncpg://{settings.TEST_POSTGRES_USER}:"
    f"{settings.TEST_POSTGRES_PASSWORD}@"
    f"{settings.TEST_POSTGRES_HOST}:{settings.TEST_POSTGRES_PORT}/"
    f"{settings.TEST_POSTGRES_DB}"
)

engine_test = create_async_engine(TEST_DSN, future=True, echo=False)

TestAsyncSessionLocal = async_sessionmaker(
    engine_test, expire_on_commit=False, class_=AsyncSession
)


@pytest_asyncio.fixture(scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def fake_user_service():
    svc = AsyncMock()

    class FakeUser:
        id = 1
        login = "user3"

        def check_password(self, pwd):
            return pwd == "pass3"

    svc.get_user_by_login.return_value = FakeUser()
    svc.login.return_value = None

    return svc


@pytest_asyncio.fixture
async def fake_auth_service():
    svc = AsyncMock()
    svc.create_access_token.return_value = "access123"
    svc.create_refresh_token.return_value = "refresh123"
    return svc


@pytest_asyncio.fixture(autouse=True)
async def clear_cached_services():
    get_user_service.cache_clear()
    get_auth_service.cache_clear()


@pytest_asyncio.fixture
async def fake_role_service():
    svc = AsyncMock()

    class FakeRole:
        id = 1
        name = "user"

    svc.get_by_name.return_value = FakeRole()

    return svc


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer testtoken123"}


@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def app(
    session: AsyncSession,
    fake_user_service,
    fake_auth_service,
) -> FastAPI:
    app = FastAPI()

    async def fake_require_superuser():
        return True

    app.dependency_overrides[require_superuser] = fake_require_superuser

    async def fake_get_current_user():
        class FakeUser:
            id = 1
            login = "user3"

        return FakeUser()

    app.dependency_overrides[get_current_user] = fake_get_current_user

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    app.dependency_overrides[get_user_service] = lambda: fake_user_service
    app.dependency_overrides[get_auth_service] = lambda: fake_auth_service

    async def override_get_role_service(
        session: AsyncSession = Depends(override_get_session),
    ):
        return RoleService(
            session=session,
            roles_repo=PgRoleRepository(session),
            user_repo=PgUserRepository(session),
        )

    app.dependency_overrides[get_role_service] = override_get_role_service

    app.include_router(role_router, prefix="/api/v1/roles")
    app.include_router(users_router, prefix="/api/v1/users")
    app.include_router(auth_router, prefix="/api/v1/auth")

    return app


@pytest.fixture(scope="session")
def event_loop():
    """
    Создает event loop на всю тестовую сессию.
    Это необходимо для корректной работы pytest-asyncio.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
