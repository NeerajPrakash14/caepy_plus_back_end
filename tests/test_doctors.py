"""Unit tests for doctor CRUD endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_doctor(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test creating a new doctor."""
    response = await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["first_name"] == sample_doctor_data["first_name"]
    assert data["data"]["last_name"] == sample_doctor_data["last_name"]
    assert data["data"]["email"] == sample_doctor_data["email"]
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_create_doctor_invalid_email(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test creating a doctor with invalid email fails."""
    sample_doctor_data["email"] = "invalid-email"
    response = await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_doctor_by_id(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test retrieving a doctor by ID."""
    # First create a doctor
    create_response = await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)
    assert create_response.status_code == 201
    doctor_id = create_response.json()["data"]["id"]

    # Then retrieve it
    response = await client.get(f"/api/v1/doctors/{doctor_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == doctor_id
    assert data["data"]["first_name"] == sample_doctor_data["first_name"]
    assert data["data"]["last_name"] == sample_doctor_data["last_name"]


@pytest.mark.asyncio
async def test_get_doctor_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test retrieving a non-existent doctor returns 404."""
    fake_id = 99999  # Use a large integer that's unlikely to exist
    response = await client.get(f"/api/v1/doctors/{fake_id}", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "DOCTOR_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_doctors(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test listing all doctors with pagination."""
    # Create a doctor first
    await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)

    # List doctors
    response = await client.get("/api/v1/doctors", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_list_doctors_pagination(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test pagination parameters work correctly."""
    # Create multiple doctors with unique email and phone
    for i in range(3):
        doctor_data = sample_doctor_data.copy()
        doctor_data["email"] = f"doctor{i}@hospital.com"
        doctor_data["phone_number"] = f"+1-555-010{i}"  # Unique phone
        doctor_data["medical_registration_number"] = f"MED-{10000 + i}"  # Unique reg number
        await client.post("/api/v1/doctors", json=doctor_data, headers=auth_headers)

    # Test with page_size
    response = await client.get("/api/v1/doctors?page_size=2", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2


@pytest.mark.asyncio
async def test_update_doctor(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test updating a doctor."""
    # Create a doctor
    create_response = await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)
    doctor_id = create_response.json()["data"]["id"]

    # Update it
    update_data = {"first_name": "Updated", "last_name": "Name", "years_of_experience": 20}
    response = await client.put(f"/api/v1/doctors/{doctor_id}", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["first_name"] == "Updated"
    assert data["data"]["last_name"] == "Name"
    assert data["data"]["years_of_experience"] == 20


@pytest.mark.asyncio
async def test_delete_doctor(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test deleting a doctor."""
    # Create a doctor
    create_response = await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)
    doctor_id = create_response.json()["data"]["id"]

    # Delete it
    response = await client.delete(f"/api/v1/doctors/{doctor_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/doctors/{doctor_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_doctors(
    client: AsyncClient,
    sample_doctor_data: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test searching doctors by specialization."""
    # Create a doctor with specific specialization
    sample_doctor_data["primary_specialization"] = "Dermatology"
    sample_doctor_data["email"] = "dermatologist@hospital.com"  # Unique email
    await client.post("/api/v1/doctors", json=sample_doctor_data, headers=auth_headers)

    # Search by specialization
    response = await client.get("/api/v1/doctors?specialization=Dermatology", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["primary_specialization"] == "Dermatology"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, sample_doctor_data: dict) -> None:
    """Test that endpoints require authentication."""
    # Try to access without auth headers
    response = await client.get("/api/v1/doctors")
    assert response.status_code == 401

    # Try to create without auth headers
    response = await client.post("/api/v1/doctors", json=sample_doctor_data)
    assert response.status_code == 401
