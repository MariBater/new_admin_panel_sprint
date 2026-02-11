import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, MagicMock

from auth_service.src.schemas.user import UserRegister, UserUpdateCredentials


@pytest.mark.asyncio
async def test_register_user_success(client, fake_user_service, fake_role_service):
    # Пользователь не существует
    fake_user_service.get_user_by_login.return_value = None

    # Мок роли
    fake_role_service.get_by_name.return_value = MagicMock(id=1, name='user')

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

    response = await client.post("/auth/api/v1/users/register", json=payload)

    assert response.status_code == 201
    fake_user_service.create_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_credentials_success(
    client: AsyncClient,
    fake_user_service: AsyncMock,
    auth_data: dict,
):
    headers = auth_data["headers"]
    user_id_from_token = auth_data["user"].id # Correctly access the user object from the fixture

    fake_user_service.update_user_credentials.return_value = MagicMock( # type: ignore
        id=user_id_from_token, login="changed"
    )

    payload = {"login": "changed", "password": "newpassword123"}

    response = await client.post(
        "/auth/api/v1/users/me/credentials",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["login"] == "changed"
    assert response.json()["user_id"] is not None

    update_model = UserUpdateCredentials(**payload)

    fake_user_service.update_user_credentials.assert_awaited_once_with(
        user_id=user_id_from_token, update_data=update_model
    )


@pytest.mark.asyncio
async def test_login_history_success(
    client: AsyncClient,
    fake_user_service: AsyncMock,
    auth_data: dict,
):

    class FakeHistory:
        def __init__(self, agent, ts):
            from datetime import datetime
            self.user_agent = agent
            self.auth_date = datetime.fromisoformat(ts)

    fake_user_service.get_login_history_paginated.return_value = [
        FakeHistory("Chrome", "2024-01-01T00:00:00"),
        FakeHistory("Safari", "2024-01-02T00:00:00"),
    ]

    response = await client.get(
        "/auth/api/v1/users/me/login-history", headers=auth_data["headers"]
    )

    assert response.status_code == 200
    assert response.json() == [
        {"user_agent": "Chrome", "login_at": "2024-01-01T00:00:00"},
        {"user_agent": "Safari", "login_at": "2024-01-02T00:00:00"},
    ]
