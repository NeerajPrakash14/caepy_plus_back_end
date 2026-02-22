"""Unit tests for LinQMD Sync Service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.app.services.linqmd_sync_service import LinQMDSyncService, LinQMDUserPayload

def test_payload_to_form_data():
    """Test the conversion to urlencoded payload."""
    payload = LinQMDUserPayload(
        name="dr.test",
        mail="test@example.com",
        password="pwd",
        fullname="Dr. Test",
        phone_number="1234567890",
        speciality="Cardiology",
        expertises=[{"head": "Heart", "content": "Care"}]
    )
    
    data = payload.to_form_data()
    
    assert data["name"] == "dr.test"
    assert data["mail"] == "test@example.com"
    assert data["pass"] == "pwd"
    assert data["fullname"] == "Dr. Test"
    assert data["speciality"] == "Cardiology"
    assert "expertises" not in data  # arrays are excluded or processed separately in the current implementation of to_form_data

def test_transform_doctor_data():
    """Test transforming internal schema to payload schema."""
    service = LinQMDSyncService()
    
    identity = {
        "email": "doctor@hospital.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "9998887776",
        "title": "dr"
    }
    details = {
        "speciality": "Neurology",
        "about_me": "Expert doctor",
        "areas_of_expertise": ["Brain", "Spine"],
        "qualifications": [{"degree": "MD"}]
    }
    media = [{"media_category": "profile_photo", "file_uri": "/path/to/pic.jpg"}]
    
    payload = service.transform_doctor_data(identity, details, media)
    
    assert "doctor" in payload.name
    assert payload.fullname == "Dr. John Doe"
    assert payload.mail == "doctor@hospital.com"
    assert payload.speciality == "Neurology"
    assert payload.degree == "MD"
    assert payload.overview == "Expert doctor"
    assert payload.display_picture_path == "/path/to/pic.jpg"
    assert len(payload.expertises) == 2
    assert payload.expertises[0]["head"] == "Brain"


@pytest.fixture
def sync_service():
    service = LinQMDSyncService()
    service.settings.LINQMD_SYNC_ENABLED = True
    service.settings.LINQMD_API_URL = "http://test-linqmd.example.com"
    return service

@pytest.mark.asyncio
async def test_sync_doctor_success(sync_service):
    """Test successful synchronization."""
    identity = {"doctor_id": 1, "email": "test@test.com", "first_name": "Test", "last_name": "Doc"}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 100}
        mock_post.return_value = mock_response
        
        result = await sync_service.sync_doctor(identity)
        
        assert result.success is True
        assert result.doctor_id == 1
        assert result.http_status_code == 200
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_sync_doctor_disabled(sync_service):
    """Test syncing when disabled in settings."""
    sync_service.settings.LINQMD_SYNC_ENABLED = False
    
    identity = {"doctor_id": 1}
    result = await sync_service.sync_doctor(identity)
    
    assert result.success is False
    assert "disabled" in result.error_message

@pytest.mark.asyncio
async def test_sync_doctor_failure(sync_service):
    """Test API failure propagation."""
    identity = {"doctor_id": 1, "email": "test@test.com", "first_name": "Test", "last_name": "Doc"}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server format exception"}
        mock_post.return_value = mock_response
        
        result = await sync_service.sync_doctor(identity)
        
        assert result.success is False
        assert result.http_status_code == 500

@pytest.mark.asyncio
async def test_sync_doctor_network_error(sync_service):
    """Test network error mapping."""
    identity = {"doctor_id": 1, "email": "test@test.com", "first_name": "Test", "last_name": "Doc"}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Network uncreachable")
        
        result = await sync_service.sync_doctor(identity)
        
        assert result.success is False
        assert "Connection error" in result.error_message
