"""add email_preferences table

Revision ID: 0033_email_preferences
Revises: 0032_privacy_consent
Create Date: 2026-10-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0033_email_preferences'
down_revision: Union[str, Sequence[str], None] = '0032_privacy_consent'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('email_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_email_preferences_id'), 'email_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_email_preferences_user_id'), 'email_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_preferences_user_id'), table_name='email_preferences')
    op.drop_index(op.f('ix_email_preferences_id'), table_name='email_preferences')
    op.drop_table('email_preferences')
