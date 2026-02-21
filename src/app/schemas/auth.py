"""Authentication Schemas for OTP-based login.

Defines request/response models for:
- OTP request (send OTP to mobile)
- OTP verification (verify OTP and login)
"""

from typing import Optional

import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

class OTPRequestSchema(BaseModel):
    """Request schema for sending OTP to mobile number."""

    mobile_number: str = Field(
        ...,
        description="10-digit Indian mobile number",
        examples=["9876543210"],
    )

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        """Validate Indian mobile number format."""
        # Remove any spaces, dashes, or country code prefix
        cleaned = re.sub(r"[\s\-]", "", v)

        # Remove +91 or 91 prefix if present
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = cleaned[2:]

        # Validate 10-digit number starting with 6-9
        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError(
                "Invalid mobile number. Must be a 10-digit Indian mobile number starting with 6-9"
            )

        return cleaned

class OTPRequestResponse(BaseModel):
    """Response schema after OTP is sent."""

    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Status message")
    mobile_number: str = Field(..., description="Mobile number OTP was sent to (masked)")
    expires_in_seconds: int = Field(
        default=300,
        description="OTP validity period in seconds",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "message": "OTP sent successfully",
            "mobile_number": "98****3210",
            "expires_in_seconds": 300,
        }
    })

class OTPVerifySchema(BaseModel):
    """Request schema for verifying OTP."""

    mobile_number: str = Field(
        ...,
        description="10-digit Indian mobile number",
        examples=["9876543210"],
    )
    otp: str = Field(
        ...,
        min_length=4,
        max_length=6,
        description="OTP code received via SMS",
        examples=["123456"],
    )

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        """Validate Indian mobile number format."""
        cleaned = re.sub(r"[\s\-]", "", v)

        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = cleaned[2:]

        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError(
                "Invalid mobile number. Must be a 10-digit Indian mobile number starting with 6-9"
            )

        return cleaned

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validate OTP format."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v

class OTPVerifyResponse(BaseModel):
    """Response schema after OTP verification."""

    success: bool = Field(..., description="Whether verification was successful")
    message: str = Field(..., description="Status message")
    doctor_id: Optional[int] = Field(
        default=None,
        description="Doctor ID (existing or newly created)",
    )
    is_new_user: bool = Field(
        default=True,
        description="Whether this is a new user (first time login)",
    )
    mobile_number: str = Field(..., description="Verified mobile number")
    role: Optional[str] = Field(
        default="user",
        description="User role: admin, operational, or user",
    )

    access_token: Optional[str] = Field(
        default=None,
        description="JWT access token with claims (doctor_id, phone, email, role)",
    )
    token_type: Optional[str] = Field(
        default="bearer",
        description="Token type, typically 'bearer'",
    )
    expires_in: Optional[int] = Field(
        default=None,
        description="Token expiration time in seconds",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "message": "OTP verified successfully",
            "doctor_id": 123,
            "is_new_user": False,
            "mobile_number": "9876543210",
            "role": "user",
            "access_token": "<jwt-token-with-claims>",
            "token_type": "bearer",
            "expires_in": 1800,
        }
    })

class OTPErrorResponse(BaseModel):
    """Error response for OTP operations."""

    success: bool = Field(default=False)
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(
        default=None,
        description="Error code for client handling",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": False,
            "message": "Invalid OTP",
            "error_code": "INVALID_OTP",
        }
    })


class GoogleAuthSchema(BaseModel):
    """Request schema for Google Sign-In authentication."""

    id_token: str = Field(
        ...,
        description="Firebase ID token from Google Sign-In popup",
    )