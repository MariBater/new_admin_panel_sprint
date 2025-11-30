import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio


async def test_create_role(test_client: AsyncClient):
    """Тест успешного создания роли."""
    role_name = "test_role"
    response = await test_client.post("/api/v1/roles/", json={"name": role_name})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == role_name
    assert "id" in data


async def test_create_existing_role_fails(test_client: AsyncClient):
    """Тест: создание роли с существующим именем вызывает ошибку."""
    role_name = "duplicate_role"
    # Первое создание - успешно
    response1 = await test_client.post("/api/v1/roles/", json={"name": role_name})
    assert response1.status_code == status.HTTP_201_CREATED
    # Второе создание - ошибка
    response = await test_client.post("/api/v1/roles/", json={"name": role_name})
    assert response.status_code == status.HTTP_409_CONFLICT


async def test_get_all_roles(test_client: AsyncClient):
    """Тест получения списка всех ролей."""
    # Создадим несколько ролей для проверки
    await test_client.post("/api/v1/roles/", json={"name": "role1"})
    await test_client.post("/api/v1/roles/", json={"name": "role2"})

    response = await test_client.get("/api/v1/roles/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "role1" in [role["name"] for role in data]
    assert "role2" in [role["name"] for role in data]


async def test_update_role(test_client: AsyncClient):
    """Тест обновления имени роли."""
    # Создаем роль
    create_response = await test_client.post("/api/v1/roles/", json={"name": "updatable_role"},)
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.json()["id"]

    # Обновляем ее
    new_name = "updated_role_name"
    response = await test_client.put(f"/api/v1/roles/{role_id}", json={"name": new_name})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == new_name


async def test_delete_role(test_client: AsyncClient):
    """Тест удаления роли."""
    # Создаем роль
    create_response = await test_client.post("/api/v1/roles/", json={"name": "deletable_role"},)
    assert create_response.status_code == status.HTTP_201_CREATED
    role_id = create_response.json()["id"]

    # Удаляем ее
    response = await test_client.delete(f"/api/v1/roles/{role_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is True

    # Проверяем, что роль действительно удалена (попытка обновить ее вызовет ошибку)
    update_response = await test_client.put(f"/api/v1/roles/{role_id}", json={"name": "new_name"})
    assert update_response.status_code == status.HTTP_404_NOT_FOUND


async def test_set_and_check_role_for_user(test_client: AsyncClient, test_user_data: dict):
    """Тест назначения и проверки роли у пользователя."""
    # 1. Создаем пользователя
    user_response = await test_client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]

    # 2. Создаем роль
    role_response = await test_client.post("/api/v1/roles/", json={"name": "viewer"},)
    role_id = role_response.json()["id"]

    # 3. Проверяем, что у пользователя еще нет этой роли
    check_payload = {"user_id": str(user_id), "role_id": str(role_id)}
    check_response_before = await test_client.post("/api/v1/roles/check", json=check_payload)
    assert check_response_before.status_code == status.HTTP_200_OK
    assert check_response_before.json() is False

    # 4. Назначаем роль
    set_payload = {"user_id": str(user_id), "role_id": str(role_id)}
    set_response = await test_client.post("/api/v1/roles/set", json=set_payload)
    assert set_response.status_code == status.HTTP_200_OK
    assert set_response.json() is True

    # 5. Проверяем, что роль назначена
    check_response_after = await test_client.post("/api/v1/roles/check", json=check_payload)
    assert check_response_after.status_code == status.HTTP_200_OK
    assert check_response_after.json() is True


async def test_revoke_role_from_user(test_client: AsyncClient, test_user_data: dict):
    """Тест отзыва роли у пользователя."""
    # 1. Создаем пользователя и роль, назначаем роль
    user_response = await test_client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    role_response = await test_client.post("/api/v1/roles/", json={"name": "temporary_role"},)
    role_id = role_response.json()["id"]
    await test_client.post("/api/v1/roles/set", json={"user_id": str(user_id), "role_id": str(role_id)})

    # 2. Проверяем, что роль действительно есть
    check_payload = {"user_id": str(user_id), "role_id": str(role_id)}
    check_response = await test_client.post("/api/v1/roles/check", json=check_payload)
    assert check_response.status_code == status.HTTP_200_OK
    assert check_response.json() is True

    # 3. Отзываем роль
    revoke_payload = {"user_id": str(user_id), "role_id": str(role_id)}
    revoke_response = await test_client.post("/api/v1/roles/revoke", json=revoke_payload)
    assert revoke_response.status_code == status.HTTP_200_OK
    assert revoke_response.json() is True

    # 4. Проверяем, что роли больше нет
    check_response_after_revoke = await test_client.post("/api/v1/roles/check", json=check_payload)
    assert check_response_after_revoke.json() is False