"""add property gallery and construction presentation fields

Revision ID: 0019_add_property_presentation_fields
Revises: 0018_sub_location
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa


revision = '0019_add_property_presentation_fields'
down_revision = '0018_sub_location'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('properties', sa.Column('gallery_urls', sa.Text(), nullable=True))
    op.add_column('properties', sa.Column('showroom_url', sa.String(length=500), nullable=True))
    op.add_column('properties', sa.Column('construction_status', sa.String(length=50), nullable=True, server_default='completed'))
    op.add_column('properties', sa.Column('completion_date', sa.DateTime(), nullable=True))
    op.add_column('properties', sa.Column('planned_finish_description', sa.Text(), nullable=True))
    op.add_column('properties', sa.Column('planned_finish_image_url', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('properties', 'planned_finish_image_url')
    op.drop_column('properties', 'planned_finish_description')
    op.drop_column('properties', 'completion_date')
    op.drop_column('properties', 'construction_status')
    op.drop_column('properties', 'showroom_url')
    op.drop_column('properties', 'gallery_urls')
