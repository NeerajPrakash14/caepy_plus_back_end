"""Unit tests for hospitals and affiliations endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.fixture
def hospital_payload() -> dict:
    return {
        "name": "Apollo City Hospital",
        "address": "123 Main St",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
        "phone_number": "044-12345678",
        "email": "contact@apollo.test",
        "website": "www.apollo.test"
    }

@pytest.mark.asyncio
async def test_create_hospital(client: AsyncClient, auth_headers: dict[str, str], hospital_payload: dict) -> None:
    """Test creating a hospital."""
    response = await client.post("/api/v1/hospitals", json=hospital_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Apollo City Hospital"
    assert data["data"]["verification_status"] == "pending" # created by doctor defaults to pending, or in this case without doctor id it might still be pending or approved depending on logic

@pytest.fixture
async def sample_hospital(client: AsyncClient, auth_headers: dict[str, str], hospital_payload: dict) -> int:
    """Create a sample hospital and return its ID."""
    response = await client.post("/api/v1/hospitals", json=hospital_payload, headers=auth_headers)
    return response.json()["data"]["id"]

@pytest.mark.asyncio
async def test_get_hospital(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test getting single hospital."""
    response = await client.get(f"/api/v1/hospitals/{sample_hospital}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == sample_hospital

@pytest.mark.asyncio
async def test_search_hospitals(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test search hospitals by name (needs verification)."""
    # First verify it so it appears in search
    verify_payload = {"action": "verify", "verified_by": "1"}
    await client.post(f"/api/v1/hospitals/{sample_hospital}/verify", json=verify_payload, headers=auth_headers)

    response = await client.get("/api/v1/hospitals?q=Apollo&autocomplete=true", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0
    assert response.json()["data"][0]["name"] == "Apollo City Hospital"

@pytest.mark.asyncio
async def test_list_hospitals(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test list all hospitals."""
    response = await client.get("/api/v1/hospitals", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0

@pytest.mark.asyncio
async def test_list_pending_hospitals(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test list pending hospitals."""
    response = await client.get("/api/v1/hospitals?verification_status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert any(h["id"] == sample_hospital for h in data) # since it's pending initially

@pytest.mark.asyncio
async def test_verify_hospital(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test verify hospital admin action."""
    payload = {
        "action": "verify",
        "verified_by": "1"
    }
    response = await client.post(f"/api/v1/hospitals/{sample_hospital}/verify", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["verification_status"] == "verified"

@pytest.mark.asyncio
async def test_reject_hospital(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test reject hospital admin action."""
    payload = {
        "action": "reject",
        "verified_by": "1",
        "rejection_reason": "Duplicate entry"
    }
    response = await client.post(f"/api/v1/hospitals/{sample_hospital}/verify", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["verification_status"] == "rejected"

@pytest.mark.asyncio
async def test_update_hospital(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test updating hospital."""
    payload = {
        "city": "Madurai",
        "website": "https://www.apollo.test"
    }
    response = await client.patch(f"/api/v1/hospitals/{sample_hospital}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["city"] == "Madurai"
    assert data["website"] == "https://www.apollo.test"

@pytest.mark.asyncio
async def test_delete_hospital(client: AsyncClient, sample_hospital: int, auth_headers: dict[str, str]) -> None:
    """Test deleting hospital."""
    response = await client.delete(f"/api/v1/hospitals/{sample_hospital}", headers=auth_headers)
    assert response.status_code == 200

    # Verify it doesn't appear in list (if active_only logic applies) or check direct get is_active=False
    get_resp = await client.get(f"/api/v1/hospitals/{sample_hospital}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["is_active"] is False

# --- Affiliations Tests ---

@pytest.fixture
async def sample_doctor_id() -> int:
    return 1 # Assume doctor ID 1 exists from mock seeds

@pytest.mark.asyncio
async def test_create_affiliation(client: AsyncClient, sample_hospital: int, sample_doctor_id: int, auth_headers: dict[str, str]) -> None:
    """Test creating doctor-hospital affiliation."""
    payload = {
        "hospital_id": sample_hospital,
        "consultation_fee": 500,
        "consultation_type": "in_person",
        "designation": "Senior Surgeon",
        "department": "Surgery",
        "is_primary": True
    }
    response = await client.post(f"/api/v1/hospitals/affiliations?doctor_id={sample_doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["hospital_id"] == sample_hospital

@pytest.mark.asyncio
async def test_create_affiliation_with_new_hospital(client: AsyncClient, sample_doctor_id: int, auth_headers: dict[str, str]) -> None:
    """Test creating affiliation along with new hospital."""
    payload = {
        "hospital_name": "New Metro Hospital",
        "hospital_city": "Bangalore",
        "hospital_state": "Karnataka",
        "consultation_fee": 1000,
        "consultation_type": "both",
        "designation": "Consultant",
        "department": "General Medicine"
    }
    response = await client.post(f"/api/v1/hospitals/affiliations/with-new-hospital?doctor_id={sample_doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["consultation_fee"] == 1000
    assert "Hospital" in response.json()["message"]
