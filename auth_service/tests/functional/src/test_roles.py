import uuid
import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock
from fastapi import status
from auth_service.src.models.entity import User, Role


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    # Mock the service layer to return a valid role object
    mock_role = MagicMock(spec=Role)
    mock_role.id = uuid.uuid4()
    mock_role.name = "admin"
    fake_role_service.create.return_value = mock_role

    resp = await client.post("/auth/api/v1/roles/", json={"name": "admin"}, headers=auth_data["headers"])
    assert resp.status_code == status.HTTP_201_CREATED

    data = resp.json()
    assert data["name"] == "admin"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_all(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    # Mock the service layer to return a list of role objects
    mock_role = MagicMock(spec=Role)
    mock_role.id = uuid.uuid4()
    mock_role.name = "viewer"
    fake_role_service.get_all.return_value = [mock_role]

    resp = await client.get("/auth/api/v1/roles/", headers=auth_data["headers"])
    assert resp.status_code == status.HTTP_200_OK

    roles = resp.json()
    assert isinstance(roles, list)
    assert len(roles) > 0


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    role_id = uuid.uuid4()
    mock_role = MagicMock(spec=Role)
    mock_role.id = role_id
    mock_role.name = "updated"
    fake_role_service.update.return_value = mock_role

    resp = await client.put(f"/auth/api/v1/roles/{role_id}", json={"name": "updated"}, headers=auth_data["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "updated"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    role_id = uuid.uuid4()
    fake_role_service.delete.return_value = True

    resp = await client.delete(f"/auth/api/v1/roles/{role_id}", headers=auth_data["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() is True


@pytest.mark.asyncio
async def test_set_and_check_role(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    user_id = uuid.uuid4()
    role_name = "manager"
    fake_role_service.set_role.return_value = True
    fake_role_service.check_role.return_value = True

    resp = await client.post(
        "/auth/api/v1/roles/set",
        json={"user_id": str(user_id), "role_name": role_name},
        headers=auth_data["headers"]
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() is True

    check = await client.post(
        "/auth/api/v1/roles/check",
        json={"user_id": str(user_id), "role_name": role_name},
        headers=auth_data["headers"]
    )
    assert check.status_code == status.HTTP_200_OK
    assert check.json() is True


@pytest.mark.asyncio
async def test_revoke_role(client: AsyncClient, auth_data: dict, fake_role_service: MagicMock):
    user_id = uuid.uuid4()

    role_name = "testrole"
    # First call to revoke succeeds
    fake_role_service.revoke_role.side_effect = [True, False]
    # We also need to mock set_role for the initial setup
    fake_role_service.set_role.return_value = True

    await client.post("/auth/api/v1/roles/set", json={"user_id": str(user_id), "role_name": role_name}, headers=auth_data["headers"])

    # First revoke should succeed
    resp1 = await client.post(
        "/auth/api/v1/roles/revoke",
        json={"user_id": str(user_id), "role_name": role_name},
        headers=auth_data["headers"],
    )
    assert resp1.status_code == status.HTTP_200_OK

    # Second revoke should fail because the role is already gone
    resp2 = await client.post(
        "/auth/api/v1/roles/revoke",
        json={"user_id": str(user_id), "role_name": role_name},
        headers=auth_data["headers"],
    )
    assert resp2.status_code == status.HTTP_404_NOT_FOUND
