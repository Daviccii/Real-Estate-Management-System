"""add sub_location and allow_direct_contact to properties

Revision ID: 0018_add_sub_location_and_direct_contact
Revises: 58b412d437ff
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa


revision = "0018_sub_location"
down_revision = '58b412d437ff'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('properties', sa.Column('sub_location', sa.String(length=200), nullable=True))
    op.add_column(
        'properties',
        sa.Column('allow_direct_contact', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'))
    )
    op.create_index('ix_properties_county', 'properties', ['county'])


def downgrade():
    op.drop_index('ix_properties_county', table_name='properties')
    op.drop_column('properties', 'allow_direct_contact')
    op.drop_column('properties', 'sub_location')
