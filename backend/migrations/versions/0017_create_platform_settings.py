"""create platform settings

Revision ID: 0013_create_platform_settings
Revises: 0012_create_payments
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa


revision = '0013_create_platform_settings'
down_revision = '0012_create_payments'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'platform_settings',
        sa.Column('id', sa.Integer(), nullable=False),

        sa.Column(
            'enable_user_registration',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('TRUE')
        ),

        sa.Column(
            'require_email_verification',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ),

        sa.Column(
            'enable_property_moderation',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ),

        sa.Column(
            'session_timeout_minutes',
            sa.Integer(),
            nullable=False,
            server_default='60'
        ),

        sa.Column(
            'password_min_length',
            sa.Integer(),
            nullable=False,
            server_default='8'
        ),

        sa.Column(
            'notify_new_users',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ),

        sa.Column(
            'notify_new_inquiries',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ),

        sa.Column(
            'notify_property_updates',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE')
        ),

        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),

        sa.Column('updated_by_id', sa.Integer(), nullable=True),

        sa.ForeignKeyConstraint(
            ['updated_by_id'],
            ['users.id'],
            ondelete='SET NULL'
        ),

        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        'ix_platform_settings_id',
        'platform_settings',
        ['id']
    )


def downgrade():
    op.drop_index(
        'ix_platform_settings_id',
        table_name='platform_settings'
    )

    op.drop_table('platform_settings')