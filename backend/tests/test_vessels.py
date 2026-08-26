"""Tests for Vessel CRUD, filtering, and availability."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_create_vessel_by_ship_owner(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["ship_owner"])
    payload = {
        "imo_number": "IMO9876543",
        "name": "MV Alpha Mariner",
        "vessel_type": "PANAMAX",
        "dwt": 75000.0,
        "loa": 225.0,
        "beam": 32.2,
        "draft": 14.2,
        "year_built": 2018,
        "flag": "Panama",
        "latitude": 1.25,
        "longitude": 103.80,
    }
    response = await client.post("/api/v1/vessels", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "MV Alpha Mariner"
    assert data["imo_number"] == "IMO9876543"
    assert data["vessel_type"] == "PANAMAX"
    assert data["status"] == "AVAILABLE"


@pytest.mark.asyncio
async def test_procurement_cannot_create_vessel(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    payload = {
        "imo_number": "IMO9111111",
        "name": "MV Unauthorized",
        "vessel_type": "CAPESIZE",
        "dwt": 180000.0,
    }
    response = await client.post("/api/v1/vessels", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_and_filter_vessels(client: AsyncClient, test_users: dict):
    owner_headers = create_auth_headers(test_users["ship_owner"])
    # Create a Supramax
    await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9222222",
            "name": "MV Supra Star",
            "vessel_type": "SUPRAMAX",
            "dwt": 55000.0,
        },
        headers=owner_headers,
    )

    # Filter by SUPRAMAX
    resp = await client.get("/api/v1/vessels?vessel_type=SUPRAMAX", headers=owner_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(v["name"] == "MV Supra Star" for v in data)


@pytest.mark.asyncio
async def test_get_available_vessels(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    resp = await client.get("/api/v1/vessels/available", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)
