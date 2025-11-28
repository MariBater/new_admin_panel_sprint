import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status

# Импортируем приложение и заглушку БД для очистки состояния между тестами
from src.main import app
from src.api.v1.auth import fake_users_db


# Маркируем все тесты в этом файле как асинхронные
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def test_client():
    """
    Фикстура для создания асинхронного тестового клиента.
    Использует `async with` для корректного открытия и закрытия клиента.
    """
    # Создаем транспорт, который направляет запросы напрямую в наше FastAPI приложение
    transport = ASGITransport(app=app)
    # Создаем клиент, используя этот транспорт
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def clear_db_before_each_test():
    """Эта фикстура автоматически очищает нашу фейковую БД перед каждым тестом."""
    fake_users_db.clear()


@pytest.fixture(scope="function")
def test_user_data():
    """Данные для тестового пользователя."""
    return {
        "login": "testuser@example.com",
        "password": "aVeryStrongPassword123!"
    }


async def test_register_user(test_client: AsyncClient, test_user_data: dict):
    """Тест успешной регистрации пользователя."""
    # Примечание: для повторных запусков теста нужна очистка БД.
    # Пока мы предполагаем, что база данных пуста или этот пользователь не существует.
    response = await test_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["login"] == test_user_data["login"]
    assert "id" in response_data


async def test_register_existing_user(test_client: AsyncClient, test_user_data: dict):
    """Тест регистрации пользователя, который уже существует."""
    # Убедимся, что пользователь существует (можно вызвать регистрацию еще раз)
    await test_client.post("/api/v1/auth/register", json=test_user_data)
    
    response = await test_client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_409_CONFLICT


async def test_login(test_client: AsyncClient, test_user_data: dict):
    """Тест успешного входа и получения токенов."""
    # Сначала регистрируем пользователя, чтобы быть уверенными, что он есть
    await test_client.post("/api/v1/auth/register", json=test_user_data)

    response = await test_client.post("/api/v1/auth/login", json=test_user_data)
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert "access_token" in response_data
    
    # Проверяем, что установилась cookie с refresh_token
    assert "refreshToken" in response.cookies
    assert response.cookies["refreshToken"] is not None


async def test_login_wrong_password(test_client: AsyncClient, test_user_data: dict):
    """Тест входа с неверным паролем."""
    await test_client.post("/api/v1/auth/register", json=test_user_data)

    wrong_credentials = test_user_data.copy()
    wrong_credentials["password"] = "wrongpassword"
    
    response = await test_client.post("/api/v1/auth/login", json=wrong_credentials)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_login_history(test_client: AsyncClient, test_user_data: dict):
    """Тест получения истории входов для авторизованного пользователя."""
    # Сначала регистрируем пользователя, а потом логинимся, чтобы получить токен
    await test_client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await test_client.get("/api/v1/users/me/login-history", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Так как у нас заглушка, мы можем проверить, что она возвращает список
    assert isinstance(response.json(), list)


async def test_get_login_history_unauthorized(test_client: AsyncClient):
    """Тест получения истории входов без авторизации."""
    response = await test_client.get("/api/v1/users/me/login-history")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_update_credentials(test_client: AsyncClient, test_user_data: dict):
    """Тест изменения логина/пароля."""
    # Сначала регистрируем пользователя, а потом логинимся
    await test_client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    new_credentials = {"login": "newlogin@example.com"}
    response = await test_client.patch("/api/v1/users/me/credentials", json=new_credentials, headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["login"] == new_credentials["login"]


async def test_logout(test_client: AsyncClient, test_user_data: dict):
    """Тест выхода из системы."""
    # Сначала регистрируем пользователя, а потом логинимся, чтобы получить cookie
    await test_client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
    
    # Убедимся, что cookie была установлена
    assert "refreshToken" in login_response.cookies

    # Устанавливаем cookie на клиент для последующих запросов
    test_client.cookies = login_response.cookies
    logout_response = await test_client.post("/api/v1/auth/logout")
    
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверяем, что cookie была удалена (expires=... in the past или max-age=0)
    set_cookie_header = logout_response.headers.get("set-cookie")
    assert set_cookie_header is not None
    assert "expires=" in set_cookie_header.lower() or "max-age=0" in set_cookie_header


async def test_refresh_token(test_client: AsyncClient, test_user_data: dict):
    """Тест обновления access-токена."""
    # Сначала регистрируем пользователя, а потом логинимся
    await test_client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
    
    # Устанавливаем cookie на клиент и выполняем запрос на обновление
    test_client.cookies = login_response.cookies
    refresh_response = await test_client.post("/api/v1/auth/refresh")
    
    assert refresh_response.status_code == status.HTTP_200_OK
    assert "access_token" in refresh_response.json()
    # В реальном приложении здесь также стоит проверить, что обновилась и refresh-cookie
