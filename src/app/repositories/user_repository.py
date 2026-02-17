"""
User Repository - Data access layer for RBAC users.

Provides methods for:
- Creating and managing users
- Looking up users by phone/email
- Role and status management
- Linking users to doctors
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.enums import UserRole

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User CRUD operations."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self.session = session
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone: str) -> User | None:
        """Get user by phone number (normalized with +91 prefix)."""
        normalized = self._normalize_phone(phone)
        query = select(User).where(User.phone == normalized)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        query = select(User).where(User.email == email.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_by_phone(self, phone: str) -> User | None:
        """Get active user by phone number."""
        normalized = self._normalize_phone(phone)
        query = select(User).where(
            and_(
                User.phone == normalized,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> Sequence[User]:
        """Get all users with optional filtering."""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_admins(self, active_only: bool = True) -> Sequence[User]:
        """Get all admin users."""
        query = select(User).where(User.role == UserRole.ADMIN.value)
        if active_only:
            query = query.where(User.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================
    
    async def create(
        self,
        phone: str,
        email: str | None = None,
        role: str = UserRole.USER.value,
        is_active: bool = True,
        doctor_id: int | None = None,
    ) -> User:
        """Create a new user."""
        normalized_phone = self._normalize_phone(phone)
        
        user = User(
            phone=normalized_phone,
            email=email.lower() if email else None,
            role=role,
            is_active=is_active,
            doctor_id=doctor_id,
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(f"Created user: id={user.id}, phone={normalized_phone}, role={role}")
        return user
    
    async def create_from_doctor(
        self,
        doctor_id: int,
        phone: str,
        email: str | None = None,
        role: str = UserRole.USER.value,
    ) -> User:
        """Create a user linked to an existing doctor."""
        return await self.create(
            phone=phone,
            email=email,
            role=role,
            is_active=True,
            doctor_id=doctor_id,
        )
    
    async def get_or_create(
        self,
        phone: str,
        email: str | None = None,
        doctor_id: int | None = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        
        Returns:
            Tuple of (user, is_new) where is_new is True if created
        """
        existing = await self.get_by_phone(phone)
        if existing:
            return existing, False
        
        new_user = await self.create(
            phone=phone,
            email=email,
            role=UserRole.USER.value,
            is_active=True,
            doctor_id=doctor_id,
        )
        return new_user, True
    
    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================
    
    async def update_role(self, user_id: int, role: str) -> User | None:
        """Update user's role."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        old_role = user.role
        user.role = role
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(f"Updated user role: id={user_id}, {old_role} -> {role}")
        return user
    
    async def set_active(self, user_id: int, is_active: bool) -> User | None:
        """Activate or deactivate a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        
        status = "activated" if is_active else "deactivated"
        logger.info(f"User {status}: id={user_id}")
        return user
    
    async def deactivate(self, user_id: int) -> User | None:
        """Deactivate a user (soft delete)."""
        return await self.set_active(user_id, False)
    
    async def activate(self, user_id: int) -> User | None:
        """Activate a user."""
        return await self.set_active(user_id, True)
    
    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def link_doctor(self, user_id: int, doctor_id: int) -> User | None:
        """Link a user to a doctor record."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.doctor_id = doctor_id
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(f"Linked user {user_id} to doctor {doctor_id}")
        return user
    
    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================
    
    async def delete(self, user_id: int) -> bool:
        """Hard delete a user (use deactivate for soft delete)."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        
        logger.info(f"Deleted user: id={user_id}")
        return True
    
    # =========================================================================
    # AUTHORIZATION HELPERS
    # =========================================================================
    
    async def is_admin(self, phone: str) -> bool:
        """Check if user with phone is an active admin."""
        user = await self.get_active_by_phone(phone)
        return user is not None and user.role == UserRole.ADMIN.value
    
    async def can_access_admin(self, phone: str) -> bool:
        """Check if user can access admin endpoints (admin or operational)."""
        user = await self.get_active_by_phone(phone)
        if not user:
            return False
        return user.role in (UserRole.ADMIN.value, UserRole.OPERATIONAL.value)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format."""
        normalized = phone.strip()
        if not normalized:
            return normalized
        
        # Extract only digits
        digits_only = ''.join(c for c in normalized if c.isdigit())
        
        # Handle different input formats
        if digits_only.startswith('91') and len(digits_only) == 12:
            # Already has country code
            return '+' + digits_only
        else:
            # Add +91 for Indian numbers
            return '+91' + digits_only
