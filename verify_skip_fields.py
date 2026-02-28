#!/usr/bin/env python3
# ============================================================
# DEV-ONLY LOCAL SCRIPT — DO NOT SHIP TO PRODUCTION
# ============================================================
# This file is intentionally excluded from the production image
# via .gitignore (see entry: verify_skip_fields.py).
#
# Purpose : Manual smoke-test for voice session field-skipping behaviour.
# Audience: Local development only — run against a local server + live DB.
#
# NOTE: The /validateandlogin endpoint referenced in older drafts of this
#       script has been removed. Authentication is now handled exclusively
#       via POST /api/v1/auth/otp/verify. Obtain a JWT from that endpoint
#       and pass it via the TOKEN env var below.
#
# NOTE: +919999999999 is a local dev placeholder only. Never substitute
#       real patient/doctor phone numbers here.
#
# Usage:
#   # 1. Start the server:       uvicorn src.app.main:app --reload
#   # 2. Set up a dev user:      python setup_test_user.py +919999999999
#   # 3. Get an OTP token first, then pass it here:
#   #        TOKEN=<jwt> python verify_skip_fields.py
# ============================================================
from __future__ import annotations

import json
import os
import sys

# ----- Production guard: fail fast if accidentally run in prod -----
if os.environ.get("APP_ENV", "development").lower() == "production":
    print(
        "ERROR: verify_skip_fields.py must not run in production (APP_ENV=production).",
        file=sys.stderr,
    )
    sys.exit(1)
# -------------------------------------------------------------------

import requests

BASE_URL = "http://localhost:8000/api/v1/voice"
AUTH_URL = "http://localhost:8000/api/v1/auth"

# Context for testing — must include email/phone to test field-skipping
context = {
    "fields": [
        {"key": "fullName",  "label": "Full Name",    "description": "Your name",         "required": True},
        {"key": "email",     "label": "Email",         "description": "Your email address", "required": True},
        {"key": "phone",     "label": "Phone Number",  "description": "Your phone number",  "required": True},
        {"key": "specialty", "label": "Specialty",     "description": "Your specialty",     "required": True},
    ]
}


def _get_token() -> str:
    """Return JWT from TOKEN env var or fail with clear instructions."""
    token = os.environ.get("TOKEN", "").strip()
    if not token:
        print(
            "ERROR: TOKEN env var not set.\n"
            "Obtain a token via POST /api/v1/auth/otp/verify, then:\n"
            "    TOKEN=<jwt> python verify_skip_fields.py",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def verify() -> None:
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Session
    print("Starting voice session with test context...")
    resp = requests.post(
        f"{BASE_URL}/start",
        json={"language": "en", "context": context},
        headers=headers,
    )
    if resp.status_code != 201:
        print(f"Start failed [{resp.status_code}]: {resp.text}", file=sys.stderr)
        sys.exit(1)

    session_id = resp.json()["session_id"]
    print(f"Session ID: {session_id}")

    # 2. Check initial field state
    status_resp = requests.get(f"{BASE_URL}/session/{session_id}", headers=headers)
    status_data = status_resp.json()

    fields_status = status_data["fields_status"]
    current_data = status_data["current_data"]
    print("\nCurrent Data:", json.dumps(current_data, indent=2))

    email_collected = any(f["field_name"] == "email" and f["is_collected"] for f in fields_status)
    phone_collected = any(f["field_name"] == "phone" and f["is_collected"] for f in fields_status)

    if phone_collected and not email_collected:
        print("PASS: Phone pre-collected, Email not yet collected.")
    else:
        print(f"FAIL: email_collected={email_collected}, phone_collected={phone_collected}", file=sys.stderr)
        sys.exit(1)

    # 3. Chat interaction
    print("\nSending: 'My name is Dr. Neeraj'")
    chat_resp = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "user_transcript": "My name is Dr. Neeraj", "context": context},
        headers=headers,
    )
    if chat_resp.status_code != 200:
        print(f"Chat error [{chat_resp.status_code}]: {chat_resp.text}", file=sys.stderr)
        sys.exit(1)

    ai_response = chat_resp.json()["ai_response"]
    print(f"AI Response: {ai_response}")

    if "email" in ai_response.lower():
        print("PASS: AI asked for email.")
    if "phone" in ai_response.lower():
        print("WARN: AI mentioned phone — check if it is asking or confirming.")

    print("\nSmoke test passed.")


if __name__ == "__main__":
    verify()
