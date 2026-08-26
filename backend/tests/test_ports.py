"""Tests for Port and Berth CRUD and operations."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_list_ports(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    response = await client.get("/api/v1/ports", headers=headers)
    assert response.status_code == 200
    ports = response.json()["data"]
    assert len(ports) >= 1
    assert ports[0]["name"] == "Port of Singapore"


@pytest.mark.asyncio
async def test_create_port_by_port_owner(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["port_owner"])
    payload = {
        "name": "Port of Rotterdam",
        "country": "Netherlands",
        "latitude": 51.9244,
        "longitude": 4.4777,
        "max_draft": 22.5,
        "max_loa": 450.0,
        "cargo_capacity": 100000000.0,
    }
    response = await client.post("/api/v1/ports", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Port of Rotterdam"


@pytest.mark.asyncio
async def test_create_berth_at_port(client: AsyncClient, test_users: dict):
    port_id = test_users["port"].id
    headers = create_auth_headers(test_users["port_owner"])
    payload = {
        "name": "Berth 101 - Deepwater",
        "max_draft": 17.5,
        "max_loa": 360.0,
        "cargo_handling_rate": 2500.0,
        "status": "AVAILABLE",
    }
    response = await client.post(f"/api/v1/berths/port/{port_id}", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Berth 101 - Deepwater"
    assert data["port_id"] == port_id
