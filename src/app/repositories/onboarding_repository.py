"""Onboarding repository.

Async data access helpers for the onboarding tables:
- doctor_identity
- doctor_details
- doctor_media
- doctor_status_history

All operations use SQLAlchemy's async session and work against SQLite
(and PostgreSQL when configured) via the shared models.
"""
from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.onboarding import (
    DoctorDetails,
    DoctorIdentity,
    DoctorMedia,
    DoctorStatusHistory,
    OnboardingStatus,
    DropdownOption,
)

class OnboardingRepository:
    """Repository providing common CRUD operations for onboarding tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------------------------------------------------------------
    # doctor_identity
    # ---------------------------------------------------------------------

    async def get_next_doctor_id(self) -> int:
        """Compute the next doctor_id as (max existing doctor_id + 1).

        Falls back to 1 when there are no rows yet.
        """
        stmt = select(func.max(DoctorIdentity.doctor_id))
        result = await self.session.execute(stmt)
        max_id = result.scalar()
        return (max_id or 0) + 1

    async def list_identities(
        self,
        *,
        status: OnboardingStatus | str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[DoctorIdentity]:
        """Return doctor_identity rows with optional status filter and pagination."""

        stmt = select(DoctorIdentity)
        
        if status is not None:
            status_enum = (
                status
                if isinstance(status, OnboardingStatus)
                else OnboardingStatus(status)
            )
            stmt = stmt.where(DoctorIdentity.onboarding_status == status_enum)
        
        stmt = stmt.offset(skip).limit(limit).order_by(DoctorIdentity.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_identities_by_status(
        self,
        status: OnboardingStatus | str | None = None,
    ) -> int:
        """Count doctor_identity rows with optional status filter."""
        
        stmt = select(func.count(DoctorIdentity.doctor_id))
        
        if status is not None:
            status_enum = (
                status
                if isinstance(status, OnboardingStatus)
                else OnboardingStatus(status)
            )
            stmt = stmt.where(DoctorIdentity.onboarding_status == status_enum)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create_identity(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        title: str | None = None,
        onboarding_status: OnboardingStatus | str = OnboardingStatus.PENDING,
        doctor_id: int | None = None,
        # Block 1
        full_name: str | None = None,
        specialty: str | None = None,
        primary_practice_location: str | None = None,
        centres_of_practice: list[str] | None = None,
        years_of_clinical_experience: int | None = None,
        years_post_specialisation: int | None = None,
        # Block 2
        year_of_mbbs: int | None = None,
        year_of_specialisation: int | None = None,
        fellowships: list[str] | None = None,
        qualifications: list[str] | None = None,
        professional_memberships: list[str] | None = None,
        awards_academic_honours: list[str] | None = None,
        # Block 3
        areas_of_clinical_interest: list[str] | None = None,
        practice_segments: str | None = None,
        conditions_commonly_treated: list[str] | None = None,
        conditions_known_for: list[str] | None = None,
        conditions_want_to_treat_more: list[str] | None = None,
        # Block 4
        training_experience: list[str] | None = None,
        motivation_in_practice: list[str] | None = None,
        unwinding_after_work: list[str] | None = None,
        recognition_identity: list[str] | None = None,
        quality_time_interests: list[str] | None = None,
        quality_time_interests_text: str | None = None,
        professional_achievement: str | None = None,
        personal_achievement: str | None = None,
        professional_aspiration: str | None = None,
        personal_aspiration: str | None = None,
        # Block 5
        what_patients_value_most: str | None = None,
        approach_to_care: str | None = None,
        availability_philosophy: str | None = None,
        # Block 6
        content_seeds: list[dict[str, Any]] | None = None,
    ) -> DoctorIdentity:
        """Create a new doctor_identity row.

        Returns the persisted identity with populated doctor_id.
        """
        status = (
            onboarding_status
            if isinstance(onboarding_status, OnboardingStatus)
            else OnboardingStatus(onboarding_status)
        )

        if doctor_id is None:
            doctor_id = await self.get_next_doctor_id()

        # Create DoctorIdentity with only its own fields
        identity = DoctorIdentity(
            doctor_id=doctor_id,
            title=title,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            onboarding_status=status,
        )
        self.session.add(identity)
        await self.session.commit()
        await self.session.refresh(identity)
        return identity

    async def get_identity_by_doctor_id(self, doctor_id: int) -> DoctorIdentity | None:
        """Fetch doctor_identity by numeric doctor_id."""
        stmt = select(DoctorIdentity).where(DoctorIdentity.doctor_id == doctor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_identity_by_email(self, email: str) -> DoctorIdentity | None:
        """Fetch doctor_identity by email."""
        stmt = select(DoctorIdentity).where(DoctorIdentity.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_identity_by_phone(self, phone_number: str) -> DoctorIdentity | None:
        """Fetch doctor_identity by phone_number."""

        stmt = select(DoctorIdentity).where(DoctorIdentity.phone_number == phone_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------------
    # Hard delete operations
    # ---------------------------------------------------------------------

    async def hard_delete_doctor(self, doctor_id: int) -> int:
        """Permanently delete onboarding data for a doctor.

        Deletes the doctor_identity row for the given doctor_id.
        Database-level cascading and ORM relationships ensure that
        related rows in doctor_details, doctor_media and
        doctor_status_history are removed as well.
        
        Returns the number of doctor_identity rows deleted (0 or 1).
        """

        identity = await self.get_identity_by_doctor_id(doctor_id)
        if not identity:
            return 0

        await self.session.delete(identity)
        await self.session.commit()
        return 1

    async def update_onboarding_status(
        self,
        *,
        doctor_id: int,
        new_status: OnboardingStatus | str,
        rejection_reason: str | None = None,
    ) -> DoctorIdentity | None:
        """Update onboarding_status (and optional rejection_reason) for a doctor.

        Returns the updated identity or None if not found.
        """
        identity = await self.get_identity_by_doctor_id(doctor_id)
        if not identity:
            return None

        status = (
            new_status
            if isinstance(new_status, OnboardingStatus)
            else OnboardingStatus(new_status)
        )

        identity.onboarding_status = status
        identity.rejection_reason = rejection_reason
        self.session.add(identity)
        await self.session.commit()
        await self.session.refresh(identity)
        return identity

    # ---------------------------------------------------------------------
    # doctor_details
    # ---------------------------------------------------------------------

    async def upsert_details(
        self,
        *,
        doctor_id: int,
        payload: dict,
    ) -> DoctorDetails:
        """Create or update doctor_details for a given doctor_id.

        `payload` should contain fields matching DoctorDetails columns
        (except detail_id and doctor_id, which are managed here).
        """
        details = await self.get_details_by_doctor_id(doctor_id)
        if details is None:
            details = DoctorDetails(doctor_id=doctor_id, **payload)
            self.session.add(details)
        else:
            for key, value in payload.items():
                if hasattr(details, key):
                    setattr(details, key, value)

        await self.session.commit()
        await self.session.refresh(details)
        return details

    async def get_details_by_doctor_id(self, doctor_id: int) -> DoctorDetails | None:
        """Fetch doctor_details by doctor_id."""
        stmt = select(DoctorDetails).where(DoctorDetails.doctor_id == doctor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------------
    # doctor_media
    # ---------------------------------------------------------------------

    async def add_media(
        self,
        *,
        doctor_id: int,
        media_type: str,
        media_category: str,
        file_uri: str,
        file_name: str,
        **extra,
    ) -> DoctorMedia:
        """Add a media record for a doctor and update media_urls.

        Keeps doctor_details.media_urls in sync by appending the new media_id
        under the appropriate field_name key when available.
        """

        field_name: str | None = extra.pop("field_name", None)
        effective_field_name = field_name or media_category

        # Special handling for profile_photo: overwrite existing record instead of
        # creating a new media_id so there is always at most one profile photo
        # per doctor.
        if effective_field_name == "profile_photo":
            stmt = select(DoctorMedia).where(
                DoctorMedia.doctor_id == doctor_id,
                DoctorMedia.field_name == effective_field_name,
            )
            result = await self.session.execute(stmt)
            existing_media = result.scalar_one_or_none()

            if existing_media is not None:
                # Update the existing media row in-place
                existing_media.media_type = media_type
                existing_media.media_category = media_category
                existing_media.file_uri = file_uri
                existing_media.file_name = file_name
                for key, value in extra.items():
                    if hasattr(existing_media, key) and value is not None:
                        setattr(existing_media, key, value)

                # Ensure doctor_details.media_urls points only to this media_id
                details = await self.get_details_by_doctor_id(doctor_id)
                if details is not None:
                    media_urls = dict(details.media_urls or {})
                    media_urls[effective_field_name] = existing_media.media_id
                    details.media_urls = media_urls
                    self.session.add(details)

                await self.session.commit()
                await self.session.refresh(existing_media)
                return existing_media

        # Default behaviour: create a new media row
        media = DoctorMedia(
            doctor_id=doctor_id,
            media_type=media_type,
            media_category=media_category,
            field_name=effective_field_name,
            file_uri=file_uri,
            file_name=file_name,
            **extra,
        )
        self.session.add(media)
        await self.session.flush()

        # Update doctor_details.media_urls to track media_ids by field_name
        if effective_field_name:
            details = await self.get_details_by_doctor_id(doctor_id)
            if details is not None:
                media_urls = dict(details.media_urls or {})
                current = media_urls.get(effective_field_name)
                media_id = media.media_id
                if isinstance(current, list):
                    if media_id not in current:
                        current.append(media_id)
                elif current:
                    # Preserve existing scalar by turning it into a list
                    values = [current]
                    if media_id not in values:
                        values.append(media_id)
                    current = values
                else:
                    current = [media_id]

                media_urls[effective_field_name] = current
                details.media_urls = media_urls
                self.session.add(details)

        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def list_media(self, doctor_id: int) -> Sequence[DoctorMedia]:
        """List all media records for a doctor."""
        stmt = select(DoctorMedia).where(DoctorMedia.doctor_id == doctor_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_media_by_doctor_id(self, doctor_id: int) -> Sequence[DoctorMedia]:
        """Get all media records for a doctor (alias for list_media)."""
        return await self.list_media(doctor_id)

    async def delete_media(self, media_id: str) -> bool:
        """Delete a media record by its media_id.

        Returns True if a row was deleted.
        """
        stmt = delete(DoctorMedia).where(DoctorMedia.media_id == media_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return (result.rowcount or 0) > 0

    # ---------------------------------------------------------------------
    # doctor_status_history
    # ---------------------------------------------------------------------

    async def log_status_change(
        self,
        *,
        doctor_id: int,
        previous_status: OnboardingStatus | str | None,
        new_status: OnboardingStatus | str,
        changed_by: str | None = None,
        changed_by_email: str | None = None,
        rejection_reason: str | None = None,
        notes: str | None = None,
    ) -> DoctorStatusHistory:
        """Insert a new row into doctor_status_history."""
        prev = (
            None
            if previous_status is None
            else previous_status
            if isinstance(previous_status, OnboardingStatus)
            else OnboardingStatus(previous_status)
        )
        new = (
            new_status
            if isinstance(new_status, OnboardingStatus)
            else OnboardingStatus(new_status)
        )

        history = DoctorStatusHistory(
            doctor_id=doctor_id,
            previous_status=prev,
            new_status=new,
            changed_by=changed_by,
            changed_by_email=changed_by_email,
            rejection_reason=rejection_reason,
            notes=notes,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def get_status_history(self, doctor_id: int) -> Sequence[DoctorStatusHistory]:
        """Get status history entries for a doctor, newest first."""
        stmt = (
            select(DoctorStatusHistory)
            .where(DoctorStatusHistory.doctor_id == doctor_id)
            .order_by(DoctorStatusHistory.changed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ---------------------------------------------------------------------
    # Dropdown/Autocomplete Data (for onboarding forms)
    # ---------------------------------------------------------------------

    async def _get_manual_dropdown_values(self, field_name: str) -> list[str]:
        """Return values stored in dropdown_options for a given field.

        Values are distinct and sorted for stable dropdown ordering.
        """

        stmt = (
            select(DropdownOption.value)
            .where(DropdownOption.field_name == field_name)
            .distinct()
            .order_by(DropdownOption.value)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def add_dropdown_values(
        self,
        *,
        field_name: str,
        values: Sequence[str],
    ) -> list[str]:
        """Add new values for a dropdown field and return the updated list.

        - Ignores empty/whitespace-only values.
        - Avoids inserting duplicates (by field_name + value).
        - Returns the full combined set of values for the field, including
          those derived from doctor_details and from dropdown_options.
        """

        cleaned_values = {
            v.strip()
            for v in values
            if isinstance(v, str) and v.strip()
        }

        if cleaned_values:
            # Fetch existing option values for this field to avoid duplicates
            stmt = select(DropdownOption.value).where(
                DropdownOption.field_name == field_name
            )
            result = await self.session.execute(stmt)
            existing_values = {row[0] for row in result.fetchall()}

            for value in cleaned_values:
                if value not in existing_values:
                    option = DropdownOption(field_name=field_name, value=value)
                    self.session.add(option)
                    existing_values.add(value)

            await self.session.commit()

        # Return combined values for the field after insertion
        if field_name == "specialisations":
            return await self.get_unique_specialities()
        if field_name == "sub_specialisations":
            return await self.get_unique_sub_specialities()
        if field_name == "degrees":
            return await self.get_unique_degrees()

        # For any other field, just return the manually stored values
        return await self._get_manual_dropdown_values(field_name)

    async def get_unique_specialities(self) -> list[str]:
        """Get all unique non-null speciality values for dropdowns.

        Combines values derived from doctor_details.speciality with any
        manually configured options stored in dropdown_options under
        field_name="specialisations".
        """

        # Values derived from existing doctor_details rows
        stmt = (
            select(DoctorDetails.speciality)
            .where(DoctorDetails.speciality.isnot(None))
            .where(DoctorDetails.speciality != "")
            .distinct()
        )
        result = await self.session.execute(stmt)
        derived_values = {row[0] for row in result.fetchall() if row[0]}

        # Manually configured values
        manual_values = set(await self._get_manual_dropdown_values("specialisations"))

        return sorted(derived_values | manual_values)

    async def get_unique_sub_specialities(self) -> list[str]:
        """Get all unique sub-speciality values for dropdowns.

        Combines values from doctor_details.sub_specialities arrays with
        manually configured options stored in dropdown_options under
        field_name="sub_specialisations".
        """

        # Get all non-empty sub_specialities arrays
        stmt = (
            select(DoctorDetails.sub_specialities)
            .where(DoctorDetails.sub_specialities.isnot(None))
        )
        result = await self.session.execute(stmt)

        # Flatten and deduplicate from doctor data
        derived_values: set[str] = set()
        for row in result.fetchall():
            sub_specs = row[0]
            if isinstance(sub_specs, list):
                for spec in sub_specs:
                    if spec and isinstance(spec, str) and spec.strip():
                        derived_values.add(spec.strip())

        manual_values = set(
            await self._get_manual_dropdown_values("sub_specialisations")
        )

        return sorted(derived_values | manual_values)

    async def get_unique_degrees(self) -> list[str]:
        """Get all unique degree values for dropdowns.

        Combines degree values derived from doctor_details.qualifications
        with manually configured options stored in dropdown_options under
        field_name="degrees".
        """

        # Get all qualifications arrays
        stmt = (
            select(DoctorDetails.qualifications)
            .where(DoctorDetails.qualifications.isnot(None))
        )
        result = await self.session.execute(stmt)

        # Extract degree from each qualification object
        derived_values: set[str] = set()
        for row in result.fetchall():
            qualifications = row[0]
            if isinstance(qualifications, list):
                for qual in qualifications:
                    if isinstance(qual, dict):
                        degree = (
                            qual.get("degree")
                            or qual.get("name")
                            or qual.get("title")
                        )
                        if degree and isinstance(degree, str) and degree.strip():
                            derived_values.add(degree.strip())

        manual_values = set(await self._get_manual_dropdown_values("degrees"))

        return sorted(derived_values | manual_values)
