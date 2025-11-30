import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Set
from sqlalchemy.pool import NullPool
from types import SimpleNamespace
from uuid import UUID, uuid4

# Импортируем приложение и заглушку БД для очистки состояния между тестами
from src.main import app
from src.db.postgres import get_session, Base # Base нужен для создания таблиц
from src.services.role import get_role_service
from src.schemas.role import RoleUserSchema
from src.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# DSN для подключения к "служебной" базе данных (которая точно существует)
MAINTENANCE_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@localhost:5433/postgres"  # Подключаемся к служебной базе 'postgres'
)

# DSN для тестовой базы данных, которую мы будем создавать и удалять
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@localhost:5433/{settings.POSTGRES_DB}_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession)


# --- Наша имитация RoleService ---
# Этот класс будет вести себя как настоящий RoleService, но использовать словари вместо БД
class MockRoleService:
    """Имитация сервиса ролей для тестов."""
    def __init__(self):
        self.roles: dict[UUID, dict] = {}
        self.user_roles: dict[str, Set[UUID]] = {}

    async def get_all(self) -> list[SimpleNamespace]:
        # Имитация получения всех ролей
        return [SimpleNamespace(**role) for role in self.roles.values()]

    async def create(self, name: str) -> SimpleNamespace:
        # Проверяем, существует ли роль с таким именем
        if any(role['name'] == name for role in self.roles.values()):
            # В реальном сервисе это вызовет IntegrityError, который API-слой превратит в 409
            # Здесь мы просто выбрасываем исключение, чтобы имитировать это поведение
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("Mock Integrity Error", params=None, orig=None)

        role_id = uuid4()
        new_role = {"id": role_id, "name": name}
        self.roles[role_id] = new_role
        return SimpleNamespace(**new_role)

    async def update(self, role_id: UUID, name: str) -> SimpleNamespace | None:
        # Имитация обновления роли
        if role_id in self.roles:
            self.roles[role_id]['name'] = name
            return SimpleNamespace(**self.roles[role_id])
        return None

    async def delete(self, role_id: UUID) -> bool:
        # Имитация удаления роли
        if role_id in self.roles:
            del self.roles[role_id]
            # Также удаляем назначения этой роли пользователям
            for user_id in self.user_roles:
                self.user_roles[user_id].discard(role_id)
            return True
        return False

    async def set_role(self, role_user: RoleUserSchema) -> bool:
        # Имитация назначения роли
        user_id_str = str(role_user.user_id)
        if user_id_str not in self.user_roles:
            self.user_roles[user_id_str] = set()
        self.user_roles[user_id_str].add(role_user.role_id)
        return True

    async def revoke_role(self, role_user: RoleUserSchema) -> bool:
        # Имитация отзыва роли
        user_id_str = str(role_user.user_id)
        if user_id_str in self.user_roles and role_user.role_id in self.user_roles[user_id_str]:
            self.user_roles[user_id_str].remove(role_user.role_id)
            return True
        return False

    async def check_role(self, role_user: RoleUserSchema) -> bool:
        # Имитация проверки роли
        user_id_str = str(role_user.user_id)
        return user_id_str in self.user_roles and role_user.role_id in self.user_roles[user_id_str]


# Создаем один экземпляр нашего мок-сервиса на всю сессию тестов
mock_role_service_instance = MockRoleService()


# --- Функция-зависимость, которая будет возвращать наш мок ---
async def get_mock_role_service() -> MockRoleService:
    return mock_role_service_instance


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Фикстура, которая выполняется один раз за сессию.
    Создает тестовую базу данных перед запуском тестов и удаляет ее после.
    """
    maintenance_engine = create_async_engine(MAINTENANCE_DATABASE_URL, isolation_level="AUTOCOMMIT")
    test_db_name = f"{settings.POSTGRES_DB}_test"

    # Удаляем БД, если она осталась от предыдущих запусков
    async with maintenance_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))

    # Создаем таблицы один раз за сессию
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Здесь запускаются все тесты

    # Удаляем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Удаляем тестовую базу данных после завершения всех тестов
    async with maintenance_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE "{test_db_name}" WITH (FORCE)'))

    await maintenance_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Фикстура, которая создает сессию БД для каждого теста в отдельной транзакции,
    которая откатывается по завершении теста.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        await session.close()
        # Гарантированно откатываем транзакцию после каждого теста
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания тестового клиента, использующего изолированную сессию БД."""
    # Подменяем зависимость реальной сессии БД на тестовую
    async def override_get_session():
        yield db_session
    app.dependency_overrides[get_session] = override_get_session
    
    # Подменяем зависимость реального сервиса ролей на нашу имитацию
    app.dependency_overrides[get_role_service] = get_mock_role_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Очищаем подмены после теста, чтобы не влиять на другие тесты
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user_data():
    """Данные для тестового пользователя."""
    return {
        "login": f"testuser_{uuid4()}@example.com",
        "password": "aVeryStrongPassword123!"
    }