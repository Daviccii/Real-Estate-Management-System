"""Create durable background jobs.

Revision ID: 0026_create_background_jobs
Revises: 0025_add_scaling_indexes
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_create_background_jobs"
down_revision = "0025_add_scaling_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_background_jobs_claim",
        "background_jobs",
        ["status", "available_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_background_jobs_claim", table_name="background_jobs")
    op.drop_table("background_jobs")
