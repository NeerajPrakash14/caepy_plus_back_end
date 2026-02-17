"""
RBAC (Role-Based Access Control) Dependencies.

FastAPI dependencies for protecting endpoints based on user roles.

Usage:
    @router.get("/admin/endpoint")
    async def admin_endpoint(
        current_user: Annotated[User, Depends(require_admin)],
    ):
        # Only admins can access this endpoint
        ...
        
    @router.get("/operational/endpoint")
    async def operational_endpoint(
        current_user: Annotated[User, Depends(require_admin_or_operational)],
    ):
        # Admins and operational users can access
        ...
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .exceptions import UnauthorizedError, ForbiddenError
from .security import _decode_jwt
from ..db.session import get_db
from ..models.user import User
from ..models.enums import UserRole
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This dependency:
    1. Extracts and validates the JWT from Authorization header
    2. Looks up the user in the users table by phone
    3. Verifies the user is active
    
    Raises:
        UnauthorizedError: If token is missing, invalid, or expired
        UnauthorizedError: If user not found in database
        ForbiddenError: If user is inactive
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise UnauthorizedError(
            message="Missing or invalid Authorization header",
            error_code="UNAUTHORIZED",
        )
    
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise UnauthorizedError(
            message="Missing access token",
            error_code="UNAUTHORIZED",
        )
    
    # Decode and validate JWT
    payload = _decode_jwt(token, settings=settings)
    
    # Get phone from JWT (sub claim)
    phone = payload.get("sub")
    if not isinstance(phone, str) or not phone:
        raise UnauthorizedError(
            message="Invalid token subject",
            error_code="INVALID_TOKEN",
        )
    
    # Look up user in database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_phone(phone)
    
    if not user:
        # User not in users table - they may have authenticated via OTP
        # but not been added to users table yet
        logger.warning(f"User not found in users table: phone={phone[:4]}****")
        raise UnauthorizedError(
            message="User not found. Please contact administrator.",
            error_code="USER_NOT_FOUND",
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: user_id={user.id}")
        raise ForbiddenError(
            message="Your account has been deactivated. Please contact administrator.",
            error_code="USER_INACTIVE",
        )
    
    return user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require the current user to be an active admin.
    
    Use this dependency on admin-only endpoints.
    
    Raises:
        ForbiddenError: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN.value:
        logger.warning(
            f"Non-admin user attempted admin access: user_id={current_user.id}, role={current_user.role}"
        )
        raise ForbiddenError(
            message="Admin access required",
            error_code="ADMIN_REQUIRED",
        )
    
    return current_user


async def require_admin_or_operational(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require the current user to be an admin or operational user.
    
    Use this dependency on endpoints that operational staff can access.
    
    Raises:
        ForbiddenError: If user is neither admin nor operational
    """
    allowed_roles = (UserRole.ADMIN.value, UserRole.OPERATIONAL.value)
    
    if current_user.role not in allowed_roles:
        logger.warning(
            f"Unauthorized role attempted access: user_id={current_user.id}, role={current_user.role}"
        )
        raise ForbiddenError(
            message="Admin or operational access required",
            error_code="INSUFFICIENT_PERMISSIONS",
        )
    
    return current_user


async def require_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Require any active authenticated user.
    
    This is essentially the same as get_current_user but makes
    the intent clearer in endpoint signatures.
    """
    return current_user


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
AdminOrOperationalUser = Annotated[User, Depends(require_admin_or_operational)]
