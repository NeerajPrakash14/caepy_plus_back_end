#!/usr/bin/env python3
# ============================================================
# DEV-ONLY LOCAL SCRIPT — DO NOT SHIP TO PRODUCTION
# ============================================================
# This file is intentionally excluded from the production image
# via .gitignore (see entry: setup_test_user.py).
#
# Purpose : Create or repair a test user record in the local DB.
# Audience: Local development only.
# Auth note: Production users are seeded via the Alembic migration
#            (SEED_ADMIN_PHONE / SEED_ADMIN_EMAIL env vars) or
#            created via POST /api/v1/auth/otp/verify.
#
# Usage:
#   DATABASE_URL=postgresql+asyncpg://... python setup_test_user.py [PHONE]
#
# Arguments:
#   PHONE  Phone number to create/check (default: +919999999999)
#          NOTE: +919999999999 is a local dev placeholder — never
#          use real patient/doctor numbers here.
# ============================================================
from __future__ import annotations

import asyncio
import os
import sys

# ----- Production guard: fail fast if accidentally run in prod -----
if os.environ.get("APP_ENV", "development").lower() == "production":
    print(
        "ERROR: setup_test_user.py must not run in production (APP_ENV=production).",
        file=sys.stderr,
    )
    sys.exit(1)
# -------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app.db.session import get_db_manager
from src.app.repositories.user_repository import UserRepository


async def main(phone: str = "+919999999999") -> None:
    db_manager = get_db_manager()
    async with db_manager.session() as db:
        repo = UserRepository(db)

        print(f"Checking user with phone {phone}...")
        user = await repo.get_by_phone(phone)

        if user:
            print(f"User found: ID={user.id}, Email={user.email}, Phone={user.phone}")
            if not user.email:
                print("Updating user email to 'dev@example.com'...")
                user.email = "dev@example.com"
                await db.commit()
                await db.refresh(user)
                print(f"User updated: Email={user.email}")
            else:
                print("User already has email.")
        else:
            print("User not found. Creating...")
            user = await repo.create(
                phone=phone,
                email="dev@example.com",
                role="admin",
                is_active=True,
            )
            print(f"User created: ID={user.id}")


if __name__ == "__main__":
    _phone = sys.argv[1] if len(sys.argv) > 1 else "+919999999999"
    asyncio.run(main(_phone))
