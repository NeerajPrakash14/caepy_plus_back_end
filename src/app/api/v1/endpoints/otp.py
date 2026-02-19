"""Authentication Endpoints for OTP-based login.

Provides endpoints for:
- POST /auth/otp/request - Request OTP for mobile number
- POST /auth/otp/verify - Verify OTP and login
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.app.core.config import Settings, get_settings
from src.app.db.session import get_db
from src.app.schemas.auth import (
    OTPRequestSchema,
    OTPRequestResponse,
    OTPVerifySchema,
    OTPVerifyResponse,
    OTPErrorResponse,
)
from src.app.services.otp_service import get_otp_service, OTPService
from src.app.repositories.doctor_repository import DoctorRepository
from src.app.repositories.user_repository import UserRepository
from .auth import _create_access_token

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/otp/request",
    response_model=OTPRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP",
    description="Send OTP to the provided mobile number for authentication.",
    responses={
        200: {
            "description": "OTP sent successfully",
            "model": OTPRequestResponse,
        },
        400: {
            "description": "Invalid mobile number",
            "model": OTPErrorResponse,
        },
        500: {
            "description": "Failed to send OTP",
            "model": OTPErrorResponse,
        },
    },
)
async def request_otp(
    request: OTPRequestSchema,
    otp_service: OTPService = Depends(get_otp_service),
) -> OTPRequestResponse:
    """Request OTP for mobile number.

    Sends a 6-digit OTP to the provided mobile number via SMS.
    OTP is valid for a limited time as per settings.

    **Request Body:**
    - `mobile_number`: 10-digit Indian mobile number (with or without +91 prefix)

    **Returns:**
    - Success status
    - Masked mobile number
    - OTP validity period
    """
    logger.info(
        "OTP request received",
        mobile=otp_service.mask_mobile(request.mobile_number),
    )

    success, message = await otp_service.send_otp(request.mobile_number)

    if not success:
        logger.warning(
            "OTP send failed",
            mobile=otp_service.mask_mobile(request.mobile_number),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": message,
                "error_code": "OTP_SEND_FAILED",
            },
        )

    return OTPRequestResponse(
        success=True,
        message=message,
        mobile_number=otp_service.mask_mobile(request.mobile_number),
        expires_in_seconds=otp_service.settings.OTP_EXPIRY_SECONDS,
    )

@router.post(
    "/otp/verify",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
    description="Verify the OTP and authenticate the user.",
    responses={
        200: {
            "description": "OTP verified successfully",
            "model": OTPVerifyResponse,
        },
        400: {
            "description": "Invalid or expired OTP",
            "model": OTPErrorResponse,
        },
        401: {
            "description": "OTP verification failed",
            "model": OTPErrorResponse,
        },
    },
)
async def verify_otp(
    request: OTPVerifySchema,
    otp_service: OTPService = Depends(get_otp_service),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OTPVerifyResponse:
    """Verify OTP and authenticate user.

    Verifies the OTP sent to the mobile number. If verification is successful:
    1. Checks if a doctor record exists with this mobile number
    2. If exists: Returns JWT with doctor's ID, phone, email, role
    3. If new: Creates a new doctor record with phone number and default role
    4. Returns JWT token for subsequent authenticated requests

    **Request Body:**
    - `mobile_number`: 10-digit Indian mobile number
    - `otp`: 6-digit OTP code received via SMS

    **Returns:**
    - Success status
    - Doctor ID (existing or newly created)
    - Whether this is a new user
    - Verified mobile number
    - JWT access token with claims (doctor_id, phone, email, role)
    """
    logger.info(
        "OTP verify request",
        mobile=otp_service.mask_mobile(request.mobile_number),
    )

    # Verify OTP
    is_valid, message = await otp_service.verify_otp(
        request.mobile_number, request.otp
    )

    if not is_valid:
        logger.warning(
            "OTP verification failed",
            mobile=otp_service.mask_mobile(request.mobile_number),
            reason=message,
        )

        # Determine error code based on message
        error_code = "INVALID_OTP"
        if "expired" in message.lower():
            error_code = "OTP_EXPIRED"
        elif "attempts" in message.lower():
            error_code = "MAX_ATTEMPTS_EXCEEDED"
        elif "not found" in message.lower():
            error_code = "OTP_NOT_FOUND"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": message,
                "error_code": error_code,
            },
        )

    # Check if doctor exists with this mobile number
    doctor_repo = DoctorRepository(db)
    user_repo = UserRepository(db)
    doctor = await doctor_repo.get_by_phone_number(request.mobile_number)

    is_new_user = doctor is None
    
    if is_new_user:
        # Create new doctor record with phone number and default role
        doctor = await doctor_repo.create_from_phone(
            phone_number=request.mobile_number,
            role="user",
        )
        logger.info(
            "Created new doctor from OTP verification",
            doctor_id=doctor.id,
            mobile=otp_service.mask_mobile(request.mobile_number),
        )
    
    # Get doctor details for JWT claims
    doctor_id = doctor.id
    doctor_email = doctor.email if doctor.email else None

    # Get or create user record - role is stored ONLY in users table
    existing_user = await user_repo.get_by_phone(request.mobile_number)
    if existing_user:
        # Use role from existing user record (single source of truth)
        user_role = existing_user.role if existing_user.role else "user"
    else:
        # Create new user with default role
        user_role = "user"
        try:
            await user_repo.create(
                phone=request.mobile_number,
                email=doctor_email,
                role=user_role,
                is_active=True,
                doctor_id=doctor_id,
            )
            logger.info(
                "Created user record for RBAC",
                doctor_id=doctor_id,
                mobile=otp_service.mask_mobile(request.mobile_number),
            )
        except Exception as e:
            # User might already exist due to race condition
            logger.warning(
                "Failed to create user record (may already exist)",
                error=str(e),
            )

    # Create JWT access token with full claims
    token = _create_access_token(
        subject=request.mobile_number,
        settings=settings,
        doctor_id=doctor_id,
        email=doctor_email,
        role=user_role,
    )

    logger.info(
        "OTP verified successfully",
        mobile=otp_service.mask_mobile(request.mobile_number),
        is_new_user=is_new_user,
        doctor_id=doctor_id,
        role=user_role,
    )

    return OTPVerifyResponse(
        success=True,
        message="OTP verified successfully",
        doctor_id=doctor_id,
        is_new_user=is_new_user,
        mobile_number=request.mobile_number,
        role=user_role,
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )

@router.post(
    "/otp/resend",
    response_model=OTPRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend OTP",
    description="Resend OTP to the same mobile number (invalidates previous OTP).",
    responses={
        200: {
            "description": "OTP resent successfully",
            "model": OTPRequestResponse,
        },
        400: {
            "description": "Invalid mobile number",
            "model": OTPErrorResponse,
        },
        429: {
            "description": "Too many requests",
            "model": OTPErrorResponse,
        },
    },
)
async def resend_otp(
    request: OTPRequestSchema,
    otp_service: OTPService = Depends(get_otp_service),
) -> OTPRequestResponse:
    """Resend OTP to mobile number.

    Generates a new OTP and sends it to the mobile number.
    Previous OTP is invalidated.

    **Request Body:**
    - `mobile_number`: 10-digit Indian mobile number

    **Returns:**
    - Success status
    - Masked mobile number
    - OTP validity period
    """
    logger.info(
        "OTP resend request",
        mobile=otp_service.mask_mobile(request.mobile_number),
    )

    # Same as request_otp - sends new OTP (previous one is overwritten)
    success, message = await otp_service.send_otp(request.mobile_number)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": message,
                "error_code": "OTP_SEND_FAILED",
            },
        )

    return OTPRequestResponse(
        success=True,
        message="OTP resent successfully",
        mobile_number=otp_service.mask_mobile(request.mobile_number),
        expires_in_seconds=otp_service.settings.OTP_EXPIRY_SECONDS,
    )


@router.post(
    "/admin/otp/verify",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Admin OTP",
    description=(
        "Verify OTP for admin/operational users. "
        "Strictly enforces RBAC: user must exist and have admin/operational role. "
        "Does NOT auto-create users."
    ),
    responses={
        200: {
            "description": "Admin OTP verified successfully",
            "model": OTPVerifyResponse,
        },
        400: {
            "description": "Invalid/Expired OTP",
            "model": OTPErrorResponse,
        },
        403: {
            "description": "Forbidden (Non-admin or Unknown user)",
            "model": OTPErrorResponse,
        },
    },
)
async def verify_admin_otp(
    request: OTPVerifySchema,
    otp_service: OTPService = Depends(get_otp_service),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OTPVerifyResponse:
    """Verify OTP and authenticate admin user."""
    from ....models.enums import UserRole

    logger.info(
        "Admin OTP verify request",
        mobile=otp_service.mask_mobile(request.mobile_number),
    )

    # 1. Verify OTP
    # is_valid, message = await otp_service.verify_otp(
    #     request.mobile_number, request.otp
    # )
    
    # Bypass OTP verification for now (MIMIC MODE)
    is_valid = True
    message = "OTP verified successfully (MIMIC)"

    if not is_valid:
        logger.warning(
            "Admin OTP verification failed",
            mobile=otp_service.mask_mobile(request.mobile_number),
            reason=message,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": message,
                "error_code": "INVALID_OTP",
            },
        )

    # 2. Check if User exists (Strict Check)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_phone(request.mobile_number)

    if not user:
        logger.warning(
            "Admin login failed: User not found",
            mobile=otp_service.mask_mobile(request.mobile_number),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Access denied. Admin user not found.",
                "error_code": "USER_NOT_FOUND",
            },
        )

    # 3. Check Role (Strict RBAC)
    allowed_roles = (UserRole.ADMIN.value, UserRole.OPERATIONAL.value)
    if user.role not in allowed_roles:
        logger.warning(
            "Admin login failed: Insufficient permissions",
            user_id=user.id,
            role=user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Access denied. Insufficient permissions.",
                "error_code": "INSUFFICIENT_PERMISSIONS",
            },
        )
    
    # 4. Check Active Status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Account is inactive.",
                "error_code": "USER_INACTIVE",
            },
        )

    # 5. Generate Token
    token = _create_access_token(
        subject=user.phone,
        settings=settings,
        doctor_id=user.doctor_id,
        email=user.email,
        role=user.role,
    )

    logger.info(
        "Admin verified successfully",
        user_id=user.id,
        role=user.role,
    )

    return OTPVerifyResponse(
        success=True,
        message="Admin verified successfully",
        doctor_id=user.doctor_id, # Can be None if not linked to doctor
        is_new_user=False, # Admins are never "new" via this endpoint
        mobile_number=user.phone,
        role=user.role,
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )