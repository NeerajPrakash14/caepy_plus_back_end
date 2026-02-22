"""
Hospital Pydantic Schemas.

Schemas for hospital CRUD operations, search, and doctor affiliations.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class HospitalVerificationStatus(str, Enum):
    """Hospital verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


# ============================================
# Hospital Schemas
# ============================================

class HospitalBase(BaseModel):
    """Base schema for hospital data."""

    name: str = Field(..., min_length=1, max_length=255, description="Hospital or clinic name")
    address: str | None = Field(default=None, description="Full street address")
    city: str | None = Field(default=None, max_length=100, description="City name")
    state: str | None = Field(default=None, max_length=100, description="State or province")
    pincode: str | None = Field(default=None, max_length=20, description="Postal/ZIP code")
    phone_number: str | None = Field(default=None, max_length=20, description="Hospital contact number")
    email: str | None = Field(default=None, max_length=255, description="Hospital email")
    website: str | None = Field(default=None, max_length=500, description="Hospital website URL")


class HospitalCreate(HospitalBase):
    """Schema for creating a hospital (by doctor or admin)."""
    pass


class HospitalCreateByDoctor(HospitalBase):
    """Schema for doctor adding a new hospital during onboarding."""
    # Doctor ID will be set from the authenticated context or request
    pass


class HospitalUpdate(BaseModel):
    """Schema for updating a hospital (admin only)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    phone_number: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class HospitalVerify(BaseModel):
    """Schema for admin verification action."""

    action: str = Field(..., pattern="^(verify|reject)$", description="Action: 'verify' or 'reject'")
    rejection_reason: str | None = Field(default=None, description="Required if action is 'reject'")
    verified_by: str | None = Field(default=None, description="Admin identifier")


class HospitalResponse(HospitalBase):
    """Schema for hospital response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_status: HospitalVerificationStatus
    verified_at: datetime | None = None
    verified_by: str | None = None
    rejection_reason: str | None = None
    created_by_doctor_id: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HospitalListResponse(BaseModel):
    """Schema for hospital list response."""

    id: int
    name: str
    city: str | None = None
    state: str | None = None
    verification_status: HospitalVerificationStatus
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class HospitalSearchResult(BaseModel):
    """Schema for hospital search autocomplete result."""

    id: int
    name: str
    city: str | None = None
    state: str | None = None
    display_name: str = Field(..., description="Formatted name for display: 'Hospital Name, City'")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Doctor-Hospital Affiliation Schemas
# ============================================

class AffiliationBase(BaseModel):
    """Base schema for doctor-hospital affiliation."""

    hospital_id: int = Field(..., description="Hospital ID to affiliate with")
    consultation_fee: float | None = Field(default=None, ge=0, description="Consultation fee at this hospital")
    consultation_type: str | None = Field(default=None, max_length=100, description="Type: In-person, Online, Both")
    weekly_schedule: str | None = Field(default=None, description="Schedule at this hospital")
    designation: str | None = Field(default=None, max_length=200, description="Designation at this hospital")
    department: str | None = Field(default=None, max_length=200, description="Department at this hospital")
    is_primary: bool = Field(default=False, description="Is this the primary practice location?")


class AffiliationCreate(AffiliationBase):
    """Schema for creating an affiliation."""
    pass


class AffiliationCreateWithNewHospital(BaseModel):
    """Schema for creating affiliation with a new hospital (not in system)."""

    # New hospital details
    hospital_name: str = Field(..., min_length=1, max_length=255, description="Hospital name")
    hospital_address: str | None = Field(default=None, description="Hospital address")
    hospital_city: str | None = Field(default=None, max_length=100, description="City")
    hospital_state: str | None = Field(default=None, max_length=100, description="State")
    hospital_pincode: str | None = Field(default=None, max_length=20, description="Pincode")
    hospital_phone: str | None = Field(default=None, max_length=20, description="Hospital phone")

    # Affiliation details
    consultation_fee: float | None = Field(default=None, ge=0)
    consultation_type: str | None = Field(default=None, max_length=100)
    weekly_schedule: str | None = None
    designation: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    is_primary: bool = Field(default=False)


class AffiliationUpdate(BaseModel):
    """Schema for updating an affiliation."""

    consultation_fee: float | None = None
    consultation_type: str | None = None
    weekly_schedule: str | None = None
    designation: str | None = None
    department: str | None = None
    is_primary: bool | None = None
    is_active: bool | None = None


class AffiliationResponse(BaseModel):
    """Schema for affiliation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: int
    hospital_id: int
    consultation_fee: float | None = None
    consultation_type: str | None = None
    weekly_schedule: str | None = None
    designation: str | None = None
    department: str | None = None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Nested hospital info
    hospital: HospitalListResponse | None = None


class AffiliationWithHospitalResponse(AffiliationResponse):
    """Affiliation response with full hospital details."""

    hospital: HospitalResponse


# ============================================
# Combined/Hybrid Schemas
# ============================================

class PracticeLocationInput(BaseModel):
    """
    Hybrid input for practice location - supports both existing and new hospitals.
    
    Frontend can provide either:
    1. hospital_id (existing hospital from dropdown)
    2. new_hospital (details for a new hospital to be created)
    """

    # Option 1: Use existing hospital
    hospital_id: int | None = Field(default=None, description="ID of existing hospital (from search/dropdown)")

    # Option 2: Add new hospital
    new_hospital: HospitalCreateByDoctor | None = Field(default=None, description="Details for new hospital")

    # Doctor-specific info at this location
    consultation_fee: float | None = Field(default=None, ge=0)
    consultation_type: str | None = Field(default=None, max_length=100)
    weekly_schedule: str | None = None
    designation: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    is_primary: bool = Field(default=False)


class DoctorPracticeLocationsResponse(BaseModel):
    """Response for doctor's practice locations with hospital details."""

    doctor_id: int
    affiliations: list[AffiliationWithHospitalResponse]
    total_count: int


# ============================================
# Admin Schemas
# ============================================

class HospitalMerge(BaseModel):
    """Schema for merging duplicate hospitals (admin)."""

    source_hospital_ids: list[int] = Field(..., min_length=1, description="Hospital IDs to merge FROM")
    target_hospital_id: int = Field(..., description="Hospital ID to merge INTO")


class HospitalStats(BaseModel):
    """Statistics about hospitals."""

    total_hospitals: int
    verified_count: int
    pending_count: int
    rejected_count: int
    active_count: int
    inactive_count: int
