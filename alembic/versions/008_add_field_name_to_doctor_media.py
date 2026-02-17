"""Add field_name to doctor_media

Revision ID: 008_add_field_name_to_doctor_media
Revises: 007_add_consultation_fee_to_doctor_details
Create Date: 2026-01-18

This migration adds a nullable VARCHAR(100) field_name column to doctor_media
for tracking which logical field each media belongs to.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008_add_field_name_to_doctor_media"
down_revision = "007_add_consultation_fee_to_doctor_details"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add field_name column to doctor_media (if missing)."""
    op.add_column(
        "doctor_media",
        sa.Column("field_name", sa.String(length=100), nullable=True),
    )

def downgrade() -> None:
    """Drop field_name column from doctor_media."""
    op.drop_column("doctor_media", "field_name")
