"""update lease fields

Revision ID: 0013_update_lease_fields
Revises: 0012_create_payments
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013_update_lease_fields'
down_revision = '0012_create_payments'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to leases table
    op.add_column('leases', sa.Column('payment_due_date', sa.Integer(), nullable=True))
    op.add_column('leases', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Remove the new columns
    op.drop_column('leases', 'notes')
    op.drop_column('leases', 'payment_due_date')