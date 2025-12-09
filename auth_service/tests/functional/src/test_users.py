import pytest
from httpx import AsyncClient
from fastapi import status

from src.schemas.user import UserRegister, UserUpdateCredentials


@pytest.mark.asyncio
async def test_register_user_success(client, fake_user_service, fake_role_service):
    # Пользователь не существует
    fake_user_service.get_user_by_login.return_value = None

    # Мок роли
    async def fake_get_by_name():
        class FakeRole:
            id = 1
            name = 'user'

        return FakeRole()

    fake_role_service.get_by_name = fake_get_by_name

    payload = {
        "login": "new_user",
        "password": "password",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "avatar": "https://example.com/avatar.jpg",
        "city": "Moscow",
    }

    response = await client.post("/api/v1/users/register", json=payload)

    assert response.status_code == 201
    fake_user_service.create_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_credentials_success(client, fake_user_service, auth_headers):
    class UpdatedUser:
        id = 1
        login = "changed"

    fake_user_service.update_user_credentials.return_value = UpdatedUser()

    payload = {"login": "changed", "password": "newpassword123"}

    response = await client.post(
        "/api/v1/users/me/credentials",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": 1, "login": "changed"}

    update_model = UserUpdateCredentials(**payload)

    fake_user_service.update_user_credentials.assert_awaited_once_with(
        user_id=1, update_data=update_model
    )


@pytest.mark.asyncio
async def test_login_history_success(client, fake_user_service, auth_headers):

    class FakeHistory:
        def __init__(self, agent, ts):
            self.user_agent = agent
            self.auth_date = ts

    fake_user_service.get_login_history.return_value = [
        FakeHistory("Chrome", "2024-01-01"),
        FakeHistory("Safari", "2024-01-02"),
    ]

    response = await client.get("/api/v1/users/me/login-history", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == [
        {"user_agent": "Chrome", "login_at": "2024-01-01"},
        {"user_agent": "Safari", "login_at": "2024-01-02"},
    ]
