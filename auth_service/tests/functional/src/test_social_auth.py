from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from starlette.responses import RedirectResponse
from httpx import AsyncClient
import uuid

from auth_service.src.models.entity import User


@pytest.fixture
def mock_user_info():
    """Фикстура, имитирующая информацию о пользователе от SSO провайдера."""
    user_info = MagicMock()
    user_info.email = "yandex_user@example.com"
    user_info.first_name = "Yandex"
    user_info.last_name = "User"
    return user_info


@pytest.mark.asyncio
@patch("auth_service.src.api.v1.social_auth.yandex_sso", new_callable=AsyncMock)
async def test_yandex_login_redirect(mock_sso, client: AsyncClient):
    """Тест: эндпоинт /login должен перенаправлять на страницу аутентификации Яндекса."""
    # Arrange
    redirect_url = "https://oauth.yandex.ru/authorize?response_type=code&client_id=..."
    mock_sso.get_login_redirect.return_value = RedirectResponse(url=redirect_url)

    # Act
    response = await client.get("/auth/api/v1/oauth/yandex/login", follow_redirects=False)

    # Assert
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == redirect_url
    mock_sso.get_login_redirect.assert_awaited_once()


@pytest.mark.asyncio
@patch("auth_service.src.api.v1.social_auth.yandex_sso", new_callable=AsyncMock)
async def test_yandex_callback_new_user(
    mock_sso,
    client: AsyncClient,
    fake_user_service: AsyncMock,
    fake_auth_service: AsyncMock,
    mock_user_info: MagicMock,
):
    """Тест: callback создает нового пользователя, если он не найден по email."""
    # Arrange
    mock_sso.verify_and_process.return_value = mock_user_info
    fake_user_service.get_user_by_email.return_value = None  # Пользователя нет
    new_user = User(id=uuid.uuid4(), login=mock_user_info.email, email=mock_user_info.email, password="social_user_pw")
    fake_user_service.create_social_user.return_value = new_user
    fake_auth_service.create_access_token.return_value = "new_access_token"
    fake_auth_service.create_refresh_token.return_value = "new_refresh_token"

    # Act
    response = await client.get("/auth/api/v1/oauth/yandex/callback?code=some_code")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
    }
    fake_user_service.get_user_by_email.assert_awaited_once_with(
        email=mock_user_info.email
    )
    fake_user_service.create_social_user.assert_awaited_once()
    # The login method is called on the user service, not the auth service
    fake_user_service.login.assert_awaited_once()


@pytest.mark.asyncio
@patch("auth_service.src.api.v1.social_auth.yandex_sso", new_callable=AsyncMock)
async def test_yandex_callback_existing_user(
    mock_sso,
    client: AsyncClient,
    fake_user_service: AsyncMock,
    fake_auth_service: AsyncMock,
    mock_user_info: MagicMock,
):
    """Тест: callback аутентифицирует существующего пользователя."""
    # Arrange
    mock_sso.verify_and_process.return_value = mock_user_info
    existing_user = User(id=uuid.uuid4(), login=mock_user_info.email, email=mock_user_info.email, password="social_user_pw")
    fake_user_service.get_user_by_email.return_value = existing_user
    fake_auth_service.create_access_token.return_value = "access_token"
    fake_auth_service.create_refresh_token.return_value = "refresh_token"

    # Act
    response = await client.get("/auth/api/v1/oauth/yandex/callback?code=some_code")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "access_token": "access_token",
        "refresh_token": "refresh_token",
    }
    fake_user_service.get_user_by_email.assert_awaited_once_with(
        email=mock_user_info.email
    )
    fake_user_service.create_social_user.assert_not_awaited()  # Не должен вызываться
    # The login method is called on the user service, not the auth service
    fake_user_service.login.assert_awaited_once()


@pytest.mark.asyncio
@patch("auth_service.src.api.v1.social_auth.yandex_sso", new_callable=AsyncMock)
async def test_yandex_callback_verification_error(mock_sso, client: AsyncClient):
    """Тест: callback возвращает ошибку, если верификация в Яндексе не удалась."""
    # Arrange
    error_message = "Invalid code"
    mock_sso.verify_and_process.side_effect = Exception(error_message)

    # Act
    response = await client.get("/auth/api/v1/oauth/yandex/callback?code=invalid_code")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error_message in response.json()["detail"]