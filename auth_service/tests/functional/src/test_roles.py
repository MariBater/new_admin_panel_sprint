import pytest
from httpx import AsyncClient
from src.models.entity import User


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    resp = await client.post("/api/v1/roles/", json={"name": "admin"})
    assert resp.status_code == 201

    data = resp.json()
    assert data["name"] == "admin"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_all(client: AsyncClient):
    await client.post("/api/v1/roles/", json={"name": "viewer"})

    resp = await client.get("/api/v1/roles/")
    assert resp.status_code == 200

    roles = resp.json()
    assert isinstance(roles, list)
    assert len(roles) > 0


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient):
    role = (await client.post("/api/v1/roles/", json={"name": "temp"})).json()

    resp = await client.put(f"/api/v1/roles/{role['id']}", json={"name": "updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "updated"


@pytest.mark.asyncio
async def test_delete_role(client):
    role = (await client.post("/api/v1/roles/", json={"name": "todelete"})).json()

    resp = await client.delete(f"/api/v1/roles/{role['id']}")
    assert resp.status_code == 200
    assert resp.json() is True


@pytest.mark.asyncio
async def test_set_and_check_role(client: AsyncClient, session):

    user = User(login="john", password="123", email="john@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    role = (await client.post("/api/v1/roles/", json={"name": "manager"})).json()

    resp = await client.post(
        "/api/v1/roles/set",
        json={"user_id": str(user.id), "role_id": role["id"]},
    )
    assert resp.status_code == 200
    assert resp.json() is True

    check = await client.post(
        "/api/v1/roles/check",
        json={"user_id": str(user.id), "role_id": role["id"]},
    )
    assert check.status_code == 200
    assert check.json() is True


@pytest.mark.asyncio
async def test_revoke_role(client: AsyncClient, session):

    user = User(login="bob", password="123", email="bob@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    role = (await client.post("/api/v1/roles/", json={"name": "testrole"})).json()

    await client.post(
        "/api/v1/roles/set", json={"user_id": str(user.id), "role_id": role["id"]}
    )

    resp = await client.post(
        "/api/v1/roles/revoke",
        json={"user_id": str(user.id), "role_id": role["id"]},
    )
    assert resp.status_code == 200
    assert resp.json() is True

    resp2 = await client.post(
        "/api/v1/roles/revoke",
        json={"user_id": str(user.id), "role_id": role["id"]},
    )
    assert resp2.status_code == 404
