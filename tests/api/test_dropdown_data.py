"""Unit tests for dropdown data endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient



@pytest.mark.asyncio
async def test_add_dropdown_values(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test adding dropdown values."""
    payload = {
        "field_name": "specialisations",
        "values": ["Test Specialty A", "Test Specialty B"]
    }
    response = await client.post("/api/v1/dropdown-data/values", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "Test Specialty A" in data["data"]["values"]

@pytest.mark.asyncio
async def test_get_specialisations(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting specialisations."""
    response = await client.get("/api/v1/dropdown-data/specialisations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # It might have predefined ones seeded from db plus the ones we added
    assert data["success"] is True
    assert isinstance(data["data"]["values"], list)

@pytest.mark.asyncio
async def test_get_sub_specialisations(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting sub-specialisations."""
    payload = {
        "field_name": "sub_specialisations",
        "values": ["Test Sub A"]
    }
    await client.post("/api/v1/dropdown-data/values", json=payload, headers=auth_headers)
    
    response = await client.get("/api/v1/dropdown-data/sub-specialisations", headers=auth_headers)
    assert response.status_code == 200
    assert "Test Sub A" in response.json()["data"]["values"]

@pytest.mark.asyncio
async def test_get_degrees(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting degrees."""
    payload = {
        "field_name": "degrees",
        "values": ["Test Degree A"]
    }
    await client.post("/api/v1/dropdown-data/values", json=payload, headers=auth_headers)
    
    response = await client.get("/api/v1/dropdown-data/degrees", headers=auth_headers)
    assert response.status_code == 200
    assert "Test Degree A" in response.json()["data"]["values"]

@pytest.mark.asyncio
async def test_get_all_dropdown_data(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting all dropdown data at once."""
    response = await client.get("/api/v1/dropdown-data/all", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "specialisations" in data
    assert "sub_specialisations" in data
    assert "degrees" in data
