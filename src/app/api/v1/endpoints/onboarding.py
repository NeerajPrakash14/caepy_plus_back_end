"""
Onboarding Endpoints.

Unified onboarding API for resume extraction and voice registration.
Demonstrates the clean architecture with service layer abstraction.
"""
import logging
from datetime import datetime, UTC
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr

from ....core.config import get_settings, Settings
from ....core.exceptions import (
    ExtractionError,
    FileValidationError,
    OnboardingProfileAlreadyExistsError,
)
from ....core.prompts import get_prompt_manager, PROFILE_SECTIONS
from ....core.responses import GenericResponse
from ....db.session import DbSession
from ....repositories.onboarding_repository import OnboardingRepository
from ....schemas.doctor import (
    ExtractionResponse,
    ProfileContentRequest,
    ProfileContentResponse,
    ProfileSessionStatsResponse,
    ResumeExtractedData,
)
from ....services.extraction_service import get_extraction_service
from ....services.gemini_service import get_gemini_service
from ....services.blob_storage_service import (
    get_blob_storage_service,
    BlobDownloadError,
    BlobUploadError,
)
from ....services.prompt_session_service import get_prompt_session_service
from ....services.linqmd_sync_service import get_linqmd_sync_service

from ....models.onboarding import OnboardingStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding")

def get_extraction_svc():
    """Dependency to get extraction service."""
    return get_extraction_service()

def validate_file(
    file: UploadFile,
    settings: Settings,
) -> None:
    """
    Validate uploaded file type and size.
    
    Raises:
        FileValidationError: If validation fails
    """
    if not file.filename:
        raise FileValidationError(
            message="Filename is required",
        )
    
    # Check extension
    extension = file.filename.lower().rsplit(".", 1)[-1]
    if extension not in settings.allowed_extensions_list:
        raise FileValidationError(
            message=f"Invalid file type: {extension}",
            filename=file.filename,
            allowed_types=settings.allowed_extensions_list,
        )
    
    # Check content type
    valid_content_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    ]
    if file.content_type and file.content_type not in valid_content_types:
        raise FileValidationError(
            message=f"Invalid content type: {file.content_type}",
            filename=file.filename,
        )

@router.post(
    "/extract-resume",
    response_model=ExtractionResponse,
    summary="Extract data from resume",
    description="""
Upload a doctor's resume (PDF or Image) and extract structured professional data.

**Supported formats:** PDF, PNG, JPG, JPEG

**Max file size:** 10MB

The extracted data includes:
- Personal details (name, email, title)
- Professional information (specialization, registration number)
- Qualifications (degrees, institutions, years)
- Expertise and skills
- Awards and memberships
- Practice locations

The response can be used to pre-fill the doctor registration form.
    """,
    responses={
        200: {
            "description": "Successfully extracted data",
            "model": ExtractionResponse,
        },
        400: {
            "description": "Invalid file or validation error",
        },
        422: {
            "description": "Failed to extract data from resume",
        },
        503: {
            "description": "AI service temporarily unavailable",
        },
    },
)
async def extract_resume(
    file: Annotated[UploadFile, File(description="Resume file (PDF, PNG, JPG)")],
    settings: Annotated[Settings, Depends(get_settings)],
    extraction_service: Annotated[Any, Depends(get_extraction_svc)],
) -> ExtractionResponse:
    """
    Extract structured data from an uploaded resume.
    
    This endpoint:
    1. Validates the uploaded file (type, size)
    2. Sends it to Gemini Vision API for analysis
    3. Returns structured JSON matching the doctor schema
    
    The extracted data can be used to pre-fill registration forms,
    reducing manual data entry and improving accuracy.
    """
    # Validate file
    validate_file(file, settings)
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > settings.max_file_size_bytes:
        raise FileValidationError(
            message=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
            filename=file.filename,
        )
    
    logger.info(f"Processing resume: {file.filename} ({len(content)} bytes)")
    
    # Extract data
    extracted_data, processing_time = await extraction_service.extract_from_file(
        file_content=content,
        filename=file.filename or "unknown",
    )
    
    return ExtractionResponse(
        success=True,
        message="Resume parsed successfully",
        data=extracted_data,
        processing_time_ms=round(processing_time, 2),
    )

@router.post(
    "/generate-profile-content",
    response_model=GenericResponse[ProfileContentResponse],
    summary="Generate professional overview, about-me, and tagline content",
    description=(
        "Accepts full doctor onboarding data and generates "
        "a professional overview, an about-me paragraph, and a short professional tagline using Gemini. "
        "Each call uses a different prompt variant to provide variety. "
        "Use doctor_identifier to track variant usage across refreshes."
    ),
)
async def generate_profile_content(
    data: ProfileContentRequest,
) -> GenericResponse[ProfileContentResponse]:
    """
    Generate profile text sections from doctor onboarding fields using Gemini.
    
    Features:
    - 3 different prompt variants per section for variety
    - Session tracking to cycle through variants on refresh
    - Optionally specify which sections to regenerate
    """
    prompt_manager = get_prompt_manager()
    gemini = get_gemini_service()
    session_service = get_prompt_session_service()
    
    # Determine which sections to generate
    sections_to_generate = data.sections or PROFILE_SECTIONS
    
    # Validate section names
    invalid_sections = [s for s in sections_to_generate if s not in PROFILE_SECTIONS]
    if invalid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sections: {invalid_sections}. Valid sections: {PROFILE_SECTIONS}",
        )
    
    # Get doctor identifier for session tracking
    # Fall back to email or generate a temporary ID
    doctor_id = (
        data.doctor_identifier 
        or getattr(data.personal_details, 'email', None) if hasattr(data, 'personal_details') else None
        or "anonymous"
    )
    
    # Get next variant for each section
    variant_indices = {}
    for section in sections_to_generate:
        variant_count = prompt_manager.get_variant_count(section)
        variant_idx = await session_service.get_next_variant(doctor_id, section, variant_count)
        variant_indices[section] = variant_idx
    
    # Build doctor payload (exclude session-tracking fields)
    doctor_payload = data.model_dump(exclude={"doctor_identifier", "sections"})
    
    # Generate prompt with variant-specific instructions
    prompt = prompt_manager.get_profile_generation_prompt_with_variants(
        doctor_payload, variant_indices
    )

    try:
        result = await gemini.generate_structured(prompt, temperature=0.5)
    except Exception as exc:
        logger.error(f"Failed to generate profile content: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate profile content. Please try again later.",
        ) from exc

    # Add variant tracking to response (1-indexed for display)
    variants_used = {k: v + 1 for k, v in variant_indices.items()}
    
    profile = ProfileContentResponse(
        **result,
        variants_used=variants_used,
    )
    
    logger.info(f"Generated profile content for {doctor_id} with variants: {variants_used}")

    return GenericResponse(
        message="Profile content generated successfully",
        data=profile,
    )

@router.get(
    "/profile-session/{doctor_identifier}",
    response_model=GenericResponse[ProfileSessionStatsResponse],
    summary="Get profile generation session statistics",
    description="View which prompt variants have been used for a doctor's profile generation.",
)
async def get_profile_session_stats(
    doctor_identifier: str,
) -> GenericResponse[ProfileSessionStatsResponse]:
    """Get session statistics showing variant usage for a doctor."""
    session_service = get_prompt_session_service()
    
    stats = await session_service.get_session_stats(doctor_identifier)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No session found for doctor: {doctor_identifier}",
        )
    
    total_regenerations = sum(
        len(section_data.get("used_variants", []))
        for section_data in stats.get("sections", {}).values()
    )
    
    response = ProfileSessionStatsResponse(
        doctor_identifier=stats["doctor_identifier"],
        sections=stats["sections"],
        total_regenerations=total_regenerations,
    )
    
    return GenericResponse(
        message="Session statistics retrieved",
        data=response,
    )

@router.delete(
    "/profile-session/{doctor_identifier}",
    response_model=GenericResponse[dict],
    summary="Clear profile generation session",
    description="Reset variant tracking for a doctor (start fresh with all variants available).",
)
async def clear_profile_session(
    doctor_identifier: str,
) -> GenericResponse[dict]:
    """Clear a doctor's profile generation session to reset variant tracking."""
    session_service = get_prompt_session_service()
    
    cleared = await session_service.clear_session(doctor_identifier)
    
    return GenericResponse(
        message="Session cleared successfully" if cleared else "No session found to clear",
        data={"cleared": cleared, "doctor_identifier": doctor_identifier},
    )

@router.get(
    "/profile-variants",
    response_model=GenericResponse[dict],
    summary="List available prompt variants",
    description="Get information about all available prompt variants for profile generation.",
)
async def list_profile_variants() -> GenericResponse[dict]:
    """List all available prompt variants for each profile section."""
    prompt_manager = get_prompt_manager()
    variants = prompt_manager.get_all_variant_info()
    
    return GenericResponse(
        message="Available prompt variants",
        data={
            "sections": variants,
            "total_sections": len(PROFILE_SECTIONS),
            "variants_per_section": 3,
        },
    )

@router.post(
    "/validate-data",
    response_model=GenericResponse[dict],
    summary="Validate extracted data",
    description="Validate extracted data before submission.",
)
async def validate_extracted_data(
    data: ResumeExtractedData,
) -> GenericResponse[dict]:
    """
    Validate extracted data for completeness.
    
    Checks for required fields and returns validation results.
    """
    missing_fields = []
    warnings = []
    
    # Check required fields
    if not data.personal_details.first_name:
        missing_fields.append("first_name")
    if not data.personal_details.last_name:
        missing_fields.append("last_name")
    if not data.personal_details.email:
        missing_fields.append("email")
    if not data.professional_information.primary_specialization:
        missing_fields.append("primary_specialization")
    if not data.registration.medical_registration_number:
        missing_fields.append("medical_registration_number")
    
    # Warnings for optional but recommended fields
    if not data.personal_details.phone:
        warnings.append("phone_number is recommended")
    if not data.qualifications:
        warnings.append("qualifications are recommended")
    
    is_valid = len(missing_fields) == 0
    
    return GenericResponse(
        message="Validation complete" if is_valid else "Validation failed",
        data={
            "is_valid": is_valid,
            "missing_required_fields": missing_fields,
            "warnings": warnings,
            "fields_extracted": {
                "personal_details": bool(data.personal_details.first_name),
                "contact": bool(data.personal_details.phone),
                "professional": bool(data.professional_information.primary_specialization),
                "qualifications": len(data.qualifications),
                "practice_locations": len(data.practice_locations),
            },
        },
    )

# ---------------------------------------------------------------------------
# Profile lifecycle endpoints
# ---------------------------------------------------------------------------

class CreateProfilePayload(BaseModel):
    """Minimal payload for creating a new profile shell.

    All fields are optional to allow partial onboarding; missing
    values are stored as empty strings in the identity record.
    """

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None

class SaveProfilePayload(BaseModel):
    """Payload for updating profile identity fields.

    doctor_id is provided in the path; only non-null fields
    in this body are applied to the record.
    """

    # Block 1: Professional Identity
    full_name: str | None = None
    specialty: str | None = None
    primary_practice_location: str | None = None
    centres_of_practice: list[str] | None = None
    years_of_clinical_experience: int | None = None
    years_post_specialisation: int | None = None

    # Block 2: Credentials & Trust Markers
    year_of_mbbs: int | None = None
    year_of_specialisation: int | None = None
    fellowships: list[str] | None = None
    qualifications: list[str] | None = None
    professional_memberships: list[str] | None = None
    awards_academic_honours: list[str] | None = None

    # Block 3: Clinical Focus & Expertise
    areas_of_clinical_interest: list[str] | None = None
    practice_segments: str | None = None
    conditions_commonly_treated: list[str] | None = None
    conditions_known_for: list[str] | None = None
    conditions_want_to_treat_more: list[str] | None = None

    # Block 4: The Human Side
    training_experience: list[str] | None = None
    motivation_in_practice: list[str] | None = None
    unwinding_after_work: list[str] | None = None
    recognition_identity: list[str] | None = None
    quality_time_interests: list[str] | None = None
    quality_time_interests_text: str | None = None
    professional_achievement: str | None = None
    personal_achievement: str | None = None
    professional_aspiration: str | None = None
    personal_aspiration: str | None = None

    # Block 5: Patient Value & Choice Factors
    what_patients_value_most: str | None = None
    approach_to_care: str | None = None
    availability_philosophy: str | None = None

    # Block 6: Content Seed (repeatable)
    content_seeds: list[dict[str, Any]] | None = None

    # Existing fields
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None

class UploadItem(BaseModel):
    field_name: str
    file_name: str
    file: str

class UploadsPayload(BaseModel):
    uploads: List[UploadItem]

@router.post(
    "/createprofile",
    response_model=GenericResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new onboarding profile",
    description=(
        "Creates entries in doctor_identity and doctor_details (with placeholder "
        "values) and returns the generated doctor_id."
    ),
)
async def create_profile(
    payload: CreateProfilePayload,
    db: DbSession,
) -> GenericResponse[dict]:
    repo = OnboardingRepository(db)

    # Generate next doctor_id explicitly (last row + 1)
    next_id = await repo.get_next_doctor_id()

    if payload.email is None or payload.phone_number is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email and phone_number are required to create a profile",
        )

    # Check for existing onboarding identity by email or phone to avoid
    # database constraint violations and return a clear 409 response.
    existing_email = await repo.get_identity_by_email(str(payload.email))
    existing_phone = await repo.get_identity_by_phone(payload.phone_number)
    if existing_email or existing_phone:
        raise OnboardingProfileAlreadyExistsError(
            email=str(payload.email),
            phone_number=payload.phone_number,
        )

    first_name = payload.first_name or ""
    last_name = payload.last_name or ""

    identity = await repo.create_identity(
        first_name=first_name,
        last_name=last_name,
        email=str(payload.email),
        phone_number=payload.phone_number,
        onboarding_status=OnboardingStatus.PENDING,
        doctor_id=next_id,
    )

    # Create a placeholder details row so that both tables have entries.
    current_year = datetime.now(UTC).year
    await repo.upsert_details(
        doctor_id=identity.doctor_id,
        payload={
            "gender": "Prefer not to say",
            "speciality": "General",
            "registration_number": f"TEMP-{identity.doctor_id}",
            "registration_year": current_year,
            "registration_authority": "Unknown",
        },
    )

    return GenericResponse(
        message="Profile created successfully",
        data={
            "doctor_id": identity.doctor_id,
        },
    )

@router.post(
    "/saveprofile/{doctor_id}",
    response_model=GenericResponse[dict],
    summary="Update profile identity and details",
)
async def save_profile(
    doctor_id: int,
    payload: SaveProfilePayload,
    db: DbSession,
) -> GenericResponse[dict]:
    from ....services.dropdown_option_service import DropdownOptionService
    
    repo = OnboardingRepository(db)

    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    updated_fields: list[str] = []

    # All fields that can be updated from SaveProfilePayload
    # These map directly to DoctorIdentity model columns
    updatable_fields = [
        # Basic identity
        "first_name", "last_name", "email", "phone_number",
        # Block 1: Professional Identity
        "full_name", "specialty", "primary_practice_location",
        "centres_of_practice", "years_of_clinical_experience",
        "years_post_specialisation",
        # Block 2: Credentials & Trust Markers
        "year_of_mbbs", "year_of_specialisation", "fellowships",
        "qualifications", "professional_memberships", "awards_academic_honours",
        # Block 3: Clinical Focus & Expertise
        "areas_of_clinical_interest", "practice_segments",
        "conditions_commonly_treated", "conditions_known_for",
        "conditions_want_to_treat_more",
        # Block 4: The Human Side
        "training_experience", "motivation_in_practice", "unwinding_after_work",
        "recognition_identity", "quality_time_interests", "quality_time_interests_text",
        "professional_achievement", "personal_achievement",
        "professional_aspiration", "personal_aspiration",
        # Block 5: Patient Value & Choice Factors
        "what_patients_value_most", "approach_to_care", "availability_philosophy",
        # Block 6: Content Seed
        "content_seeds",
    ]

    for field_name in updatable_fields:
        new_value = getattr(payload, field_name, None)
        if new_value is not None and hasattr(identity, field_name):
            current_value = getattr(identity, field_name)
            if current_value != new_value:
                setattr(identity, field_name, new_value)
                updated_fields.append(field_name)

    identity.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(identity)

    # Auto-detect and save new dropdown values contributed by this doctor
    new_dropdown_values: dict[str, list[str]] = {}
    try:
        dropdown_service = DropdownOptionService(db)
        form_data = payload.model_dump(exclude_none=True)
        new_dropdown_values = await dropdown_service.process_form_submission(
            form_data=form_data,
            doctor_id=doctor_id,
            doctor_name=identity.full_name or f"{identity.first_name} {identity.last_name}",
            doctor_email=identity.email,
        )
        await db.commit()  # Commit new dropdown values
    except Exception as e:
        # Log but don't fail the main save operation
        logger.warning(f"Failed to auto-detect dropdown values for doctor {doctor_id}: {e}")

    return GenericResponse(
        message="Profile saved successfully",
        data={
            "doctor_id": identity.doctor_id,
            "updated_fields": updated_fields,
            "new_dropdown_values": new_dropdown_values if new_dropdown_values else None,
        },
    )

@router.post(
    "/submit/{doctor_id}",
    response_model=GenericResponse[dict],
    summary="Submit profile for verification",
)
async def submit_profile(
    doctor_id: int,
    db: DbSession,
) -> GenericResponse[dict]:
    from ....repositories.doctor_repository import DoctorRepository

    doctor_repo = DoctorRepository(db)
    repo = OnboardingRepository(db)

    # Update the primary doctors table
    doctor = await doctor_repo.get_by_id(doctor_id)
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    now = datetime.now(UTC)
    previous_status = doctor.onboarding_status

    doctor.onboarding_status = "submitted"
    doctor.updated_at = now

    # Also update doctor_identity if it exists
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is not None:
        identity.onboarding_status = OnboardingStatus.SUBMITTED
        identity.updated_at = now
        identity.status_updated_at = now

    await db.commit()
    await db.refresh(doctor)

    return GenericResponse(
        message="Profile submitted successfully",
        data={
            "doctor_id": doctor.id,
            "previous_status": previous_status,
            "new_status": doctor.onboarding_status,
        },
    )

@router.post(
    "/uploads/{doctor_id}",
    response_model=GenericResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Register uploaded files for a profile",
    description="""
Upload files for a doctor profile. The endpoint:
1. Downloads files from the provided URLs
2. Stores them in local blob storage
3. Generates permanent URIs
4. Saves metadata to the doctor_media table

**Supported file types:** Images (JPG, PNG, GIF), Documents (PDF)
**Max file size:** 50MB per file
    """,
    responses={
        201: {"description": "Files uploaded and registered successfully"},
        404: {"description": "Doctor profile not found"},
        400: {"description": "File download or upload failed"},
    },
)
async def register_uploads(
    doctor_id: int,
    payload: UploadsPayload,
    db: DbSession,
) -> GenericResponse[dict]:
    """
    Download files from external URLs, store in blob storage, and register in database.
    
    Flow:
    1. Validate doctor exists
    2. For each upload item:
       a. Download file from provided URL
       b. Store in local blob storage
       c. Get generated blob URI
       d. Save to doctor_media table with the blob URI
    3. Return list of created media records
    """
    repo = OnboardingRepository(db)
    blob_service = get_blob_storage_service()

    # Validate doctor exists
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    created_media: list[dict] = []
    failed_uploads: list[dict] = []

    for item in payload.uploads:
        try:
            logger.info(
                f"Processing upload: doctor_id={doctor_id}, "
                f"field={item.field_name}, file={item.file_name}"
            )

            # Download from URL and store in blob storage
            upload_result = await blob_service.upload_from_url(
                source_url=item.file,
                file_name=item.file_name,
                doctor_id=doctor_id,
                media_category=item.field_name,
            )

            if not upload_result.success:
                logger.error(
                    f"Blob upload failed for {item.file_name}: {upload_result.error_message}"
                )
                failed_uploads.append({
                    "field_name": item.field_name,
                    "file_name": item.file_name,
                    "error": upload_result.error_message or "Unknown error",
                })
                continue

            # Save to database with the blob URI

            media = await repo.add_media(
                doctor_id=doctor_id,
                media_type=item.field_name,
                media_category=item.field_name,
                field_name=item.field_name,
                file_uri=upload_result.file_uri,  # Use blob storage URI
                file_name=item.file_name,
                file_size=upload_result.file_size,
                mime_type=upload_result.mime_type,
            )

            created_media.append({
                "media_id": media.media_id,
                "field_name": item.field_name,
                "file_name": item.file_name,
                "file_uri": upload_result.file_uri,
                "file_size": upload_result.file_size,
                "mime_type": upload_result.mime_type,
                "content_hash": upload_result.content_hash,
            })

            logger.info(
                f"Media registered: media_id={media.media_id}, "
                f"blob_uri={upload_result.file_uri}"
            )

        except BlobDownloadError as e:
            logger.error(f"Download failed for {item.file_name}: {e}")
            failed_uploads.append({
                "field_name": item.field_name,
                "file_name": item.file_name,
                "error": f"Download failed: {str(e)}",
            })
        except BlobUploadError as e:
            logger.error(f"Upload failed for {item.file_name}: {e}")
            failed_uploads.append({
                "field_name": item.field_name,
                "file_name": item.file_name,
                "error": f"Storage failed: {str(e)}",
            })
        except Exception as e:
            logger.error(f"Unexpected error processing {item.file_name}: {e}")
            failed_uploads.append({
                "field_name": item.field_name,
                "file_name": item.file_name,
                "error": f"Unexpected error: {str(e)}",
            })

    # Determine response status
    if not created_media and failed_uploads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "All uploads failed",
                "failed_uploads": failed_uploads,
            },
        )

    return GenericResponse(
        message=(
            "Uploads registered successfully"
            if not failed_uploads
            else f"Partially successful: {len(created_media)} succeeded, {len(failed_uploads)} failed"
        ),
        data={
            "doctor_id": doctor_id,
            "media": created_media,
            "failed_uploads": failed_uploads if failed_uploads else None,
        },
    )

@router.post(
    "/delete/{doctor_id}",
    response_model=GenericResponse[dict],
    summary="Soft delete a profile",
)
async def delete_profile(
    doctor_id: int,
    db: DbSession,
) -> GenericResponse[dict]:
    repo = OnboardingRepository(db)

    identity = await repo.get_identity_by_doctor_id(doctor_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    now = datetime.now(UTC)
    identity.deleted_at = now
    identity.is_active = False

    await db.commit()
    await db.refresh(identity)

    return GenericResponse(
        message="Profile deleted successfully",
        data={
            "doctor_id": identity.doctor_id,
            "deleted_at": identity.deleted_at,
        },
    )

# =============================================================================
# LinQMD Integration Endpoints
# =============================================================================

class LinQMDSyncRequest(BaseModel):
    """Request to sync a doctor to LinQMD platform."""
    doctor_id: int

class LinQMDSyncResponse(BaseModel):
    """Response from LinQMD sync operation."""
    success: bool
    doctor_id: int
    linqmd_response: dict[str, Any] | None = None
    error_message: str | None = None
    http_status_code: int | None = None

@router.post(
    "/sync-to-linqmd/{doctor_id}",
    response_model=GenericResponse[LinQMDSyncResponse],
    summary="Sync doctor profile to LinQMD platform",
    description=(
        "Syncs a verified doctor's profile to the LinQMD platform. "
        "This creates/updates the doctor's account on LinQMD with their profile data. "
        "Requires LINQMD_SYNC_ENABLED=true in configuration."
    ),
)
async def sync_doctor_to_linqmd(
    doctor_id: int,
    db: DbSession,
) -> GenericResponse[LinQMDSyncResponse]:
    """
    Sync a doctor's profile to LinQMD platform.
    
    This endpoint:
    1. Fetches the doctor's data from the database
    2. Transforms it to LinQMD API format
    3. Sends it to the LinQMD user creation API
    4. Returns the sync result
    """
    settings = get_settings()
    sync_service = get_linqmd_sync_service()
    
    # Check if sync is enabled
    if not sync_service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinQMD sync is disabled. Set LINQMD_SYNC_ENABLED=true to enable.",
        )
    
    # Verify doctor exists
    repo = OnboardingRepository(db)
    identity = await repo.get_identity_by_doctor_id(doctor_id)
    
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found",
        )
    
    # Check if doctor is verified (optional - you may want to allow any status)
    # if identity.onboarding_status != OnboardingStatus.VERIFIED:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Doctor must be verified before syncing. Current status: {identity.onboarding_status.value}",
    #     )
    
    # Perform sync
    result = await sync_service.sync_doctor_by_id(doctor_id, db)
    
    response = LinQMDSyncResponse(
        success=result.success,
        doctor_id=result.doctor_id,
        linqmd_response=result.linqmd_response,
        error_message=result.error_message,
        http_status_code=result.http_status_code,
    )
    
    if result.success:
        return GenericResponse(
            message="Doctor profile synced to LinQMD successfully",
            data=response,
        )
    else:
        # Return success=false but don't raise exception - caller can decide what to do
        return GenericResponse(
            message=f"LinQMD sync failed: {result.error_message}",
            data=response,
        )

@router.get(
    "/linqmd-sync-status",
    response_model=GenericResponse[dict],
    summary="Check LinQMD sync configuration status",
    description="Check if LinQMD sync is enabled and properly configured.",
)
async def get_linqmd_sync_status() -> GenericResponse[dict]:
    """Check LinQMD sync configuration status."""
    settings = get_settings()
    sync_service = get_linqmd_sync_service()
    
    
    return GenericResponse(
        message="LinQMD sync configuration",
        data={
            "enabled": settings.LINQMD_SYNC_ENABLED,
            "api_url": settings.LINQMD_API_URL,
            "auth_configured": bool(settings.LINQMD_AUTH_TOKEN),
            "cookie_configured": bool(settings.LINQMD_COOKIE),
            "timeout_seconds": settings.LINQMD_API_TIMEOUT,
        },
    )

class LinQMDBulkSyncRequest(BaseModel):
    """Request to sync multiple doctors to LinQMD platform."""
    doctor_ids: list[int]

@router.post(
    "/sync-to-linqmd-bulk",
    response_model=GenericResponse[dict],
    summary="Bulk sync doctor profiles to LinQMD platform",
    description="Sync multiple verified doctor profiles to the LinQMD platform.",
)
async def sync_doctors_to_linqmd_bulk(
    request: LinQMDBulkSyncRequest,
    db: DbSession,
) -> GenericResponse[dict]:
    """
    Bulk sync multiple doctors to LinQMD platform.
    
    Processes each doctor and returns summary of successes/failures.
    """
    settings = get_settings()
    sync_service = get_linqmd_sync_service()
    
    if not sync_service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinQMD sync is disabled. Set LINQMD_SYNC_ENABLED=true to enable.",
        )
    
    results = {
        "total": len(request.doctor_ids),
        "successful": 0,
        "failed": 0,
        "details": [],
    }
    
    for doctor_id in request.doctor_ids:
        result = await sync_service.sync_doctor_by_id(doctor_id, db)
        
        if result.success:
            results["successful"] += 1
        else:
            results["failed"] += 1
        
        results["details"].append({
            "doctor_id": doctor_id,
            "success": result.success,
            "error": result.error_message,
        })
    
    return GenericResponse(
        message=f"Bulk sync complete: {results['successful']}/{results['total']} successful",
        data=results,
    )

