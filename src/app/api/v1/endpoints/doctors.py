""" 
Doctor CRUD Endpoints.

RESTful API for doctor resource management.
"""

import os
from datetime import datetime, UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.exceptions import DoctorNotFoundError
from ....core.responses import GenericResponse, PaginatedResponse, PaginationMeta
from ....db.session import DbSession, Base
from ....repositories.doctor_repository import DoctorRepository
from ....repositories.onboarding_repository import OnboardingRepository
from ....repositories.hospital_repository import HospitalRepository, DoctorHospitalAffiliationRepository
from ....schemas.doctor import (
    DoctorCreate,
    DoctorResponse,
    DoctorSummary,
    DoctorUpdate,
)

router = APIRouter(prefix="/doctors")


def _is_dev_environment() -> bool:
    """Check if running in development environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local", "test")


def get_doctor_repository(db: DbSession) -> DoctorRepository:
    """Dependency to get doctor repository."""
    return DoctorRepository(db)

@router.post(
    "",
    response_model=GenericResponse[DoctorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new doctor",
    description="Register a new doctor with their professional information.",
)
async def create_doctor(
    data: DoctorCreate,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> GenericResponse[DoctorResponse]:
    """
    Create a new doctor record.
    
    - **email**: Must be unique across all doctors
    - **medical_registration_number**: Required for verification
    - **qualifications**: List of educational qualifications
    - **practice_locations**: List of clinic/hospital locations
    """
    doctor = await repo.create(data)
    
    return GenericResponse(
        message="Doctor created successfully",
        data=DoctorResponse.model_validate(doctor),
    )

@router.get(
    "",
    response_model=PaginatedResponse[DoctorSummary],
    summary="List all doctors",
    description="Get a paginated list of all registered doctors.",
)
async def list_doctors(
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    specialization: str | None = Query(default=None, description="Filter by specialization"),
) -> PaginatedResponse[DoctorSummary]:
    """
    List doctors with pagination.
    
    Supports filtering by specialization using partial matching.
    """
    skip = (page - 1) * page_size
    
    doctors = await repo.get_all(
        skip=skip,
        limit=page_size,
        specialization=specialization,
    )
    total = await repo.count(specialization=specialization)
    
    return PaginatedResponse(
        message="Doctors retrieved successfully",
        data=[DoctorSummary.model_validate(d) for d in doctors],
        pagination=PaginationMeta.from_total(total, page, page_size),
    )

@router.delete(
    "/erase-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Erase all records (DEV ONLY)",
    description=(
        "⚠️ DANGEROUS: Permanently and irreversibly delete all records from all "
        "application tables. Only available in development/test environments."
    ),
    tags=["Development"],
)
async def erase_all_records(db: DbSession) -> None:
    """Erase all records from all application tables.
    
    ⚠️ WARNING: This endpoint is only available in development environments.
    It will return 403 Forbidden in production.

    This iterates over every table registered in the shared SQLAlchemy
    ``Base`` metadata and issues a ``DELETE`` against each one,
    respecting foreign-key dependency order.
    """
    # Security check: Only allow in development environments
    if not _is_dev_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development environments"
        )

    # Delete from all tables in reverse dependency order so that
    # child tables are cleared before their parents.
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(table.delete())

    await db.commit()

@router.get(
    "/email/{email}",
    response_model=GenericResponse[DoctorResponse],
    summary="Get doctor by email",
    description="Look up a doctor by their email address.",
)
async def get_doctor_by_email(
    email: str,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> GenericResponse[DoctorResponse]:
    """
    Get a doctor by email address.
    
    Useful for checking if a doctor is already registered.
    """
    from ....core.exceptions import DoctorNotFoundError
    
    doctor = await repo.get_by_email(email)
    if not doctor:
        raise DoctorNotFoundError(email=email)
    
    return GenericResponse(
        message="Doctor retrieved successfully",
        data=DoctorResponse.model_validate(doctor),
    )

@router.get(
    "/phone/{phone_number}",
    response_model=GenericResponse[DoctorResponse],
    summary="Get doctor by phone number",
    description="Look up a doctor by their phone number.",
)
async def get_doctor_by_phone_number(
    phone_number: str,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> GenericResponse[DoctorResponse]:
    """Get a doctor by phone number (normalized to digits)."""
    from ....core.exceptions import DoctorNotFoundError

    doctor = await repo.get_by_phone_number(phone_number)
    if not doctor:
        raise DoctorNotFoundError(message=f"Doctor not found: {phone_number}")

    return GenericResponse(
        message="Doctor retrieved successfully",
        data=DoctorResponse.model_validate(doctor),
    )

@router.get(
    "/{doctor_id}",
    response_model=GenericResponse[DoctorResponse],
    summary="Get doctor by ID",
    description="Retrieve detailed information about a specific doctor.",
)
async def get_doctor(
    doctor_id: int,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> GenericResponse[DoctorResponse]:
    """Get a doctor by their ID."""
    doctor = await repo.get_by_id_or_raise(doctor_id)

    return GenericResponse(
        message="Doctor retrieved successfully",
        data=DoctorResponse.model_validate(doctor),
    )

@router.put(
    "/{doctor_id}",
    response_model=GenericResponse[DoctorResponse],
    summary="Update doctor",
    description="Update an existing doctor's information.",
)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> GenericResponse[DoctorResponse]:
    """Update a doctor's information."""
    doctor = await repo.update(doctor_id, data)

    return GenericResponse(
        message="Doctor updated successfully",
        data=DoctorResponse.model_validate(doctor),
    )

@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete doctor",
    description="Remove a doctor from the system.",
)
async def delete_doctor(
    doctor_id: int,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> None:
    """Delete a doctor by ID.

    In addition to removing the doctor record from the main
    `doctors` table, this will also soft-delete the corresponding
    entry in the `doctor_identity` onboarding table (if it exists)
    by setting `is_active` to False and populating `deleted_at`.
    """

    # First, delete the doctor row from the primary doctors table.
    await repo.delete_or_raise(doctor_id)

    # Then, attempt to soft-delete the related onboarding identity row.
    onboarding_repo = OnboardingRepository(repo.session)
    identity = await onboarding_repo.get_identity_by_doctor_id(doctor_id)
    if identity is not None:
        identity.is_active = False
        identity.deleted_at = datetime.now(UTC)
        await repo.session.commit()
        await repo.session.refresh(identity)

@router.delete(
    "/{doctor_id}/erase",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Erase doctor records",
    description=(
        "Permanently and irreversibly remove a doctor's records from all "
        "related tables by doctor_id. Use this for full erasure/" 
        "right-to-be-forgotten workflows."
    ),
)
async def erase_doctor(
    doctor_id: int,
    repo: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> None:
    """Completely erase a doctor across all related tables.

    This endpoint attempts to remove:
    - The doctor row from the primary ``doctors`` table
    - Onboarding data (doctor_identity, doctor_details, doctor_media,
      doctor_status_history)
    - Doctor-hospital affiliations and creator references on hospitals

    If no records are found in any of these tables for the given
    ``doctor_id``, a ``DoctorNotFoundError`` is raised.
    """

    # Use the same database session across all repositories so the
    # operation participates in a single transaction boundary provided
    # by the request-scoped session.
    onboarding_repo = OnboardingRepository(repo.session)
    hospital_repo = HospitalRepository(repo.session)
    affiliation_repo = DoctorHospitalAffiliationRepository(repo.session)

    # Delete main doctor row (if present).
    deleted_main = await repo.delete(doctor_id)

    # Hard delete onboarding data (identity + cascading tables).
    deleted_onboarding = await onboarding_repo.hard_delete_doctor(doctor_id)

    # Remove doctor-hospital affiliations and clear creator references.
    deleted_affiliations = await affiliation_repo.hard_delete_by_doctor(doctor_id)
    cleared_hospitals = await hospital_repo.clear_created_by_doctor(doctor_id)

    # If nothing was affected anywhere, treat as not found.
    if (
        not deleted_main
        and deleted_onboarding == 0
        and deleted_affiliations == 0
        and cleared_hospitals == 0
    ):
        raise DoctorNotFoundError(doctor_id=doctor_id)
