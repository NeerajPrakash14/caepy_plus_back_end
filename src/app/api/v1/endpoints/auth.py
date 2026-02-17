"""Authentication and OTP endpoints.

Provides simple OTP-based login flow for development:
- /validateandlogin: accepts phone_number and otp, validates them and returns a JWT token

NOTE: The legacy /generateotp endpoint has been removed in favor of the
fully featured /auth/otp/request implemented in the dedicated OTP router.
This module now only exposes the mock validate-and-login flow for
backwards compatibility with older clients.

SECURITY: The mock OTP endpoint is ONLY available in development mode.
In production, use the real OTP flow via /auth/otp/request and /auth/otp/verify.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated
import base64
import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ....core.config import Settings, get_settings
from ....core.exceptions import UnauthorizedError
from ....core.responses import GenericResponse
from ....db.session import get_db

router = APIRouter()


def _is_dev_environment() -> bool:
    """Check if we're running in development environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local", "testing", "test")

class GenerateOtpRequest(BaseModel):
    """Request body for OTP generation."""

    phone_number: str = Field(..., description="Phone number to send the OTP to")

class GenerateOtpPayload(BaseModel):
    """Payload returned when an OTP is generated (mocked)."""

    phone_number: str = Field(..., description="Phone number the OTP was 'sent' to")
    message: str = Field(..., description="Human readable description of the operation")

class ValidateAndLoginRequest(BaseModel):
    """Request body for OTP validation and login."""

    phone_number: str = Field(..., description="Phone number used for login")
    otp: str = Field(..., description="One-time password received by the user")

class TokenResponse(BaseModel):
    """JWT access token response payload."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    expires_in: int = Field(..., description="Token expiration time in seconds")

def _base64url_encode(data: bytes) -> str:
    """Encode bytes using base64 URL-safe encoding without padding."""

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _encode_jwt(payload: dict, *, secret: str, algorithm: str = "HS256") -> str:
    """Minimal HS256 JWT encoder using only standard library.

    This is intentionally simple and suitable for development/testing. For
    production, consider using a well-maintained JWT library.
    """

    if algorithm != "HS256":  # Only HS256 is supported in this helper
        raise ValueError("Only HS256 algorithm is supported in this implementation")

    header = {"alg": algorithm, "typ": "JWT"}

    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    encoded_header = _base64url_encode(header_json)
    encoded_payload = _base64url_encode(payload_json)

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def _create_access_token(
    *,
    subject: str,
    settings: Settings,
    doctor_id: int | None = None,
    email: str | None = None,
    role: str = "user",
) -> TokenResponse:
    """Create a signed JWT access token with user claims.

    Args:
        subject: Primary identifier (phone number)
        settings: Application settings
        doctor_id: Doctor's database ID (None for new users)
        email: Doctor's email address (None for new users)
        role: User role (admin, operational, user). Defaults to 'user'.
    
    Returns:
        TokenResponse with access_token, token_type, and expires_in
    """

    now = datetime.now(timezone.utc)
    expire_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + expire_delta

    to_encode = {
        "sub": subject,  # phone number
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "doctor_id": doctor_id,
        "phone": subject,
        "email": email,
        "role": role,
    }

    encoded_jwt = _encode_jwt(to_encode, secret=settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return TokenResponse(
        access_token=encoded_jwt,
        token_type="bearer",
        expires_in=int(expire_delta.total_seconds()),
    )


# Mock OTP code - ONLY used in development mode
_MOCK_OTP_CODE = "123456"


@router.post(
    "/validateandlogin",
    response_model=GenericResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate OTP and login (Development Only)",
    description=(
        "DEV ONLY: Accepts phone_number and otp from the request body, validates the OTP "
        "and, on success, returns a signed JWT access token. "
        "This endpoint is disabled in production. Use /auth/otp/verify instead."
    ),
)
async def validate_and_login(
    payload: ValidateAndLoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenericResponse[TokenResponse]:
    """Validate the provided OTP and issue a JWT token.

    SECURITY: This mock endpoint is ONLY available in development mode.
    In production, returns 403 Forbidden. Use /auth/otp/verify for production.
    """
    # Security check: Only allow in development
    if not _is_dev_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Mock OTP endpoint is disabled in production",
                "error_code": "PRODUCTION_DISABLED",
                "hint": "Use /auth/otp/request and /auth/otp/verify for production authentication"
            }
        )

    if payload.otp != _MOCK_OTP_CODE:
        raise UnauthorizedError(
            message="Invalid OTP provided",
            error_code="INVALID_OTP",
            details={"phone_number": payload.phone_number},
        )

    token = _create_access_token(subject=payload.phone_number, settings=settings)

    return GenericResponse[TokenResponse](
        message="Login successful",
        data=token,
    )


# =============================================================================
# ADMIN MIMIC LOGIN (DEV ONLY)
# =============================================================================

class AdminLoginRequest(BaseModel):
    """Request body for admin login mimic."""
    email: str | None = Field(None, description="Admin email address")
    phone: str | None = Field(None, description="Admin phone number")


class AdminLoginResponse(BaseModel):
    """Response for admin login mimic."""
    access_token: str
    token_type: str
    expires_in: int
    user: dict  # Simplified user object


@router.post(
    "/admin/login/mimic",
    response_model=GenericResponse[AdminLoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Mimic Admin Login (Development Only)",
    description=(
        "DEV ONLY: Login as an existing admin user by email or phone without OTP/Password. "
        "Strictly for development/testing to quickly switch to admin context."
    ),
)
async def mimic_admin_login(
    payload: AdminLoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[any, Depends(get_db)],
) -> GenericResponse[AdminLoginResponse]:
    """Mimic admin login - requires existing admin user."""
    from ....repositories.user_repository import UserRepository
    from ....models.enums import UserRole

    # Security check: Only allow in development
    if not _is_dev_environment():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Admin mimic endpoint is disabled in production",
                "error_code": "PRODUCTION_DISABLED",
            }
        )

    if not payload.email and not payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required",
        )

    repo = UserRepository(db)
    user = None

    if payload.email:
        user = await repo.get_by_email(payload.email)
    elif payload.phone:
        user = await repo.get_by_phone(payload.phone)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an admin",
        )

    # Generate real JWT with admin claims
    token_response = _create_access_token(
        subject=user.phone,
        settings=settings,
        doctor_id=user.doctor_id,
        email=user.email,
        role=user.role,
    )

    return GenericResponse[AdminLoginResponse](
        message="Admin login successful (mimic)",
        data=AdminLoginResponse(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            user={
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
            },
        ),
    )
