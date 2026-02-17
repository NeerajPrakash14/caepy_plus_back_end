"""Make required fields nullable for new user registration.

Revision ID: 015_make_required_fields_nullable
Revises: 014_add_role_to_doctors
Create Date: 2026-02-14

When users register via OTP verification, they only provide their phone number.
We need to create a minimal doctor record and allow them to complete their
profile later. This migration makes previously required fields nullable.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015_make_required_fields_nullable"
down_revision = "014_add_role_to_doctors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make required fields nullable for new user registration flow."""
    # Make primary_specialization nullable
    op.alter_column(
        "doctors",
        "primary_specialization",
        existing_type=sa.Text(),
        nullable=True,
    )
    
    # Make medical_registration_number nullable
    op.alter_column(
        "doctors",
        "medical_registration_number",
        existing_type=sa.String(100),
        nullable=True,
    )


def downgrade() -> None:
    """Revert to required fields."""
    # Make primary_specialization required again
    op.alter_column(
        "doctors",
        "primary_specialization",
        existing_type=sa.Text(),
        nullable=False,
    )
    
    # Make medical_registration_number required again
    op.alter_column(
        "doctors",
        "medical_registration_number",
        existing_type=sa.String(100),
        nullable=False,
    )
