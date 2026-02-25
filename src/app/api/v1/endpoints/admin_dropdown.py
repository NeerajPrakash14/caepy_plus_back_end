"""Admin API Endpoints for Dropdown Options Management.

Provides endpoints for:
- Viewing and managing dropdown values
- Seeding initial data
- Reviewing and verifying doctor contributions
- Statistics and monitoring
"""
from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....models.dropdown_option import (
    DROPDOWN_FIELD_CONFIG,
    DropdownFieldCategory,
    DropdownOption,
)
from ....schemas.dropdown_option import (
    BulkCreateResponse,
    DeactivateResponse,
    DropdownDataResponse,
    DropdownFieldConfigResponse,
    DropdownFieldResponse,
    DropdownOptionBulkCreate,
    DropdownOptionCreate,
    DropdownOptionResponse,
    DropdownOptionUpdate,
    DropdownStatsResponse,
    SeedResponse,
    SingleCreateResponse,
    UnverifiedOptionResponse,
    VerifyResponse,
)
from ....services.dropdown_option_service import DropdownOptionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/dropdown-options",
    tags=["Admin - Dropdown Options"],
)

# =============================================================================
# Dependencies
# =============================================================================

async def get_dropdown_service(
    session: AsyncSession = Depends(get_db),
) -> DropdownOptionService:
    """Get dropdown option service with database session."""
    return DropdownOptionService(session)


# Type alias for cleaner annotations
DropdownServiceDep = Annotated[DropdownOptionService, Depends(get_dropdown_service)]


# =============================================================================
# Field Configuration Endpoints
# =============================================================================

@router.get(
    "/fields",
    response_model=list[DropdownFieldConfigResponse],
    summary="List all dropdown fields",
    description="Get configuration for all dropdown fields available for management.",
)
async def list_dropdown_fields() -> list[dict[str, Any]]:
    """List all configured dropdown fields with their metadata."""
    fields = []

    for field_name, config in DROPDOWN_FIELD_CONFIG.items():
        category = config["category"]
        fields.append({
            "field_name": field_name,
            "display_name": config["display_name"],
            "category": category.value if isinstance(category, DropdownFieldCategory) else category,
            "multi_select": config.get("multi_select", False),
            "allow_custom": config.get("allow_custom", True),
        })

    return fields


@router.get(
    "/fields/{field_name}",
    response_model=DropdownFieldResponse,
    summary="Get options for a field",
    description="Get all dropdown options for a specific field.",
)
async def get_field_options(
    field_name: str,
    service: DropdownServiceDep,
    include_inactive: bool = Query(False, description="Include deactivated options"),
) -> dict[str, Any]:
    """Get all options for a specific dropdown field."""
    if field_name not in DROPDOWN_FIELD_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_name}' is not a valid dropdown field",
        )

    config = DROPDOWN_FIELD_CONFIG[field_name]
    category = config["category"]

    # Get options from repository
    repo = service.repo
    options = await repo.get_options_for_field(
        field_name,
        active_only=not include_inactive,
    )

    return {
        "field_name": field_name,
        "display_name": config["display_name"],
        "category": category.value if isinstance(category, DropdownFieldCategory) else category,
        "multi_select": config.get("multi_select", False),
        "allow_custom": config.get("allow_custom", True),
        "total_options": len(options),
        "options": [
            {
                "id": str(opt.id),
                "value": opt.value,
                "display_label": opt.display_label,
                "creator_type": opt.creator_type,
                "is_verified": opt.is_verified,
            }
            for opt in options
        ],
    }


# =============================================================================
# CRUD Endpoints
# =============================================================================

@router.post(
    "/fields/{field_name}",
    response_model=SingleCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add option to field",
    description="Add a new option to a dropdown field (admin operation).",
)
async def create_option(
    field_name: str,
    data: DropdownOptionCreate,
    service: DropdownServiceDep,
) -> dict[str, Any]:
    """Create a new dropdown option for a field."""
    if field_name not in DROPDOWN_FIELD_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_name}' is not a valid dropdown field",
        )

    result = await service.admin_add_value(
        field_name=field_name,
        value=data.value,
        display_label=data.display_label,
        description=data.description,
    )

    return result


@router.post(
    "/fields/{field_name}/bulk",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk add options",
    description="Add multiple options to a dropdown field at once.",
)
async def bulk_create_options(
    field_name: str,
    data: DropdownOptionBulkCreate,
    service: DropdownServiceDep,
) -> dict[str, Any]:
    """Bulk create dropdown options for a field."""
    if field_name not in DROPDOWN_FIELD_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_name}' is not a valid dropdown field",
        )

    result = await service.admin_bulk_add_values(
        field_name=field_name,
        values=data.values,
    )

    return result


@router.put(
    "/options/{option_id}",
    response_model=DropdownOptionResponse,
    summary="Update option",
    description="Update an existing dropdown option.",
)
async def update_option(
    option_id: str,
    data: DropdownOptionUpdate,
    service: DropdownServiceDep,
) -> DropdownOption:
    """Update a dropdown option."""
    repo = service.repo

    # Get existing option
    option = await repo.get_by_id(option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID '{option_id}' not found",
        )

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        option = await repo.update(option_id, **update_data)

    return option


@router.delete(
    "/options/{option_id}",
    response_model=DeactivateResponse,
    summary="Deactivate option",
    description="Soft-delete (deactivate) a dropdown option.",
)
async def deactivate_option(
    option_id: str,
    service: DropdownServiceDep,
) -> dict[str, Any]:
    """Deactivate a dropdown option (soft delete)."""
    result = await service.admin_deactivate_value(option_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID '{option_id}' not found",
        )

    return result


# =============================================================================
# Verification Endpoints
# =============================================================================

@router.post(
    "/options/{option_id}/verify",
    response_model=VerifyResponse,
    summary="Verify option",
    description="Mark a doctor-contributed option as verified.",
)
async def verify_option(
    option_id: str,
    service: DropdownServiceDep,
) -> dict[str, Any]:
    """Verify a dropdown option (approve doctor contribution)."""
    result = await service.admin_verify_value(option_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID '{option_id}' not found",
        )

    return result


@router.get(
    "/unverified",
    response_model=list[UnverifiedOptionResponse],
    summary="List unverified options",
    description="Get all doctor-contributed options pending verification.",
)
async def list_unverified_options(
    service: DropdownServiceDep,
) -> list[dict[str, Any]]:
    """List all unverified doctor contributions."""
    return await service.admin_get_unverified()


# =============================================================================
# Seeding & Statistics
# =============================================================================

@router.post(
    "/seed",
    response_model=SeedResponse,
    summary="Seed initial values",
    description="Seed the database with initial admin-defined dropdown values.",
)
async def seed_dropdown_values(
    service: DropdownServiceDep,
    force: bool = Query(False, description="Force re-seed even if data exists"),
) -> dict[str, Any]:
    """Seed initial dropdown values."""
    results = await service.seed_initial_values(force=force)

    total = sum(results.values())

    return {
        "success": True,
        "total_seeded": total,
        "fields_seeded": results,
        "message": f"Seeded {total} values across {len(results)} fields" if results else "Already seeded (use force=true to re-seed)",
    }


@router.get(
    "/stats",
    response_model=DropdownStatsResponse,
    summary="Get statistics",
    description="Get statistics about dropdown options in the system.",
)
async def get_dropdown_stats(
    service: DropdownServiceDep,
) -> dict[str, Any]:
    """Get dropdown options statistics."""
    return await service.get_stats()


# =============================================================================
# Public Data Endpoint
# =============================================================================

@router.get(
    "/data",
    response_model=DropdownDataResponse,
    summary="Get all dropdown data",
    description="Get all dropdown data for frontend forms (grouped by field).",
)
async def get_dropdown_data(
    service: DropdownServiceDep,
    include_metadata: bool = Query(False, description="Include field metadata"),
) -> dict[str, Any]:
    """Get all dropdown data for frontend consumption."""
    data = await service.get_dropdown_data(include_metadata=include_metadata)

    if include_metadata:
        # Data is already in the right format with metadata
        return {
            "data": {field: info.get("values", []) if isinstance(info, dict) else info for field, info in data.items()},
            "metadata": {field: {k: v for k, v in info.items() if k != "values"} for field, info in data.items() if isinstance(info, dict)},
        }

    return {
        "data": data,
        "metadata": None,
    }
