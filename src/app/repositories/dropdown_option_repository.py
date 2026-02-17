"""Dropdown Options Repository.

Data access layer for dropdown options with support for:
- CRUD operations
- Bulk seeding
- Auto-detection of new values
- Admin management
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models.dropdown_option import (
    DropdownOption,
    CreatorType,
    DropdownFieldCategory,
    DROPDOWN_FIELD_CONFIG,
)

logger = logging.getLogger(__name__)


class DropdownOptionRepository:
    """Repository for dropdown option database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # READ Operations
    # =========================================================================

    async def get_by_id(self, option_id: str) -> DropdownOption | None:
        """Get a dropdown option by ID."""
        stmt = select(DropdownOption).where(DropdownOption.id == option_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_options_for_field(
        self,
        field_name: str,
        *,
        active_only: bool = True,
        verified_only: bool = False,
    ) -> Sequence[DropdownOption]:
        """
        Get all dropdown options for a specific field.
        
        Args:
            field_name: The field to get options for
            active_only: Only return active options
            verified_only: Only return verified options
            
        Returns:
            List of dropdown options ordered by display_order, then value
        """
        stmt = select(DropdownOption).where(DropdownOption.field_name == field_name)
        
        if active_only:
            stmt = stmt.where(DropdownOption.is_active.is_(True))
        
        if verified_only:
            stmt = stmt.where(DropdownOption.is_verified.is_(True))
        
        stmt = stmt.order_by(
            DropdownOption.display_order.asc(),
            DropdownOption.value.asc(),
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_values_for_field(
        self,
        field_name: str,
        *,
        active_only: bool = True,
    ) -> list[str]:
        """Get just the values (strings) for a field."""
        options = await self.get_options_for_field(field_name, active_only=active_only)
        return [opt.value for opt in options]

    async def get_options_by_category(
        self,
        category: DropdownFieldCategory | str,
        *,
        active_only: bool = True,
    ) -> dict[str, list[str]]:
        """
        Get all dropdown options grouped by field for a category.
        
        Returns:
            Dict mapping field_name to list of values
        """
        cat_value = category.value if isinstance(category, DropdownFieldCategory) else category
        
        stmt = select(DropdownOption).where(DropdownOption.category == cat_value)
        
        if active_only:
            stmt = stmt.where(DropdownOption.is_active.is_(True))
        
        stmt = stmt.order_by(
            DropdownOption.field_name,
            DropdownOption.display_order.asc(),
            DropdownOption.value.asc(),
        )
        
        result = await self.session.execute(stmt)
        options = result.scalars().all()
        
        # Group by field_name
        grouped: dict[str, list[str]] = {}
        for opt in options:
            if opt.field_name not in grouped:
                grouped[opt.field_name] = []
            grouped[opt.field_name].append(opt.value)
        
        return grouped

    async def get_all_dropdown_data(
        self,
        *,
        active_only: bool = True,
        include_metadata: bool = False,
    ) -> dict[str, Any]:
        """
        Get all dropdown data for all fields.
        
        Returns:
            Dict with field configurations and values
        """
        stmt = select(DropdownOption)
        
        if active_only:
            stmt = stmt.where(DropdownOption.is_active.is_(True))
        
        stmt = stmt.order_by(
            DropdownOption.field_name,
            DropdownOption.display_order.asc(),
            DropdownOption.value.asc(),
        )
        
        result = await self.session.execute(stmt)
        options = result.scalars().all()
        
        # Build response
        data: dict[str, Any] = {}
        
        for field_name, config in DROPDOWN_FIELD_CONFIG.items():
            field_options = [opt for opt in options if opt.field_name == field_name]
            
            if include_metadata:
                data[field_name] = {
                    "display_name": config["display_name"],
                    "category": config["category"].value if isinstance(config["category"], DropdownFieldCategory) else config["category"],
                    "multi_select": config.get("multi_select", False),
                    "allow_custom": config.get("allow_custom", True),
                    "values": [opt.value for opt in field_options],
                    "count": len(field_options),
                }
            else:
                data[field_name] = [opt.value for opt in field_options]
        
        return data

    async def value_exists(self, field_name: str, value: str) -> bool:
        """Check if a value already exists for a field."""
        stmt = select(func.count(DropdownOption.id)).where(
            and_(
                DropdownOption.field_name == field_name,
                DropdownOption.value == value,
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    async def create(
        self,
        field_name: str,
        value: str,
        *,
        creator_type: CreatorType = CreatorType.SYSTEM,
        created_by_id: int | None = None,
        created_by_name: str | None = None,
        created_by_email: str | None = None,
        display_label: str | None = None,
        description: str | None = None,
        is_verified: bool = False,
        display_order: int = 0,
    ) -> DropdownOption:
        """
        Create a new dropdown option.
        
        Args:
            field_name: The field this option belongs to
            value: The option value
            creator_type: Who is creating this (system, admin, doctor)
            created_by_id: Doctor ID if created by doctor
            created_by_name: Name of creator
            created_by_email: Email of creator
            display_label: Optional display label
            description: Optional description
            is_verified: Whether pre-verified (True for admin/system)
            display_order: Display order in dropdown
            
        Returns:
            Created DropdownOption
        """
        # Get category from config
        config = DROPDOWN_FIELD_CONFIG.get(field_name, {})
        category = config.get("category", DropdownFieldCategory.GENERAL)
        if isinstance(category, DropdownFieldCategory):
            category = category.value
        
        option = DropdownOption(
            field_name=field_name,
            category=category,
            value=value,
            display_label=display_label,
            description=description,
            creator_type=creator_type.value if isinstance(creator_type, CreatorType) else creator_type,
            created_by_id=created_by_id,
            created_by_name=created_by_name,
            created_by_email=created_by_email,
            is_verified=is_verified,
            display_order=display_order,
        )
        
        self.session.add(option)
        await self.session.commit()
        await self.session.refresh(option)
        
        logger.info(
            f"Created dropdown option: field={field_name}, value={value[:50]}, "
            f"creator={creator_type}"
        )
        
        return option

    async def create_if_not_exists(
        self,
        field_name: str,
        value: str,
        *,
        creator_type: CreatorType = CreatorType.DOCTOR,
        created_by_id: int | None = None,
        created_by_name: str | None = None,
        created_by_email: str | None = None,
    ) -> tuple[DropdownOption | None, bool]:
        """
        Create a dropdown option only if it doesn't already exist.
        
        Returns:
            Tuple of (option, was_created)
            - If exists: (None, False)
            - If created: (new_option, True)
        """
        # Check if exists
        if await self.value_exists(field_name, value):
            return None, False
        
        # Create new
        option = await self.create(
            field_name=field_name,
            value=value,
            creator_type=creator_type,
            created_by_id=created_by_id,
            created_by_name=created_by_name,
            created_by_email=created_by_email,
            is_verified=creator_type in (CreatorType.SYSTEM, CreatorType.ADMIN),
        )
        
        return option, True

    async def bulk_create(
        self,
        field_name: str,
        values: list[str],
        *,
        creator_type: CreatorType = CreatorType.SYSTEM,
        created_by_name: str = "system",
        skip_existing: bool = True,
    ) -> int:
        """
        Bulk create dropdown options for a field.
        
        Args:
            field_name: Field name
            values: List of values to create
            creator_type: Creator type
            created_by_name: Creator name
            skip_existing: If True, skip values that already exist
            
        Returns:
            Number of options created
        """
        created_count = 0
        
        for idx, value in enumerate(values):
            if not value or not value.strip():
                continue
            
            value = value.strip()
            
            if skip_existing and await self.value_exists(field_name, value):
                continue
            
            await self.create(
                field_name=field_name,
                value=value,
                creator_type=creator_type,
                created_by_name=created_by_name,
                is_verified=True,
                display_order=idx,
            )
            created_count += 1
        
        logger.info(f"Bulk created {created_count} options for field={field_name}")
        return created_count

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    async def update(
        self,
        option_id: str,
        **kwargs: Any,
    ) -> DropdownOption | None:
        """Update a dropdown option."""
        option = await self.get_by_id(option_id)
        if not option:
            return None
        
        allowed_fields = {
            "value", "display_label", "description", "is_active",
            "is_verified", "display_order", "category",
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(option, key, value)
        
        await self.session.commit()
        await self.session.refresh(option)
        return option

    async def verify(self, option_id: str) -> DropdownOption | None:
        """Mark an option as verified."""
        return await self.update(option_id, is_verified=True)

    async def deactivate(self, option_id: str) -> DropdownOption | None:
        """Soft-delete an option by deactivating it."""
        return await self.update(option_id, is_active=False)

    async def activate(self, option_id: str) -> DropdownOption | None:
        """Re-activate a deactivated option."""
        return await self.update(option_id, is_active=True)

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    async def delete(self, option_id: str) -> bool:
        """Hard delete a dropdown option."""
        option = await self.get_by_id(option_id)
        if not option:
            return False
        
        await self.session.delete(option)
        await self.session.commit()
        
        logger.info(f"Deleted dropdown option: {option_id}")
        return True

    # =========================================================================
    # Auto-Detection Operations
    # =========================================================================

    async def detect_and_save_new_values(
        self,
        field_name: str,
        values: list[str],
        *,
        doctor_id: int | None = None,
        doctor_name: str | None = None,
        doctor_email: str | None = None,
    ) -> list[str]:
        """
        Detect new values in a list and automatically save them.
        
        This is called when a doctor submits a form section with dropdown values.
        Any values not already in the database are added with the doctor as creator.
        
        Args:
            field_name: The field being saved
            values: List of values from the form
            doctor_id: ID of the doctor submitting
            doctor_name: Name of the doctor
            doctor_email: Email of the doctor
            
        Returns:
            List of newly created values
        """
        # Check if field allows custom values
        config = DROPDOWN_FIELD_CONFIG.get(field_name, {})
        if config.get("predefined_only", False):
            logger.debug(f"Field {field_name} does not allow custom values")
            return []
        
        new_values = []
        
        for value in values:
            if not value or not value.strip():
                continue
            
            value = value.strip()
            
            option, was_created = await self.create_if_not_exists(
                field_name=field_name,
                value=value,
                creator_type=CreatorType.DOCTOR,
                created_by_id=doctor_id,
                created_by_name=doctor_name,
                created_by_email=doctor_email,
            )
            
            if was_created:
                new_values.append(value)
                logger.info(
                    f"Auto-saved new dropdown value: field={field_name}, "
                    f"value={value[:50]}, doctor_id={doctor_id}"
                )
        
        return new_values

    async def get_unverified(self) -> Sequence[DropdownOption]:
        """Get all unverified options (doctor contributions pending review)."""
        stmt = select(DropdownOption).where(
            and_(
                DropdownOption.is_verified.is_(False),
                DropdownOption.is_active.is_(True),
            )
        ).order_by(
            DropdownOption.created_at.desc(),
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about dropdown options."""
        # Get counts by field and creator type
        stmt = select(
            DropdownOption.field_name,
            DropdownOption.category,
            DropdownOption.creator_type,
            DropdownOption.is_active,
            DropdownOption.is_verified,
            func.count(DropdownOption.id).label("count"),
        ).group_by(
            DropdownOption.field_name,
            DropdownOption.category,
            DropdownOption.creator_type,
            DropdownOption.is_active,
            DropdownOption.is_verified,
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        # Initialize stats
        stats: dict[str, Any] = {
            "total_options": 0,
            "active_options": 0,
            "verified_options": 0,
            "options_by_field": {},
            "options_by_category": {},
            "options_by_creator_type": {
                CreatorType.SYSTEM.value: 0,
                CreatorType.ADMIN.value: 0,
                CreatorType.DOCTOR.value: 0,
            },
            "unverified_doctor_contributions": 0,
        }
        
        for field_name, category, creator_type, is_active, is_verified, count in rows:
            stats["total_options"] += count
            
            if is_active:
                stats["active_options"] += count
            
            if is_verified:
                stats["verified_options"] += count
            
            # Count by field
            stats["options_by_field"][field_name] = stats["options_by_field"].get(field_name, 0) + count
            
            # Count by category
            stats["options_by_category"][category] = stats["options_by_category"].get(category, 0) + count
            
            # Count by creator type
            stats["options_by_creator_type"][creator_type] = stats["options_by_creator_type"].get(creator_type, 0) + count
            
            # Count unverified doctor contributions
            if creator_type == CreatorType.DOCTOR.value and not is_verified and is_active:
                stats["unverified_doctor_contributions"] += count
        
        return stats
