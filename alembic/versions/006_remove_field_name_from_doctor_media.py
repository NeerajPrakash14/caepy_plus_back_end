"""Remove field_name from doctor_media

Revision ID: 006_remove_field_name_from_doctor_media
Revises: 005_add_hospitals_table
Create Date: 2026-01-18

This migration drops the deprecated field_name column from doctor_media.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006_remove_field_name_from_doctor_media"
down_revision = "005_add_hospitals_table"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Drop field_name column from doctor_media if it exists."""
    op.execute("ALTER TABLE doctor_media DROP COLUMN IF EXISTS field_name;")

def downgrade() -> None:
    """Recreate field_name column on doctor_media (best-effort)."""
    op.add_column(
        "doctor_media",
        sa.Column("field_name", sa.String(length=100), nullable=True),
    )
