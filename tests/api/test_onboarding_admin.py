"""Unit tests for onboarding admin endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.fixture
def identity_payload() -> dict:
    return {
        "doctor_id": 999,
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin.test@example.com",
        "phone_number": "1112223334",
        "onboarding_status": "pending"
    }

@pytest.fixture
async def sample_identity(client: AsyncClient, auth_headers: dict[str, str], identity_payload: dict) -> dict:
    """Create a sample identity."""
    response = await client.post("/api/v1/onboarding-admin/identities", json=identity_payload, headers=auth_headers)
    return response.json()

@pytest.mark.asyncio
async def test_create_identity(client: AsyncClient, auth_headers: dict[str, str], identity_payload: dict) -> None:
    """Test create identity."""
    payload = identity_payload.copy()
    payload["doctor_id"] = 888
    payload["email"] = "another.test@example.com"
    payload["phone_number"] = "2223334445"
    response = await client.post("/api/v1/onboarding-admin/identities", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["email"] == "another.test@example.com"

@pytest.mark.asyncio
async def test_get_identity(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test get identity by doctor_id."""
    doctor_id = sample_identity["doctor_id"]
    response = await client.get(f"/api/v1/onboarding-admin/identities?doctor_id={doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin.test@example.com"

@pytest.mark.asyncio
async def test_get_identity_by_email(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test get identity by email."""
    email = sample_identity["email"]
    response = await client.get(f"/api/v1/onboarding-admin/identities?email={email}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["doctor_id"] == sample_identity["doctor_id"]

@pytest.mark.asyncio
async def test_upsert_details(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test upsert details."""
    doctor_id = sample_identity["doctor_id"]
    payload = {
        "specialty": "Neurology",
        "years_of_experience": 15
    }
    response = await client.put(f"/api/v1/onboarding-admin/details/{doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["specialty"] == "Neurology"

@pytest.mark.asyncio
async def test_get_details(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test get details."""
    doctor_id = sample_identity["doctor_id"]
    # Upsert first to ensure it's there
    await client.put(f"/api/v1/onboarding-admin/details/{doctor_id}", json={"specialty": "Test"}, headers=auth_headers)

    response = await client.get(f"/api/v1/onboarding-admin/details/{doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["doctor_id"] == doctor_id

@pytest.mark.asyncio
async def test_add_media(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test add media record."""
    doctor_id = sample_identity["doctor_id"]
    payload = {
        "media_type": "image",
        "media_category": "profile_photo",
        "field_name": "profile_photo",
        "file_uri": "/path/to/photo.jpg",
        "file_name": "photo.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg"
    }
    response = await client.post(f"/api/v1/onboarding-admin/media/{doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["doctor_id"] == doctor_id

@pytest.mark.asyncio
async def test_list_media(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test list media records."""
    doctor_id = sample_identity["doctor_id"]
    payload = {
        "media_type": "image",
        "media_category": "profile_photo",
        "field_name": "profile_photo",
        "file_uri": "/path/to/photo.jpg",
        "file_name": "photo.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg"
    }
    await client.post(f"/api/v1/onboarding-admin/media/{doctor_id}", json=payload, headers=auth_headers)

    response = await client.get(f"/api/v1/onboarding-admin/media/{doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_delete_media(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test delete media record."""
    doctor_id = sample_identity["doctor_id"]
    payload = {
        "media_type": "image",
        "media_category": "profile_photo",
        "field_name": "profile_photo",
        "file_uri": "/path/to/photo_del.jpg",
        "file_name": "photo_del.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg"
    }
    create_resp = await client.post(f"/api/v1/onboarding-admin/media/{doctor_id}", json=payload, headers=auth_headers)
    media_id = create_resp.json()["media_id"]

    response = await client.delete(f"/api/v1/onboarding-admin/media/{media_id}", headers=auth_headers)
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_status_history(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test log and get status history."""
    doctor_id = sample_identity["doctor_id"]
    payload = {
        "previous_status": "pending",
        "new_status": "verified",
        "changed_by": "1",
        "reason": "Looking good"
    }

    # Log status
    post_resp = await client.post(f"/api/v1/onboarding-admin/status-history/{doctor_id}", json=payload, headers=auth_headers)
    assert post_resp.status_code == 201

    # Get history
    get_resp = await client.get(f"/api/v1/onboarding-admin/status-history/{doctor_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()) > 0

@pytest.mark.asyncio
async def test_list_doctors_with_filter(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test aggregated doctors list."""
    response = await client.get("/api/v1/onboarding-admin/doctors", headers=auth_headers)
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

@pytest.mark.asyncio
async def test_get_doctor_full_by_id(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test full aggregate fetch."""
    doctor_id = sample_identity["doctor_id"]
    response = await client.get(f"/api/v1/onboarding-admin/doctors/lookup?doctor_id={doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "identity" in data
    assert data["identity"]["email"] == sample_identity["email"]

@pytest.mark.asyncio
async def test_get_doctor_full_by_email(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test full aggregate fetch by email."""
    email = sample_identity["email"]
    response = await client.get(f"/api/v1/onboarding-admin/doctors/lookup?email={email}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["identity"]["doctor_id"] == sample_identity["doctor_id"]

@pytest.mark.asyncio
async def test_get_doctor_full_by_phone(client: AsyncClient, auth_headers: dict[str, str], sample_identity: dict) -> None:
    """Test full aggregate fetch by phone."""
    phone = sample_identity["phone_number"]
    response = await client.get(f"/api/v1/onboarding-admin/doctors/lookup?phone={phone}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["identity"]["doctor_id"] == sample_identity["doctor_id"]
