"""Add hospitals and doctor affiliations tables

Revision ID: 005_add_hospitals_table
Revises: 004_phone_to_varchar
Create Date: 2026-01-17

This migration adds:
1. hospitals - Master table for hospitals/clinics
2. doctor_hospital_affiliations - Links doctors to hospitals

Features:
- Hospital verification workflow (pending → verified/rejected)
- Doctor self-add with admin review
- One doctor can have multiple hospital affiliations
- Each affiliation stores doctor-specific info (fee, schedule)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_hospitals_table'
down_revision = '004_phone_to_varchar'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Create hospitals table
    # ==========================================================================
    op.create_table(
        'hospitals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, comment='Hospital or clinic name'),
        sa.Column('address', sa.Text(), nullable=True, comment='Full street address'),
        sa.Column('city', sa.String(100), nullable=True, comment='City name'),
        sa.Column('state', sa.String(100), nullable=True, comment='State or province'),
        sa.Column('pincode', sa.String(20), nullable=True, comment='Postal/ZIP code'),
        sa.Column('phone_number', sa.String(20), nullable=True, comment='Hospital contact number'),
        sa.Column('email', sa.String(255), nullable=True, comment='Hospital email'),
        sa.Column('website', sa.String(500), nullable=True, comment='Hospital website URL'),
        sa.Column(
            'verification_status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='Verification status: pending, verified, rejected'
        ),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True, comment='When the hospital was verified'),
        sa.Column('verified_by', sa.String(100), nullable=True, comment='Admin who verified this hospital'),
        sa.Column('rejection_reason', sa.Text(), nullable=True, comment='Reason for rejection (if rejected)'),
        sa.Column('created_by_doctor_id', sa.BigInteger(), nullable=True, comment='Doctor ID who added this hospital'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Soft delete flag'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for hospitals
    op.create_index('ix_hospitals_id', 'hospitals', ['id'])
    op.create_index('ix_hospitals_name', 'hospitals', ['name'])
    op.create_index('ix_hospitals_city', 'hospitals', ['city'])
    op.create_index('ix_hospitals_state', 'hospitals', ['state'])
    op.create_index('ix_hospitals_verification_status', 'hospitals', ['verification_status'])
    op.create_index('ix_hospitals_name_city', 'hospitals', ['name', 'city'])
    op.create_index('ix_hospitals_verification_active', 'hospitals', ['verification_status', 'is_active'])
    
    # ==========================================================================
    # Create doctor_hospital_affiliations table
    # ==========================================================================
    op.create_table(
        'doctor_hospital_affiliations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('doctor_id', sa.BigInteger(), nullable=False, comment='References doctor_identity.doctor_id'),
        sa.Column('hospital_id', sa.Integer(), nullable=False),
        sa.Column('consultation_fee', sa.Float(), nullable=True, comment='Consultation fee at this hospital'),
        sa.Column('consultation_type', sa.String(100), nullable=True, comment='Type: In-person, Online, Both'),
        sa.Column('weekly_schedule', sa.Text(), nullable=True, comment='Schedule at this hospital'),
        sa.Column('designation', sa.String(200), nullable=True, comment="Doctor's designation at this hospital"),
        sa.Column('department', sa.String(200), nullable=True, comment='Department at this hospital'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false', comment='Is this the primary practice location?'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Soft delete flag'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('doctor_id', 'hospital_id', name='uq_doctor_hospital')
    )
    
    # Indexes for affiliations
    op.create_index('ix_affiliations_doctor_id', 'doctor_hospital_affiliations', ['doctor_id'])
    op.create_index('ix_affiliations_hospital_id', 'doctor_hospital_affiliations', ['hospital_id'])
    op.create_index('ix_affiliations_doctor_primary', 'doctor_hospital_affiliations', ['doctor_id', 'is_primary'])


def downgrade() -> None:
    # Drop affiliations table first (has FK to hospitals)
    op.drop_index('ix_affiliations_doctor_primary', table_name='doctor_hospital_affiliations')
    op.drop_index('ix_affiliations_hospital_id', table_name='doctor_hospital_affiliations')
    op.drop_index('ix_affiliations_doctor_id', table_name='doctor_hospital_affiliations')
    op.drop_table('doctor_hospital_affiliations')
    
    # Drop hospitals table
    op.drop_index('ix_hospitals_verification_active', table_name='hospitals')
    op.drop_index('ix_hospitals_name_city', table_name='hospitals')
    op.drop_index('ix_hospitals_verification_status', table_name='hospitals')
    op.drop_index('ix_hospitals_state', table_name='hospitals')
    op.drop_index('ix_hospitals_city', table_name='hospitals')
    op.drop_index('ix_hospitals_name', table_name='hospitals')
    op.drop_index('ix_hospitals_id', table_name='hospitals')
    op.drop_table('hospitals')
