"""Dropdown Options Service.

Business logic for managing dropdown options including:
- Seeding initial admin values
- Auto-detection of new values during onboarding
- Admin management operations
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.dropdown_option import (
    DROPDOWN_FIELD_CONFIG,
    CreatorType,
    DropdownFieldCategory,
)
from ..repositories.dropdown_option_repository import DropdownOptionRepository

logger = logging.getLogger(__name__)


# =============================================================================
# Initial Seed Data - Admin-defined defaults
# =============================================================================

INITIAL_DROPDOWN_VALUES: dict[str, list[str]] = {
    # Block 1: Specialties
    "specialty": [
        "Cardiology",
        "Dermatology",
        "Endocrinology",
        "Gastroenterology",
        "General Medicine",
        "General Surgery",
        "Gynaecology",
        "Nephrology",
        "Neurology",
        "Oncology",
        "Ophthalmology",
        "Orthopaedics",
        "Paediatrics",
        "Psychiatry",
        "Pulmonology",
        "Radiology",
        "Rheumatology",
        "Urology",
    ],

    # Block 1: Cities/Locations
    "primary_practice_location": [
        "Mumbai",
        "Delhi",
        "Bangalore",
        "Chennai",
        "Hyderabad",
        "Kolkata",
        "Pune",
        "Ahmedabad",
        "Jaipur",
        "Lucknow",
        "Chandigarh",
        "Kochi",
        "Coimbatore",
        "Indore",
        "Nagpur",
    ],

    # Block 2: Fellowships
    "fellowships": [
        "FRCS (UK)",
        "MRCP (UK)",
        "FACC (USA)",
        "FACS (USA)",
        "FRCOG (UK)",
        "DNB",
        "DM",
        "MCh",
        "Fellowship in Interventional Cardiology",
        "Fellowship in Gastroenterology",
        "Fellowship in Nephrology",
    ],

    # Block 2: Qualifications
    "qualifications": [
        "MBBS",
        "MD",
        "MS",
        "DNB",
        "DM",
        "MCh",
        "FRCS",
        "MRCP",
        "DCH",
        "DA",
        "DMRD",
        "PhD",
    ],

    # Block 2: Professional Memberships
    "professional_memberships": [
        "Indian Medical Association (IMA)",
        "Association of Physicians of India (API)",
        "Cardiological Society of India (CSI)",
        "Indian Academy of Pediatrics (IAP)",
        "Indian Orthopaedic Association (IOA)",
        "Association of Surgeons of India (ASI)",
        "Indian Psychiatric Society (IPS)",
        "Indian Radiological and Imaging Association (IRIA)",
        "Federation of Obstetric and Gynaecological Societies of India (FOGSI)",
    ],

    # Block 3: Practice Segments
    "practice_segments": [
        "Adult",
        "Paediatric",
        "Both Adult and Paediatric",
    ],

    # Block 4: Training Experience
    "training_experience": [
        "Government Medical College",
        "Private Medical College",
        "AIIMS",
        "PGIMER Chandigarh",
        "CMC Vellore",
        "JIPMER",
        "International Training",
        "Fellowship Abroad",
    ],

    # Block 4: Motivation in Practice
    "motivation_in_practice": [
        "Patient outcomes",
        "Medical research",
        "Teaching and mentoring",
        "Community service",
        "Clinical excellence",
        "Innovation in treatment",
        "Preventive healthcare",
    ],

    # Block 4: Unwinding After Work
    "unwinding_after_work": [
        "Reading",
        "Music",
        "Sports",
        "Travel",
        "Family time",
        "Gardening",
        "Meditation/Yoga",
        "Cooking",
        "Art/Painting",
        "Photography",
    ],

    # Block 4: Quality Time Interests
    "quality_time_interests": [
        "Family",
        "Friends",
        "Solo activities",
        "Community involvement",
        "Professional networking",
        "Hobbies",
        "Fitness",
        "Spiritual activities",
    ],

    # General: Languages
    "languages_spoken": [
        "English",
        "Hindi",
        "Tamil",
        "Telugu",
        "Kannada",
        "Malayalam",
        "Marathi",
        "Bengali",
        "Gujarati",
        "Punjabi",
        "Urdu",
        "Odia",
    ],

    # General: Age Groups
    "age_groups_treated": [
        "Neonates (0-28 days)",
        "Infants (1-12 months)",
        "Children (1-12 years)",
        "Adolescents (13-18 years)",
        "Adults (19-64 years)",
        "Elderly (65+ years)",
    ],
}


class DropdownOptionService:
    """
    Service for managing dropdown options.
    
    Provides business logic for:
    - Seeding initial values
    - Auto-detecting new values during onboarding
    - Admin management of options
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DropdownOptionRepository(session)

    # =========================================================================
    # Seeding Operations
    # =========================================================================

    async def seed_initial_values(self, force: bool = False) -> dict[str, int]:
        """
        Seed initial dropdown values from admin-defined defaults.
        
        Args:
            force: If True, re-seed all values even if table has data
            
        Returns:
            Dict mapping field_name to number of values created
        """
        # Check if already seeded (unless force)
        if not force:
            stats = await self.repo.get_stats()
            if stats["total_options"] > 0:
                logger.info(
                    f"Dropdown options already seeded ({stats['total_options']} options). "
                    "Use force=True to re-seed."
                )
                return {}

        results: dict[str, int] = {}

        for field_name, values in INITIAL_DROPDOWN_VALUES.items():
            count = await self.repo.bulk_create(
                field_name=field_name,
                values=values,
                creator_type=CreatorType.SYSTEM,
                created_by_name="admin",
                skip_existing=True,
            )
            results[field_name] = count

        total = sum(results.values())
        logger.info(f"Seeded {total} initial dropdown values across {len(results)} fields")

        return results

    # =========================================================================
    # Auto-Detection During Onboarding
    # =========================================================================

    async def process_form_submission(
        self,
        form_data: dict[str, Any],
        *,
        doctor_id: int | None = None,
        doctor_name: str | None = None,
        doctor_email: str | None = None,
    ) -> dict[str, list[str]]:
        """
        Process a form submission and auto-detect new dropdown values.
        
        Called when a doctor saves a form section. Checks all dropdown fields
        in the form data and saves any new values to the database.
        
        Args:
            form_data: Dict of field_name -> value(s) from the form
            doctor_id: ID of the doctor submitting
            doctor_name: Name of the doctor
            doctor_email: Email of the doctor
            
        Returns:
            Dict mapping field_name to list of newly created values
        """
        new_values_by_field: dict[str, list[str]] = {}

        for field_name, value in form_data.items():
            # Skip non-dropdown fields
            if field_name not in DROPDOWN_FIELD_CONFIG:
                continue

            # Skip if field doesn't allow custom values
            config = DROPDOWN_FIELD_CONFIG[field_name]
            if config.get("predefined_only", False):
                continue

            # Normalize to list
            values = value if isinstance(value, list) else [value]
            values = [v for v in values if v and isinstance(v, str)]

            if not values:
                continue

            # Detect and save new values
            new_values = await self.repo.detect_and_save_new_values(
                field_name=field_name,
                values=values,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                doctor_email=doctor_email,
            )

            if new_values:
                new_values_by_field[field_name] = new_values

        if new_values_by_field:
            total_new = sum(len(v) for v in new_values_by_field.values())
            logger.info(
                f"Auto-saved {total_new} new dropdown values from doctor {doctor_id}"
            )

        return new_values_by_field

    # =========================================================================
    # Public API Methods
    # =========================================================================

    async def get_dropdown_data(
        self,
        *,
        include_metadata: bool = False,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """Get all dropdown data for frontend forms."""
        return await self.repo.get_all_dropdown_data(
            active_only=active_only,
            include_metadata=include_metadata,
        )

    async def get_options_for_field(
        self,
        field_name: str,
        *,
        active_only: bool = True,
    ) -> list[str]:
        """Get dropdown options for a specific field."""
        return await self.repo.get_values_for_field(
            field_name,
            active_only=active_only,
        )

    async def get_field_config(self) -> dict[str, Any]:
        """Get field configuration metadata for frontend."""
        config: dict[str, Any] = {}

        for field_name, field_config in DROPDOWN_FIELD_CONFIG.items():
            category = field_config["category"]
            config[field_name] = {
                "display_name": field_config["display_name"],
                "category": category.value if isinstance(category, DropdownFieldCategory) else category,
                "multi_select": field_config.get("multi_select", False),
                "allow_custom": field_config.get("allow_custom", True),
            }

        return config

    # =========================================================================
    # Admin Operations
    # =========================================================================

    async def admin_add_value(
        self,
        field_name: str,
        value: str,
        *,
        admin_name: str = "admin",
        admin_email: str | None = None,
        display_label: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Admin endpoint to add a new dropdown value.
        
        Values added by admin are automatically verified.
        """
        option, was_created = await self.repo.create_if_not_exists(
            field_name=field_name,
            value=value,
            creator_type=CreatorType.ADMIN,
            created_by_name=admin_name,
            created_by_email=admin_email,
        )

        if option and display_label:
            await self.repo.update(option.id, display_label=display_label)

        if option and description:
            await self.repo.update(option.id, description=description)

        return {
            "success": was_created,
            "message": "Value created" if was_created else "Value already exists",
            "value": value,
            "field_name": field_name,
        }

    async def admin_bulk_add_values(
        self,
        field_name: str,
        values: list[str],
        *,
        admin_name: str = "admin",
    ) -> dict[str, Any]:
        """Admin endpoint to bulk add dropdown values."""
        count = await self.repo.bulk_create(
            field_name=field_name,
            values=values,
            creator_type=CreatorType.ADMIN,
            created_by_name=admin_name,
            skip_existing=True,
        )

        return {
            "success": True,
            "created_count": count,
            "field_name": field_name,
            "total_submitted": len(values),
        }

    async def admin_verify_value(self, option_id: str) -> dict[str, Any]:
        """Mark a doctor-contributed value as verified."""
        option = await self.repo.verify(option_id)

        return {
            "success": option is not None,
            "option_id": option_id,
            "is_verified": option.is_verified if option else None,
        }

    async def admin_deactivate_value(self, option_id: str) -> dict[str, Any]:
        """Soft-delete a dropdown value."""
        option = await self.repo.deactivate(option_id)

        return {
            "success": option is not None,
            "option_id": option_id,
            "is_active": option.is_active if option else None,
        }

    async def admin_get_unverified(self) -> list[dict[str, Any]]:
        """Get all unverified (doctor-contributed) values for review."""
        options = await self.repo.get_unverified()

        return [
            {
                "id": str(opt.id),
                "field_name": opt.field_name,
                "value": opt.value,
                "created_by_name": opt.created_by_name,
                "created_by_email": opt.created_by_email,
                "created_at": opt.created_at,
            }
            for opt in options
        ]

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about dropdown options."""
        return await self.repo.get_stats()


# =============================================================================
# Service Factory
# =============================================================================

def get_dropdown_option_service(session: AsyncSession) -> DropdownOptionService:
    """Factory function to create DropdownOptionService."""
    return DropdownOptionService(session)
