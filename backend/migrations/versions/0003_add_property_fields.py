"""add property fields

Revision ID: 0003_add_property_fields
Revises: 0002_add_properties
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_property_fields'
down_revision = '0002_add_properties'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to properties table
    with op.batch_alter_table('properties', recreate='auto') as batch_op:
        batch_op.add_column(sa.Column('price', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('price_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('bedrooms', sa.Integer, nullable=True))
        batch_op.add_column(sa.Column('bathrooms', sa.Integer, nullable=True))
        batch_op.add_column(sa.Column('area', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('purpose', sa.String(50), nullable=True, index=True))
        batch_op.add_column(sa.Column('deposit', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('lease_term', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('availability_date', sa.DateTime, nullable=True))


def downgrade():
    # Remove the columns
    with op.batch_alter_table('properties', recreate='auto') as batch_op:
        batch_op.drop_column('availability_date')
        batch_op.drop_column('lease_term')
        batch_op.drop_column('deposit')
        batch_op.drop_column('purpose')
        batch_op.drop_column('image_url')
        batch_op.drop_column('area')
        batch_op.drop_column('bathrooms')
        batch_op.drop_column('bedrooms')
        batch_op.drop_column('price_label')
        batch_op.drop_column('price')