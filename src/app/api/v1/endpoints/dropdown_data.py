"""Dropdown/Autocomplete data endpoints for onboarding forms.

These endpoints provide pre-populated dropdown values based on
existing doctor data in the system. Frontend can use these to
populate dropdowns during doctor onboarding.

Data sources:
- Specialisation: from doctor_details.speciality
- Sub-specialisation: from doctor_details.sub_specialities (JSON array)
- Degrees: from doctor_details.qualifications (JSON array of objects)
"""
from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from ....core.responses import GenericResponse
from ....db.session import DbSession
from ....repositories import OnboardingRepository

router = APIRouter(prefix="/dropdown-data", tags=["Dropdown Data"])

# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class DropdownValuesResponse(BaseModel):
    """Response containing list of dropdown values."""
    
    values: list[str] = Field(
        description="List of unique values for the dropdown"
    )
    count: int = Field(
        description="Number of unique values"
    )

class AllDropdownDataResponse(BaseModel):
    """Response containing all dropdown data for onboarding forms."""
    
    specialisations: list[str] = Field(
        default_factory=list,
        description="Unique specialisation values"
    )
    sub_specialisations: list[str] = Field(
        default_factory=list,
        description="Unique sub-specialisation values"
    )
    degrees: list[str] = Field(
        default_factory=list,
        description="Unique degree/qualification values"
    )

# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class DropdownValuesUpdateRequest(BaseModel):
    """Payload for adding new values to a dropdown field."""

    field_name: str = Field(
        ...,
        description=(
            "Dropdown field name (e.g. 'specialisations', "
            "'sub_specialisations', 'degrees')."
        ),
    )
    values: list[str] = Field(
        ..., min_length=1, description="List of values to add for this field"
    )
    sub_specialisations: list[str] = Field(
        default_factory=list,
        description="Unique sub-specialisation values"
    )
    degrees: list[str] = Field(
        default_factory=list,
        description="Unique degree/qualification values"
    )

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/specialisations",
    response_model=GenericResponse[DropdownValuesResponse],
    summary="Get specialisation dropdown values",
    description="""
Fetch unique specialisation values from existing doctor data.

**Use case:** Populate specialisation dropdown during doctor onboarding.
Values are sorted alphabetically.
    """,
)
async def get_specialisations(db: DbSession) -> GenericResponse[DropdownValuesResponse]:
    """Get unique specialisation values for dropdown."""
    
    repo = OnboardingRepository(db)
    values = await repo.get_unique_specialities()
    
    return GenericResponse(
        message=f"Found {len(values)} specialisation(s)",
        data=DropdownValuesResponse(values=values, count=len(values)),
    )

@router.get(
    "/sub-specialisations",
    response_model=GenericResponse[DropdownValuesResponse],
    summary="Get sub-specialisation dropdown values",
    description="""
Fetch unique sub-specialisation values from existing doctor data.

**Use case:** Populate sub-specialisation dropdown during doctor onboarding.
Values are extracted from all doctors' sub_specialities arrays and deduplicated.
    """,
)
async def get_sub_specialisations(db: DbSession) -> GenericResponse[DropdownValuesResponse]:
    """Get unique sub-specialisation values for dropdown."""
    
    repo = OnboardingRepository(db)
    values = await repo.get_unique_sub_specialities()
    
    return GenericResponse(
        message=f"Found {len(values)} sub-specialisation(s)",
        data=DropdownValuesResponse(values=values, count=len(values)),
    )

@router.get(
    "/degrees",
    response_model=GenericResponse[DropdownValuesResponse],
    summary="Get degree/qualification dropdown values",
    description="""
Fetch unique degree values from existing doctor qualifications.

**Use case:** Populate degree dropdown during doctor onboarding.
Values are extracted from qualifications JSON (degree/name/title field).
    """,
)
async def get_degrees(db: DbSession) -> GenericResponse[DropdownValuesResponse]:
    """Get unique degree values for dropdown."""
    
    repo = OnboardingRepository(db)
    values = await repo.get_unique_degrees()
    
    return GenericResponse(
        message=f"Found {len(values)} degree(s)",
        data=DropdownValuesResponse(values=values, count=len(values)),
    )

@router.get(
    "/all",
    response_model=GenericResponse[AllDropdownDataResponse],
    summary="Get all dropdown data for onboarding",
    description="""
Fetch all dropdown values in a single request for onboarding forms.

**Returns:**
- specialisations: Unique specialisation values
- sub_specialisations: Unique sub-specialisation values  
- degrees: Unique degree/qualification values

**Use case:** Single API call to populate all dropdowns during doctor onboarding.
Frontend can cache this response and refresh periodically.
    """,
)
async def get_all_dropdown_data(db: DbSession) -> GenericResponse[AllDropdownDataResponse]:
    """Get all dropdown data in a single request."""
    
    repo = OnboardingRepository(db)
    
    specialisations = await repo.get_unique_specialities()
    sub_specialisations = await repo.get_unique_sub_specialities()
    degrees = await repo.get_unique_degrees()
    
    return GenericResponse(
        message="Dropdown data retrieved successfully",
        data=AllDropdownDataResponse(
            specialisations=specialisations,
            sub_specialisations=sub_specialisations,
            degrees=degrees,
        ),
    )

@router.post(
    "/values",
    response_model=GenericResponse[DropdownValuesResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add values to a dropdown field",
    description=(
        "Add new values for a specific dropdown field so that they "
        "are persisted in the database and included in subsequent "
        "GET /dropdown-data endpoints."
    ),
)
async def add_dropdown_values(
    payload: DropdownValuesUpdateRequest,
    db: DbSession,
) -> GenericResponse[DropdownValuesResponse]:
    """Persist new dropdown values for a given field and return all values.

    This allows admins to configure additional options that may not yet be
    present in existing doctor data but should be available in onboarding
    forms.
    """

    repo = OnboardingRepository(db)

    all_values = await repo.add_dropdown_values(
        field_name=payload.field_name,
        values=payload.values,
    )

    return GenericResponse(
        message=(
            f"Added {len(payload.values)} value(s) to dropdown field "
            f"'{payload.field_name}'."
        ),
        data=DropdownValuesResponse(values=all_values, count=len(all_values)),
    )
