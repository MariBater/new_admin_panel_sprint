import asyncio
from unittest.mock import AsyncMock, MagicMock
import uuid

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Pre-import Configuration ---
# This must run BEFORE any application modules are imported.
from src.core.config import settings
settings.TRACING_ENABLED = False
# --- End Pre-import Configuration ---

from src.db.postgres import Base, get_session
from src.main import app
from src.models import entity, social_account  # Import all models
from src.services.auth import get_auth_service
from src.services.role import get_role_service
from src.services.user import get_user_service


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    # Для тестов, запускаемых локально, переопределяем хост БД
    if settings.POSTGRES_HOST == 'auth-db':
        settings.POSTGRES_HOST = 'localhost'

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Фикстура для создания тестового движка и таблиц с ожиданием готовности БД."""
    engine = create_async_engine(str(settings.POSTGRES_DSN), echo=False)
    
    # Добавляем механизм ожидания готовности БД
    for _ in range(5):  # Попробуем подключиться 5 раз
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            yield engine
            await engine.dispose()
            return
        except ConnectionRefusedError:
            print("Connection to DB refused, retrying in 2 seconds...")
            await asyncio.sleep(2)

    raise ConnectionError("Could not connect to the database after several retries.")


@pytest_asyncio.fixture
async def session(test_engine):
    """Фикстура для создания сессии БД для одного теста."""
    TestSessionLocal = sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client( # This fixture now correctly uses the `session` fixture
    session: AsyncSession, # It depends on the session fixture below
    fake_user_service: AsyncMock,
    fake_auth_service: AsyncMock,
    fake_role_service: AsyncMock,
) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания тестового клиента с сессией БД."""
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_user_service] = lambda: fake_user_service
    app.dependency_overrides[get_auth_service] = lambda: fake_auth_service
    app.dependency_overrides[get_role_service] = lambda: fake_role_service

    # Add X-Request-Id to all requests
    headers = {"X-Request-Id": str(uuid.uuid4())}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.fixture
def fake_user_service():
    return AsyncMock()


@pytest.fixture
def fake_auth_service():
    return AsyncMock()


@pytest.fixture
def fake_role_service():
    return AsyncMock()


@pytest_asyncio.fixture(autouse=True)
async def clear_cached_services():
    get_user_service.cache_clear()
    get_auth_service.cache_clear()
    get_role_service.cache_clear()
    yield
    app.dependency_overrides = {}


@pytest.fixture
def auth_data(fake_auth_service: AsyncMock, fake_user_service: AsyncMock):
    """Фикстура для аутентификации, мокает get_current_user и require_superuser."""
    mock_superuser = entity.User( # type: ignore
        id=uuid.uuid4(),
        login="superuser",
        password="superpassword",
        email="super@user.com",
    )
    mock_superuser.is_superuser = True

    fake_auth_service.get_user_from_token.return_value = mock_superuser

    return {
        "headers": {"Authorization": "Bearer testtoken123"},
        "user": mock_superuser,
    }