"""add favorites table

Revision ID: 0004_add_favorites
Revises: 0003_add_property_fields
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_favorites'
down_revision = '0003_add_property_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create table with unique constraint directly in table definition
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('property_id', sa.Integer, sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'property_id', name='uq_user_property')
    )
    op.create_index(op.f('ix_favorites_id'), 'favorites', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_favorites_id'), table_name='favorites')
    op.drop_table('favorites')