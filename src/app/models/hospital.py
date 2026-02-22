"""
Hospital Domain Models.

SQLAlchemy 2.0 ORM models for the hospitals domain.

Architecture:
    - Hospital: Master hospital/clinic table
    - DoctorHospitalAffiliation: Many-to-many linking doctors to hospitals
    
Design Decisions:
    - Hospitals have verification_status for admin review workflow
    - Doctors can add new hospitals (pending verification)
    - One doctor can have multiple hospital affiliations
    - Each affiliation has doctor-specific info (fee, schedule)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class HospitalVerificationStatus(str, Enum):
    """Hospital verification status enum.
    
    Allowed values: pending, verified, rejected.
    """
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Hospital(Base):
    """
    Hospital entity - Master table for hospitals/clinics.
    
    Doctors select from this list during onboarding.
    If their hospital isn't found, they can add a new one (pending verification).
    Admin can verify, reject, or merge duplicate hospitals.
    
    Attributes:
        Basic: name, address, city, state, pincode, phone_number
        Verification: verification_status, verified_at, verified_by
        Meta: created_by_doctor_id (who added it), timestamps
        
    Relationships:
        affiliations: One-to-many with DoctorHospitalAffiliation
    """

    __tablename__ = "hospitals"

    # ==========================================================================
    # PRIMARY KEY
    # ==========================================================================
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    # ==========================================================================
    # HOSPITAL DETAILS
    # ==========================================================================
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Hospital or clinic name",
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full street address",
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="City name",
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="State or province",
    )

    pincode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Postal/ZIP code",
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Hospital contact number",
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Hospital email",
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Hospital website URL",
    )

    # ==========================================================================
    # VERIFICATION STATUS
    # ==========================================================================
    verification_status: Mapped[HospitalVerificationStatus] = mapped_column(
        SQLEnum(HospitalVerificationStatus, name="hospital_verification_status_enum", native_enum=False),
        nullable=False,
        default=HospitalVerificationStatus.PENDING,
        index=True,
        comment="Verification status: pending, verified, rejected",
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the hospital was verified",
    )

    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Admin who verified this hospital",
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for rejection (if rejected)",
    )

    # ==========================================================================
    # TRACKING
    # ==========================================================================
    created_by_doctor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Doctor ID who added this hospital (if doctor-added)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft delete flag",
    )

    # ==========================================================================
    # TIMESTAMPS
    # ==========================================================================
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

    # ==========================================================================
    # RELATIONSHIPS
    # ==========================================================================
    affiliations: Mapped[list[DoctorHospitalAffiliation]] = relationship(
        back_populates="hospital",
        cascade="all, delete-orphan",
    )

    # ==========================================================================
    # INDEXES
    # ==========================================================================
    __table_args__ = (
        Index("ix_hospitals_name_city", "name", "city"),
        Index("ix_hospitals_verification_active", "verification_status", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Hospital(id={self.id}, name='{self.name}', city='{self.city}')>"


class DoctorHospitalAffiliation(Base):
    """
    Doctor-Hospital affiliation - Links doctors to hospitals.
    
    A doctor can be affiliated with multiple hospitals.
    Each affiliation stores doctor-specific information like:
        - Consultation fee at this hospital
        - Consultation type (in-person, online, etc.)
        - Weekly schedule at this hospital
        - Whether this is the primary location
    
    Attributes:
        Links: doctor_id, hospital_id
        Doctor-specific: consultation_fee, consultation_type, weekly_schedule
        Flags: is_primary, is_active
        Timestamps: created_at, updated_at
        
    Relationships:
        hospital: Many-to-one with Hospital
    """

    __tablename__ = "doctor_hospital_affiliations"

    # ==========================================================================
    # PRIMARY KEY
    # ==========================================================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ==========================================================================
    # FOREIGN KEYS
    # ==========================================================================
    doctor_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="References doctor_identity.doctor_id",
    )

    hospital_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ==========================================================================
    # DOCTOR-SPECIFIC INFO AT THIS HOSPITAL
    # ==========================================================================
    consultation_fee: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Consultation fee at this hospital",
    )

    consultation_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Type: In-person, Online, Both",
    )

    weekly_schedule: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Schedule at this hospital (e.g., Mon-Fri 9AM-5PM)",
    )

    designation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Doctor's designation at this hospital",
    )

    department: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Department at this hospital",
    )

    # ==========================================================================
    # FLAGS
    # ==========================================================================
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the doctor's primary practice location?",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft delete flag",
    )

    # ==========================================================================
    # TIMESTAMPS
    # ==========================================================================
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

    # ==========================================================================
    # RELATIONSHIPS
    # ==========================================================================
    hospital: Mapped[Hospital] = relationship(back_populates="affiliations")

    # ==========================================================================
    # CONSTRAINTS
    # ==========================================================================
    __table_args__ = (
        # A doctor can only have one affiliation per hospital
        UniqueConstraint("doctor_id", "hospital_id", name="uq_doctor_hospital"),
        Index("ix_affiliations_doctor_primary", "doctor_id", "is_primary"),
    )

    def __repr__(self) -> str:
        return f"<DoctorHospitalAffiliation(doctor_id={self.doctor_id}, hospital_id={self.hospital_id})>"
