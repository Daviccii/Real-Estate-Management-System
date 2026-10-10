"""create notifications table

Revision ID: 0016_create_notifications
Revises: 0015_update_maintenance_fields
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0016_create_notifications'
down_revision = '0015_update_maintenance_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('recipient_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, server_default='NORMAL', index=True),
        sa.Column('related_entity_type', sa.String(50), nullable=True, index=True),
        sa.Column('related_entity_id', sa.Integer, nullable=True, index=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    # Additional index for common queries: recipient's unread notifications
    op.create_index('ix_notifications_recipient_unread', 'notifications', ['recipient_id', 'is_read'], unique=False)
    # Index for chronological queries
    op.create_index('ix_notifications_recipient_created', 'notifications', ['recipient_id', 'created_at'], unique=False)


def downgrade():
    op.drop_index('ix_notifications_recipient_created', table_name='notifications')
    op.drop_index('ix_notifications_recipient_unread', table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
