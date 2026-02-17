"""Add missing columns to doctor_details table.

Revision ID: 017_add_missing_doctor_details_columns
Revises: 016_add_users_table
Create Date: 2026-02-14

This migration adds 30 missing columns to the doctor_details table
to match the DoctorDetails SQLAlchemy model in onboarding.py.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '017_add_missing_doctor_details_columns'
down_revision = '016_add_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Block 1: Professional Identity
    op.add_column('doctor_details', sa.Column('full_name', sa.String(200), nullable=True))
    op.add_column('doctor_details', sa.Column('specialty', sa.String(100), nullable=True))
    op.add_column('doctor_details', sa.Column('primary_practice_location', sa.String(100), nullable=True))
    op.add_column('doctor_details', sa.Column('centres_of_practice', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('years_of_clinical_experience', sa.Integer(), nullable=True))
    op.add_column('doctor_details', sa.Column('years_post_specialisation', sa.Integer(), nullable=True))

    # Block 2: Credentials & Trust Markers
    op.add_column('doctor_details', sa.Column('year_of_mbbs', sa.Integer(), nullable=True))
    op.add_column('doctor_details', sa.Column('year_of_specialisation', sa.Integer(), nullable=True))
    op.add_column('doctor_details', sa.Column('fellowships', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('awards_academic_honours', JSON, nullable=False, server_default='[]'))

    # Block 3: Clinical Focus & Expertise
    op.add_column('doctor_details', sa.Column('areas_of_clinical_interest', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('practice_segments', sa.String(50), nullable=True))
    op.add_column('doctor_details', sa.Column('conditions_commonly_treated', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('conditions_known_for', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('conditions_want_to_treat_more', JSON, nullable=False, server_default='[]'))

    # Block 4: The Human Side
    op.add_column('doctor_details', sa.Column('training_experience', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('motivation_in_practice', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('unwinding_after_work', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('recognition_identity', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('quality_time_interests', JSON, nullable=False, server_default='[]'))
    op.add_column('doctor_details', sa.Column('quality_time_interests_text', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('professional_achievement', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('personal_achievement', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('professional_aspiration', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('personal_aspiration', sa.Text(), nullable=True))

    # Block 5: Patient Value & Choice Factors
    op.add_column('doctor_details', sa.Column('what_patients_value_most', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('approach_to_care', sa.Text(), nullable=True))
    op.add_column('doctor_details', sa.Column('availability_philosophy', sa.Text(), nullable=True))

    # Block 6: Content Seed
    op.add_column('doctor_details', sa.Column('content_seeds', JSON, nullable=False, server_default='[]'))

    # Additional field
    op.add_column('doctor_details', sa.Column('consultation_fee', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove all added columns in reverse order
    op.drop_column('doctor_details', 'consultation_fee')
    op.drop_column('doctor_details', 'content_seeds')
    op.drop_column('doctor_details', 'availability_philosophy')
    op.drop_column('doctor_details', 'approach_to_care')
    op.drop_column('doctor_details', 'what_patients_value_most')
    op.drop_column('doctor_details', 'personal_aspiration')
    op.drop_column('doctor_details', 'professional_aspiration')
    op.drop_column('doctor_details', 'personal_achievement')
    op.drop_column('doctor_details', 'professional_achievement')
    op.drop_column('doctor_details', 'quality_time_interests_text')
    op.drop_column('doctor_details', 'quality_time_interests')
    op.drop_column('doctor_details', 'recognition_identity')
    op.drop_column('doctor_details', 'unwinding_after_work')
    op.drop_column('doctor_details', 'motivation_in_practice')
    op.drop_column('doctor_details', 'training_experience')
    op.drop_column('doctor_details', 'conditions_want_to_treat_more')
    op.drop_column('doctor_details', 'conditions_known_for')
    op.drop_column('doctor_details', 'conditions_commonly_treated')
    op.drop_column('doctor_details', 'practice_segments')
    op.drop_column('doctor_details', 'areas_of_clinical_interest')
    op.drop_column('doctor_details', 'awards_academic_honours')
    op.drop_column('doctor_details', 'fellowships')
    op.drop_column('doctor_details', 'year_of_specialisation')
    op.drop_column('doctor_details', 'year_of_mbbs')
    op.drop_column('doctor_details', 'years_post_specialisation')
    op.drop_column('doctor_details', 'years_of_clinical_experience')
    op.drop_column('doctor_details', 'centres_of_practice')
    op.drop_column('doctor_details', 'primary_practice_location')
    op.drop_column('doctor_details', 'specialty')
    op.drop_column('doctor_details', 'full_name')
