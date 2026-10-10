"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('role', sa.String(length=50), nullable=True, server_default='tenant'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
