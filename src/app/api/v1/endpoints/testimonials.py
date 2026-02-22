"""Testimonials API endpoints.

Public and admin endpoints for managing doctor testimonials displayed on the homepage carousel.
"""
import logging

from fastapi import APIRouter, HTTPException, Query, status

from ....core.responses import GenericResponse
from ....db.session import DbSession
from ....repositories.testimonial_repository import TestimonialRepository
from ....schemas.testimonial import (
    TestimonialCreate,
    TestimonialListResponse,
    TestimonialResponse,
    TestimonialUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/testimonials")


# ---------------------------------------------------------------------------
# Public endpoints (for homepage carousel)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=GenericResponse[TestimonialListResponse],
    summary="Get active testimonials for homepage",
    description="Returns list of active doctor testimonials for the homepage carousel. Ordered by display_order.",
)
async def list_testimonials(
    db: DbSession,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return"),
) -> GenericResponse[TestimonialListResponse]:
    """Get active testimonials for public display."""
    repo = TestimonialRepository(db)

    testimonials = await repo.list_active(skip=skip, limit=limit)
    total = await repo.count_active()

    return GenericResponse(
        message="Testimonials retrieved successfully",
        data=TestimonialListResponse(
            testimonials=[TestimonialResponse.model_validate(t) for t in testimonials],
            total=total,
        ),
    )


# ---------------------------------------------------------------------------
# Admin endpoints (for managing testimonials)
# ---------------------------------------------------------------------------

@router.get(
    "/admin",
    response_model=GenericResponse[TestimonialListResponse],
    summary="Get all testimonials (admin)",
    description="Returns all testimonials including inactive ones. For admin management.",
)
async def list_all_testimonials(
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> GenericResponse[TestimonialListResponse]:
    """Get all testimonials for admin view."""
    repo = TestimonialRepository(db)

    testimonials = await repo.list_all(skip=skip, limit=limit)
    total = await repo.count_all()

    return GenericResponse(
        message="All testimonials retrieved",
        data=TestimonialListResponse(
            testimonials=[TestimonialResponse.model_validate(t) for t in testimonials],
            total=total,
        ),
    )


@router.get(
    "/{testimonial_id}",
    response_model=GenericResponse[TestimonialResponse],
    summary="Get testimonial by ID",
)
async def get_testimonial(
    testimonial_id: str,
    db: DbSession,
) -> GenericResponse[TestimonialResponse]:
    """Get a single testimonial by ID."""
    repo = TestimonialRepository(db)

    testimonial = await repo.get_by_id(testimonial_id)
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Testimonial not found: {testimonial_id}",
        )

    return GenericResponse(
        message="Testimonial retrieved",
        data=TestimonialResponse.model_validate(testimonial),
    )


@router.post(
    "",
    response_model=GenericResponse[TestimonialResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new testimonial",
)
async def create_testimonial(
    payload: TestimonialCreate,
    db: DbSession,
) -> GenericResponse[TestimonialResponse]:
    """Create a new testimonial."""
    repo = TestimonialRepository(db)

    testimonial = await repo.create(
        doctor_name=payload.doctor_name,
        comment=payload.comment,
        specialty=payload.specialty,
        designation=payload.designation,
        hospital_name=payload.hospital_name,
        location=payload.location,
        profile_image_url=payload.profile_image_url,
        rating=payload.rating,
        is_active=payload.is_active,
        display_order=payload.display_order,
    )

    logger.info(f"Created testimonial: {testimonial.id} for {testimonial.doctor_name}")

    return GenericResponse(
        message="Testimonial created successfully",
        data=TestimonialResponse.model_validate(testimonial),
    )


@router.patch(
    "/{testimonial_id}",
    response_model=GenericResponse[TestimonialResponse],
    summary="Update a testimonial",
)
async def update_testimonial(
    testimonial_id: str,
    payload: TestimonialUpdate,
    db: DbSession,
) -> GenericResponse[TestimonialResponse]:
    """Update an existing testimonial."""
    repo = TestimonialRepository(db)

    # Filter out None values
    update_data = payload.model_dump(exclude_unset=True)

    testimonial = await repo.update(testimonial_id, **update_data)
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Testimonial not found: {testimonial_id}",
        )

    logger.info(f"Updated testimonial: {testimonial_id}")

    return GenericResponse(
        message="Testimonial updated successfully",
        data=TestimonialResponse.model_validate(testimonial),
    )


@router.delete(
    "/{testimonial_id}",
    response_model=GenericResponse[dict],
    summary="Delete a testimonial",
)
async def delete_testimonial(
    testimonial_id: str,
    db: DbSession,
) -> GenericResponse[dict]:
    """Delete a testimonial."""
    repo = TestimonialRepository(db)

    deleted = await repo.delete(testimonial_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Testimonial not found: {testimonial_id}",
        )

    logger.info(f"Deleted testimonial: {testimonial_id}")

    return GenericResponse(
        message="Testimonial deleted successfully",
        data={"deleted": True, "id": testimonial_id},
    )


@router.post(
    "/{testimonial_id}/toggle-active",
    response_model=GenericResponse[TestimonialResponse],
    summary="Toggle testimonial active status",
)
async def toggle_testimonial_active(
    testimonial_id: str,
    db: DbSession,
) -> GenericResponse[TestimonialResponse]:
    """Toggle a testimonial's active/inactive status."""
    repo = TestimonialRepository(db)

    testimonial = await repo.toggle_active(testimonial_id)
    if not testimonial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Testimonial not found: {testimonial_id}",
        )

    status_text = "activated" if testimonial.is_active else "deactivated"
    logger.info(f"Testimonial {testimonial_id} {status_text}")

    return GenericResponse(
        message=f"Testimonial {status_text} successfully",
        data=TestimonialResponse.model_validate(testimonial),
    )
