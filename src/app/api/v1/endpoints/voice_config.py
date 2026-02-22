"""Voice Onboarding Configuration API endpoints.

Admin endpoints for managing configurable voice onboarding blocks and fields.
"""
import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from ....core.responses import GenericResponse
from ....db.session import DbSession
from ....repositories.voice_config_repository import VoiceConfigRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-config")


# =============================================================================
# Schemas
# =============================================================================

class VoiceBlockBase(BaseModel):
    """Base schema for voice onboarding block."""
    block_number: int
    block_name: str = Field(max_length=100)
    display_name: str = Field(max_length=200)
    ai_prompt: str | None = None
    ai_disclaimer: str | None = None
    completion_percentage: int = Field(default=0, ge=0, le=100)
    completion_message: str | None = Field(default=None, max_length=200)
    is_active: bool = True
    display_order: int = 0


class VoiceBlockCreate(VoiceBlockBase):
    """Schema for creating a voice block."""
    pass


class VoiceBlockUpdate(BaseModel):
    """Schema for updating a voice block."""
    block_name: str | None = None
    display_name: str | None = None
    ai_prompt: str | None = None
    ai_disclaimer: str | None = None
    completion_percentage: int | None = None
    completion_message: str | None = None
    is_active: bool | None = None
    display_order: int | None = None


class VoiceFieldBase(BaseModel):
    """Base schema for voice onboarding field."""
    field_name: str = Field(max_length=100)
    display_name: str = Field(max_length=200)
    field_type: str = Field(max_length=50)  # text, number, select, multi_select, year, multi_entry
    is_required: bool = False
    validation_regex: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    max_selections: int | None = None
    options: list[str] | None = None
    ai_question: str | None = None
    ai_followup: str | None = None
    is_active: bool = True
    display_order: int = 0


class VoiceFieldCreate(VoiceFieldBase):
    """Schema for creating a voice field."""
    block_id: int


class VoiceFieldUpdate(BaseModel):
    """Schema for updating a voice field."""
    display_name: str | None = None
    field_type: str | None = None
    is_required: bool | None = None
    validation_regex: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    max_selections: int | None = None
    options: list[str] | None = None
    ai_question: str | None = None
    ai_followup: str | None = None
    is_active: bool | None = None
    display_order: int | None = None


class VoiceFieldResponse(VoiceFieldBase):
    """Response schema for voice field."""
    id: int
    block_id: int

    model_config = ConfigDict(from_attributes=True)


class VoiceBlockResponse(VoiceBlockBase):
    """Response schema for voice block."""
    id: int
    fields: list[VoiceFieldResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VoiceConfigResponse(BaseModel):
    """Full voice configuration response."""
    blocks: list[VoiceBlockResponse]
    total_blocks: int
    total_fields: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "",
    response_model=GenericResponse[VoiceConfigResponse],
    summary="Get full voice onboarding configuration",
    description="Returns all blocks and fields for voice onboarding questionnaire.",
)
async def get_voice_config(
    db: DbSession,
    active_only: bool = Query(default=True, description="Only return active blocks/fields"),
) -> GenericResponse[VoiceConfigResponse]:
    """Get the complete voice onboarding configuration."""
    repo = VoiceConfigRepository(db)

    blocks = await repo.list_blocks(active_only=active_only)

    # Convert to response format
    block_responses = []
    total_fields = 0

    for block in blocks:
        fields = [f for f in block.fields if (not active_only or f.is_active)]
        total_fields += len(fields)

        block_responses.append(VoiceBlockResponse(
            id=block.id,
            block_number=block.block_number,
            block_name=block.block_name,
            display_name=block.display_name,
            ai_prompt=block.ai_prompt,
            ai_disclaimer=block.ai_disclaimer,
            completion_percentage=block.completion_percentage,
            completion_message=block.completion_message,
            is_active=block.is_active,
            display_order=block.display_order,
            fields=[VoiceFieldResponse(
                id=f.id,
                block_id=f.block_id,
                field_name=f.field_name,
                display_name=f.display_name,
                field_type=f.field_type,
                is_required=f.is_required,
                validation_regex=f.validation_regex,
                min_length=f.min_length,
                max_length=f.max_length,
                min_value=f.min_value,
                max_value=f.max_value,
                max_selections=f.max_selections,
                options=f.options,
                ai_question=f.ai_question,
                ai_followup=f.ai_followup,
                is_active=f.is_active,
                display_order=f.display_order,
            ) for f in fields],
        ))

    return GenericResponse(
        message="Voice configuration retrieved",
        data=VoiceConfigResponse(
            blocks=block_responses,
            total_blocks=len(block_responses),
            total_fields=total_fields,
        ),
    )


@router.get(
    "/blocks/{block_number}",
    response_model=GenericResponse[VoiceBlockResponse],
    summary="Get a specific block",
)
async def get_block(
    block_number: int,
    db: DbSession,
) -> GenericResponse[VoiceBlockResponse]:
    """Get a specific block by number."""
    repo = VoiceConfigRepository(db)

    block = await repo.get_block_by_number(block_number)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block {block_number} not found",
        )

    return GenericResponse(
        message="Block retrieved",
        data=VoiceBlockResponse(
            id=block.id,
            block_number=block.block_number,
            block_name=block.block_name,
            display_name=block.display_name,
            ai_prompt=block.ai_prompt,
            ai_disclaimer=block.ai_disclaimer,
            completion_percentage=block.completion_percentage,
            completion_message=block.completion_message,
            is_active=block.is_active,
            display_order=block.display_order,
            fields=[VoiceFieldResponse(
                id=f.id,
                block_id=f.block_id,
                field_name=f.field_name,
                display_name=f.display_name,
                field_type=f.field_type,
                is_required=f.is_required,
                validation_regex=f.validation_regex,
                min_length=f.min_length,
                max_length=f.max_length,
                min_value=f.min_value,
                max_value=f.max_value,
                max_selections=f.max_selections,
                options=f.options,
                ai_question=f.ai_question,
                ai_followup=f.ai_followup,
                is_active=f.is_active,
                display_order=f.display_order,
            ) for f in block.fields],
        ),
    )


@router.post(
    "/blocks",
    response_model=GenericResponse[VoiceBlockResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new block",
)
async def create_block(
    payload: VoiceBlockCreate,
    db: DbSession,
) -> GenericResponse[VoiceBlockResponse]:
    """Create a new voice onboarding block."""
    repo = VoiceConfigRepository(db)

    block = await repo.create_block(
        block_number=payload.block_number,
        block_name=payload.block_name,
        display_name=payload.display_name,
        ai_prompt=payload.ai_prompt,
        ai_disclaimer=payload.ai_disclaimer,
        completion_percentage=payload.completion_percentage,
        completion_message=payload.completion_message,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )

    logger.info(f"Created voice block: {block.block_number} - {block.block_name}")

    return GenericResponse(
        message="Block created successfully",
        data=VoiceBlockResponse(
            id=block.id,
            block_number=block.block_number,
            block_name=block.block_name,
            display_name=block.display_name,
            ai_prompt=block.ai_prompt,
            ai_disclaimer=block.ai_disclaimer,
            completion_percentage=block.completion_percentage,
            completion_message=block.completion_message,
            is_active=block.is_active,
            display_order=block.display_order,
            fields=[],
        ),
    )


@router.patch(
    "/blocks/{block_id}",
    response_model=GenericResponse[VoiceBlockResponse],
    summary="Update a block",
)
async def update_block(
    block_id: int,
    payload: VoiceBlockUpdate,
    db: DbSession,
) -> GenericResponse[VoiceBlockResponse]:
    """Update a voice onboarding block."""
    repo = VoiceConfigRepository(db)

    update_data = payload.model_dump(exclude_unset=True)
    block = await repo.update_block(block_id, **update_data)

    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block {block_id} not found",
        )

    logger.info(f"Updated voice block: {block_id}")

    return GenericResponse(
        message="Block updated successfully",
        data=VoiceBlockResponse(
            id=block.id,
            block_number=block.block_number,
            block_name=block.block_name,
            display_name=block.display_name,
            ai_prompt=block.ai_prompt,
            ai_disclaimer=block.ai_disclaimer,
            completion_percentage=block.completion_percentage,
            completion_message=block.completion_message,
            is_active=block.is_active,
            display_order=block.display_order,
            fields=[VoiceFieldResponse(
                id=f.id,
                block_id=f.block_id,
                field_name=f.field_name,
                display_name=f.display_name,
                field_type=f.field_type,
                is_required=f.is_required,
                validation_regex=f.validation_regex,
                min_length=f.min_length,
                max_length=f.max_length,
                min_value=f.min_value,
                max_value=f.max_value,
                max_selections=f.max_selections,
                options=f.options,
                ai_question=f.ai_question,
                ai_followup=f.ai_followup,
                is_active=f.is_active,
                display_order=f.display_order,
            ) for f in block.fields],
        ),
    )


@router.delete(
    "/blocks/{block_id}",
    response_model=GenericResponse[dict],
    summary="Delete a block",
)
async def delete_block(
    block_id: int,
    db: DbSession,
) -> GenericResponse[dict]:
    """Delete a voice onboarding block."""
    repo = VoiceConfigRepository(db)

    deleted = await repo.delete_block(block_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block {block_id} not found",
        )

    logger.info(f"Deleted voice block: {block_id}")

    return GenericResponse(
        message="Block deleted successfully",
        data={"deleted": True, "id": block_id},
    )


# =============================================================================
# Field Endpoints
# =============================================================================

@router.post(
    "/fields",
    response_model=GenericResponse[VoiceFieldResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new field",
)
async def create_field(
    payload: VoiceFieldCreate,
    db: DbSession,
) -> GenericResponse[VoiceFieldResponse]:
    """Create a new voice onboarding field."""
    repo = VoiceConfigRepository(db)

    field = await repo.create_field(
        block_id=payload.block_id,
        field_name=payload.field_name,
        display_name=payload.display_name,
        field_type=payload.field_type,
        is_required=payload.is_required,
        validation_regex=payload.validation_regex,
        min_length=payload.min_length,
        max_length=payload.max_length,
        min_value=payload.min_value,
        max_value=payload.max_value,
        max_selections=payload.max_selections,
        options=payload.options,
        ai_question=payload.ai_question,
        ai_followup=payload.ai_followup,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )

    logger.info(f"Created voice field: {field.field_name}")

    return GenericResponse(
        message="Field created successfully",
        data=VoiceFieldResponse(
            id=field.id,
            block_id=field.block_id,
            field_name=field.field_name,
            display_name=field.display_name,
            field_type=field.field_type,
            is_required=field.is_required,
            validation_regex=field.validation_regex,
            min_length=field.min_length,
            max_length=field.max_length,
            min_value=field.min_value,
            max_value=field.max_value,
            max_selections=field.max_selections,
            options=field.options,
            ai_question=field.ai_question,
            ai_followup=field.ai_followup,
            is_active=field.is_active,
            display_order=field.display_order,
        ),
    )


@router.patch(
    "/fields/{field_id}",
    response_model=GenericResponse[VoiceFieldResponse],
    summary="Update a field",
)
async def update_field(
    field_id: int,
    payload: VoiceFieldUpdate,
    db: DbSession,
) -> GenericResponse[VoiceFieldResponse]:
    """Update a voice onboarding field."""
    repo = VoiceConfigRepository(db)

    update_data = payload.model_dump(exclude_unset=True)
    field = await repo.update_field(field_id, **update_data)

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field {field_id} not found",
        )

    logger.info(f"Updated voice field: {field_id}")

    return GenericResponse(
        message="Field updated successfully",
        data=VoiceFieldResponse(
            id=field.id,
            block_id=field.block_id,
            field_name=field.field_name,
            display_name=field.display_name,
            field_type=field.field_type,
            is_required=field.is_required,
            validation_regex=field.validation_regex,
            min_length=field.min_length,
            max_length=field.max_length,
            min_value=field.min_value,
            max_value=field.max_value,
            max_selections=field.max_selections,
            options=field.options,
            ai_question=field.ai_question,
            ai_followup=field.ai_followup,
            is_active=field.is_active,
            display_order=field.display_order,
        ),
    )


@router.delete(
    "/fields/{field_id}",
    response_model=GenericResponse[dict],
    summary="Delete a field",
)
async def delete_field(
    field_id: int,
    db: DbSession,
) -> GenericResponse[dict]:
    """Delete a voice onboarding field."""
    repo = VoiceConfigRepository(db)

    deleted = await repo.delete_field(field_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field {field_id} not found",
        )

    logger.info(f"Deleted voice field: {field_id}")

    return GenericResponse(
        message="Field deleted successfully",
        data={"deleted": True, "id": field_id},
    )


@router.get(
    "/field-config",
    response_model=GenericResponse[dict],
    summary="Get field configuration dictionary",
    description="Returns field configuration in the format used by voice_service.",
)
async def get_field_config(
    db: DbSession,
) -> GenericResponse[dict]:
    """Get field configuration for voice service integration."""
    repo = VoiceConfigRepository(db)

    config = await repo.get_field_config_dict()

    return GenericResponse(
        message="Field configuration retrieved",
        data=config,
    )
