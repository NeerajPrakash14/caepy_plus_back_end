"""Unit tests for auth endpoints (mimic login, etc.)."""

from __future__ import annotations

from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.mark.asyncio
async def test_validate_and_login_success(client: AsyncClient) -> None:
    """Test validateandlogin with mock OTP."""
    payload = {
        "phone_number": "+1234567890",
        "otp": "123456"  # Mock OTP from auth.py
    }
    response = await client.post("/api/v1/validateandlogin", json=payload)
    # the endpoint requires development mode, should succeed during pytest
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_validate_and_login_invalid_otp(client: AsyncClient) -> None:
    """Test validateandlogin with wrong OTP."""
    payload = {
        "phone_number": "+1234567890",
        "otp": "wrong"
    }
    response = await client.post("/api/v1/validateandlogin", json=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_mimic_admin_login(client: AsyncClient) -> None:
    """Test admin mimic login using the pre-seeded admin phone."""
    payload = {
        "phone": "+919999999999" # seeded admin from conftest setup_admin_user
    }
    response = await client.post("/api/v1/admin/login/mimic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert data["data"]["user"]["role"] == "admin"

@pytest.mark.asyncio
async def test_mimic_admin_login_not_found(client: AsyncClient) -> None:
    """Test admin mimic login with non-existent admin."""
    payload = {
        "phone": "+99999999999"
    }
    response = await client.post("/api/v1/admin/login/mimic", json=payload)
    assert response.status_code == 404
