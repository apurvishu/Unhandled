"""Tests for user management and RBAC authorization."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_admin_can_list_users(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["admin"])
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 4


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_user_can_view_own_profile(client: AsyncClient, test_users: dict):
    user = test_users["ship_owner"]
    headers = create_auth_headers(user)
    response = await client.get(f"/api/v1/users/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == user.id


@pytest.mark.asyncio
async def test_user_cannot_view_others_profile(client: AsyncClient, test_users: dict):
    user1 = test_users["ship_owner"]
    user2 = test_users["port_owner"]
    headers = create_auth_headers(user1)
    response = await client.get(f"/api/v1/users/{user2.id}", headers=headers)
    assert response.status_code == 403
