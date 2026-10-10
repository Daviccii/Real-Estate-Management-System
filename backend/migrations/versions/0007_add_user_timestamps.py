"""add user timestamps

Revision ID: 0007_add_user_timestamps
Revises: 0006_update_user_roles
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007_add_user_timestamps'
down_revision = '0006_update_user_roles'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at and updated_at columns to users table
    # SQLite requires nullable columns with dynamic defaults
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Update existing rows with current timestamp
    op.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    op.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    
    # Make columns NOT NULL after updating existing data
    # SQLite doesn't support ALTER COLUMN with NOT NULL constraint directly
    # This will be handled at the application level


def downgrade():
    # Remove columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')