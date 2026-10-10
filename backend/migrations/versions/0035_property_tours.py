"""property 360/virtual tours

Revision ID: 0035_property_tours
Revises: 0034_marketplace_expansion
Create Date: 2026-10-10 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0035_property_tours'
down_revision: Union[str, Sequence[str], None] = '0034_marketplace_expansion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'property_tours',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='link'),
        sa.Column('embed_url', sa.String(length=1000), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_property_tours_id', 'property_tours', ['id'])
    op.create_index('ix_property_tours_property_id', 'property_tours', ['property_id'])


def downgrade() -> None:
    op.drop_index('ix_property_tours_property_id', table_name='property_tours')
    op.drop_index('ix_property_tours_id', table_name='property_tours')
    op.drop_table('property_tours')
