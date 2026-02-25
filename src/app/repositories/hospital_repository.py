"""
Hospital Repository.

Data access layer for Hospital and DoctorHospitalAffiliation entities.
Provides CRUD operations, search, and admin functions.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.hospital import DoctorHospitalAffiliation, Hospital, HospitalVerificationStatus

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)

class HospitalRepository:
    """Repository for Hospital entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    async def create(
        self,
        name: str,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        pincode: str | None = None,
        phone_number: str | None = None,
        email: str | None = None,
        website: str | None = None,
        created_by_doctor_id: int | None = None,
        verification_status: HospitalVerificationStatus = HospitalVerificationStatus.PENDING,
    ) -> Hospital:
        """Create a new hospital."""
        hospital = Hospital(
            name=name,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            phone_number=phone_number,
            email=email,
            website=website,
            created_by_doctor_id=created_by_doctor_id,
            verification_status=verification_status,
        )
        self.session.add(hospital)
        await self.session.flush()
        await self.session.refresh(hospital)
        logger.info(f"Created hospital: id={hospital.id}, name='{hospital.name}', status={hospital.verification_status}")
        return hospital

    async def get_by_id(self, hospital_id: int) -> Hospital | None:
        """Get a hospital by ID."""
        stmt = select(Hospital).where(Hospital.id == hospital_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_affiliations(self, hospital_id: int) -> Hospital | None:
        """Get a hospital by ID with its affiliations."""
        stmt = (
            select(Hospital)
            .options(selectinload(Hospital.affiliations))
            .where(Hospital.id == hospital_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        hospital_id: int,
        **kwargs,
    ) -> Hospital | None:
        """Update a hospital."""
        hospital = await self.get_by_id(hospital_id)
        if not hospital:
            return None

        for key, value in kwargs.items():
            if hasattr(hospital, key) and value is not None:
                setattr(hospital, key, value)

        hospital.updated_at = utc_now()
        await self.session.flush()
        await self.session.refresh(hospital)
        logger.info(f"Updated hospital: id={hospital_id}")
        return hospital

    async def soft_delete(self, hospital_id: int) -> bool:
        """Soft delete a hospital by setting is_active=False."""
        hospital = await self.get_by_id(hospital_id)
        if not hospital:
            return False

        hospital.is_active = False
        hospital.updated_at = utc_now()
        await self.session.flush()
        logger.info(f"Soft deleted hospital: id={hospital_id}")
        return True

    # ==========================================================================
    # Search & List Operations
    # ==========================================================================

    async def search(
        self,
        query: str,
        city: str | None = None,
        state: str | None = None,
        verified_only: bool = True,
        active_only: bool = True,
        limit: int = 20,
    ) -> Sequence[Hospital]:
        """
        Search hospitals by name with optional filters.
        Used for autocomplete dropdown.
        """
        conditions = []

        # Name search (case-insensitive)
        conditions.append(Hospital.name.ilike(f"%{query}%"))

        # Optional filters
        if city:
            conditions.append(Hospital.city.ilike(f"%{city}%"))
        if state:
            conditions.append(Hospital.state.ilike(f"%{state}%"))
        if verified_only:
            conditions.append(Hospital.verification_status == HospitalVerificationStatus.VERIFIED)
        if active_only:
            conditions.append(Hospital.is_active == True)

        stmt = (
            select(Hospital)
            .where(and_(*conditions))
            .order_by(Hospital.name)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        verification_status: HospitalVerificationStatus | None = None,
        active_only: bool = True,
        city: str | None = None,
        state: str | None = None,
    ) -> tuple[Sequence[Hospital], int]:
        """List hospitals with pagination and filters."""
        conditions = []

        if verification_status:
            conditions.append(Hospital.verification_status == verification_status)
        if active_only:
            conditions.append(Hospital.is_active == True)
        if city:
            conditions.append(Hospital.city.ilike(f"%{city}%"))
        if state:
            conditions.append(Hospital.state.ilike(f"%{state}%"))

        # Count query
        count_stmt = select(func.count(Hospital.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Data query
        stmt = select(Hospital).order_by(Hospital.name).offset(skip).limit(limit)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        hospitals = result.scalars().all()

        return hospitals, total

    async def list_pending(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Hospital], int]:
        """List hospitals pending verification (admin view)."""
        return await self.list_all(
            skip=skip,
            limit=limit,
            verification_status=HospitalVerificationStatus.PENDING,
            active_only=True,
        )

    # ==========================================================================
    # Admin Operations
    # ==========================================================================

    async def verify(
        self,
        hospital_id: int,
        verified_by: str | None = None,
    ) -> Hospital | None:
        """Verify a hospital (admin action)."""
        hospital = await self.get_by_id(hospital_id)
        if not hospital:
            return None

        hospital.verification_status = HospitalVerificationStatus.VERIFIED
        hospital.verified_at = utc_now()
        hospital.verified_by = verified_by
        hospital.rejection_reason = None
        hospital.updated_at = utc_now()

        await self.session.flush()
        await self.session.refresh(hospital)
        logger.info(f"Verified hospital: id={hospital_id}, by={verified_by}")
        return hospital

    async def reject(
        self,
        hospital_id: int,
        rejection_reason: str,
        rejected_by: str | None = None,
    ) -> Hospital | None:
        """Reject a hospital (admin action)."""
        hospital = await self.get_by_id(hospital_id)
        if not hospital:
            return None

        hospital.verification_status = HospitalVerificationStatus.REJECTED
        hospital.rejection_reason = rejection_reason
        hospital.verified_by = rejected_by  # Store who rejected
        hospital.verified_at = utc_now()
        hospital.updated_at = utc_now()

        await self.session.flush()
        await self.session.refresh(hospital)
        logger.info(f"Rejected hospital: id={hospital_id}, reason='{rejection_reason}'")
        return hospital

    async def merge_hospitals(
        self,
        source_ids: list[int],
        target_id: int,
    ) -> int:
        """
        Merge duplicate hospitals into a target hospital.
        Moves all affiliations from source hospitals to target, then deactivates sources.
        Returns the number of affiliations moved.
        """
        # Update all affiliations to point to target hospital
        stmt = (
            update(DoctorHospitalAffiliation)
            .where(DoctorHospitalAffiliation.hospital_id.in_(source_ids))
            .values(hospital_id=target_id, updated_at=utc_now())
        )
        result = await self.session.execute(stmt)
        affiliations_moved = result.rowcount

        # Soft delete source hospitals
        for source_id in source_ids:
            await self.soft_delete(source_id)

        logger.info(f"Merged hospitals {source_ids} into {target_id}, moved {affiliations_moved} affiliations")
        return affiliations_moved

    async def get_stats(self) -> dict:
        """Get hospital statistics."""
        # Total count
        total_stmt = select(func.count(Hospital.id))
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar() or 0

        # By verification status
        verified_stmt = select(func.count(Hospital.id)).where(
            Hospital.verification_status == HospitalVerificationStatus.VERIFIED
        )
        verified_result = await self.session.execute(verified_stmt)
        verified = verified_result.scalar() or 0

        pending_stmt = select(func.count(Hospital.id)).where(
            Hospital.verification_status == HospitalVerificationStatus.PENDING
        )
        pending_result = await self.session.execute(pending_stmt)
        pending = pending_result.scalar() or 0

        rejected_stmt = select(func.count(Hospital.id)).where(
            Hospital.verification_status == HospitalVerificationStatus.REJECTED
        )
        rejected_result = await self.session.execute(rejected_stmt)
        rejected = rejected_result.scalar() or 0

        # Active/Inactive
        active_stmt = select(func.count(Hospital.id)).where(Hospital.is_active == True)
        active_result = await self.session.execute(active_stmt)
        active = active_result.scalar() or 0

        return {
            "total_hospitals": total,
            "verified_count": verified,
            "pending_count": pending,
            "rejected_count": rejected,
            "active_count": active,
            "inactive_count": total - active,
        }

    async def clear_created_by_doctor(self, doctor_id: int) -> int:
        """Clear created_by_doctor_id for all hospitals created by a doctor.

        This is useful for irreversible doctor erasure workflows where we
        want to remove direct references to the doctor but keep the
        hospital records themselves.
        
        Returns the number of rows updated.
        """

        stmt = (
            update(Hospital)
            .where(Hospital.created_by_doctor_id == doctor_id)
            .values(created_by_doctor_id=None, updated_at=utc_now())
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0

class DoctorHospitalAffiliationRepository:
    """Repository for DoctorHospitalAffiliation entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    async def create(
        self,
        doctor_id: int,
        hospital_id: int,
        consultation_fee: float | None = None,
        consultation_type: str | None = None,
        weekly_schedule: str | None = None,
        designation: str | None = None,
        department: str | None = None,
        is_primary: bool = False,
    ) -> DoctorHospitalAffiliation:
        """Create a new doctor-hospital affiliation."""
        # If this is marked as primary, unset other primaries for this doctor
        if is_primary:
            await self._unset_primary_for_doctor(doctor_id)

        affiliation = DoctorHospitalAffiliation(
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            consultation_fee=consultation_fee,
            consultation_type=consultation_type,
            weekly_schedule=weekly_schedule,
            designation=designation,
            department=department,
            is_primary=is_primary,
        )
        self.session.add(affiliation)
        await self.session.flush()
        await self.session.refresh(affiliation)
        logger.info(f"Created affiliation: doctor_id={doctor_id}, hospital_id={hospital_id}")
        return affiliation

    async def get_by_id(self, affiliation_id: str) -> DoctorHospitalAffiliation | None:
        """Get an affiliation by ID."""
        stmt = (
            select(DoctorHospitalAffiliation)
            .options(selectinload(DoctorHospitalAffiliation.hospital))
            .where(DoctorHospitalAffiliation.id == affiliation_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_doctor_and_hospital(
        self,
        doctor_id: int,
        hospital_id: int,
    ) -> DoctorHospitalAffiliation | None:
        """Get affiliation by doctor and hospital IDs."""
        stmt = (
            select(DoctorHospitalAffiliation)
            .options(selectinload(DoctorHospitalAffiliation.hospital))
            .where(
                and_(
                    DoctorHospitalAffiliation.doctor_id == doctor_id,
                    DoctorHospitalAffiliation.hospital_id == hospital_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        affiliation_id: str,
        **kwargs,
    ) -> DoctorHospitalAffiliation | None:
        """Update an affiliation."""
        affiliation = await self.get_by_id(affiliation_id)
        if not affiliation:
            return None

        # Handle is_primary specially
        if kwargs.get("is_primary") is True:
            await self._unset_primary_for_doctor(affiliation.doctor_id)

        for key, value in kwargs.items():
            if hasattr(affiliation, key) and value is not None:
                setattr(affiliation, key, value)

        affiliation.updated_at = utc_now()
        await self.session.flush()
        await self.session.refresh(affiliation)
        logger.info(f"Updated affiliation: id={affiliation_id}")
        return affiliation

    async def soft_delete(self, affiliation_id: str) -> bool:
        """Soft delete an affiliation."""
        affiliation = await self.get_by_id(affiliation_id)
        if not affiliation:
            return False

        affiliation.is_active = False
        affiliation.updated_at = utc_now()
        await self.session.flush()
        logger.info(f"Soft deleted affiliation: id={affiliation_id}")
        return True

    async def hard_delete(self, affiliation_id: str) -> bool:
        """Permanently delete an affiliation."""
        stmt = delete(DoctorHospitalAffiliation).where(
            DoctorHospitalAffiliation.id == affiliation_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Hard deleted affiliation: id={affiliation_id}")
        return deleted

    async def hard_delete_by_doctor(self, doctor_id: int) -> int:
        """Permanently delete all affiliations for a doctor.

        Returns the number of affiliation rows deleted.
        """

        stmt = delete(DoctorHospitalAffiliation).where(
            DoctorHospitalAffiliation.doctor_id == doctor_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        deleted = result.rowcount or 0
        if deleted:
            logger.info(f"Hard deleted {deleted} affiliations for doctor_id={doctor_id}")
        return deleted

    # ==========================================================================
    # Query Operations
    # ==========================================================================

    async def list_by_doctor(
        self,
        doctor_id: int,
        active_only: bool = True,
        include_unverified_hospitals: bool = False,
    ) -> Sequence[DoctorHospitalAffiliation]:
        """Get all affiliations for a doctor."""
        conditions = [DoctorHospitalAffiliation.doctor_id == doctor_id]

        if active_only:
            conditions.append(DoctorHospitalAffiliation.is_active == True)

        stmt = (
            select(DoctorHospitalAffiliation)
            .options(selectinload(DoctorHospitalAffiliation.hospital))
            .where(and_(*conditions))
            .order_by(DoctorHospitalAffiliation.is_primary.desc(), DoctorHospitalAffiliation.created_at)
        )

        result = await self.session.execute(stmt)
        affiliations = result.scalars().all()

        # Optionally filter out unverified hospitals
        if not include_unverified_hospitals:
            affiliations = [
                a for a in affiliations
                if a.hospital.verification_status == HospitalVerificationStatus.VERIFIED
                or a.hospital.created_by_doctor_id == doctor_id  # Show hospitals they created
            ]

        return affiliations

    async def list_by_hospital(
        self,
        hospital_id: int,
        active_only: bool = True,
    ) -> Sequence[DoctorHospitalAffiliation]:
        """Get all affiliations for a hospital (doctors at this hospital)."""
        conditions = [DoctorHospitalAffiliation.hospital_id == hospital_id]

        if active_only:
            conditions.append(DoctorHospitalAffiliation.is_active == True)

        stmt = (
            select(DoctorHospitalAffiliation)
            .options(selectinload(DoctorHospitalAffiliation.hospital))
            .where(and_(*conditions))
            .order_by(DoctorHospitalAffiliation.created_at)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_primary_for_doctor(
        self,
        doctor_id: int,
    ) -> DoctorHospitalAffiliation | None:
        """Get the primary affiliation for a doctor."""
        stmt = (
            select(DoctorHospitalAffiliation)
            .options(selectinload(DoctorHospitalAffiliation.hospital))
            .where(
                and_(
                    DoctorHospitalAffiliation.doctor_id == doctor_id,
                    DoctorHospitalAffiliation.is_primary == True,
                    DoctorHospitalAffiliation.is_active == True,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    async def _unset_primary_for_doctor(self, doctor_id: int) -> None:
        """Unset the primary flag for all affiliations of a doctor."""
        stmt = (
            update(DoctorHospitalAffiliation)
            .where(
                and_(
                    DoctorHospitalAffiliation.doctor_id == doctor_id,
                    DoctorHospitalAffiliation.is_primary == True,
                )
            )
            .values(is_primary=False, updated_at=utc_now())
        )
        await self.session.execute(stmt)

# ==========================================================================
# Dependency Injection
# ==========================================================================

async def get_hospital_repository(session: AsyncSession) -> HospitalRepository:
    """Get hospital repository instance."""
    return HospitalRepository(session)

async def get_affiliation_repository(session: AsyncSession) -> DoctorHospitalAffiliationRepository:
    """Get affiliation repository instance."""
    return DoctorHospitalAffiliationRepository(session)
