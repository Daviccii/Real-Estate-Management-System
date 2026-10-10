"""add properties table

Revision ID: 0002_add_properties
Revises: 0001_initial
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_properties'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'properties',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('property_type', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=200), nullable=True),
        sa.Column('county', sa.String(length=200), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('units_count', sa.Integer, nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index(op.f('ix_properties_id'), 'properties', ['id'], unique=False)
    op.create_index(op.f('ix_properties_owner_id'), 'properties', ['owner_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_properties_owner_id'), table_name='properties')
    op.drop_index(op.f('ix_properties_id'), table_name='properties')
    op.drop_table('properties')
