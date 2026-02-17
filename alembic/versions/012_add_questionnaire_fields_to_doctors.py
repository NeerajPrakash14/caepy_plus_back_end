"""Add questionnaire fields to doctors table

Revision ID: 012_add_questionnaire_fields_to_doctors
Revises: 011_add_voice_onboarding_fields
Create Date: 2026-02-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = "012_add_questionnaire_fields_to_doctors"
down_revision = "011_add_voice_onboarding_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add all questionnaire fields to doctors table."""
    
    # Block 1: Professional Identity
    op.add_column('doctors', sa.Column('full_name', sa.String(200), nullable=True))
    op.add_column('doctors', sa.Column('specialty', sa.String(200), nullable=True))
    op.add_column('doctors', sa.Column('primary_practice_location', sa.String(500), nullable=True))
    op.add_column('doctors', sa.Column('centres_of_practice', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('years_of_clinical_experience', sa.Integer(), nullable=True))
    op.add_column('doctors', sa.Column('years_post_specialisation', sa.Integer(), nullable=True))
    
    # Block 2: Credentials & Trust Markers
    op.add_column('doctors', sa.Column('year_of_mbbs', sa.Integer(), nullable=True))
    op.add_column('doctors', sa.Column('year_of_specialisation', sa.Integer(), nullable=True))
    op.add_column('doctors', sa.Column('fellowships', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('awards_academic_honours', JSON, nullable=True, server_default='[]'))
    
    # Block 3: Clinical Focus & Expertise
    op.add_column('doctors', sa.Column('areas_of_clinical_interest', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('practice_segments', sa.String(100), nullable=True))
    op.add_column('doctors', sa.Column('conditions_commonly_treated', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('conditions_known_for', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('conditions_want_to_treat_more', JSON, nullable=True, server_default='[]'))
    
    # Block 4: The Human Side
    op.add_column('doctors', sa.Column('training_experience', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('motivation_in_practice', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('unwinding_after_work', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('recognition_identity', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('quality_time_interests', JSON, nullable=True, server_default='[]'))
    op.add_column('doctors', sa.Column('quality_time_interests_text', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('professional_achievement', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('personal_achievement', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('professional_aspiration', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('personal_aspiration', sa.Text(), nullable=True))
    
    # Block 5: Patient Value & Choice Factors
    op.add_column('doctors', sa.Column('what_patients_value_most', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('approach_to_care', sa.Text(), nullable=True))
    op.add_column('doctors', sa.Column('availability_philosophy', sa.Text(), nullable=True))
    
    # Block 6: Content Seeds
    op.add_column('doctors', sa.Column('content_seeds', JSON, nullable=True, server_default='[]'))


def downgrade() -> None:
    """Remove questionnaire fields from doctors table."""
    
    # Block 6
    op.drop_column('doctors', 'content_seeds')
    
    # Block 5
    op.drop_column('doctors', 'availability_philosophy')
    op.drop_column('doctors', 'approach_to_care')
    op.drop_column('doctors', 'what_patients_value_most')
    
    # Block 4
    op.drop_column('doctors', 'personal_aspiration')
    op.drop_column('doctors', 'professional_aspiration')
    op.drop_column('doctors', 'personal_achievement')
    op.drop_column('doctors', 'professional_achievement')
    op.drop_column('doctors', 'quality_time_interests_text')
    op.drop_column('doctors', 'quality_time_interests')
    op.drop_column('doctors', 'recognition_identity')
    op.drop_column('doctors', 'unwinding_after_work')
    op.drop_column('doctors', 'motivation_in_practice')
    op.drop_column('doctors', 'training_experience')
    
    # Block 3
    op.drop_column('doctors', 'conditions_want_to_treat_more')
    op.drop_column('doctors', 'conditions_known_for')
    op.drop_column('doctors', 'conditions_commonly_treated')
    op.drop_column('doctors', 'practice_segments')
    op.drop_column('doctors', 'areas_of_clinical_interest')
    
    # Block 2
    op.drop_column('doctors', 'awards_academic_honours')
    op.drop_column('doctors', 'fellowships')
    op.drop_column('doctors', 'year_of_specialisation')
    op.drop_column('doctors', 'year_of_mbbs')
    
    # Block 1
    op.drop_column('doctors', 'years_post_specialisation')
    op.drop_column('doctors', 'years_of_clinical_experience')
    op.drop_column('doctors', 'centres_of_practice')
    op.drop_column('doctors', 'primary_practice_location')
    op.drop_column('doctors', 'specialty')
    op.drop_column('doctors', 'full_name')
