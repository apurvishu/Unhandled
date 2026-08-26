"""Tests for Port Congestion prediction endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_get_port_congestion(client: AsyncClient, test_users: dict):
    port_id = test_users["port"].id
    headers = create_auth_headers(test_users["port_owner"])
    response = await client.get(f"/api/v1/congestion/{port_id}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_predict_port_congestion(client: AsyncClient, test_users: dict):
    port_id = test_users["port"].id
    headers = create_auth_headers(test_users["procurement"])
    payload = {
        "port_id": port_id,
        "horizon_hours": 48,
    }
    response = await client.post("/api/v1/congestion/predict", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["port_id"] == port_id
    assert data["congestion_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["predicted_waiting_time"] >= 0
    assert 0.0 <= data["berth_utilization"] <= 100.0
    assert 0.0 <= data["confidence"] <= 1.0
