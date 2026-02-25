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

from typing import Annotated, Any
from fastapi import APIRouter, status, Query
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
    "",
    response_model=GenericResponse[DropdownValuesResponse | AllDropdownDataResponse],
    summary="Get dropdown reference data",
    description="""
Fetch dropdown values.

If a `type` query parameter is provided (e.g., `specialisations`, `sub_specialisations`, `degrees`), 
it returns just that type. 
If no `type` is provided, it returns all dropdown data in a single response (useful for caching).
    """,
)
async def get_dropdown_data(
    dropdown_type: Annotated[str | None, Query(alias="type", description="The specific type of data to fetch (specialisations, sub_specialisations, degrees)")] = None,
    db: DbSession = None,
) -> GenericResponse[Any]:
    """Get reference data for dropdowns."""
    repo = OnboardingRepository(db)

    if dropdown_type == "specialisations":
        values = await repo.get_unique_specialities()
        return GenericResponse(
            message=f"Found {len(values)} specialisation(s)",
            data=DropdownValuesResponse(values=values, count=len(values)),
        )
    elif dropdown_type == "sub_specialisations":
        values = await repo.get_unique_sub_specialities()
        return GenericResponse(
            message=f"Found {len(values)} sub-specialisation(s)",
            data=DropdownValuesResponse(values=values, count=len(values)),
        )
    elif dropdown_type == "degrees":
        values = await repo.get_unique_degrees()
        return GenericResponse(
            message=f"Found {len(values)} degree(s)",
            data=DropdownValuesResponse(values=values, count=len(values)),
        )
    elif dropdown_type is not None:
        raise BadRequestError(message=f"Unknown dropdown type: {dropdown_type}")
        
    # Default to all if no type specifier
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
