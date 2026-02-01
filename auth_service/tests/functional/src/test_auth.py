import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import uuid
from src.main import app
from src.services.auth import get_auth_service
from src.services.user import get_user_service
from src.models.entity import User


@pytest.mark.asyncio
async def test_login(client: AsyncClient, fake_auth_service: AsyncMock, fake_user_service: AsyncMock):
    user_login = {"login": "user3", "password": "pass3"} # type: ignore

    # Настраиваем моки
    mock_user = User(login="user3", password="pass3", email="user3@example.com")
    mock_user.check_password = lambda x: True  # Мокаем проверку пароля
    fake_user_service.get_user_by_login.return_value = mock_user
    fake_auth_service.create_access_token.return_value = "access123"
    fake_auth_service.create_refresh_token.return_value = "refresh123"

    response = await client.post("/auth/api/v1/auth/login", json=user_login)

    assert response.status_code == 200
    data = response.json()

    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, fake_auth_service: AsyncMock, fake_user_service: AsyncMock):
    """
    Проверяет, что logout:
      - вызывает метод auth_service.logout
      - возвращает 204 No Content
    """
    # Мокаем get_current_user
    mock_user = User(login="user", password="pw", email="e@e.com")
    fake_auth_service.get_user_from_token.return_value = mock_user

    fake_auth_service.logout.return_value = None

    headers = {"Authorization": "Bearer access123"}

    response = await client.post("/auth/api/v1/auth/logout", headers=headers)

    # --- Проверка ---
    assert response.status_code == 204
    fake_auth_service.logout.assert_awaited_once()


# ==========================================================
# TEST: POST /refresh
# ==========================================================


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, fake_auth_service: AsyncMock):
    # The actual method being called is create_access_token and create_refresh_token
    # The endpoint calls `auth_service.refresh`. We need to mock this method.
    fake_auth_service.refresh.return_value = {
        "access_token": "new_access", "refresh_token": "new_refresh"
    }
    fake_auth_service.get_user_from_token.return_value = User(id=uuid.uuid4(), login="test", email="test@test.com", password="pw")

    payload = {"refresh_token": "refresh123"}

    response = await client.post("/auth/api/v1/auth/refresh", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new_access",
        "refresh_token": "new_refresh",
    }

    # The service decodes the token, gets the user, and creates new tokens.
    # We can assert that the token decoding was attempted.
    fake_auth_service.refresh.assert_awaited_once_with("refresh123")


# @pytest.mark.asyncio
# async def test_login(client: AsyncClient):
#     """Тест успешного входа и получения токенов."""

#     resp = await client.post("/api/v1/roles/", json={"name": "user"})
#     assert resp.status_code == 201

#     user = UserRegister(
#         login="user3",
#         password="pass3",
#         email="user3@example.com",
#         first_name="Third",
#         last_name="User",
#         avatar="https://example.com/avatar.jpg",
#         phone="+79991234567",
#         city="Saint Petersburg",
#     )

#     response = await client.post("/api/v1/users/register", json=user.dict())

#     user_login = {"login": "user3", "password": "pass3"}
#     response = await client.post("/api/v1/auth/login", json=user_login)

#     assert response.status_code == status.HTTP_200_OK

#     response_data = response.json()
#     assert "access_token" in response_data
#     assert "refresh_token" in response_data


# async def test_login_wrong_password(test_client: AsyncClient, test_user_data: dict):
#     """Тест входа с неверным паролем."""
#     await test_client.post("/api/v1/auth/register", json=test_user_data)

#     wrong_credentials = test_user_data.copy()
#     wrong_credentials["password"] = "wrongpassword"

#     response = await test_client.post("/api/v1/auth/login", json=wrong_credentials)
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED


# async def test_get_login_history(test_client: AsyncClient, test_user_data: dict):
#     """Тест получения истории входов для авторизованного пользователя."""
#     # Сначала регистрируем пользователя, а потом логинимся, чтобы получить токен
#     await test_client.post("/api/v1/auth/register", json=test_user_data)
#     login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
#     access_token = login_response.json()["access_token"]
#     headers = {"Authorization": f"Bearer {access_token}"}

#     response = await test_client.get("/api/v1/users/me/login-history", headers=headers)
#     assert response.status_code == status.HTTP_200_OK

#     # Так как у нас заглушка, мы можем проверить, что она возвращает список
#     assert isinstance(response.json(), list)


# async def test_get_login_history_unauthorized(test_client: AsyncClient):
#     """Тест получения истории входов без авторизации."""
#     response = await test_client.get("/api/v1/users/me/login-history")
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED


# async def test_update_credentials(test_client: AsyncClient, test_user_data: dict):
#     """Тест изменения логина/пароля."""
#     # Сначала регистрируем пользователя, а потом логинимся
#     await test_client.post("/api/v1/auth/register", json=test_user_data)
#     login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)
#     access_token = login_response.json()["access_token"]
#     headers = {"Authorization": f"Bearer {access_token}"}

#     new_credentials = {"login": "newlogin@example.com"}
#     response = await test_client.patch("/api/v1/users/me/credentials", json=new_credentials, headers=headers)

#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()["login"] == new_credentials["login"]


# async def test_logout(test_client: AsyncClient, test_user_data: dict):
#     """Тест выхода из системы."""
#     # Сначала регистрируем пользователя, а потом логинимся, чтобы получить cookie
#     await test_client.post("/api/v1/auth/register", json=test_user_data)
#     login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)

#     # Убедимся, что cookie была установлена
#     assert "refreshToken" in login_response.cookies

#     # Устанавливаем cookie на клиент для последующих запросов
#     test_client.cookies = login_response.cookies
#     logout_response = await test_client.post("/api/v1/auth/logout")

#     assert logout_response.status_code == status.HTTP_204_NO_CONTENT

#     # Проверяем, что cookie была удалена (expires=... in the past или max-age=0)
#     set_cookie_header = logout_response.headers.get("set-cookie")
#     assert set_cookie_header is not None
#     assert "expires=" in set_cookie_header.lower() or "max-age=0" in set_cookie_header


# async def test_refresh_token(test_client: AsyncClient, test_user_data: dict):
#     """Тест обновления access-токена."""
#     # Сначала регистрируем пользователя, а потом логинимся
#     await test_client.post("/api/v1/auth/register", json=test_user_data)
#     login_response = await test_client.post("/api/v1/auth/login", json=test_user_data)

#     # Устанавливаем cookie на клиент и выполняем запрос на обновление
#     test_client.cookies = login_response.cookies
#     refresh_response = await test_client.post("/api/v1/auth/refresh")

#     assert refresh_response.status_code == status.HTTP_200_OK
#     assert "access_token" in refresh_response.json()
#     # В реальном приложении здесь также стоит проверить, что обновилась и refresh-cookie
