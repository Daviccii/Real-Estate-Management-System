"""add inquiries table

Revision ID: 0005_add_inquiries
Revises: 0004_add_favorites
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_inquiries'
down_revision = '0004_add_favorites'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'inquiries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('property_id', sa.Integer, sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index(op.f('ix_inquiries_id'), 'inquiries', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_inquiries_id'), table_name='inquiries')
    op.drop_table('inquiries')