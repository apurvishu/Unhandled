"""Tests for authentication and token validation."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "password123",
        "role": "PROCUREMENT_OFFICER",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "jane@example.com"
    assert data["data"]["role"] == "PROCUREMENT_OFFICER"
    assert "password_hash" not in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_users: dict):
    payload = {
        "name": "Duplicate User",
        "email": "admin@test.com",  # Already exists
        "password": "password123",
        "role": "ADMIN",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_users: dict):
    form_data = {
        "username": "admin@test.com",
        "password": "password123",
    }
    response = await client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_users: dict):
    form_data = {
        "username": "admin@test.com",
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_users: dict):
    # Login first
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.com", "password": "password123"},
    )
    tokens = login_resp.json()

    # Refresh
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


@pytest.mark.asyncio
async def test_get_me_profile(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "procurement@test.com"
    assert data["data"]["role"] == "PROCUREMENT_OFFICER"
