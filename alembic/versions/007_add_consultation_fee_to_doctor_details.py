"""Add consultation_fee to doctor_details

Revision ID: 007_add_consultation_fee_to_doctor_details
Revises: 006_remove_field_name_from_doctor_media
Create Date: 2026-01-18

This migration adds a nullable numeric consultation_fee column to doctor_details.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "007_add_consultation_fee_to_doctor_details"
down_revision = "006_remove_field_name_from_doctor_media"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add consultation_fee column to doctor_details."""
    op.add_column(
        "doctor_details",
        sa.Column("consultation_fee", sa.Numeric(10, 2), nullable=True),
    )

def downgrade() -> None:
    """Drop consultation_fee column from doctor_details."""
    op.drop_column("doctor_details", "consultation_fee")
