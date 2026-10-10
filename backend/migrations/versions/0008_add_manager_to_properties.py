"""add manager to properties

Revision ID: 0008_add_manager_to_properties
Revises: 0007_add_user_timestamps
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_add_manager_to_properties'
down_revision = '0007_add_user_timestamps'
branch_labels = None
depends_on = None


def upgrade():
    # Add manager_id column to properties table
    # SQLite doesn't support adding foreign keys directly, constraint will be handled at model level
    op.add_column('properties', sa.Column('manager_id', sa.Integer(), nullable=True))
    op.create_index('ix_properties_manager_id', 'properties', ['manager_id'])


def downgrade():
    op.drop_index('ix_properties_manager_id', table_name='properties')
    op.drop_column('properties', 'manager_id')