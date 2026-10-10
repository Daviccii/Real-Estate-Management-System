"""add_mfa

Revision ID: 0031_add_mfa
Revises: 0030_password_reset_history
Create Date: 2026-10-09 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0031_add_mfa'
down_revision: Union[str, Sequence[str], None] = '0030_password_reset_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=64), nullable=True))

    op.create_table('mfa_recovery_codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('used_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mfa_recovery_codes_id'), 'mfa_recovery_codes', ['id'], unique=False)
    op.create_index(op.f('ix_mfa_recovery_codes_user_id'), 'mfa_recovery_codes', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_recovery_codes_code_hash'), 'mfa_recovery_codes', ['code_hash'], unique=True)

    op.create_table('mfa_sms_challenges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('used_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mfa_sms_challenges_id'), 'mfa_sms_challenges', ['id'], unique=False)
    op.create_index(op.f('ix_mfa_sms_challenges_user_id'), 'mfa_sms_challenges', ['user_id'], unique=False)
    op.create_index(op.f('ix_mfa_sms_challenges_code_hash'), 'mfa_sms_challenges', ['code_hash'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_mfa_sms_challenges_code_hash'), table_name='mfa_sms_challenges')
    op.drop_index(op.f('ix_mfa_sms_challenges_user_id'), table_name='mfa_sms_challenges')
    op.drop_index(op.f('ix_mfa_sms_challenges_id'), table_name='mfa_sms_challenges')
    op.drop_table('mfa_sms_challenges')
    op.drop_index(op.f('ix_mfa_recovery_codes_code_hash'), table_name='mfa_recovery_codes')
    op.drop_index(op.f('ix_mfa_recovery_codes_user_id'), table_name='mfa_recovery_codes')
    op.drop_index(op.f('ix_mfa_recovery_codes_id'), table_name='mfa_recovery_codes')
    op.drop_table('mfa_recovery_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
