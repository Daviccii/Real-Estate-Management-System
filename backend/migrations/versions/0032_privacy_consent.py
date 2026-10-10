"""add privacy consent tables

Revision ID: 0032_privacy_consent
Revises: 0031_add_mfa
Create Date: 2026-10-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0032_privacy_consent'
down_revision: Union[str, Sequence[str], None] = '0031_add_mfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('consent_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('client_id', sa.String(length=64), nullable=True),
    sa.Column('consent_type', sa.String(length=50), nullable=False),
    sa.Column('granted', sa.Boolean(), nullable=False),
    sa.Column('policy_version', sa.String(length=20), nullable=False),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_records_id'), 'consent_records', ['id'], unique=False)
    op.create_index(op.f('ix_consent_records_user_id'), 'consent_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_consent_records_client_id'), 'consent_records', ['client_id'], unique=False)
    op.create_index(op.f('ix_consent_records_consent_type'), 'consent_records', ['consent_type'], unique=False)
    op.create_index(op.f('ix_consent_records_created_at'), 'consent_records', ['created_at'], unique=False)

    op.create_table('data_deletion_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('requested_at', sa.DateTime(), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.Column('processed_by', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_deletion_requests_id'), 'data_deletion_requests', ['id'], unique=False)
    op.create_index(op.f('ix_data_deletion_requests_user_id'), 'data_deletion_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_data_deletion_requests_status'), 'data_deletion_requests', ['status'], unique=False)
    op.create_index('ix_data_deletion_requests_user_status', 'data_deletion_requests', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_data_deletion_requests_user_status', table_name='data_deletion_requests')
    op.drop_index(op.f('ix_data_deletion_requests_status'), table_name='data_deletion_requests')
    op.drop_index(op.f('ix_data_deletion_requests_user_id'), table_name='data_deletion_requests')
    op.drop_index(op.f('ix_data_deletion_requests_id'), table_name='data_deletion_requests')
    op.drop_table('data_deletion_requests')
    op.drop_index(op.f('ix_consent_records_created_at'), table_name='consent_records')
    op.drop_index(op.f('ix_consent_records_consent_type'), table_name='consent_records')
    op.drop_index(op.f('ix_consent_records_client_id'), table_name='consent_records')
    op.drop_index(op.f('ix_consent_records_user_id'), table_name='consent_records')
    op.drop_index(op.f('ix_consent_records_id'), table_name='consent_records')
    op.drop_table('consent_records')
