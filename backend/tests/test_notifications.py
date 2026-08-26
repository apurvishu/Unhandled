"""Tests for Notification endpoints and health check."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["success"] is True


@pytest.mark.asyncio
async def test_notifications_endpoint(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    response = await client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)
