"""Testimonial schemas.

Pydantic models for testimonial/doctor comments displayed on homepage carousel.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TestimonialBase(BaseModel):
    """Base schema for testimonials."""
    
    doctor_name: str = Field(..., min_length=1, max_length=200, description="Doctor's full name")
    specialty: str | None = Field(default=None, max_length=100, description="Doctor's specialty")
    designation: str | None = Field(default=None, max_length=200, description="Doctor's designation/title")
    hospital_name: str | None = Field(default=None, max_length=200, description="Hospital/clinic name")
    location: str | None = Field(default=None, max_length=100, description="City or location")
    profile_image_url: str | None = Field(default=None, description="URL to doctor's profile image")
    comment: str = Field(..., min_length=10, max_length=1000, description="Testimonial comment text")
    rating: int | None = Field(default=None, ge=1, le=5, description="Rating out of 5 stars")
    is_active: bool = Field(default=True, description="Whether testimonial is visible")
    display_order: int = Field(default=0, description="Order in which to display (lower = first)")


class TestimonialCreate(TestimonialBase):
    """Payload for creating a new testimonial."""
    pass


class TestimonialUpdate(BaseModel):
    """Payload for updating an existing testimonial."""
    
    doctor_name: str | None = Field(default=None, min_length=1, max_length=200)
    specialty: str | None = None
    designation: str | None = None
    hospital_name: str | None = None
    location: str | None = None
    profile_image_url: str | None = None
    comment: str | None = Field(default=None, min_length=10, max_length=1000)
    rating: int | None = Field(default=None, ge=1, le=5)
    is_active: bool | None = None
    display_order: int | None = None


class TestimonialResponse(TestimonialBase):
    """API response model for testimonial."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime


class TestimonialListResponse(BaseModel):
    """Response for list of testimonials."""
    
    testimonials: list[TestimonialResponse]
    total: int
