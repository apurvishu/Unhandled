"""
End-to-End Tests for Chartering Workflow:
Cargo -> Charter Request -> Vessel Registration -> Charter Offer -> Selection -> Contract
"""

import pytest
from httpx import AsyncClient

from tests.conftest import create_auth_headers


@pytest.mark.asyncio
async def test_full_chartering_workflow(client: AsyncClient, test_users: dict):
    proc_headers = create_auth_headers(test_users["procurement"])
    owner_headers = create_auth_headers(test_users["ship_owner"])
    port_id = test_users["port"].id

    # Step 1: Procurement Officer creates cargo requirement
    cargo_resp = await client.post(
        "/api/v1/cargo",
        json={
            "commodity": "Coking Coal",
            "quantity_mt": 75000.0,
            "origin": "Richards Bay, South Africa",
            "destination_port_id": port_id,
            "preferred_vessel_type": "PANAMAX",
        },
        headers=proc_headers,
    )
    assert cargo_resp.status_code == 201
    cargo_id = cargo_resp.json()["data"]["id"]

    # Step 2: Procurement Officer publishes Charter Request
    req_resp = await client.post(
        "/api/v1/charters/requests",
        json={
            "cargo_requirement_id": cargo_id,
            "vessel_type": "PANAMAX",
            "minimum_dwt": 75000.0,
            "maximum_draft": 14.5,
        },
        headers=proc_headers,
    )
    assert req_resp.status_code == 201
    charter_req_id = req_resp.json()["data"]["id"]

    # Step 3: Ship Owner registers a suitable vessel
    vessel_resp = await client.post(
        "/api/v1/vessels",
        json={
            "imo_number": "IMO9345678",
            "name": "MV Ocean Voyager",
            "vessel_type": "PANAMAX",
            "dwt": 82000.0,
            "draft": 14.0,
            "loa": 229.0,
        },
        headers=owner_headers,
    )
    assert vessel_resp.status_code == 201
    vessel_id = vessel_resp.json()["data"]["id"]

    # Step 4: Ship Owner submits a Charter Offer
    offer_resp = await client.post(
        "/api/v1/charters/offers",
        json={
            "charter_request_id": charter_req_id,
            "vessel_id": vessel_id,
            "freight_rate": 24.50,
            "total_cost": 24.50 * 75000.0,
        },
        headers=owner_headers,
    )
    assert offer_resp.status_code == 201
    offer_id = offer_resp.json()["data"]["id"]
    assert offer_resp.json()["data"]["status"] == "PENDING"

    # Step 5: Procurement Officer retrieves offers
    offers_list_resp = await client.get(
        f"/api/v1/charters/requests/{charter_req_id}/offers",
        headers=proc_headers,
    )
    assert offers_list_resp.status_code == 200
    offers = offers_list_resp.json()["data"]
    assert len(offers) == 1
    assert offers[0]["id"] == offer_id

    # Step 6: Procurement Officer selects the winning offer
    select_resp = await client.post(
        f"/api/v1/charters/{charter_req_id}/select-offer",
        json={"offer_id": offer_id},
        headers=proc_headers,
    )
    assert select_resp.status_code == 200
    contract_data = select_resp.json()["data"]
    assert contract_data["selected_offer_id"] == offer_id
    assert contract_data["status"] == "ACTIVE"
    assert contract_data["agreed_rate"] == 24.50

    # Step 7: Verify Vessel status is now CHARTERED
    vessel_check = await client.get(f"/api/v1/vessels/{vessel_id}", headers=proc_headers)
    assert vessel_check.json()["data"]["status"] == "CHARTERED"
