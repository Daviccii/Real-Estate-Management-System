"""create units

Revision ID: 0009_create_units
Revises: 0008_add_manager_to_properties
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009_create_units'
down_revision = '0008_add_manager_to_properties'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('unit_number', sa.String(length=50), nullable=False),
        sa.Column('unit_type', sa.String(length=100), nullable=True),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Integer(), nullable=True),
        sa.Column('area', sa.String(length=100), nullable=True),
        sa.Column('rent', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='available'),
        sa.Column('availability_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_units_id', 'units', ['id'])
    op.create_index('ix_units_property_id', 'units', ['property_id'])
    op.create_index('ix_units_unit_number', 'units', ['unit_number'])
    op.create_index('ix_units_unit_type', 'units', ['unit_type'])
    op.create_index('ix_units_status', 'units', ['status'])


def downgrade():
    op.drop_index('ix_units_status', table_name='units')
    op.drop_index('ix_units_unit_type', table_name='units')
    op.drop_index('ix_units_unit_number', table_name='units')
    op.drop_index('ix_units_property_id', table_name='units')
    op.drop_index('ix_units_id', table_name='units')
    op.drop_table('units')