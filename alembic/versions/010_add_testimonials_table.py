"""Add testimonials table

Revision ID: 010_add_testimonials_table
Revises: 009_add_dropdown_options_table
Create Date: 2026-02-12

Creates the testimonials table for storing doctor comments
displayed on the homepage carousel.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_testimonials_table'
down_revision = '009_add_dropdown_options_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'testimonials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('doctor_name', sa.String(200), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('designation', sa.String(200), nullable=True),
        sa.Column('hospital_name', sa.String(200), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('profile_image_url', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create index for faster queries on active testimonials
    op.create_index('ix_testimonials_is_active', 'testimonials', ['is_active'])
    op.create_index('ix_testimonials_display_order', 'testimonials', ['display_order'])


def downgrade() -> None:
    op.drop_index('ix_testimonials_display_order', table_name='testimonials')
    op.drop_index('ix_testimonials_is_active', table_name='testimonials')
    op.drop_table('testimonials')
