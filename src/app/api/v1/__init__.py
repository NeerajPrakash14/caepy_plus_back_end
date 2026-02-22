"""API v1 package - Versioned API endpoints."""

from fastapi import APIRouter, Depends

from ...core.rbac import require_admin, require_admin_or_operational
from ...core.security import require_authentication
from .endpoints import (
	admin_dropdown,
	admin_users,
	auth,
	blobs,
	doctors,
	dropdown_data,
	health,
	hospitals,
	onboarding,
	onboarding_admin,
	otp,
	testimonials,
	voice,
	voice_config,
)

# Create versioned router
router = APIRouter(prefix="/api/v1")

# Include endpoint routers (order matters for Swagger display)

router.include_router(
	health.router,
	tags=["Health"],
)

# Testimonials - public endpoint for homepage carousel (no auth required)
router.include_router(
	testimonials.router,
	tags=["Testimonials"],
)

# Regular authenticated endpoints
router.include_router(
	onboarding.router,
	tags=["Onboarding"],
	dependencies=[Depends(require_authentication)],
)
router.include_router(
	dropdown_data.router,
	tags=["Dropdown Data"],
	dependencies=[Depends(require_authentication)],
)
router.include_router(
	voice.router,
	tags=["Voice Onboarding"],
	dependencies=[Depends(require_authentication)],
)
router.include_router(
	doctors.router,
	tags=["Doctors"],
	dependencies=[Depends(require_authentication)],
)
router.include_router(
	hospitals.router,
	tags=["Hospitals"],
	dependencies=[Depends(require_authentication)],
)
router.include_router(
	blobs.router,
	tags=["Blob Storage"],
	dependencies=[Depends(require_authentication)],
)

# =============================================================================
# ADMIN ENDPOINTS (Require admin or operational role)
# =============================================================================

# Onboarding Admin - admin endpoint for managing doctor onboarding
router.include_router(
	onboarding_admin.router,
	dependencies=[Depends(require_authentication)],
)

# Voice Config - admin endpoint for managing voice onboarding configuration
router.include_router(
	voice_config.router,
	tags=["Voice Config Admin"],
	dependencies=[Depends(require_admin_or_operational)],
)

# Admin Dropdown Options - manage dropdown/multi-select field values
router.include_router(
	admin_dropdown.router,
	tags=["Admin - Dropdown Options"],
	dependencies=[Depends(require_admin_or_operational)],
)

# Admin User Management - RBAC user administration (admin only)
router.include_router(
	admin_users.router,
	tags=["Admin - User Management"],
	# Note: RBAC is enforced at endpoint level via AdminUser dependency
)

# =============================================================================
# PUBLIC ENDPOINTS (No auth required)
# =============================================================================

# Auth/OTP endpoints remain publicly accessible so clients can obtain tokens
router.include_router(auth.router, tags=["Authentication"])
router.include_router(otp.router, tags=["Authentication"])

