"""marketplace expansion: provider availability, review aggregates, review<->work order link

Revision ID: 0034_marketplace_expansion
Revises: 0033_email_preferences
Create Date: 2026-10-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0034_marketplace_expansion'
down_revision: Union[str, Sequence[str], None] = '0033_email_preferences'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'service_provider_profiles',
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        'service_provider_profiles',
        sa.Column('reviews_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'provider_ratings',
        sa.Column('work_order_id', sa.Integer(), nullable=True),
    )
    with op.batch_alter_table('provider_ratings') as batch_op:
        batch_op.create_foreign_key(
            'fk_provider_ratings_work_order_id',
            'maintenance_work_orders',
            ['work_order_id'],
            ['id'],
            ondelete='SET NULL',
        )

    # Backfill review aggregates from any pre-existing ratings
    op.execute(
        """
        UPDATE service_provider_profiles
        SET reviews_count = COALESCE(
            (SELECT COUNT(*) FROM provider_ratings pr WHERE pr.provider_id = service_provider_profiles.user_id),
            0
        )
        """
    )
    op.execute(
        """
        UPDATE service_provider_profiles
        SET rating = (
            SELECT ROUND(AVG(pr.score), 2)
            FROM provider_ratings pr
            WHERE pr.provider_id = service_provider_profiles.user_id
        )
        WHERE EXISTS (
            SELECT 1 FROM provider_ratings pr WHERE pr.provider_id = service_provider_profiles.user_id
        )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table('provider_ratings') as batch_op:
        batch_op.drop_constraint('fk_provider_ratings_work_order_id', type_='foreignkey')
        batch_op.drop_column('work_order_id')
    op.drop_column('service_provider_profiles', 'reviews_count')
    op.drop_column('service_provider_profiles', 'is_available')
