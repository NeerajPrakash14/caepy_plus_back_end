"""Unit tests for blob endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

@pytest.fixture
def temp_blob_storage(tmp_path: Path):
    """Create a temporary directory with a dummy blob for testing."""
    doctor_id = 99
    media_category = "profile_photo"
    blob_filename = "test_blob.jpg"

    blob_dir = tmp_path / str(doctor_id) / media_category
    blob_dir.mkdir(parents=True, exist_ok=True)

    blob_path = blob_dir / blob_filename
    blob_path.write_bytes(b"dummy image content")

    return tmp_path, doctor_id, media_category, blob_filename

@pytest.mark.asyncio
async def test_get_blob_success(client: AsyncClient, temp_blob_storage, auth_headers: dict[str, str]) -> None:
    """Test successful blob retrieval."""
    base_path, doctor_id, media_category, blob_filename = temp_blob_storage

    # We patch the service factory to return a mock with the temp base_path
    with patch("src.app.api.v1.endpoints.blobs.get_blob_storage_service") as mock_get_service:
        mock_service = mock_get_service.return_value
        mock_service.base_path = base_path

        response = await client.get(
            f"/api/v1/blobs/{doctor_id}/{media_category}/{blob_filename}",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert response.content == b"dummy image content"
    assert response.headers["content-type"] == "image/jpeg"

@pytest.mark.asyncio
async def test_get_blob_not_found(client: AsyncClient, temp_blob_storage, auth_headers: dict[str, str]) -> None:
    """Test blob retrieval for non-existent file."""
    base_path, doctor_id, media_category, _ = temp_blob_storage

    with patch("src.app.api.v1.endpoints.blobs.get_blob_storage_service") as mock_get_service:
        mock_service = mock_get_service.return_value
        mock_service.base_path = base_path

        response = await client.get(
            f"/api/v1/blobs/{doctor_id}/{media_category}/missing.jpg",
            headers=auth_headers
        )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_storage_stats(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test getting storage stats."""
    with patch("src.app.api.v1.endpoints.blobs.get_blob_storage_service") as mock_get_service:
        mock_service = mock_get_service.return_value
        mock_service.get_storage_stats.return_value = {
            "total_files": 10,
            "total_size_bytes": 1024
        }

        response = await client.get("/api/v1/blobs/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_files"] == 10

@pytest.mark.asyncio
async def test_check_blob_exists(client: AsyncClient, temp_blob_storage, auth_headers: dict[str, str]) -> None:
    """Test HEAD request to check blob existence."""
    base_path, doctor_id, media_category, blob_filename = temp_blob_storage

    with patch("src.app.api.v1.endpoints.blobs.get_blob_storage_service") as mock_get_service:
        mock_service = mock_get_service.return_value
        mock_service.base_path = base_path

        response = await client.head(
            f"/api/v1/blobs/{doctor_id}/{media_category}/{blob_filename}",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert "content-length" in response.headers
    assert int(response.headers["content-length"]) > 0

@pytest.mark.asyncio
async def test_check_blob_not_exists(client: AsyncClient, temp_blob_storage, auth_headers: dict[str, str]) -> None:
    """Test HEAD request for non-existent blob."""
    base_path, doctor_id, media_category, _ = temp_blob_storage

    with patch("src.app.api.v1.endpoints.blobs.get_blob_storage_service") as mock_get_service:
        mock_service = mock_get_service.return_value
        mock_service.base_path = base_path

        response = await client.head(
            f"/api/v1/blobs/{doctor_id}/{media_category}/missing.jpg",
            headers=auth_headers
        )

    assert response.status_code == 404
