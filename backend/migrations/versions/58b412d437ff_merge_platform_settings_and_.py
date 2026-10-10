"""merge platform settings and notifications branches

Revision ID: 58b412d437ff
Revises: 0016_create_notifications, 0013_create_platform_settings
Create Date: 2026-09-08 23:05:23.963435
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '58b412d437ff'
down_revision: Union[str, Sequence[str], None] = ('0016_create_notifications', '0013_create_platform_settings')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass