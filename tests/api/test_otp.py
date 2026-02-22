"""Unit tests for otp endpoints (request, verify, google)."""

from __future__ import annotations

from typing import TYPE_CHECKING
import pytest
from unittest.mock import patch

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.mark.asyncio
async def test_request_otp(client: AsyncClient) -> None:
    """Test OTP request."""
    # We patch the service so it doesn't try connecting to external SMS or Redis logic if possible
    # But since it falls back to in-memory, we can just test the endpoint directly.
    payload = {"mobile_number": "9876543210"}
    with patch("src.app.services.otp_service.OTPService.send_otp") as mock_send:
        mock_send.return_value = (True, "OTP Sent")
        response = await client.post("/api/v1/auth/otp/request", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_verify_otp(client: AsyncClient) -> None:
    """Test OTP verify."""
    payload = {"mobile_number": "9876543210", "otp": "999999"}
    with patch("src.app.services.otp_service.OTPService.verify_otp") as mock_verify:
        mock_verify.return_value = (True, "OTP Verified")
        
        response = await client.post("/api/v1/auth/otp/verify", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data

@pytest.mark.asyncio
async def test_resend_otp(client: AsyncClient) -> None:
    """Test OTP resend."""
    payload = {"mobile_number": "9876543210"}
    with patch("src.app.services.otp_service.OTPService.send_otp") as mock_send:
        mock_send.return_value = (True, "OTP Resent")
        response = await client.post("/api/v1/auth/otp/resend", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_verify_admin_otp(client: AsyncClient) -> None:
    """Test admin OTP verify."""
    # The endpoint bypasses OTP verification in mimic mode according to source comments
    # We just need to give it the valid seeded admin phone number
    payload = {"mobile_number": "+919999999999", "otp": "123456"}
    response = await client.post("/api/v1/auth/admin/otp/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_google_verify(client: AsyncClient, mock_firebase) -> None:
    """Test Google sign-in verify."""
    # The mock_firebase fixture in conftest.py mocks verify_firebase_token.
    payload = {"id_token": "valid_mock_token"}
    response = await client.post("/api/v1/auth/google/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data
    # The default mock_firebase email is test@example.com
    assert data["role"] == "user"
