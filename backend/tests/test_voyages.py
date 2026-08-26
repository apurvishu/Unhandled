"""Tests for Voyage and Port Call management."""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_create_and_list_voyages(client: AsyncClient, test_users: dict):
    owner_headers = create_auth_headers(test_users["ship_owner"])
    port_id = test_users["port"].id

    # Create vessel first
    vessel_resp = await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9993333",
            "name": "MV Transoceanic",
            "vessel_type": "CAPESIZE",
            "dwt": 175000.0,
        },
        headers=owner_headers,
    )
    vessel_id = vessel_resp.json()["data"]["id"]

    # Create voyage
    voyage_payload = {
        "vessel_id": vessel_id,
        "origin_port_id": port_id,
        "destination_port_id": port_id,
        "departure_time": datetime.now(timezone.utc).isoformat(),
        "estimated_cost": 1500000.0,
    }
    create_resp = await client.post("/api/v1/voyages", json=voyage_payload, headers=owner_headers)
    assert create_resp.status_code == 201
    voyage_id = create_resp.json()["data"]["id"]

    # List voyages
    list_resp = await client.get("/api/v1/voyages", headers=owner_headers)
    assert list_resp.status_code == 200
    voyages = list_resp.json()["data"]
    assert any(v["id"] == voyage_id for v in voyages)

    # Get single voyage
    get_resp = await client.get(f"/api/v1/voyages/{voyage_id}", headers=owner_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == voyage_id

    # Update voyage
    update_resp = await client.put(
        f"/api/v1/voyages/{voyage_id}",
        json={"status": "IN_PROGRESS", "actual_cost": 1480000.0},
        headers=owner_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_create_port_call(client: AsyncClient, test_users: dict):
    owner_headers = create_auth_headers(test_users["ship_owner"])
    port_id = test_users["port"].id

    # Create vessel and voyage
    v_resp = await client.post(
        "/api/v1/vessels",
        json={"imo_number": "IMO9994444", "name": "MV Port Caller", "vessel_type": "SUPRAMAX", "dwt": 58000.0},
        headers=owner_headers,
    )
    vessel_id = v_resp.json()["data"]["id"]

    voyage_resp = await client.post(
        "/api/v1/voyages",
        json={"vessel_id": vessel_id, "origin_port_id": port_id, "destination_port_id": port_id},
        headers=owner_headers,
    )
    voyage_id = voyage_resp.json()["data"]["id"]

    # Add port call
    pc_resp = await client.post(
        f"/api/v1/voyages/{voyage_id}/port-calls",
        json={"voyage_id": voyage_id, "port_id": port_id},
        headers=owner_headers,
    )
    assert pc_resp.status_code == 201
    assert pc_resp.json()["data"]["port_id"] == port_id
