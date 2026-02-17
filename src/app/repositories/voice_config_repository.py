"""Voice Onboarding Configuration Repository.

Data access layer for voice onboarding blocks and fields configuration.
"""
from __future__ import annotations

from typing import Sequence, Any
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.voice_config import VoiceOnboardingBlock, VoiceOnboardingField


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class VoiceConfigRepository:
    """Repository for voice onboarding configuration."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Block Operations
    # =========================================================================

    async def list_blocks(
        self,
        *,
        active_only: bool = True,
    ) -> Sequence[VoiceOnboardingBlock]:
        """Return all blocks with their fields, ordered by display_order."""
        stmt = (
            select(VoiceOnboardingBlock)
            .options(selectinload(VoiceOnboardingBlock.fields))
            .order_by(VoiceOnboardingBlock.display_order)
        )
        
        if active_only:
            stmt = stmt.where(VoiceOnboardingBlock.is_active == True)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_block_by_number(self, block_number: int) -> VoiceOnboardingBlock | None:
        """Get a block by its number."""
        stmt = (
            select(VoiceOnboardingBlock)
            .options(selectinload(VoiceOnboardingBlock.fields))
            .where(VoiceOnboardingBlock.block_number == block_number)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_block_by_id(self, block_id: int) -> VoiceOnboardingBlock | None:
        """Get a block by ID."""
        stmt = (
            select(VoiceOnboardingBlock)
            .options(selectinload(VoiceOnboardingBlock.fields))
            .where(VoiceOnboardingBlock.id == block_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_block(
        self,
        *,
        block_number: int,
        block_name: str,
        display_name: str,
        ai_prompt: str | None = None,
        ai_disclaimer: str | None = None,
        completion_percentage: int = 0,
        completion_message: str | None = None,
        is_active: bool = True,
        display_order: int = 0,
    ) -> VoiceOnboardingBlock:
        """Create a new block."""
        block = VoiceOnboardingBlock(
            block_number=block_number,
            block_name=block_name,
            display_name=display_name,
            ai_prompt=ai_prompt,
            ai_disclaimer=ai_disclaimer,
            completion_percentage=completion_percentage,
            completion_message=completion_message,
            is_active=is_active,
            display_order=display_order,
        )
        self.session.add(block)
        await self.session.commit()
        await self.session.refresh(block)
        return block

    async def update_block(
        self,
        block_id: int,
        **kwargs: Any,
    ) -> VoiceOnboardingBlock | None:
        """Update a block."""
        block = await self.get_block_by_id(block_id)
        if not block:
            return None
        
        for key, value in kwargs.items():
            if value is not None and hasattr(block, key):
                setattr(block, key, value)
        
        block.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(block)
        return block

    async def delete_block(self, block_id: int) -> bool:
        """Delete a block."""
        block = await self.get_block_by_id(block_id)
        if not block:
            return False
        
        await self.session.delete(block)
        await self.session.commit()
        return True

    # =========================================================================
    # Field Operations
    # =========================================================================

    async def list_fields(
        self,
        *,
        block_id: int | None = None,
        active_only: bool = True,
    ) -> Sequence[VoiceOnboardingField]:
        """Return fields, optionally filtered by block."""
        stmt = select(VoiceOnboardingField).order_by(VoiceOnboardingField.display_order)
        
        if block_id is not None:
            stmt = stmt.where(VoiceOnboardingField.block_id == block_id)
        
        if active_only:
            stmt = stmt.where(VoiceOnboardingField.is_active == True)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_field_by_name(self, field_name: str) -> VoiceOnboardingField | None:
        """Get a field by its name."""
        stmt = select(VoiceOnboardingField).where(VoiceOnboardingField.field_name == field_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_field_by_id(self, field_id: int) -> VoiceOnboardingField | None:
        """Get a field by ID."""
        stmt = select(VoiceOnboardingField).where(VoiceOnboardingField.id == field_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_field(
        self,
        *,
        block_id: int,
        field_name: str,
        display_name: str,
        field_type: str,
        is_required: bool = False,
        validation_regex: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
        max_selections: int | None = None,
        options: list[str] | None = None,
        ai_question: str | None = None,
        ai_followup: str | None = None,
        is_active: bool = True,
        display_order: int = 0,
    ) -> VoiceOnboardingField:
        """Create a new field."""
        field = VoiceOnboardingField(
            block_id=block_id,
            field_name=field_name,
            display_name=display_name,
            field_type=field_type,
            is_required=is_required,
            validation_regex=validation_regex,
            min_length=min_length,
            max_length=max_length,
            min_value=min_value,
            max_value=max_value,
            max_selections=max_selections,
            options=options,
            ai_question=ai_question,
            ai_followup=ai_followup,
            is_active=is_active,
            display_order=display_order,
        )
        self.session.add(field)
        await self.session.commit()
        await self.session.refresh(field)
        return field

    async def update_field(
        self,
        field_id: int,
        **kwargs: Any,
    ) -> VoiceOnboardingField | None:
        """Update a field."""
        field = await self.get_field_by_id(field_id)
        if not field:
            return None
        
        for key, value in kwargs.items():
            if hasattr(field, key):
                setattr(field, key, value)
        
        field.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(field)
        return field

    async def delete_field(self, field_id: int) -> bool:
        """Delete a field."""
        field = await self.get_field_by_id(field_id)
        if not field:
            return False
        
        await self.session.delete(field)
        await self.session.commit()
        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_required_fields(self) -> Sequence[VoiceOnboardingField]:
        """Get all required fields across all active blocks."""
        stmt = (
            select(VoiceOnboardingField)
            .join(VoiceOnboardingBlock)
            .where(VoiceOnboardingField.is_required == True)
            .where(VoiceOnboardingField.is_active == True)
            .where(VoiceOnboardingBlock.is_active == True)
            .order_by(VoiceOnboardingBlock.display_order, VoiceOnboardingField.display_order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_field_config_dict(self) -> dict[str, dict[str, Any]]:
        """Get field configuration as a dictionary for voice service.
        
        Returns a dict compatible with the FIELD_CONFIG format used by voice_service.
        """
        fields = await self.list_fields(active_only=True)
        
        config = {}
        for field in fields:
            config[field.field_name] = {
                "display": field.display_name,
                "order": field.display_order,
                "required": field.is_required,
                "field_type": field.field_type,
                "options": field.options,
                "ai_question": field.ai_question,
                "ai_followup": field.ai_followup,
                "validation": {
                    "regex": field.validation_regex,
                    "min_length": field.min_length,
                    "max_length": field.max_length,
                    "min_value": field.min_value,
                    "max_value": field.max_value,
                    "max_selections": field.max_selections,
                },
            }
        
        return config
