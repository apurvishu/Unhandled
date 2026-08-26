"""Tests for Vessel Matching and Optimization Recommendation Engine."""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_match_vessels_endpoint(client: AsyncClient, test_users: dict):
    proc_headers = create_auth_headers(test_users["procurement"])
    owner_headers = create_auth_headers(test_users["ship_owner"])
    port_id = test_users["port"].id

    # Seed suitable available vessel
    await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9555555",
            "name": "MV Optimum Carrier",
            "vessel_type": "PANAMAX",
            "dwt": 76000.0,
            "draft": 13.8,
            "loa": 225.0,
            "latitude": 1.20,
            "longitude": 103.80,
        },
        headers=owner_headers,
    )

    payload = {
        "cargo_quantity_mt": 70000.0,
        "origin": "Dampier, Australia",
        "destination_port_id": port_id,
        "preferred_vessel_type": "PANAMAX",
        "max_draft": 15.0,
    }
    response = await client.post("/api/v1/optimization/match-vessels", json=payload, headers=proc_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_candidates"] >= 1
    top_match = data["matches"][0]
    assert "score" in top_match
    assert top_match["score"] > 0
    assert "estimated_freight_rate" in top_match
    assert "estimated_total_cost" in top_match
    assert "congestion_risk" in top_match


@pytest.mark.asyncio
async def test_optimization_recommend_endpoint(client: AsyncClient, test_users: dict):
    proc_headers = create_auth_headers(test_users["procurement"])
    port_id = test_users["port"].id

    payload = {
        "cargo_quantity_mt": 65000.0,
        "origin": "Santos, Brazil",
        "destination_port_id": port_id,
        "preferred_vessel_type": "PANAMAX",
    }
    response = await client.post("/api/v1/optimization/recommend", json=payload, headers=proc_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["recommendation"] in ["BOOK_NOW", "WAIT", "REVIEW_ALTERNATIVES"]
    assert "freight_rate" in data
    assert "reason" in data
    assert len(data["reason"]) > 10
    assert "confidence" in data
