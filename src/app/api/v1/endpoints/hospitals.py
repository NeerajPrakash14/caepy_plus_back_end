"""
Hospital API Endpoints.

Provides endpoints for:
- Hospital search/autocomplete (for onboarding dropdown)
- Hospital CRUD (admin)
- Doctor-hospital affiliations
- Hospital verification (admin)
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.exceptions import BadRequestError, ConflictError, NotFoundError
from ....core.rbac import AdminOrOperationalUser
from ....core.responses import GenericResponse
from ....db.session import get_db
from ....models.hospital import HospitalVerificationStatus as ModelHospitalVerificationStatus
from ....repositories.hospital_repository import (
    DoctorHospitalAffiliationRepository,
    HospitalRepository,
)
from ....schemas.hospital import (
    AffiliationCreate,
    AffiliationCreateWithNewHospital,
    AffiliationResponse,
    AffiliationUpdate,
    AffiliationWithHospitalResponse,
    DoctorPracticeLocationsResponse,
    HospitalCreate,
    HospitalListResponse,
    HospitalMerge,
    HospitalResponse,
    HospitalSearchResult,
    HospitalStats,
    HospitalUpdate,
    HospitalVerificationStatus,
    HospitalVerify,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


# =============================================================================
# Dependencies
# =============================================================================

async def get_hospital_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HospitalRepository:
    """Get hospital repository."""
    return HospitalRepository(db)


async def get_affiliation_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorHospitalAffiliationRepository:
    """Get affiliation repository."""
    return DoctorHospitalAffiliationRepository(db)


# =============================================================================
# Search Endpoints (Public - for onboarding dropdown)
# =============================================================================

@router.get(
    "/search",
    response_model=GenericResponse[list[HospitalSearchResult]],
    summary="Search hospitals for autocomplete",
    description="Search verified hospitals by name. Used for dropdown during doctor onboarding.",
)
async def search_hospitals(
    q: Annotated[str, Query(min_length=1, description="Search query (hospital name)")],
    city: Annotated[str | None, Query(description="Filter by city")] = None,
    state: Annotated[str | None, Query(description="Filter by state")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Max results")] = 20,
    repo: HospitalRepository = Depends(get_hospital_repo),
) -> GenericResponse[list[HospitalSearchResult]]:
    """Search hospitals for autocomplete dropdown."""
    hospitals = await repo.search(
        query=q,
        city=city,
        state=state,
        verified_only=True,
        active_only=True,
        limit=limit,
    )

    results = [
        HospitalSearchResult(
            id=h.id,
            name=h.name,
            city=h.city,
            state=h.state,
            display_name=f"{h.name}, {h.city}" if h.city else h.name,
        )
        for h in hospitals
    ]

    return GenericResponse(
        message=f"Found {len(results)} hospitals",
        data=results,
    )


@router.get(
    "/{hospital_id}",
    response_model=GenericResponse[HospitalResponse],
    summary="Get hospital by ID",
)
async def get_hospital(
    hospital_id: Annotated[int, Path(description="Hospital ID")],
    repo: HospitalRepository = Depends(get_hospital_repo),
) -> GenericResponse[HospitalResponse]:
    """Get hospital details by ID."""
    hospital = await repo.get_by_id(hospital_id)
    if not hospital:
        raise NotFoundError(message=f"Hospital with ID {hospital_id} not found")

    return GenericResponse(
        message="Hospital retrieved successfully",
        data=HospitalResponse.model_validate(hospital),
    )


# =============================================================================
# Hospital Creation (Doctor Self-Add)
# =============================================================================

@router.post(
    "",
    response_model=GenericResponse[HospitalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add new hospital",
    description="Add a new hospital. If added by a doctor, it will be pending verification.",
)
async def create_hospital(
    hospital_data: HospitalCreate,
    doctor_id: Annotated[int | None, Query(description="Doctor ID if adding during onboarding")] = None,
    repo: HospitalRepository = Depends(get_hospital_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[HospitalResponse]:
    """Create a new hospital."""
    hospital = await repo.create(
        name=hospital_data.name,
        address=hospital_data.address,
        city=hospital_data.city,
        state=hospital_data.state,
        pincode=hospital_data.pincode,
        phone_number=hospital_data.phone_number,
        email=hospital_data.email,
        website=hospital_data.website,
        created_by_doctor_id=doctor_id,
        verification_status=ModelHospitalVerificationStatus.PENDING,
    )

    await db.commit()

    return GenericResponse(
        message="Hospital added successfully. Pending verification." if doctor_id else "Hospital created successfully.",
        data=HospitalResponse.model_validate(hospital),
    )


# =============================================================================
# Hospital List (Admin)
# =============================================================================

@router.get(
    "",
    response_model=GenericResponse[list[HospitalListResponse]],
    summary="List all hospitals",
)
async def list_hospitals(
    skip: Annotated[int, Query(ge=0, description="Skip N records")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max records")] = 50,
    verification_status: Annotated[HospitalVerificationStatus | None, Query(description="Filter by status")] = None,
    city: Annotated[str | None, Query(description="Filter by city")] = None,
    state: Annotated[str | None, Query(description="Filter by state")] = None,
    include_inactive: Annotated[bool, Query(description="Include inactive hospitals")] = False,
    repo: HospitalRepository = Depends(get_hospital_repo),
) -> GenericResponse[list[HospitalListResponse]]:
    """List hospitals with filters (admin view)."""
    model_status = None
    if verification_status:
        model_status = ModelHospitalVerificationStatus(verification_status.value)

    hospitals, total = await repo.list_all(
        skip=skip,
        limit=limit,
        verification_status=model_status,
        active_only=not include_inactive,
        city=city,
        state=state,
    )

    results = [HospitalListResponse.model_validate(h) for h in hospitals]

    return GenericResponse(
        message=f"Retrieved {len(results)} of {total} hospitals",
        data=results,
    )


@router.get(
    "/admin/pending",
    response_model=GenericResponse[list[HospitalResponse]],
    summary="List pending hospitals (admin)",
)
async def list_pending_hospitals(
    admin: AdminOrOperationalUser,  # Require admin or operational role
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    repo: HospitalRepository = Depends(get_hospital_repo),
) -> GenericResponse[list[HospitalResponse]]:
    """List hospitals pending verification (admin view). Requires admin or operational role."""
    hospitals, total = await repo.list_pending(skip=skip, limit=limit)
    results = [HospitalResponse.model_validate(h) for h in hospitals]

    return GenericResponse(
        message=f"Found {total} hospitals pending verification",
        data=results,
    )


@router.get(
    "/admin/stats",
    response_model=GenericResponse[HospitalStats],
    summary="Get hospital statistics (admin)",
)
async def get_hospital_stats(
    admin: AdminOrOperationalUser,  # Require admin or operational role
    repo: HospitalRepository = Depends(get_hospital_repo),
) -> GenericResponse[HospitalStats]:
    """Get hospital statistics. Requires admin or operational role."""
    stats = await repo.get_stats()
    return GenericResponse(
        message="Hospital statistics retrieved",
        data=HospitalStats(**stats),
    )


# =============================================================================
# Hospital Update (Admin)
# =============================================================================

@router.patch(
    "/{hospital_id}",
    response_model=GenericResponse[HospitalResponse],
    summary="Update hospital (admin)",
)
async def update_hospital(
    hospital_id: Annotated[int, Path(description="Hospital ID")],
    hospital_data: HospitalUpdate,
    repo: HospitalRepository = Depends(get_hospital_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[HospitalResponse]:
    """Update hospital details (admin only)."""
    update_data = hospital_data.model_dump(exclude_unset=True)
    if not update_data:
        raise BadRequestError(message="No update data provided")

    hospital = await repo.update(hospital_id, **update_data)
    if not hospital:
        raise NotFoundError(message=f"Hospital with ID {hospital_id} not found")

    await db.commit()

    return GenericResponse(
        message="Hospital updated successfully",
        data=HospitalResponse.model_validate(hospital),
    )


@router.delete(
    "/{hospital_id}",
    response_model=GenericResponse[dict],
    summary="Delete hospital (admin)",
)
async def delete_hospital(
    hospital_id: Annotated[int, Path(description="Hospital ID")],
    repo: HospitalRepository = Depends(get_hospital_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[dict]:
    """Soft delete a hospital (admin only)."""
    deleted = await repo.soft_delete(hospital_id)
    if not deleted:
        raise NotFoundError(message=f"Hospital with ID {hospital_id} not found")

    await db.commit()

    return GenericResponse(
        message="Hospital deleted successfully",
        data={"hospital_id": hospital_id},
    )


# =============================================================================
# Hospital Verification (Admin)
# =============================================================================

@router.post(
    "/{hospital_id}/verify",
    response_model=GenericResponse[HospitalResponse],
    summary="Verify or reject hospital (admin)",
)
async def verify_hospital(
    hospital_id: Annotated[int, Path(description="Hospital ID")],
    verification: HospitalVerify,
    admin: AdminOrOperationalUser,  # Require admin or operational role
    repo: HospitalRepository = Depends(get_hospital_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[HospitalResponse]:
    """Verify or reject a hospital (admin action). Requires admin or operational role."""
    if verification.action == "reject" and not verification.rejection_reason:
        raise BadRequestError(message="Rejection reason is required when rejecting a hospital")

    if verification.action == "verify":
        hospital = await repo.verify(
            hospital_id=hospital_id,
            verified_by=verification.verified_by,
        )
        message = "Hospital verified successfully"
    else:
        hospital = await repo.reject(
            hospital_id=hospital_id,
            rejection_reason=verification.rejection_reason or "",
            rejected_by=verification.verified_by,
        )
        message = "Hospital rejected"

    if not hospital:
        raise NotFoundError(message=f"Hospital with ID {hospital_id} not found")

    await db.commit()

    return GenericResponse(
        message=message,
        data=HospitalResponse.model_validate(hospital),
    )


@router.post(
    "/admin/merge",
    response_model=GenericResponse[dict],
    summary="Merge duplicate hospitals (admin)",
)
async def merge_hospitals(
    merge_data: HospitalMerge,
    admin: AdminOrOperationalUser,  # Require admin or operational role
    repo: HospitalRepository = Depends(get_hospital_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[dict]:
    """Merge duplicate hospitals into a target hospital. Requires admin or operational role."""
    # Validate target exists
    target = await repo.get_by_id(merge_data.target_hospital_id)
    if not target:
        raise NotFoundError(message=f"Target hospital with ID {merge_data.target_hospital_id} not found")

    # Validate sources exist and are different from target
    if merge_data.target_hospital_id in merge_data.source_hospital_ids:
        raise BadRequestError(message="Target hospital cannot be in source list")

    for source_id in merge_data.source_hospital_ids:
        source = await repo.get_by_id(source_id)
        if not source:
            raise NotFoundError(message=f"Source hospital with ID {source_id} not found")

    affiliations_moved = await repo.merge_hospitals(
        source_ids=merge_data.source_hospital_ids,
        target_id=merge_data.target_hospital_id,
    )

    await db.commit()

    return GenericResponse(
        message=f"Merged {len(merge_data.source_hospital_ids)} hospitals, moved {affiliations_moved} affiliations",
        data={
            "merged_hospitals": merge_data.source_hospital_ids,
            "target_hospital": merge_data.target_hospital_id,
            "affiliations_moved": affiliations_moved,
        },
    )


# =============================================================================
# Doctor-Hospital Affiliations
# =============================================================================

@router.post(
    "/affiliations",
    response_model=GenericResponse[AffiliationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create doctor-hospital affiliation",
)
async def create_affiliation(
    affiliation_data: AffiliationCreate,
    doctor_id: Annotated[int, Query(description="Doctor ID")],
    hospital_repo: HospitalRepository = Depends(get_hospital_repo),
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[AffiliationResponse]:
    """Create an affiliation between a doctor and an existing hospital."""
    # Verify hospital exists
    hospital = await hospital_repo.get_by_id(affiliation_data.hospital_id)
    if not hospital:
        raise NotFoundError(message=f"Hospital with ID {affiliation_data.hospital_id} not found")

    # Check if affiliation already exists
    existing = await affiliation_repo.get_by_doctor_and_hospital(
        doctor_id=doctor_id,
        hospital_id=affiliation_data.hospital_id,
    )
    if existing:
        raise ConflictError(message="Doctor is already affiliated with this hospital")

    affiliation = await affiliation_repo.create(
        doctor_id=doctor_id,
        hospital_id=affiliation_data.hospital_id,
        consultation_fee=affiliation_data.consultation_fee,
        consultation_type=affiliation_data.consultation_type,
        weekly_schedule=affiliation_data.weekly_schedule,
        designation=affiliation_data.designation,
        department=affiliation_data.department,
        is_primary=affiliation_data.is_primary,
    )

    await db.commit()

    # Reload with hospital
    affiliation = await affiliation_repo.get_by_id(affiliation.id)

    return GenericResponse(
        message="Affiliation created successfully",
        data=AffiliationResponse.model_validate(affiliation),
    )


@router.post(
    "/affiliations/with-new-hospital",
    response_model=GenericResponse[AffiliationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create affiliation with new hospital",
)
async def create_affiliation_with_new_hospital(
    data: AffiliationCreateWithNewHospital,
    doctor_id: Annotated[int, Query(description="Doctor ID")],
    hospital_repo: HospitalRepository = Depends(get_hospital_repo),
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[AffiliationResponse]:
    """Create a new hospital and affiliate the doctor with it in one step."""
    # Create the hospital (pending verification)
    hospital = await hospital_repo.create(
        name=data.hospital_name,
        address=data.hospital_address,
        city=data.hospital_city,
        state=data.hospital_state,
        pincode=data.hospital_pincode,
        phone_number=data.hospital_phone,
        created_by_doctor_id=doctor_id,
        verification_status=ModelHospitalVerificationStatus.PENDING,
    )

    # Create the affiliation
    affiliation = await affiliation_repo.create(
        doctor_id=doctor_id,
        hospital_id=hospital.id,
        consultation_fee=data.consultation_fee,
        consultation_type=data.consultation_type,
        weekly_schedule=data.weekly_schedule,
        designation=data.designation,
        department=data.department,
        is_primary=data.is_primary,
    )

    await db.commit()

    # Reload with hospital
    affiliation = await affiliation_repo.get_by_id(affiliation.id)

    return GenericResponse(
        message="Hospital added (pending verification) and affiliation created",
        data=AffiliationResponse.model_validate(affiliation),
    )


@router.get(
    "/affiliations/doctor/{doctor_id}",
    response_model=GenericResponse[DoctorPracticeLocationsResponse],
    summary="Get doctor's practice locations",
)
async def get_doctor_affiliations(
    doctor_id: Annotated[int, Path(description="Doctor ID")],
    include_unverified: Annotated[bool, Query(description="Include unverified hospitals")] = True,
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
) -> GenericResponse[DoctorPracticeLocationsResponse]:
    """Get all practice locations (hospital affiliations) for a doctor."""
    affiliations = await affiliation_repo.list_by_doctor(
        doctor_id=doctor_id,
        active_only=True,
        include_unverified_hospitals=include_unverified,
    )

    # Convert to response with nested hospital
    affiliation_responses = []
    for a in affiliations:
        aff_dict = {
            "id": a.id,
            "doctor_id": a.doctor_id,
            "hospital_id": a.hospital_id,
            "consultation_fee": a.consultation_fee,
            "consultation_type": a.consultation_type,
            "weekly_schedule": a.weekly_schedule,
            "designation": a.designation,
            "department": a.department,
            "is_primary": a.is_primary,
            "is_active": a.is_active,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "hospital": HospitalResponse.model_validate(a.hospital) if a.hospital else None,
        }
        affiliation_responses.append(AffiliationWithHospitalResponse(**aff_dict))

    return GenericResponse(
        message=f"Retrieved {len(affiliations)} practice locations",
        data=DoctorPracticeLocationsResponse(
            doctor_id=doctor_id,
            affiliations=affiliation_responses,
            total_count=len(affiliation_responses),
        ),
    )


@router.get(
    "/affiliations/hospital/{hospital_id}",
    response_model=GenericResponse[list[AffiliationResponse]],
    summary="Get doctors at a hospital",
)
async def get_hospital_doctors(
    hospital_id: Annotated[int, Path(description="Hospital ID")],
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
) -> GenericResponse[list[AffiliationResponse]]:
    """Get all doctors affiliated with a hospital."""
    affiliations = await affiliation_repo.list_by_hospital(
        hospital_id=hospital_id,
        active_only=True,
    )

    results = [AffiliationResponse.model_validate(a) for a in affiliations]

    return GenericResponse(
        message=f"Found {len(results)} doctors at this hospital",
        data=results,
    )


@router.patch(
    "/affiliations/{affiliation_id}",
    response_model=GenericResponse[AffiliationResponse],
    summary="Update affiliation",
)
async def update_affiliation(
    affiliation_id: Annotated[str, Path(description="Affiliation ID")],
    data: AffiliationUpdate,
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[AffiliationResponse]:
    """Update doctor-hospital affiliation details."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise BadRequestError(message="No update data provided")

    affiliation = await affiliation_repo.update(affiliation_id, **update_data)
    if not affiliation:
        raise NotFoundError(message=f"Affiliation with ID {affiliation_id} not found")

    await db.commit()

    return GenericResponse(
        message="Affiliation updated successfully",
        data=AffiliationResponse.model_validate(affiliation),
    )


@router.delete(
    "/affiliations/{affiliation_id}",
    response_model=GenericResponse[dict],
    summary="Remove affiliation",
)
async def delete_affiliation(
    affiliation_id: Annotated[str, Path(description="Affiliation ID")],
    affiliation_repo: DoctorHospitalAffiliationRepository = Depends(get_affiliation_repo),
    db: AsyncSession = Depends(get_db),
) -> GenericResponse[dict]:
    """Remove a doctor-hospital affiliation."""
    deleted = await affiliation_repo.soft_delete(affiliation_id)
    if not deleted:
        raise NotFoundError(message=f"Affiliation with ID {affiliation_id} not found")

    await db.commit()

    return GenericResponse(
        message="Affiliation removed successfully",
        data={"affiliation_id": affiliation_id},
    )
