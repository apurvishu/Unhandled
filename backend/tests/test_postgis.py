"""Tests for PostGIS Spatial queries, vessel tracking, and AIS integration."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_vessel_spatial_near_port_query(client: AsyncClient, test_users: dict):
    port = test_users["port"]
    owner_headers = create_auth_headers(test_users["ship_owner"])
    proc_headers = create_auth_headers(test_users["procurement"])

    # Create vessel near Singapore (port coordinates: 1.290270, 103.851959)
    await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9991111",
            "name": "MV Singapore Strait",
            "vessel_type": "PANAMAX",
            "dwt": 75000.0,
            "latitude": 1.28,
            "longitude": 103.84,  # ~1 nautical mile away
        },
        headers=owner_headers,
    )

    # Query near port
    resp = await client.get(f"/api/v1/vessels/near-port/{port.id}?radius_nm=50.0", headers=proc_headers)
    assert resp.status_code == 200
    vessels = resp.json()["data"]
    assert len(vessels) >= 1
    found = next((v for v in vessels if v["name"] == "MV Singapore Strait"), None)
    assert found is not None
    assert "distance_nm" in found
    assert found["distance_nm"] < 50.0


@pytest.mark.asyncio
async def test_ais_position_ingestion_and_track(client: AsyncClient, test_users: dict):
    owner_headers = create_auth_headers(test_users["ship_owner"])
    vessel_resp = await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9992222",
            "name": "MV Tracked Vessel",
            "vessel_type": "CAPESIZE",
            "dwt": 180000.0,
        },
        headers=owner_headers,
    )
    vessel_id = vessel_resp.json()["data"]["id"]

    # Ingest position
    pos_payload = {
        "latitude": 1.30,
        "longitude": 103.86,
        "speed": 13.4,
        "course": 95.0,
        "destination": "SG SIN",
    }
    ingest_resp = await client.post(
        f"/api/v1/ais/positions/{vessel_id}", json=pos_payload, headers=owner_headers
    )
    assert ingest_resp.status_code == 201
    assert ingest_resp.json()["data"]["vessel_id"] == vessel_id

    # Retrieve current position
    curr_pos = await client.get(f"/api/v1/ais/vessel/{vessel_id}/position", headers=owner_headers)
    assert curr_pos.status_code == 200
    assert curr_pos.json()["data"]["latitude"] == 1.30

    # Retrieve vessel track
    track_resp = await client.get(f"/api/v1/ais/vessel/{vessel_id}/track", headers=owner_headers)
    assert track_resp.status_code == 200
    assert track_resp.json()["data"]["total_positions"] >= 1
