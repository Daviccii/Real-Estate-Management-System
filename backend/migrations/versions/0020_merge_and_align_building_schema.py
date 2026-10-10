"""merge migration branches and align building schema with the ORM

Revision ID: 0020_merge_and_align_building_schema
Revises: 0019_add_property_presentation_fields, f82fd04ad360
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa


revision = '0020_merge_and_align_building_schema'
down_revision = ('0019_add_property_presentation_fields', 'f82fd04ad360')
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('buildings', 'property_id', existing_type=sa.Integer(), nullable=True)
    op.drop_constraint('buildings_property_id_fkey', 'buildings', type_='foreignkey')
    op.create_foreign_key(
        'buildings_property_id_fkey',
        'buildings',
        'properties',
        ['property_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_buildings_city', 'buildings', ['city'])
    op.create_index('ix_buildings_county', 'buildings', ['county'])


def downgrade():
    op.drop_index('ix_buildings_county', table_name='buildings')
    op.drop_index('ix_buildings_city', table_name='buildings')
    op.drop_constraint('buildings_property_id_fkey', 'buildings', type_='foreignkey')
    op.create_foreign_key(
        'buildings_property_id_fkey',
        'buildings',
        'properties',
        ['property_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column('buildings', 'property_id', existing_type=sa.Integer(), nullable=False)
