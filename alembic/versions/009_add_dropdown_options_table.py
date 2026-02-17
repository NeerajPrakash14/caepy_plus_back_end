"""add dropdown_options table

Revision ID: 009_add_dropdown_options_table
Revises: 008_add_field_name_to_doctor_media
Create Date: 2026-01-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009_add_dropdown_options_table"
down_revision: Union[str, None] = "008_add_field_name_to_doctor_media"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:

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

def downgrade() -> None:

    op.drop_index("ix_dropdown_options_field_name", table_name="dropdown_options")
    op.drop_table("dropdown_options")
