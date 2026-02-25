"""
Blob Storage Endpoints.

REST API for serving blob content stored in local blob storage.
Provides endpoints for:
- Retrieving blob content by path
- Getting blob metadata
- Storage statistics (admin)
"""
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, Response

from ....core.responses import GenericResponse
from ....services.blob_storage_service import get_blob_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blobs", tags=["Blob Storage"])


@router.get(
    "/{doctor_id}/{media_category}/{blob_filename}",
    summary="Retrieve a blob file",
    description="Stream a blob file from storage. Used to serve uploaded media files.",
    responses={
        200: {"description": "File content"},
        404: {"description": "Blob not found"},
    },
)
async def get_blob(
    doctor_id: Annotated[int, PathParam(description="Doctor ID")],
    media_category: Annotated[str, PathParam(description="Media category (e.g., profile_photo)")],
    blob_filename: Annotated[str, PathParam(description="Blob filename with extension")],
) -> FileResponse:
    """
    Serve a blob file from local storage.
    
    The blob path is constructed from:
    - doctor_id: identifies the doctor
    - media_category: the type of media (profile_photo, certificate, etc.)
    - blob_filename: the unique blob ID with file extension
    """
    blob_service = get_blob_storage_service()

    # Construct the file path
    blob_path = blob_service.base_path / str(doctor_id) / media_category / blob_filename

    if not blob_path.exists():
        logger.warning(f"Blob not found: {blob_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blob not found",
        )

    # Determine media type from extension
    extension = Path(blob_filename).suffix.lower()
    media_type_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(extension, "application/octet-stream")

    logger.info(f"Serving blob: {blob_path}")

    return FileResponse(
        path=blob_path,
        media_type=media_type,
        filename=blob_filename,
    )


@router.get(
    "/stats",
    response_model=GenericResponse[dict],
    summary="Get blob storage statistics",
    description="Returns storage statistics including total files, size, and path.",
)
async def get_storage_stats() -> GenericResponse[dict]:
    """Get blob storage statistics."""
    blob_service = get_blob_storage_service()
    stats = blob_service.get_storage_stats()

    return GenericResponse(
        message="Storage statistics retrieved",
        data=stats,
    )


@router.head(
    "/{doctor_id}/{media_category}/{blob_filename}",
    summary="Check if blob exists",
    description="Returns 200 if blob exists, 404 otherwise. Useful for checking blob availability.",
)
async def check_blob_exists(
    doctor_id: Annotated[int, PathParam(description="Doctor ID")],
    media_category: Annotated[str, PathParam(description="Media category")],
    blob_filename: Annotated[str, PathParam(description="Blob filename")],
) -> Response:
    """Check if a blob exists without downloading it."""
    blob_service = get_blob_storage_service()

    blob_path = blob_service.base_path / str(doctor_id) / media_category / blob_filename

    if not blob_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blob not found",
        )

    # Return file size in header
    file_size = blob_path.stat().st_size
    return Response(
        status_code=status.HTTP_200_OK,
        headers={"Content-Length": str(file_size)},
    )
