"""Store background job results.

Revision ID: 0028_add_job_results
Revises: 0027_companies_and_invitations
"""

from alembic import op
import sqlalchemy as sa


revision = "0028_add_job_results"
down_revision = "0027_companies_and_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("background_jobs", sa.Column("result", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("background_jobs", "result")
