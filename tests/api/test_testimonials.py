"""Unit tests for testimonials endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.fixture
async def sample_testimonial(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    """Create a sample testimonial and return its ID."""
    payload = {
        "doctor_name": "Dr. Test",
        "comment": "Great doctor!",
        "specialty": "Cardiology",
        "designation": "Senior Consultant",
        "hospital_name": "Test Hospital",
        "location": "Test City",
        "rating": 5,
        "is_active": True,
        "display_order": 1
    }
    response = await client.post("/api/v1/testimonials", json=payload, headers=auth_headers)
    return response.json()["data"]["id"]

@pytest.mark.asyncio
async def test_create_testimonial(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test creating a testimonial."""
    payload = {
        "doctor_name": "Dr. Test",
        "comment": "Great doctor!",
        "specialty": "Cardiology",
        "designation": "Senior Consultant",
        "hospital_name": "Test Hospital",
        "location": "Test City",
        "rating": 5,
        "is_active": True,
        "display_order": 1
    }
    response = await client.post("/api/v1/testimonials", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["doctor_name"] == "Dr. Test"

@pytest.mark.asyncio
async def test_list_testimonials(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test public list API."""
    response = await client.get("/api/v1/testimonials", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "testimonials" in data
    assert True in (t["doctor_name"] == "Dr. Test" for t in data["testimonials"])

@pytest.mark.asyncio
async def test_list_all_testimonials_admin(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test admin list API."""
    response = await client.get("/api/v1/testimonials/admin", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["testimonials"]) > 0

@pytest.mark.asyncio
async def test_get_testimonial(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test get single testimonial by ID."""
    response = await client.get(f"/api/v1/testimonials/{sample_testimonial}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == sample_testimonial

@pytest.mark.asyncio
async def test_update_testimonial(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test update testimonial."""
    payload = {"doctor_name": "Dr. Updated Name"}
    response = await client.patch(f"/api/v1/testimonials/{sample_testimonial}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["doctor_name"] == "Dr. Updated Name"

@pytest.mark.asyncio
async def test_toggle_testimonial_active(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test toggling testimonial status."""
    response = await client.post(f"/api/v1/testimonials/{sample_testimonial}/toggle-active", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False # toggled

    # Toggle back
    response2 = await client.post(f"/api/v1/testimonials/{sample_testimonial}/toggle-active", headers=auth_headers)
    assert response2.json()["data"]["is_active"] is True

@pytest.mark.asyncio
async def test_delete_testimonial(client: AsyncClient, sample_testimonial: str, auth_headers: dict[str, str]) -> None:
    """Test soft delete testimonial."""
    response = await client.delete(f"/api/v1/testimonials/{sample_testimonial}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    # Verify it's gone
    response2 = await client.get(f"/api/v1/testimonials/{sample_testimonial}", headers=auth_headers)
    assert response2.status_code == 404
