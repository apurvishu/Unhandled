"""Tests for Cargo Requirement management."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_create_cargo_by_procurement_officer(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["procurement"])
    port_id = test_users["port"].id
    payload = {
        "commodity": "Iron Ore Fine",
        "quantity_mt": 70000.0,
        "origin": "Dampier, Australia",
        "destination_port_id": port_id,
        "preferred_vessel_type": "PANAMAX",
    }
    response = await client.post("/api/v1/cargo", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["commodity"] == "Iron Ore Fine"
    assert data["quantity_mt"] == 70000.0
    assert data["status"] == "OPEN"


@pytest.mark.asyncio
async def test_ship_owner_cannot_post_cargo(client: AsyncClient, test_users: dict):
    headers = create_auth_headers(test_users["ship_owner"])
    payload = {
        "commodity": "Thermal Coal",
        "quantity_mt": 50000.0,
        "origin": "Newcastle",
    }
    response = await client.post("/api/v1/cargo", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_cargo_requirements(client: AsyncClient, test_users: dict):
    proc_headers = create_auth_headers(test_users["procurement"])
    await client.post(
        "/api/v1/cargo",
        json={"commodity": "Grain Wheat", "quantity_mt": 40000.0, "origin": "Santos"},
        headers=proc_headers,
    )
    resp = await client.get("/api/v1/cargo", headers=proc_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
