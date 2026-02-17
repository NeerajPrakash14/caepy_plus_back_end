"""add comprehensive doctor profile fields

Revision ID: 001
Revises: 000
Create Date: 2026-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = '000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add new fields to doctors table for comprehensive profile capture."""
    
    # Add registration_year field
    op.add_column('doctors', sa.Column('registration_year', sa.Integer(), nullable=True, comment='Year of medical registration'))
    
    # Add new professional information fields
    op.add_column('doctors', sa.Column('conditions_treated', sa.JSON(), nullable=False, server_default='[]', comment='List of conditions commonly treated'))
    op.add_column('doctors', sa.Column('procedures_performed', sa.JSON(), nullable=False, server_default='[]', comment='List of procedures performed'))
    op.add_column('doctors', sa.Column('age_groups_treated', sa.JSON(), nullable=False, server_default='[]', comment='Age groups treated'))
    
    # Add publications field to achievements
    op.add_column('doctors', sa.Column('publications', sa.JSON(), nullable=False, server_default='[]', comment='Notable publications'))
    
    # Add media & documents fields
    op.add_column('doctors', sa.Column('verbal_intro_file', sa.String(length=500), nullable=True, comment='URL or filename for verbal introduction'))
    op.add_column('doctors', sa.Column('professional_documents', sa.JSON(), nullable=False, server_default='[]', comment='List of professional document URLs or filenames'))
    op.add_column('doctors', sa.Column('achievement_images', sa.JSON(), nullable=False, server_default='[]', comment='List of achievement image URLs or filenames'))
    op.add_column('doctors', sa.Column('external_links', sa.JSON(), nullable=False, server_default='[]', comment='List of external profile URLs'))
    
    # Rename registration_council to registration_authority for consistency
    op.alter_column('doctors', 'registration_council',
                    new_column_name='registration_authority',
                    existing_type=sa.String(length=200),
                    comment='Issuing medical council or authority')

def downgrade() -> None:
    """Remove comprehensive profile fields."""
    
    # Remove added columns
    op.drop_column('doctors', 'external_links')
    op.drop_column('doctors', 'achievement_images')
    op.drop_column('doctors', 'professional_documents')
    op.drop_column('doctors', 'verbal_intro_file')
    op.drop_column('doctors', 'publications')
    op.drop_column('doctors', 'age_groups_treated')
    op.drop_column('doctors', 'procedures_performed')
    op.drop_column('doctors', 'conditions_treated')
    op.drop_column('doctors', 'registration_year')
    
    # Rename back to registration_council
    op.alter_column('doctors', 'registration_authority',
                    new_column_name='registration_council',
                    existing_type=sa.String(length=200))
