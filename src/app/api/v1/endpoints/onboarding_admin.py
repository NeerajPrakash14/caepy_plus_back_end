"""Admin CRUD endpoints for onboarding tables.

These endpoints expose basic CRUD operations over:
- doctor_identity
- doctor_details
- doctor_media
- doctor_status_history

They are intended for internal/admin use, not public-facing flows.
"""

from __future__ import annotations

import logging
from typing import Sequence

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, Request
from pydantic import BaseModel, EmailStr

from ....core.responses import PaginatedResponse, PaginationMeta
from ....db.session import DbSession
from ....repositories import OnboardingRepository
from ....schemas import (
    DoctorDetailsResponse,
    DoctorDetailsUpsert,
    DoctorIdentityCreate,
    DoctorIdentityResponse,
    DoctorMediaCreate,
    DoctorMediaResponse,
    DoctorStatusHistoryCreate,
    DoctorStatusHistoryResponse,
    DoctorWithFullInfoResponse,
    OnboardingStatusEnum,
)
from ....services.blob_storage_service import get_blob_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding-admin", tags=["Onboarding Admin"])

# ---------------------------------------------------------------------------
# doctor_identity
# ---------------------------------------------------------------------------

@router.post("/identities", response_model=DoctorIdentityResponse, status_code=status.HTTP_201_CREATED)
async def create_identity(payload: DoctorIdentityCreate, db: DbSession) -> DoctorIdentityResponse:
    repo = OnboardingRepository(db)
    identity = await repo.create_identity(**payload.model_dump())
    return identity

@router.get("/identities/by-email", response_model=DoctorIdentityResponse)
async def get_identity_by_email(email: str, db: DbSession) -> DoctorIdentityResponse:
    repo = OnboardingRepository(db)
    identity = await repo.get_identity_by_email(email)
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor identity not found")
    return identity

@router.get("/identities/{doctor_id}", response_model=DoctorIdentityResponse)
async def get_identity(doctor_id: int, db: DbSession) -> DoctorIdentityResponse:
    repo = OnboardingRepository(db)
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor identity not found")
    return identity

# ---------------------------------------------------------------------------
# doctor_details
# ---------------------------------------------------------------------------

@router.put("/details/{doctor_id}", response_model=DoctorDetailsResponse)
async def upsert_details(doctor_id: int, payload: DoctorDetailsUpsert, db: DbSession) -> DoctorDetailsResponse:
    repo = OnboardingRepository(db)
    details_payload = {k: v for k, v in payload.model_dump().items() if v is not None}
    details = await repo.upsert_details(doctor_id=doctor_id, payload=details_payload)
    return details

@router.get("/details/{doctor_id}", response_model=DoctorDetailsResponse)
async def get_details(doctor_id: int, db: DbSession) -> DoctorDetailsResponse:
    repo = OnboardingRepository(db)
    details = await repo.get_details_by_doctor_id(doctor_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor details not found")
    return details

# ---------------------------------------------------------------------------
# doctor_media
# ---------------------------------------------------------------------------

def _build_absolute_uri(request: Request, file_uri: str) -> str:
    """Build an absolute URL for a stored blob from its file_uri.

    If file_uri is already absolute (http/https), it is returned unchanged.
    Otherwise it is prefixed with the current request base URL.
    """

    if file_uri.startswith("http://") or file_uri.startswith("https://"):
        return file_uri

    base = str(request.base_url).rstrip("/")
    if file_uri.startswith("/"):
        return f"{base}{file_uri}"
    return f"{base}/{file_uri}"

@router.post("/media/{doctor_id}", response_model=DoctorMediaResponse, status_code=status.HTTP_201_CREATED)
async def add_media(
    doctor_id: int,
    payload: DoctorMediaCreate,
    db: DbSession,
    request: Request,
) -> DoctorMediaResponse:
    repo = OnboardingRepository(db)

    media = await repo.add_media(doctor_id=doctor_id, **payload.model_dump())
    media.file_uri = _build_absolute_uri(request, media.file_uri)
    return media

@router.get("/media/{doctor_id}", response_model=list[DoctorMediaResponse])
async def list_media(
    doctor_id: int,
    db: DbSession,
    request: Request,
) -> Sequence[DoctorMediaResponse]:
    repo = OnboardingRepository(db)
    media = await repo.list_media(doctor_id)
    for item in media:
        item.file_uri = _build_absolute_uri(request, item.file_uri)
    return list(media)

@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: str, db: DbSession) -> None:
    repo = OnboardingRepository(db)
    deleted = await repo.delete_media(media_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

@router.post(
    "/media/{doctor_id}/upload",
    response_model=DoctorMediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file for a doctor profile (Admin)",
    description="""
Admin endpoint to upload a file directly for a doctor profile.
The file is stored in blob storage and metadata is saved to doctor_media table.

**Supported file types:** Images (JPG, PNG, GIF), Documents (PDF)
**Max file size:** 50MB
    """,
)
async def upload_media_file(
    doctor_id: int,
    media_category: str,
    db: DbSession,
    field_name: str | None = None,
    file: UploadFile = File(...),
) -> DoctorMediaResponse:
    """
    Upload a file directly to blob storage and register in database.
    
    Args:
        doctor_id: The doctor's ID
        media_category: Category of media (e.g., 'profile_photo', 'certificate', 'resume')
        field_name: Logical field key used for media_urls (defaults to media_category)
        file: The file to upload
    """
    repo = OnboardingRepository(db)
    blob_service = get_blob_storage_service()

    # Validate doctor exists
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    # Read file content
    file_content = await file.read()
    file_name = file.filename or "uploaded_file"

    logger.info(
        f"Admin uploading file: doctor_id={doctor_id}, "
        f"category={media_category}, file={file_name}, size={len(file_content)}"
    )

    # Upload to blob storage
    upload_result = await blob_service.upload_from_bytes(
        content=file_content,
        file_name=file_name,
        doctor_id=doctor_id,
        media_category=media_category,
    )

    if not upload_result.success:
        logger.error(f"Blob upload failed for {file_name}: {upload_result.error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload failed: {upload_result.error_message}",
        )

    # Determine media type from content type
    media_type = "document"
    if file.content_type and file.content_type.startswith("image/"):
        media_type = "image"

    # Save to database

    media = await repo.add_media(
        doctor_id=doctor_id,
        media_type=media_type,
        media_category=media_category,
        field_name=field_name or media_category,
        file_uri=upload_result.file_uri,
        file_name=file_name,
        file_size=len(file_content),
        mime_type=file.content_type,
    )
    media.file_uri = upload_result.file_uri

    logger.info(f"Admin upload complete: media_id={media.media_id}, uri={upload_result.file_uri}")
    return media

# ---------------------------------------------------------------------------
# doctor_status_history
# ---------------------------------------------------------------------------

@router.post("/status-history/{doctor_id}", response_model=DoctorStatusHistoryResponse, status_code=status.HTTP_201_CREATED)
async def log_status_history(
    doctor_id: int,
    payload: DoctorStatusHistoryCreate,
    db: DbSession,
) -> DoctorStatusHistoryResponse:
    repo = OnboardingRepository(db)
    history = await repo.log_status_change(doctor_id=doctor_id, **payload.model_dump())
    return history

@router.get("/status-history/{doctor_id}", response_model=list[DoctorStatusHistoryResponse])
async def get_status_history(doctor_id: int, db: DbSession) -> Sequence[DoctorStatusHistoryResponse]:
    repo = OnboardingRepository(db)
    history = await repo.get_status_history(doctor_id)
    return list(history)

# ---------------------------------------------------------------------------
# Helper: build DoctorIdentityResponse from the legacy doctors table row
# ---------------------------------------------------------------------------

def _build_identity_from_doctor(doctor) -> DoctorIdentityResponse:
    """Construct a DoctorIdentityResponse from a legacy Doctor model row.

    When a doctor exists only in the `doctors` table (e.g. created via OTP)
    and has no matching `doctor_identity` row, this helper synthesises an
    equivalent response so the admin endpoints can return consistent data.
    """
    from datetime import datetime, UTC

    return DoctorIdentityResponse(
        id=str(doctor.id),
        doctor_id=doctor.id,
        title=doctor.title,
        first_name=doctor.first_name or "",
        last_name=doctor.last_name or "",
        email=doctor.email,
        phone_number=doctor.phone or "",
        onboarding_status=doctor.onboarding_status or "pending",
        status_updated_at=None,
        status_updated_by=None,
        rejection_reason=None,
        verified_at=None,
        is_active=True,
        registered_at=doctor.created_at or datetime.now(UTC),
        created_at=doctor.created_at or datetime.now(UTC),
        updated_at=doctor.updated_at or doctor.created_at or datetime.now(UTC),
        deleted_at=None,
    )


# ---------------------------------------------------------------------------
# Aggregated doctor endpoints (use doctors table as primary source)
# ---------------------------------------------------------------------------

@router.get("/doctors/full", response_model=list[DoctorWithFullInfoResponse])
async def list_doctors_with_full_info(db: DbSession) -> list[DoctorWithFullInfoResponse]:
    """Fetch all doctors with identity, details, media, and status history.

    Intended for admin/internal use to get a complete view of each doctor.
    Uses the primary `doctors` table as the source of truth and enriches
    with onboarding data when available.
    """

    from ....repositories.doctor_repository import DoctorRepository

    repo = OnboardingRepository(db)
    doctor_repo = DoctorRepository(db)

    all_doctors = await doctor_repo.get_all(skip=0, limit=10000)
    doctors: list[DoctorWithFullInfoResponse] = []

    for doctor in all_doctors:
        identity = await repo.get_identity_by_doctor_id(doctor.id)
        if identity is not None:
            identity_resp = DoctorIdentityResponse.model_validate(identity)
        else:
            identity_resp = _build_identity_from_doctor(doctor)

        details = await repo.get_details_by_doctor_id(doctor.id)
        media = await repo.list_media(doctor.id)
        status_history = await repo.get_status_history(doctor.id)

        doctors.append(
            DoctorWithFullInfoResponse(
                identity=identity_resp,
                details=DoctorDetailsResponse.model_validate(details) if details else None,
                media=[DoctorMediaResponse.model_validate(m) for m in media],
                status_history=[DoctorStatusHistoryResponse.model_validate(h) for h in status_history],
            )
        )

    return doctors

@router.get(
    "/doctors",
    response_model=PaginatedResponse[DoctorWithFullInfoResponse],
    summary="List doctors with optional status filter",
    description="""
Admin endpoint to list doctors with filtering and pagination.

**Filter Options:**
- `status`: Filter by onboarding status (PENDING, SUBMITTED, VERIFIED, REJECTED)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Example Usage:**
- Get pending doctors: `GET /onboarding-admin/doctors?status=pending`
- Get verified doctors: `GET /onboarding-admin/doctors?status=verified`
- Get all doctors (page 2): `GET /onboarding-admin/doctors?page=2`
    """,
)
async def list_doctors_with_filter(
    db: DbSession,
    status: OnboardingStatusEnum | None = Query(
        default=None,
        description="Filter by onboarding status"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[DoctorWithFullInfoResponse]:
    """List doctors with optional status filter and pagination."""

    from ....repositories.doctor_repository import DoctorRepository

    repo = OnboardingRepository(db)
    doctor_repo = DoctorRepository(db)

    skip = (page - 1) * page_size
    
    if status is not None:
        # When filtering by status, use the onboarding identity table
        identities = await repo.list_identities(
            status=status.value if status else None,
            skip=skip,
            limit=page_size,
        )
        total = await repo.count_identities_by_status(
            status=status.value if status else None
        )

        doctors: list[DoctorWithFullInfoResponse] = []
        for identity in identities:
            details = await repo.get_details_by_doctor_id(identity.doctor_id)
            media = await repo.list_media(identity.doctor_id)
            status_history = await repo.get_status_history(identity.doctor_id)

            doctors.append(
                DoctorWithFullInfoResponse(
                    identity=identity,
                    details=details,
                    media=list(media),
                    status_history=list(status_history),
                )
            )
    else:
        # No status filter: use the primary doctors table as source of truth
        all_doctors = await doctor_repo.get_all(skip=skip, limit=page_size)
        total = await doctor_repo.count()

        doctors = []
        for doctor in all_doctors:
            identity = await repo.get_identity_by_doctor_id(doctor.id)
            if identity is not None:
                identity_resp = DoctorIdentityResponse.model_validate(identity)
            else:
                identity_resp = _build_identity_from_doctor(doctor)

            details = await repo.get_details_by_doctor_id(doctor.id)
            media = await repo.list_media(doctor.id)
            status_history = await repo.get_status_history(doctor.id)

            doctors.append(
                DoctorWithFullInfoResponse(
                    identity=identity_resp,
                    details=DoctorDetailsResponse.model_validate(details) if details else None,
                    media=[DoctorMediaResponse.model_validate(m) for m in media],
                    status_history=[DoctorStatusHistoryResponse.model_validate(h) for h in status_history],
                )
            )

    return PaginatedResponse(
        message=f"Found {total} doctor(s)" + (f" with status '{status.value}'" if status else ""),
        data=doctors,
        pagination=PaginationMeta.from_total(total=total, page=page, page_size=page_size),
    )

class DoctorLookupByEmailPayload(BaseModel):
    email: EmailStr

class DoctorLookupByPhonePayload(BaseModel):
    phone_number: str

@router.get("/doctors/{doctor_id}/full", response_model=DoctorWithFullInfoResponse)
async def get_doctor_with_full_info_by_id(
    doctor_id: int,
    db: DbSession,
) -> DoctorWithFullInfoResponse:
    """Fetch a single doctor's complete onboarding data by doctor_id."""

    from ....repositories.doctor_repository import DoctorRepository

    repo = OnboardingRepository(db)
    doctor_repo = DoctorRepository(db)

    # Try onboarding identity first, fall back to doctors table
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is not None:
        identity_resp = DoctorIdentityResponse.model_validate(identity)
    else:
        doctor = await doctor_repo.get_by_id(doctor_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        identity_resp = _build_identity_from_doctor(doctor)

    details = await repo.get_details_by_doctor_id(doctor_id)
    media = await repo.list_media(doctor_id)
    status_history = await repo.get_status_history(doctor_id)

    return DoctorWithFullInfoResponse(
        identity=identity_resp,
        details=DoctorDetailsResponse.model_validate(details) if details else None,
        media=[DoctorMediaResponse.model_validate(m) for m in media],
        status_history=[DoctorStatusHistoryResponse.model_validate(h) for h in status_history],
    )

@router.post("/doctors/by-email/full", response_model=DoctorWithFullInfoResponse)
async def get_doctor_with_full_info_by_email(
    payload: DoctorLookupByEmailPayload,
    db: DbSession,
) -> DoctorWithFullInfoResponse:
    """Fetch a single doctor's complete onboarding data by email."""

    from ....repositories.doctor_repository import DoctorRepository

    repo = OnboardingRepository(db)
    doctor_repo = DoctorRepository(db)

    identity = await repo.get_identity_by_email(payload.email)
    if identity is not None:
        identity_resp = DoctorIdentityResponse.model_validate(identity)
        doctor_id = identity.doctor_id
    else:
        doctor = await doctor_repo.get_by_email(payload.email)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        identity_resp = _build_identity_from_doctor(doctor)
        doctor_id = doctor.id

    details = await repo.get_details_by_doctor_id(doctor_id)
    media = await repo.list_media(doctor_id)
    status_history = await repo.get_status_history(doctor_id)

    return DoctorWithFullInfoResponse(
        identity=identity_resp,
        details=DoctorDetailsResponse.model_validate(details) if details else None,
        media=[DoctorMediaResponse.model_validate(m) for m in media],
        status_history=[DoctorStatusHistoryResponse.model_validate(h) for h in status_history],
    )

@router.post("/doctors/by-phone/full", response_model=DoctorWithFullInfoResponse)
async def get_doctor_with_full_info_by_phone(
    payload: DoctorLookupByPhonePayload,
    db: DbSession,
) -> DoctorWithFullInfoResponse:
    """Fetch a single doctor's complete onboarding data by phone number."""

    from ....repositories.doctor_repository import DoctorRepository

    repo = OnboardingRepository(db)
    doctor_repo = DoctorRepository(db)

    identity = await repo.get_identity_by_phone(payload.phone_number)
    if identity is not None:
        identity_resp = DoctorIdentityResponse.model_validate(identity)
        doctor_id = identity.doctor_id
    else:
        doctor = await doctor_repo.get_by_phone_number(payload.phone_number)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        identity_resp = _build_identity_from_doctor(doctor)
        doctor_id = doctor.id

    details = await repo.get_details_by_doctor_id(doctor_id)
    media = await repo.list_media(doctor_id)
    status_history = await repo.get_status_history(doctor_id)

    return DoctorWithFullInfoResponse(
        identity=identity_resp,
        details=DoctorDetailsResponse.model_validate(details) if details else None,
        media=[DoctorMediaResponse.model_validate(m) for m in media],
        status_history=[DoctorStatusHistoryResponse.model_validate(h) for h in status_history],
    )
