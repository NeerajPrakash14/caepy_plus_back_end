"""Unit tests for admin dropdown endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.mark.asyncio
async def test_seed_dropdown_values(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test seeding initial dropdown values."""
    response = await client.post("/api/v1/admin/dropdown-options/seed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_list_dropdown_fields(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test listing all configured dropdown fields."""
    response = await client.get("/api/v1/admin/dropdown-options/fields", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_option(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test creating a new dropdown option."""
    payload = {
        "value": "Test Specialty",
        "display_label": "Test Specialty Label",
        "description": "Test description"
    }
    response = await client.post(
        "/api/v1/admin/dropdown-options/fields/specialty",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["value"] == "Test Specialty"

@pytest.mark.asyncio
async def test_get_field_options(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting options for a field."""
    response = await client.get("/api/v1/admin/dropdown-options/fields/specialty", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert isinstance(data["options"], list)

@pytest.mark.asyncio
async def test_bulk_create_options(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test bulk creating dropdown options."""
    payload = {
        "values": ["Bulk 1", "Bulk 2"]
    }
    response = await client.post(
        "/api/v1/admin/dropdown-options/fields/specialty/bulk",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["created_count"] == 2

@pytest.mark.asyncio
async def test_update_option(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test updating a dropdown option."""
    # First create
    create_resp = await client.post(
        "/api/v1/admin/dropdown-options/fields/specialty",
        json={"value": "Update Me"},
        headers=auth_headers
    )
    assert create_resp.status_code == 201

    # Get ID
    list_resp = await client.get("/api/v1/admin/dropdown-options/fields/specialty", headers=auth_headers)
    option_id = next(opt["id"] for opt in list_resp.json()["options"] if opt["value"] == "Update Me")

    # Update
    payload = {"display_label": "Updated Label", "is_verified": True}
    response = await client.put(
        f"/api/v1/admin/dropdown-options/options/{option_id}",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_label"] == "Updated Label"
    assert data["is_verified"] is True

@pytest.mark.asyncio
async def test_deactivate_option(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test deactivating a dropdown option."""
    create_resp = await client.post(
        "/api/v1/admin/dropdown-options/fields/specialty",
        json={"value": "Deactivate Me"},
        headers=auth_headers
    )
    assert create_resp.status_code == 201

    # Get ID
    list_resp = await client.get("/api/v1/admin/dropdown-options/fields/specialty", headers=auth_headers)
    option_id = next(opt["id"] for opt in list_resp.json()["options"] if opt["value"] == "Deactivate Me")

    response = await client.delete(
        f"/api/v1/admin/dropdown-options/options/{option_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["is_active"] is False

@pytest.mark.asyncio
async def test_verify_option(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test verifying a dropdown option."""
    create_resp = await client.post(
        "/api/v1/admin/dropdown-options/fields/specialty",
        json={"value": "Verify Me"},
        headers=auth_headers
    )
    assert create_resp.status_code == 201

    # Get ID
    list_resp = await client.get("/api/v1/admin/dropdown-options/fields/specialty", headers=auth_headers)
    option_id = next(opt["id"] for opt in list_resp.json()["options"] if opt["value"] == "Verify Me")

    response = await client.post(
        f"/api/v1/admin/dropdown-options/options/{option_id}/verify",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["is_verified"] is True

@pytest.mark.asyncio
async def test_list_unverified_options(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test listing unverified options."""
    response = await client.get("/api/v1/admin/dropdown-options/unverified", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_dropdown_stats(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting dropdown stats."""
    response = await client.get("/api/v1/admin/dropdown-options/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_options" in data

@pytest.mark.asyncio
async def test_get_dropdown_data(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting public dropdown data."""
    response = await client.get("/api/v1/admin/dropdown-options/data", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
