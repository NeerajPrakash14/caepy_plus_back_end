"""Firebase token verification for Google Sign-In.

Provides verify_firebase_token() which verifies Firebase ID tokens.
Uses firebase-admin SDK with a fallback to Google's public token verification
endpoint for local development without a service account.
"""

import os
import firebase_admin
from firebase_admin import auth as firebase_auth
import httpx
import structlog

logger = structlog.get_logger(__name__)

FIREBASE_PROJECT_ID = "hospitalappointment-booking"

# Set project ID env var for firebase-admin
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", FIREBASE_PROJECT_ID)

_firebase_app = None


def _init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
        try:
            _firebase_app = firebase_admin.initialize_app(
                options={"projectId": FIREBASE_PROJECT_ID}
            )
            logger.info("Firebase Admin initialized", project_id=FIREBASE_PROJECT_ID)
        except ValueError:
            _firebase_app = firebase_admin.get_app()
            logger.info("Firebase Admin already initialized")


def _verify_via_google_api(id_token: str) -> dict:
    """Verify Firebase ID token via Google's public API (fallback).
    
    This calls Google's secure token verification endpoint which
    doesn't require a service account — ideal for local development.
    """
    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key=AIzaSyDVHfAHIom36kPAuyx0ohqPxfLoR3YB5Vo"

    # First, verify the token with Google's secure token verifier
    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=AIzaSyDVHfAHIom36kPAuyx0ohqPxfLoR3YB5Vo"
    
    response = httpx.post(
        verify_url,
        json={"idToken": id_token},
        timeout=10.0,
    )
    
    if response.status_code != 200:
        error_msg = response.json().get("error", {}).get("message", "Unknown error")
        raise ValueError(f"Google token verification failed: {error_msg}")
    
    data = response.json()
    users = data.get("users", [])
    
    if not users:
        raise ValueError("No user found for this token")
    
    user_info = users[0]
    
    # Build a decoded token dict matching firebase-admin's format
    return {
        "uid": user_info.get("localId", ""),
        "email": user_info.get("email", ""),
        "name": user_info.get("displayName", ""),
        "email_verified": user_info.get("emailVerified", False),
        "picture": user_info.get("photoUrl", ""),
    }


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims.

    Attempts firebase-admin SDK first, falls back to Google's public API.

    Args:
        id_token: The Firebase ID token string from the frontend.

    Returns:
        dict with keys like 'uid', 'email', 'name', 'email_verified', etc.

    Raises:
        ValueError: If the token is invalid or expired.
    """
    # Try firebase-admin SDK first
    _init_firebase()
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        logger.info(
            "Firebase token verified (SDK)",
            uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
        )
        return decoded_token
    except Exception as sdk_error:
        logger.warning(
            "Firebase SDK verification failed, trying Google API fallback",
            error=str(sdk_error),
        )

    # Fallback: verify via Google's public API
    try:
        decoded_token = _verify_via_google_api(id_token)
        logger.info(
            "Firebase token verified (Google API)",
            uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
        )
        return decoded_token
    except Exception as api_error:
        logger.error("All token verification methods failed", error=str(api_error))
        raise ValueError(f"Firebase token verification failed: {api_error}")
