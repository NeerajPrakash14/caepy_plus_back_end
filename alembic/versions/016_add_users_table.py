"""Add users table for RBAC.

Revision ID: 016_add_users_table
Revises: 015_make_required_fields_nullable
Create Date: 2026-02-14

This migration creates the users table for Role-Based Access Control (RBAC).
The users table is separate from doctors to allow:
- Admin staff who are not doctors
- Operational staff with limited access
- Regular users (doctors) with standard access

Features:
- Role-based access: admin, operational, user
- Soft delete via is_active flag
- Optional link to doctor record
- Phone as primary identifier (matches JWT sub)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "016_add_users_table"
down_revision = "015_make_required_fields_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table with RBAC fields."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "phone",
            sa.String(20),
            nullable=False,
            comment="Phone number with country code (e.g., +919988776655)",
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=True,
            comment="Optional email address",
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="user",
            comment="User role: admin, operational, user",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Active status - inactive users cannot authenticate",
        ),
        sa.Column(
            "doctor_id",
            sa.Integer(),
            sa.ForeignKey("doctors.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional link to doctor record",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last successful authentication timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create indexes
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_doctor_id", "users", ["doctor_id"])
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])
    op.create_index("ix_users_phone_active", "users", ["phone", "is_active"])


def downgrade() -> None:
    """Drop users table."""
    op.drop_index("ix_users_phone_active", table_name="users")
    op.drop_index("ix_users_role_active", table_name="users")
    op.drop_index("ix_users_doctor_id", table_name="users")
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
