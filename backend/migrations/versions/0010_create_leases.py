"""create leases

Revision ID: 0010_create_leases
Revises: 0009_create_units
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010_create_leases'
down_revision = '0009_create_units'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'leases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('rent_amount', sa.String(length=100), nullable=False),
        sa.Column('deposit', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_leases_id', 'leases', ['id'])
    op.create_index('ix_leases_tenant_id', 'leases', ['tenant_id'])
    op.create_index('ix_leases_unit_id', 'leases', ['unit_id'])
    op.create_index('ix_leases_property_id', 'leases', ['property_id'])
    op.create_index('ix_leases_status', 'leases', ['status'])


def downgrade():
    op.drop_index('ix_leases_status', table_name='leases')
    op.drop_index('ix_leases_property_id', table_name='leases')
    op.drop_index('ix_leases_unit_id', table_name='leases')
    op.drop_index('ix_leases_tenant_id', table_name='leases')
    op.drop_index('ix_leases_id', table_name='leases')
    op.drop_table('leases')