"""Dropdown Options Model.

Enhanced model for managing configurable dropdown values across the application.
Supports admin-seeded defaults and user-contributed values with full audit trail.
"""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import Base


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class DropdownFieldCategory(str, Enum):
    """Categories of dropdown fields for grouping."""
    
    PROFESSIONAL_IDENTITY = "professional_identity"  # Block 1
    CREDENTIALS = "credentials"  # Block 2
    CLINICAL_EXPERTISE = "clinical_expertise"  # Block 3
    PERSONAL = "personal"  # Block 4
    LOCATION = "location"
    GENERAL = "general"


class CreatorType(str, Enum):
    """Type of entity that created the dropdown value."""
    
    SYSTEM = "system"  # Initial seed data
    ADMIN = "admin"  # Admin-added values
    DOCTOR = "doctor"  # Doctor-contributed during onboarding


class DropdownOption(Base):
    """
    Enhanced dropdown_options table for configurable dropdown values.
    
    Features:
    - Supports multiple dropdown fields (specialty, cities, fellowships, etc.)
    - Tracks who created each value (system, admin, or doctor)
    - Maintains audit trail with timestamps
    - Supports soft-delete for admin-managed values
    - Allows categorization of fields for UI grouping
    
    Field Types Supported:
    - Block 1: specialty, primary_practice_location, centres_of_practice
    - Block 2: fellowships, qualifications, professional_memberships
    - Block 3: areas_of_clinical_interest, conditions (various)
    - Block 4: training_experience, motivation_in_practice, etc.
    - General: languages, age_groups_treated, etc.
    """

    __tablename__ = "dropdown_options_v2"

    # Primary Key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Field identification
    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="The model field this option belongs to (e.g., 'specialty', 'fellowships')",
    )
    
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DropdownFieldCategory.GENERAL.value,
        index=True,
        comment="Category for UI grouping",
    )

    # The actual dropdown value
    value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="The dropdown option value",
    )
    
    # Optional display label (if different from value)
    display_label: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional display label for UI (if different from value)",
    )
    
    # Optional description/help text
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description or help text for this option",
    )

    # Creator tracking
    creator_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CreatorType.SYSTEM.value,
        comment="Who created this: system, admin, or doctor",
    )
    
    created_by_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Doctor ID if created by a doctor during onboarding",
    )
    
    created_by_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Name of creator (doctor name or admin username)",
    )
    
    created_by_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email of creator for audit trail",
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this option is currently available for selection",
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this option has been verified/approved by admin",
    )
    
    # Display ordering
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Order for display in dropdowns (lower = first)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Table configuration
    __table_args__ = (
        # Unique constraint: same value can't exist twice for same field
        Index("ix_dropdown_field_value", "field_name", "value", unique=True),
        # Index for category lookups
        Index("ix_dropdown_category", "category"),
        # Index for active options
        Index("ix_dropdown_active", "field_name", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<DropdownOption(field={self.field_name}, value={self.value[:30]}...)>"


# =============================================================================
# Field Configuration - Maps model fields to dropdown categories
# =============================================================================

DROPDOWN_FIELD_CONFIG: dict[str, dict[str, Any]] = {
    # Block 1: Professional Identity
    "specialty": {
        "category": DropdownFieldCategory.PROFESSIONAL_IDENTITY,
        "display_name": "Specialty",
        "allow_custom": True,
        "multi_select": False,
    },
    "primary_practice_location": {
        "category": DropdownFieldCategory.LOCATION,
        "display_name": "Primary Practice Location (City)",
        "allow_custom": True,
        "multi_select": False,
    },
    "centres_of_practice": {
        "category": DropdownFieldCategory.LOCATION,
        "display_name": "Centres of Practice",
        "allow_custom": True,
        "multi_select": True,
    },
    
    # Block 2: Credentials & Trust Markers
    "fellowships": {
        "category": DropdownFieldCategory.CREDENTIALS,
        "display_name": "Fellowships",
        "allow_custom": True,
        "multi_select": True,
    },
    "qualifications": {
        "category": DropdownFieldCategory.CREDENTIALS,
        "display_name": "Qualifications/Degrees",
        "allow_custom": True,
        "multi_select": True,
    },
    "professional_memberships": {
        "category": DropdownFieldCategory.CREDENTIALS,
        "display_name": "Professional Memberships",
        "allow_custom": True,
        "multi_select": True,
    },
    "awards_academic_honours": {
        "category": DropdownFieldCategory.CREDENTIALS,
        "display_name": "Awards & Academic Honours",
        "allow_custom": True,
        "multi_select": True,
    },
    
    # Block 3: Clinical Focus & Expertise
    "areas_of_clinical_interest": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Areas of Clinical Interest",
        "allow_custom": True,
        "multi_select": True,
    },
    "practice_segments": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Practice Segments",
        "allow_custom": False,
        "multi_select": False,
        "predefined_only": True,  # Adult, Paediatric, Both
    },
    "conditions_commonly_treated": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Conditions Commonly Treated",
        "allow_custom": True,
        "multi_select": True,
    },
    "conditions_known_for": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Conditions Known For",
        "allow_custom": True,
        "multi_select": True,
    },
    "conditions_want_to_treat_more": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Conditions Want to Treat More",
        "allow_custom": True,
        "multi_select": True,
    },
    
    # Block 4: The Human Side
    "training_experience": {
        "category": DropdownFieldCategory.PERSONAL,
        "display_name": "Training Experience",
        "allow_custom": True,
        "multi_select": True,
    },
    "motivation_in_practice": {
        "category": DropdownFieldCategory.PERSONAL,
        "display_name": "Motivation in Practice",
        "allow_custom": True,
        "multi_select": True,
    },
    "unwinding_after_work": {
        "category": DropdownFieldCategory.PERSONAL,
        "display_name": "Unwinding After Work",
        "allow_custom": True,
        "multi_select": True,
    },
    "recognition_identity": {
        "category": DropdownFieldCategory.PERSONAL,
        "display_name": "Recognition Identity",
        "allow_custom": True,
        "multi_select": True,
    },
    "quality_time_interests": {
        "category": DropdownFieldCategory.PERSONAL,
        "display_name": "Quality Time Interests",
        "allow_custom": True,
        "multi_select": True,
    },
    
    # General fields
    "languages_spoken": {
        "category": DropdownFieldCategory.GENERAL,
        "display_name": "Languages Spoken",
        "allow_custom": True,
        "multi_select": True,
    },
    "age_groups_treated": {
        "category": DropdownFieldCategory.GENERAL,
        "display_name": "Age Groups Treated",
        "allow_custom": False,
        "multi_select": True,
        "predefined_only": True,
    },
    "sub_specialities": {
        "category": DropdownFieldCategory.PROFESSIONAL_IDENTITY,
        "display_name": "Sub-Specialities",
        "allow_custom": True,
        "multi_select": True,
    },
    "areas_of_expertise": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Areas of Expertise",
        "allow_custom": True,
        "multi_select": True,
    },
    "conditions_treated": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Conditions Treated",
        "allow_custom": True,
        "multi_select": True,
    },
    "procedures_performed": {
        "category": DropdownFieldCategory.CLINICAL_EXPERTISE,
        "display_name": "Procedures Performed",
        "allow_custom": True,
        "multi_select": True,
    },
}
