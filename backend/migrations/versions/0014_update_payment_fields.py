"""update payment fields

Revision ID: 0014_update_payment_fields
Revises: 0013_update_lease_fields
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014_update_payment_fields'
down_revision = '0013_update_lease_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to payments table
    op.add_column('payments', sa.Column('payment_method', sa.String(length=50), nullable=True))
    op.add_column('payments', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Remove the new columns
    op.drop_column('payments', 'notes')
    op.drop_column('payments', 'payment_method')