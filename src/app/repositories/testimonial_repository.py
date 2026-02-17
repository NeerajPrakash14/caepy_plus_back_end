"""Testimonial repository.

Async data access helpers for testimonials table.
"""
from __future__ import annotations

from typing import Sequence
from datetime import datetime, UTC

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.testimonial import Testimonial


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class TestimonialRepository:
    """Repository providing CRUD operations for testimonials."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Testimonial]:
        """Return active testimonials ordered by display_order."""
        stmt = (
            select(Testimonial)
            .where(Testimonial.is_active == True)
            .order_by(Testimonial.display_order.asc(), Testimonial.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Testimonial]:
        """Return all testimonials (admin view)."""
        stmt = (
            select(Testimonial)
            .order_by(Testimonial.display_order.asc(), Testimonial.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_active(self) -> int:
        """Count active testimonials."""
        stmt = select(func.count(Testimonial.id)).where(Testimonial.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_all(self) -> int:
        """Count all testimonials."""
        stmt = select(func.count(Testimonial.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_by_id(self, testimonial_id: str) -> Testimonial | None:
        """Fetch testimonial by ID."""
        stmt = select(Testimonial).where(Testimonial.id == testimonial_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        doctor_name: str,
        comment: str,
        specialty: str | None = None,
        designation: str | None = None,
        hospital_name: str | None = None,
        location: str | None = None,
        profile_image_url: str | None = None,
        rating: int | None = None,
        is_active: bool = True,
        display_order: int = 0,
    ) -> Testimonial:
        """Create a new testimonial."""
        testimonial = Testimonial(
            doctor_name=doctor_name,
            comment=comment,
            specialty=specialty,
            designation=designation,
            hospital_name=hospital_name,
            location=location,
            profile_image_url=profile_image_url,
            rating=rating,
            is_active=is_active,
            display_order=display_order,
        )
        self.session.add(testimonial)
        await self.session.commit()
        await self.session.refresh(testimonial)
        return testimonial

    async def update(
        self,
        testimonial_id: str,
        **kwargs,
    ) -> Testimonial | None:
        """Update an existing testimonial."""
        testimonial = await self.get_by_id(testimonial_id)
        if not testimonial:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(testimonial, key):
                setattr(testimonial, key, value)

        testimonial.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(testimonial)
        return testimonial

    async def delete(self, testimonial_id: str) -> bool:
        """Delete a testimonial."""
        testimonial = await self.get_by_id(testimonial_id)
        if not testimonial:
            return False

        await self.session.delete(testimonial)
        await self.session.commit()
        return True

    async def toggle_active(self, testimonial_id: str) -> Testimonial | None:
        """Toggle testimonial active status."""
        testimonial = await self.get_by_id(testimonial_id)
        if not testimonial:
            return None

        testimonial.is_active = not testimonial.is_active
        testimonial.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(testimonial)
        return testimonial
