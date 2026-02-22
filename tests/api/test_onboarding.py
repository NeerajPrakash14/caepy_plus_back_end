"""Unit tests for onboarding endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.doctor import Doctor


@pytest.fixture
async def seeded_doctor(db_session: AsyncSession) -> int:
    """Insert a valid doctor into the database to satisfy the explicit exists queries."""
    doctor = Doctor(
        first_name="Base",
        last_name="Doctor",
        email="base.doctor@example.com",
        phone="1231231234",
        primary_specialization="General",
        medical_registration_number="REG123"
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor.id



@pytest.fixture
async def sample_onboarding_profile(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    """Create a profile and return doctor_id."""
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe.onboard@example.com",
        "phone_number": "9876543210"
    }
    response = await client.post("/api/v1/onboarding/createprofile", json=payload, headers=auth_headers)
    return response.json()["data"]

@pytest.mark.asyncio
async def test_create_profile(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test create onboarding profile."""
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith.onboard@example.com",
        "phone_number": "9876543211"
    }
    response = await client.post("/api/v1/onboarding/createprofile", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert "doctor_id" in response.json()["data"]

@pytest.mark.asyncio
async def test_save_profile(client: AsyncClient, sample_onboarding_profile: dict, auth_headers: dict[str, str]) -> None:
    """Test updating identity and details."""
    doctor_id = sample_onboarding_profile["doctor_id"]
    payload = {
        "first_name": "Johnny",
        "specialty": "Cardiology",
        "years_of_experience": 10
    }
    response = await client.post(f"/api/v1/onboarding/saveprofile/{doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "first_name" in data["updated_fields"]
    assert "specialty" in data["updated_fields"]

@pytest.mark.asyncio
async def test_submit_profile(client: AsyncClient, auth_headers: dict[str, str], seeded_doctor: int) -> None:
    """Test submitting profile for verification."""
    doctor_id = seeded_doctor
    response = await client.post(f"/api/v1/onboarding/submit/{doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["new_status"] == "submitted"

@pytest.mark.asyncio
async def test_verify_profile(client: AsyncClient, auth_headers: dict[str, str], seeded_doctor: int) -> None:
    """Test verifying profile as admin."""
    doctor_id = seeded_doctor
    response = await client.post(f"/api/v1/onboarding/verify/{doctor_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["new_status"] == "verified"

@pytest.mark.asyncio
async def test_reject_profile(client: AsyncClient, auth_headers: dict[str, str], seeded_doctor: int) -> None:
    """Test rejecting profile as admin."""
    doctor_id = seeded_doctor
    payload = {"reason": "Incomplete information"}
    response = await client.post(f"/api/v1/onboarding/reject/{doctor_id}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["new_status"] == "rejected"

@pytest.mark.asyncio
async def test_validate_data(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test validation of extracted data."""
    payload = {
        "personal_details": {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com"
        },
        "professional_information": {
            "primary_specialization": "Cardiology"
        },
        "registration": {
            "medical_registration_number": "MED123"
        }
    }
    response = await client.post("/api/v1/onboarding/validate-data", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["is_valid"] is True

@pytest.mark.asyncio
async def test_extract_resume(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test extracting resume via mock."""
    with patch("src.app.services.extraction_service.ResumeExtractionService.extract_from_file", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = ({
            "personal_details": {"first_name": "John", "last_name": "Doe"}
        }, 123.4)

        # FastAPI UploadFile expects form-data
        files = {"file": ("resume.pdf", b"dummy content", "application/pdf")}
        response = await client.post("/api/v1/onboarding/extract-resume", files=files, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["personal_details"]["first_name"] == "John"

@pytest.mark.asyncio
async def test_generate_profile_content(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test profile content generation mock."""
    payload = {
        "doctor_identifier": "test_doc_1",
        "first_name": "Test",
        "last_name": "Doctor",
        "email": "test@example.com",
        "primary_specialization": "Surgery",
        "medical_registration_number": "MED123",
        "sections": ["professional_overview"]
    }

    with patch("src.app.services.gemini_service.GeminiService.generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"professional_overview": "Generated overview string"}

        response = await client.post("/api/v1/onboarding/generate-profile-content", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "professional_overview" in data

@pytest.mark.asyncio
async def test_profile_session_stats(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting and clearing profile variant session stats."""
    # First generate content to ensure session exists
    payload = {
        "doctor_identifier": "test_session_doc",
        "first_name": "Test",
        "last_name": "Doc",
        "email": "session@example.com",
        "primary_specialization": "ENT",
        "medical_registration_number": "MED456",
        "sections": ["professional_overview"]
    }
    with patch("src.app.services.gemini_service.GeminiService.generate_structured", new_callable=AsyncMock) as mock_gen, \
         patch("src.app.services.prompt_session_service.PromptSessionService.get_session_stats", new_callable=AsyncMock) as mock_stats, \
         patch("src.app.services.prompt_session_service.PromptSessionService.clear_session", new_callable=AsyncMock) as mock_clear:
        mock_gen.return_value = {"professional_overview": "A generated overview"}
        mock_stats.return_value = {"doctor_identifier": "test_session_doc", "sections": {"professional_overview": {"used_variants": [0]}}}
        mock_clear.return_value = True

        await client.post("/api/v1/onboarding/generate-profile-content", json=payload, headers=auth_headers)

        # Get stats
        response = await client.get("/api/v1/onboarding/profile-session/test_session_doc", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["doctor_identifier"] == "test_session_doc"

        # Clear session
        clear_resp = await client.delete("/api/v1/onboarding/profile-session/test_session_doc", headers=auth_headers)
        assert clear_resp.status_code == 200
        assert "cleared" in clear_resp.json()["data"]

@pytest.mark.asyncio
async def test_list_profile_variants(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting all available AI prompt variants."""
    response = await client.get("/api/v1/onboarding/profile-variants", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sections" in data["data"]
