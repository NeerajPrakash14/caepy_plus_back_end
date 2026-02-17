"""Add role field to doctors table.

Revision ID: 014_add_role_to_doctors
Revises: 013_enhance_dropdown_options
Create Date: 2026-02-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "014_add_role_to_doctors"
down_revision: Union[str, None] = "013_enhance_dropdown_options"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column to doctors table with default 'user'."""
    op.add_column(
        "doctors",
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="user",
            comment="User role: admin, operational, or user (default)",
        ),
    )
    
    # Add index for role-based queries
    op.create_index(
        "ix_doctors_role",
        "doctors",
        ["role"],
    )


def downgrade() -> None:
    """Remove role column from doctors table."""
    op.drop_index("ix_doctors_role", table_name="doctors")
    op.drop_column("doctors", "role")
