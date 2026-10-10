"""create payments

Revision ID: 0012_create_payments
Revises: 0011_create_maintenance
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_create_payments'
down_revision = '0011_create_maintenance'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('lease_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.String(length=100), nullable=False),
        sa.Column('payment_type', sa.String(length=50), nullable=True),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lease_id'], ['leases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_tenant_id', 'payments', ['tenant_id'])
    op.create_index('ix_payments_lease_id', 'payments', ['lease_id'])
    op.create_index('ix_payments_property_id', 'payments', ['property_id'])
    op.create_index('ix_payments_unit_id', 'payments', ['unit_id'])
    op.create_index('ix_payments_payment_type', 'payments', ['payment_type'])
    op.create_index('ix_payments_status', 'payments', ['status'])


def downgrade():
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_payment_type', table_name='payments')
    op.drop_index('ix_payments_unit_id', table_name='payments')
    op.drop_index('ix_payments_property_id', table_name='payments')
    op.drop_index('ix_payments_lease_id', table_name='payments')
    op.drop_index('ix_payments_tenant_id', table_name='payments')
    op.drop_index('ix_payments_id', table_name='payments')
    op.drop_table('payments')