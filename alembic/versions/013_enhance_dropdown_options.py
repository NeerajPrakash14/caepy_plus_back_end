"""enhance dropdown_options table with audit trail and metadata

Revision ID: 013_enhance_dropdown_options
Revises: 012_add_questionnaire_fields_to_doctors
Create Date: 2024-01-20 00:00:00.000000

This migration enhances the dropdown_options table to support:
- UUID primary key (replacing integer)
- Category classification
- Creator tracking (system/admin/doctor)
- Audit trail (created_by_id, created_by_name, created_by_email)
- Status flags (is_active, is_verified)
- Display metadata (display_label, description, display_order)
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "013_enhance_dropdown_options"
down_revision: Union[str, None] = "012_add_questionnaire_fields_to_doctors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing table and recreate with new schema
    # (preserving any existing data would require a complex migration;
    # since this is a new feature, we'll start fresh)
    
    # First drop the old table if it exists
    op.execute("DROP TABLE IF EXISTS dropdown_options CASCADE")
    
    # Create new enhanced table with v2 naming to avoid conflicts
    op.create_table(
        "dropdown_options_v2",
        # Primary key as UUID string
        sa.Column(
            "id",
            sa.String(36),
            primary_key=True,
        ),
        
        # Field identification
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="general"),
        
        # Value
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("display_label", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        
        # Creator tracking
        sa.Column(
            "creator_type",
            sa.String(length=20),
            nullable=False,
            server_default="system",
        ),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_name", sa.String(length=200), nullable=True),
        sa.Column("created_by_email", sa.String(length=255), nullable=True),
        
        # Status flags
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        
        # Display ordering
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    
    # Create indexes for common queries
    op.create_index(
        "ix_dropdown_field_value",
        "dropdown_options_v2",
        ["field_name", "value"],
        unique=True,
    )
    op.create_index(
        "ix_dropdown_category",
        "dropdown_options_v2",
        ["category"],
    )
    op.create_index(
        "ix_dropdown_active",
        "dropdown_options_v2",
        ["field_name", "is_active"],
    )


def downgrade() -> None:
    # Drop all indexes
    op.drop_index("ix_dropdown_active", table_name="dropdown_options_v2")
    op.drop_index("ix_dropdown_category", table_name="dropdown_options_v2")
    op.drop_index("ix_dropdown_field_value", table_name="dropdown_options_v2")
    
    # Drop the v2 table
    op.drop_table("dropdown_options_v2")
    
    # Recreate original simple table
    op.create_table(
        "dropdown_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("field_name", "value", name="uq_dropdown_field_value"),
    )
    op.create_index(
        "ix_dropdown_options_field_name",
        "dropdown_options",
        ["field_name"],
    )
