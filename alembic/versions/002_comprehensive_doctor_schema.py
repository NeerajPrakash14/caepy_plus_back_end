"""Comprehensive doctor schema with all fields and correct data types

Revision ID: 002_comprehensive_doctor_schema
Revises: 001
Create Date: 2026-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_comprehensive_doctor_schema'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Apply comprehensive schema changes."""
    
    # Drop qualifications table if it exists (moving to single table design)
    op.execute("""
        DROP TABLE IF EXISTS qualifications CASCADE;
    """)
    
    # Modify existing columns to correct data types
    # Note: Some of these might already exist from previous migration
    
    # Update string field lengths
    with op.batch_alter_table('doctors', schema=None) as batch_op:
        # Resize varchar fields to 100
        batch_op.alter_column('email',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=False)
        
        batch_op.alter_column('first_name',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=False)
        
        batch_op.alter_column('last_name',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=False)
        
        batch_op.alter_column('gender',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=True)
        
        batch_op.alter_column('registration_number',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=True)
        
        batch_op.alter_column('registration_authority',
                              existing_type=sa.String(255),
                              type_=sa.String(100),
                              existing_nullable=True)
        
        # Change primary_specialization to Text
        batch_op.alter_column('primary_specialization',
                              existing_type=sa.String(200),
                              type_=sa.Text(),
                              existing_nullable=True)
        
        # Change phone from String to Integer (if it exists as string)
        # First, need to check if column exists and its type
        # Assuming it might be varchar, we'll drop and recreate
        try:
            batch_op.drop_column('phone_number')
        except:
            pass  # Column might not exist
        
        # Add phone as Integer
        batch_op.add_column(sa.Column('phone', sa.Integer(), nullable=True))
        
        # Add Blob fields (LargeBinary)
        batch_op.add_column(sa.Column('profile_photo', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('verbal_intro_file', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('professional_documents', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('achievement_images', sa.LargeBinary(), nullable=True))
        
        # Add/modify JSON fields for complex structures
        batch_op.add_column(sa.Column('qualifications', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('achievements', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('publications', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('practice_locations', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        # Update external_links to JSON object (was JSON array)
        batch_op.alter_column('external_links',
                              existing_type=sa.JSON(),
                              type_=postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                              existing_nullable=True)
        
        # Add Array fields (stored as JSON arrays)
        batch_op.add_column(sa.Column('sub_specialties', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('areas_of_expertise', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('conditions_treated', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('procedures_performed', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('age_groups_treated', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('professional_memberships', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        batch_op.add_column(sa.Column('languages', 
                                      postgresql.JSONB(astext_type=sa.Text()) if op.get_bind().dialect.name == 'postgresql' else sa.JSON(),
                                      nullable=True))
        
        # Add Integer fields
        batch_op.add_column(sa.Column('registration_year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('years_of_experience', sa.Integer(), nullable=True))

def downgrade() -> None:
    """Revert comprehensive schema changes."""
    
    with op.batch_alter_table('doctors', schema=None) as batch_op:
        # Remove added columns
        batch_op.drop_column('years_of_experience')
        batch_op.drop_column('registration_year')
        batch_op.drop_column('languages')
        batch_op.drop_column('professional_memberships')
        batch_op.drop_column('age_groups_treated')
        batch_op.drop_column('procedures_performed')
        batch_op.drop_column('conditions_treated')
        batch_op.drop_column('areas_of_expertise')
        batch_op.drop_column('sub_specialties')
        batch_op.drop_column('achievement_images')
        batch_op.drop_column('professional_documents')
        batch_op.drop_column('verbal_intro_file')
        batch_op.drop_column('profile_photo')
        batch_op.drop_column('phone')
        batch_op.drop_column('practice_locations')
        batch_op.drop_column('publications')
        batch_op.drop_column('achievements')
        batch_op.drop_column('qualifications')
        
        # Revert column type changes
        batch_op.alter_column('primary_specialization',
                              existing_type=sa.Text(),
                              type_=sa.String(200),
                              existing_nullable=True)
        
        batch_op.alter_column('registration_authority',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=True)
        
        batch_op.alter_column('registration_number',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=True)
        
        batch_op.alter_column('gender',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=True)
        
        batch_op.alter_column('last_name',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=False)
        
        batch_op.alter_column('first_name',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=False)
        
        batch_op.alter_column('email',
                              existing_type=sa.String(100),
                              type_=sa.String(255),
                              existing_nullable=False)
        
        # Recreate phone_number as string
        batch_op.add_column(sa.Column('phone_number', sa.String(20), nullable=True))
    
    # Recreate qualifications table
    op.create_table('qualifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('degree', sa.String(255), nullable=False),
        sa.Column('institution', sa.String(255), nullable=False),
        sa.Column('year_of_completion', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
