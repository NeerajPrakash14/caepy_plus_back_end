"""Schemas for Dropdown Option Management.

Pydantic models for:
- Admin API requests/responses
- Dropdown data retrieval
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Enums (mirror model enums for serialization)
# =============================================================================

class CreatorTypeEnum(str, Enum):
    """Type of entity that created the dropdown option."""
    SYSTEM = "system"
    ADMIN = "admin"
    DOCTOR = "doctor"


class DropdownCategoryEnum(str, Enum):
    """Categories for dropdown fields."""
    SPECIALTY = "specialty"
    LOCATION = "location"
    QUALIFICATION = "qualification"
    MEDICAL = "medical"
    LANGUAGE = "language"
    INTEREST = "interest"
    LIFESTYLE = "lifestyle"
    OTHER = "other"


# =============================================================================
# Base Schemas
# =============================================================================

class DropdownOptionBase(BaseModel):
    """Base schema for dropdown options."""
    value: str = Field(..., min_length=1, max_length=500)
    display_label: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=2000)


class DropdownOptionCreate(DropdownOptionBase):
    """Schema for creating a new dropdown option (admin)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "Interventional Cardiology",
                "display_label": "Interventional Cardiology",
                "description": "Subspecialty of cardiology focusing on catheter-based treatments"
            }
        }
    )


class DropdownOptionBulkCreate(BaseModel):
    """Schema for bulk creating dropdown options."""
    values: list[str] = Field(..., min_length=1, max_length=100)

    @field_validator("values")
    @classmethod
    def validate_values(cls, v: list[str]) -> list[str]:
        # Remove duplicates and empty strings
        cleaned = list(dict.fromkeys(val.strip() for val in v if val.strip()))
        if not cleaned:
            raise ValueError("At least one non-empty value is required")
        return cleaned

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "values": [
                    "Pediatric Cardiology",
                    "Electrophysiology",
                    "Heart Failure Specialist"
                ]
            }
        }
    )


class DropdownOptionUpdate(BaseModel):
    """Schema for updating a dropdown option."""
    display_label: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=2000)
    is_active: bool | None = None
    is_verified: bool | None = None


# =============================================================================
# Response Schemas
# =============================================================================

class DropdownOptionResponse(BaseModel):
    """Full response schema for a dropdown option."""
    id: str
    field_name: str
    category: str
    value: str
    display_label: str | None = None
    description: str | None = None
    creator_type: str
    created_by_id: int | None = None
    created_by_name: str | None = None
    created_by_email: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DropdownOptionSummary(BaseModel):
    """Summary response for a dropdown option (for lists)."""
    id: str
    value: str
    display_label: str | None = None
    creator_type: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class DropdownFieldResponse(BaseModel):
    """Response for a single dropdown field with its options."""
    field_name: str
    display_name: str
    category: str
    multi_select: bool
    allow_custom: bool
    total_options: int
    options: list[DropdownOptionSummary] = []


class DropdownFieldConfigResponse(BaseModel):
    """Response for field configuration metadata."""
    field_name: str
    display_name: str
    category: str
    multi_select: bool
    allow_custom: bool


# =============================================================================
# Bulk Response Schemas
# =============================================================================

class BulkCreateResponse(BaseModel):
    """Response for bulk create operation."""
    success: bool
    field_name: str
    total_submitted: int
    created_count: int
    message: str = "Bulk create completed"


class SingleCreateResponse(BaseModel):
    """Response for single create operation."""
    success: bool
    field_name: str
    value: str
    message: str
    option: DropdownOptionResponse | None = None


class VerifyResponse(BaseModel):
    """Response for verify operation."""
    success: bool
    option_id: str
    is_verified: bool | None


class DeactivateResponse(BaseModel):
    """Response for deactivate operation."""
    success: bool
    option_id: str
    is_active: bool | None


# =============================================================================
# Statistics & Admin Schemas
# =============================================================================

class DropdownStatsResponse(BaseModel):
    """Statistics about dropdown options."""
    total_options: int
    active_options: int
    verified_options: int
    options_by_field: dict[str, int]
    options_by_category: dict[str, int]
    options_by_creator_type: dict[str, int]
    unverified_doctor_contributions: int


class SeedResponse(BaseModel):
    """Response for seeding operation."""
    success: bool
    total_seeded: int
    fields_seeded: dict[str, int]
    message: str


class UnverifiedOptionResponse(BaseModel):
    """Response for unverified options pending review."""
    id: str
    field_name: str
    value: str
    created_by_name: str | None
    created_by_email: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Frontend-Facing Schemas
# =============================================================================

class DropdownDataResponse(BaseModel):
    """
    Complete dropdown data for frontend forms.
    
    Returns all dropdown values grouped by field name,
    suitable for populating select/multi-select components.
    """
    data: dict[str, list[str]]
    metadata: dict[str, dict[str, Any]] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "specialty": ["Cardiology", "Dermatology", "Neurology"],
                    "primary_practice_location": ["Mumbai", "Delhi", "Bangalore"],
                    "languages_spoken": ["English", "Hindi", "Tamil"]
                },
                "metadata": {
                    "specialty": {
                        "display_name": "Specialty",
                        "category": "specialty",
                        "multi_select": True
                    }
                }
            }
        }
    )
