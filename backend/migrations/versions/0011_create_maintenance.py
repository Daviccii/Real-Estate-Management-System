"""create maintenance

Revision ID: 0011_create_maintenance
Revises: 0010_create_leases
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_create_maintenance'
down_revision = '0010_create_leases'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'maintenance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('assigned_manager_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_manager_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_maintenance_id', 'maintenance', ['id'])
    op.create_index('ix_maintenance_tenant_id', 'maintenance', ['tenant_id'])
    op.create_index('ix_maintenance_property_id', 'maintenance', ['property_id'])
    op.create_index('ix_maintenance_unit_id', 'maintenance', ['unit_id'])
    op.create_index('ix_maintenance_assigned_manager_id', 'maintenance', ['assigned_manager_id'])
    op.create_index('ix_maintenance_priority', 'maintenance', ['priority'])
    op.create_index('ix_maintenance_status', 'maintenance', ['status'])


def downgrade():
    op.drop_index('ix_maintenance_status', table_name='maintenance')
    op.drop_index('ix_maintenance_priority', table_name='maintenance')
    op.drop_index('ix_maintenance_assigned_manager_id', table_name='maintenance')
    op.drop_index('ix_maintenance_unit_id', table_name='maintenance')
    op.drop_index('ix_maintenance_property_id', table_name='maintenance')
    op.drop_index('ix_maintenance_tenant_id', table_name='maintenance')
    op.drop_index('ix_maintenance_id', table_name='maintenance')
    op.drop_table('maintenance')