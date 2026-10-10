"""update user roles and add role constraints

Revision ID: 0006_update_user_roles
Revises: 0005_add_inquiries
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_update_user_roles'
down_revision = '0005_add_inquiries'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing users from 'tenant' to 'user' role
    op.execute("UPDATE users SET role = 'user' WHERE role = 'tenant'")
    
    # SQLite doesn't support ALTER TABLE with ADD CONSTRAINT directly
    # Role validation is handled at the application level in schemas/repositories


def downgrade():
    # Revert role changes (optional - you might want to keep current roles)
    op.execute("UPDATE users SET role = 'tenant' WHERE role = 'user'")