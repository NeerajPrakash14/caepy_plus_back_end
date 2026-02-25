"""Voice Onboarding Configuration Models.

SQLAlchemy models for configurable voice onboarding blocks and fields.
These allow the questionnaire structure to be managed via database.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class VoiceOnboardingBlock(Base):
    """Voice onboarding block configuration.
    
    Represents a section/block in the doctor onboarding questionnaire.
    """

    __tablename__ = "voice_onboarding_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    block_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ai_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_disclaimer: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    completion_message: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    # Relationship to fields
    fields: Mapped[list[VoiceOnboardingField]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="VoiceOnboardingField.display_order",
    )


class VoiceOnboardingField(Base):
    """Voice onboarding field configuration.
    
    Represents a single field within a block that can be collected via voice.
    """

    __tablename__ = "voice_onboarding_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("voice_onboarding_blocks.id", ondelete="CASCADE"),
        nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, number, select, multi_select, year, multi_entry
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Validation constraints
    validation_regex: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_selections: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For multi-select

    # Options for select/multi-select fields
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # AI prompts for this field
    ai_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_followup: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    # Relationship to block
    block: Mapped[VoiceOnboardingBlock] = relationship(back_populates="fields")
