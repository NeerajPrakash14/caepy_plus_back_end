"""Add voice_onboarding_fields table for configurable voice onboarding

Revision ID: 011_add_voice_onboarding_fields
Revises: 010_add_testimonials_table
Create Date: 2026-02-12

Creates configurable fields table for voice onboarding that matches
the doctor onboarding questionnaire blocks.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_add_voice_onboarding_fields'
down_revision = '010_add_testimonials_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create voice_onboarding_blocks table for block metadata
    op.create_table(
        'voice_onboarding_blocks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('block_number', sa.Integer(), nullable=False, unique=True),
        sa.Column('block_name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('ai_disclaimer', sa.Text(), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), default=0),
        sa.Column('completion_message', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create voice_onboarding_fields table for field configuration
    op.create_table(
        'voice_onboarding_fields',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('block_id', sa.Integer(), sa.ForeignKey('voice_onboarding_blocks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False),  # text, number, select, multi_select, year
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('validation_regex', sa.String(500), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('min_value', sa.Integer(), nullable=True),
        sa.Column('max_value', sa.Integer(), nullable=True),
        sa.Column('max_selections', sa.Integer(), nullable=True),  # For multi-select
        sa.Column('options', sa.JSON(), nullable=True),  # For select/multi-select fields
        sa.Column('ai_question', sa.Text(), nullable=True),  # AI question prompt
        sa.Column('ai_followup', sa.Text(), nullable=True),  # Follow-up question
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_voice_onboarding_blocks_block_number', 'voice_onboarding_blocks', ['block_number'])
    op.create_index('ix_voice_onboarding_blocks_is_active', 'voice_onboarding_blocks', ['is_active'])
    op.create_index('ix_voice_onboarding_fields_block_id', 'voice_onboarding_fields', ['block_id'])
    op.create_index('ix_voice_onboarding_fields_is_active', 'voice_onboarding_fields', ['is_active'])
    op.create_index('ix_voice_onboarding_fields_field_name', 'voice_onboarding_fields', ['field_name'])
    
    # Insert default blocks based on the questionnaire
    op.execute("""
        INSERT INTO voice_onboarding_blocks (block_number, block_name, display_name, ai_prompt, ai_disclaimer, completion_percentage, completion_message, is_active, display_order)
        VALUES 
        (0, 'warm_start', 'Warm Start & Expectation Setting', 
         'Welcome. This setup usually takes about 12–15 minutes. You can pause at any point and continue later. We''ll begin with a few quick details, and gradually move into areas where you can express your practice in your own way.',
         NULL, 0, NULL, true, 0),
        
        (1, 'professional_identity', 'Professional Identity', 
         'Let''s start with the basics. These help patients recognise you quickly and accurately.',
         NULL, 20, 'Profile strength: 20%', true, 1),
        
        (2, 'credentials_trust', 'Credentials & Trust Markers', 
         'This section highlights your training and professional milestones. You may keep this factual.',
         NULL, 40, 'Profile strength: 40% - Authority badge unlocked', true, 2),
        
        (3, 'clinical_focus', 'Clinical Focus & Expertise', 
         'This reflects what you actually practice, not just what you were trained in.',
         NULL, 60, 'Profile strength: 60%', true, 3),
        
        (4, 'human_side', 'The Human Side (Know Your Doctor)', 
         NULL,
         'There are no right or wrong answers here. This section is not evaluated or compared. Everything here can be edited later.',
         80, 'Profile strength: 80% - Human Touch added', true, 4),
        
        (5, 'patient_value', 'Patient Value & Choice Factors', 
         'If a patient had 30 seconds to understand your practice, what would you want them to know?',
         NULL, 90, 'Profile strength: 90%', true, 5),
        
        (6, 'content_seed', 'Content Seed (Optional)', 
         'Just answer as you would explain to a patient in your clinic. No need to write an article.',
         NULL, 95, 'First content seed created', true, 6),
        
        (7, 'completion', 'Completion & Handoff', 
         'Your onboarding is complete. You can edit or refine your profile anytime. Welcome to LinQMD.',
         NULL, 100, 'Profile complete', true, 7)
    """)
    
    # Insert default fields for each block
    # Block 1: Professional Identity
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, min_length, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'full_name', 'Full Name', 'text', true, 2, NULL, 'What is your full name as you would like it to appear on your profile?', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'specialty', 'Specialty', 'select', true, NULL, NULL, 'What is your primary medical specialty?', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'primary_practice_location', 'Primary Practice Location', 'text', true, 2, NULL, 'Which city is your primary practice location?', true, 3),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'centres_of_practice', 'Centres of Practice', 'multi_entry', true, NULL, NULL, 'What are the names of the hospitals or clinics where you practice?', true, 4),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'years_of_clinical_experience', 'Years of Clinical Experience', 'number', true, NULL, NULL, 'How many years of clinical experience do you have?', true, 5),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 1), 'years_post_specialisation', 'Years Post-Specialisation', 'number', false, NULL, NULL, 'How many years has it been since you completed your specialisation?', true, 6)
    """)
    
    # Block 2: Credentials & Trust Markers
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, min_value, max_value, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'year_of_mbbs', 'Year of MBBS', 'year', true, 1950, 2030, NULL, 'What year did you complete your MBBS?', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'year_of_specialisation', 'Year of Specialisation', 'year', false, 1950, 2030, NULL, 'What year did you complete your specialisation?', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'fellowships', 'Fellowships / Diplomas / Special Training', 'multi_entry', false, NULL, NULL, NULL, 'Do you have any fellowships, diplomas, or special training you would like to mention?', true, 3),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'qualifications', 'Qualifications', 'multi_entry', false, NULL, NULL, NULL, 'What are your educational qualifications?', true, 4),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'professional_memberships', 'Professional Memberships', 'multi_entry', false, NULL, NULL, NULL, 'Are you a member of any professional medical associations?', true, 5),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 2), 'awards_academic_honours', 'Awards / Academic Honours', 'multi_entry', false, NULL, NULL, NULL, 'Have you received any awards or academic honours?', true, 6)
    """)
    
    # Block 3: Clinical Focus & Expertise
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, max_selections, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 3), 'areas_of_clinical_interest', 'Areas of Clinical Interest', 'multi_select', false, NULL, NULL, 'What are your areas of clinical interest?', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 3), 'practice_segments', 'Practice Segments', 'select', false, NULL, '["OPD", "Surgical", "Academic", "Mixed"]', 'Would you describe your practice as primarily OPD, Surgical, Academic, or Mixed?', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 3), 'conditions_commonly_treated', 'Conditions Commonly Treated', 'multi_select', true, NULL, NULL, 'What conditions do you commonly treat in your practice?', true, 3),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 3), 'conditions_known_for', 'Conditions Known For', 'multi_select', true, NULL, NULL, 'What conditions are you particularly known for treating?', true, 4),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 3), 'conditions_want_to_treat_more', 'Conditions You Want to Treat More', 'multi_select', false, NULL, NULL, 'Are there any conditions you would like to treat more of?', true, 5)
    """)
    
    # Block 4: The Human Side
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, max_selections, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'training_experience', 'Training Experience', 'multi_select', false, 2, '["Demanding", "Exhaustive", "Challenging", "Stimulating", "Interesting", "Satisfying"]', 'How would you describe your training period? You can choose up to 2 options.', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'motivation_in_practice', 'Motivation in Practice', 'multi_select', false, 2, '["Helping patients", "Clinical challenges", "Professional growth", "Teaching / mentoring", "Recognition", "Work–life balance"]', 'What keeps you going in your practice? You can choose up to 2 options.', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'unwinding_after_work', 'Unwinding After Work', 'multi_select', false, NULL, '["Family time", "Music", "Reading", "Sports", "Meditation", "Academic work", "Movies / entertainment"]', 'How do you typically unwind after work?', true, 3),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'recognition_identity', 'Recognition & Identity', 'multi_select', false, NULL, '["Dedicated", "Knowledgeable", "Compassionate", "Calm", "Driven", "Innovative"]', 'How would you like to be recognised by your patients?', true, 4),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'quality_time_interests', 'Quality Time & Interests', 'multi_select', false, NULL, '["Travel", "Reading", "Academics / writing", "Arts / music", "Networking", "Entrepreneurship"]', 'How do you prefer to spend your quality time?', true, 5),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'quality_time_interests_text', 'Quality Time (Additional)', 'text', false, NULL, NULL, 'Would you like to add anything else about how you spend your quality time?', true, 6),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'professional_achievement', 'Professional Achievement', 'text', false, NULL, NULL, 'What is one professional achievement you are proud of?', true, 7),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'personal_achievement', 'Personal Achievement', 'text', false, NULL, NULL, 'What is one personal achievement outside of medicine that you are proud of?', true, 8),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'professional_aspiration', 'Professional Aspiration', 'text', false, NULL, NULL, 'What is your professional aspiration?', true, 9),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 4), 'personal_aspiration', 'Personal Aspiration', 'text', false, NULL, NULL, 'What is your personal aspiration?', true, 10)
    """)
    
    # Block 5: Patient Value & Choice Factors
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 5), 'what_patients_value_most', 'What Patients Value Most', 'text', false, NULL, 'What do you think patients value most about your practice?', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 5), 'approach_to_care', 'Approach to Care', 'text', false, NULL, 'How would you describe your approach to patient care?', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 5), 'availability_philosophy', 'Availability / Philosophy of Practice', 'text', false, NULL, 'What is your philosophy regarding availability and practice?', true, 3)
    """)
    
    # Block 6: Content Seed (stored as JSON in content_seeds field)
    op.execute("""
        INSERT INTO voice_onboarding_fields (block_id, field_name, display_name, field_type, is_required, options, ai_question, is_active, display_order)
        VALUES 
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_condition', 'Condition Name', 'text', false, NULL, 'What condition would you like to create content about?', true, 1),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_presentation', 'Typical Presentation', 'text', false, NULL, 'What is the typical presentation of this condition?', true, 2),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_investigations', 'Investigations', 'text', false, NULL, 'What investigations do you typically recommend?', true, 3),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_treatment', 'Treatment Options', 'text', false, NULL, 'What are the treatment options?', true, 4),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_consequences', 'Consequences of Delay', 'text', false, NULL, 'What are the consequences of delayed treatment?', true, 5),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_prevention', 'Prevention', 'text', false, NULL, 'How can this condition be prevented?', true, 6),
        ((SELECT id FROM voice_onboarding_blocks WHERE block_number = 6), 'content_seed_insights', 'Additional Insights', 'text', false, NULL, 'Any additional insights you would like to share?', true, 7)
    """)


def downgrade() -> None:
    op.drop_index('ix_voice_onboarding_fields_field_name', table_name='voice_onboarding_fields')
    op.drop_index('ix_voice_onboarding_fields_is_active', table_name='voice_onboarding_fields')
    op.drop_index('ix_voice_onboarding_fields_block_id', table_name='voice_onboarding_fields')
    op.drop_index('ix_voice_onboarding_blocks_is_active', table_name='voice_onboarding_blocks')
    op.drop_index('ix_voice_onboarding_blocks_block_number', table_name='voice_onboarding_blocks')
    op.drop_table('voice_onboarding_fields')
    op.drop_table('voice_onboarding_blocks')
