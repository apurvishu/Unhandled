"""Tests for Freight Rate AI/ML forecasting endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_get_freight_forecast(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    response = await client.get(
        "/api/v1/forecast/freight?origin=Tubarao&destination=Qingdao&vessel_type=CAPESIZE&horizon_days=30",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["predicted_rate"] > 0
    assert data["currency"] == "USD"
    assert data["unit"] == "MT"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["trend"] in ["INCREASING", "DECREASING", "STABLE"]
    assert data["recommendation"] in ["BOOK_NOW", "WAIT", "NEUTRAL"]
    assert "model_version" in data


@pytest.mark.asyncio
async def test_post_freight_forecast(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    payload = {
        "origin": "Santos",
        "destination": "Rotterdam",
        "vessel_type": "PANAMAX",
        "forecast_horizon_days": 60,
    }
    response = await client.post("/api/v1/forecast/freight", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["predicted_rate"] > 0
    assert data["lower_bound"] <= data["predicted_rate"] <= data["upper_bound"]
