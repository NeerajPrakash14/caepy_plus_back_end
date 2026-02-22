"""Unit tests for voice onboarding configuration endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient



@pytest.fixture
async def sample_voice_block(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    """Create a sample voice block and return its data."""
    payload = {
        "block_number": 1,
        "block_name": "personal_info",
        "display_name": "Personal Information",
        "ai_prompt": "Please gather personal details.",
        "ai_disclaimer": "This is recorded.",
        "completion_percentage": 20,
        "completion_message": "Block 1 complete.",
        "is_active": True,
        "display_order": 1
    }
    response = await client.post("/api/v1/voice-config/blocks", json=payload, headers=auth_headers)
    return response.json()["data"]

@pytest.fixture
async def sample_voice_field(client: AsyncClient, sample_voice_block: dict, auth_headers: dict[str, str]) -> dict:
    """Create a sample voice field for the block."""
    payload = {
        "block_id": sample_voice_block["id"],
        "field_name": "first_name",
        "display_name": "First Name",
        "field_type": "text",
        "is_required": True,
        "ai_question": "What is your first name?",
        "is_active": True,
        "display_order": 1
    }
    response = await client.post("/api/v1/voice-config/fields", json=payload, headers=auth_headers)
    return response.json()["data"]

@pytest.mark.asyncio
async def test_create_block(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test creating a voice block."""
    payload = {
        "block_number": 2,
        "block_name": "education_info",
        "display_name": "Education Information"
    }
    response = await client.post("/api/v1/voice-config/blocks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["block_name"] == "education_info"

@pytest.mark.asyncio
async def test_get_voice_config(client: AsyncClient, sample_voice_field: dict, auth_headers: dict[str, str]) -> None:
    """Test get full config."""
    response = await client.get("/api/v1/voice-config", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_blocks"] >= 1
    assert len(data["blocks"]) > 0
    assert len(data["blocks"][0]["fields"]) > 0

@pytest.mark.asyncio
async def test_get_block(client: AsyncClient, sample_voice_block: dict, auth_headers: dict[str, str]) -> None:
    """Test getting block by number."""
    block_num = sample_voice_block["block_number"]
    response = await client.get(f"/api/v1/voice-config/blocks/{block_num}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == sample_voice_block["id"]

@pytest.mark.asyncio
async def test_update_block(client: AsyncClient, sample_voice_block: dict, auth_headers: dict[str, str]) -> None:
    """Test update block."""
    payload = {"display_name": "Updated Name", "is_active": False}
    response = await client.patch(f"/api/v1/voice-config/blocks/{sample_voice_block['id']}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["display_name"] == "Updated Name"
    assert data["is_active"] is False

@pytest.mark.asyncio
async def test_delete_block(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test delete block."""
    # Create one to delete
    block_payload = {"block_number": 99, "block_name": "to_delete", "display_name": "Delete Me"}
    create_resp = await client.post("/api/v1/voice-config/blocks", json=block_payload, headers=auth_headers)
    block_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/voice-config/blocks/{block_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    # Try getting it
    get_resp = await client.get("/api/v1/voice-config/blocks/99", headers=auth_headers)
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_create_field(client: AsyncClient, sample_voice_block: dict, auth_headers: dict[str, str]) -> None:
    """Test creating field."""
    payload = {
        "block_id": sample_voice_block["id"],
        "field_name": "last_name",
        "display_name": "Last Name",
        "field_type": "text"
    }
    response = await client.post("/api/v1/voice-config/fields", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["field_name"] == "last_name"

@pytest.mark.asyncio
async def test_update_field(client: AsyncClient, sample_voice_field: dict, auth_headers: dict[str, str]) -> None:
    """Test updating field."""
    payload = {"is_required": False, "ai_question": "Updated?"}
    response = await client.patch(f"/api/v1/voice-config/fields/{sample_voice_field['id']}", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_required"] is False
    assert data["ai_question"] == "Updated?"

@pytest.mark.asyncio
async def test_delete_field(client: AsyncClient, sample_voice_block: dict, auth_headers: dict[str, str]) -> None:
    """Test deleting field."""
    payload = {
        "block_id": sample_voice_block["id"],
        "field_name": "temp_field",
        "display_name": "Temp",
        "field_type": "text"
    }
    create_resp = await client.post("/api/v1/voice-config/fields", json=payload, headers=auth_headers)
    field_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/voice-config/fields/{field_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

@pytest.mark.asyncio
async def test_get_field_config(client: AsyncClient, sample_voice_field: dict, auth_headers: dict[str, str]) -> None:
    """Test getting flat field config."""
    response = await client.get("/api/v1/voice-config/field-config", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, dict)
    # The config dict keys are the field names
    assert sample_voice_field["field_name"] in data
