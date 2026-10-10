"""update maintenance fields

Revision ID: 0015_update_maintenance_fields
Revises: 0014_update_payment_fields
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0015_update_maintenance_fields'
down_revision = '0014_update_payment_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to maintenance table
    op.add_column('maintenance', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('maintenance', sa.Column('cost', sa.String(length=100), nullable=True))
    op.add_column('maintenance', sa.Column('notes', sa.Text(), nullable=True))
    
    # Update default status from 'open' to 'pending'
    op.execute("UPDATE maintenance SET status = 'pending' WHERE status = 'open'")


def downgrade():
    # Remove the new columns
    op.drop_column('maintenance', 'notes')
    op.drop_column('maintenance', 'cost')
    op.drop_column('maintenance', 'category')
    
    # Revert status changes
    op.execute("UPDATE maintenance SET status = 'open' WHERE status = 'pending'")