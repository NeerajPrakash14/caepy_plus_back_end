"""Change phone column from INTEGER to VARCHAR(20) to support international phone formats.

Revision ID: 004_phone_to_varchar
Revises: 003_unique_email_and_phone
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_phone_to_varchar'
down_revision: Union[str, None] = '003_unique_email_and_phone'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change phone column from INTEGER to VARCHAR(20)."""
    # Drop the index first (if exists)
    op.drop_index('ix_doctors_phone', table_name='doctors', if_exists=True)
    
    # Alter column type from INTEGER to VARCHAR(20)
    # PostgreSQL requires USING clause to cast existing data
    op.execute("""
        ALTER TABLE doctors 
        ALTER COLUMN phone TYPE VARCHAR(20) 
        USING CASE WHEN phone IS NOT NULL THEN '+' || phone::text ELSE NULL END
    """)
    
    # Recreate the index
    op.create_index('ix_doctors_phone', 'doctors', ['phone'], unique=True)


def downgrade() -> None:
    """Revert phone column back to INTEGER."""
    # Drop the index first
    op.drop_index('ix_doctors_phone', table_name='doctors', if_exists=True)
    
    # Alter column type back to INTEGER (will lose + prefix)
    op.execute("""
        ALTER TABLE doctors 
        ALTER COLUMN phone TYPE INTEGER 
        USING NULLIF(REGEXP_REPLACE(phone, '[^0-9]', '', 'g'), '')::INTEGER
    """)
    
    # Recreate the index
    op.create_index('ix_doctors_phone', 'doctors', ['phone'], unique=True)
