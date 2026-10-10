"""add owner expenses and provider billing records

Revision ID: 0023_add_owner_expenses_provider_billing
Revises: 0022_add_property_media_and_verification_evidence
"""
from alembic import op
import sqlalchemy as sa

revision = "0023_add_owner_expenses_provider_billing"
down_revision = "0022_add_property_media_and_verification_evidence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "owner_expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("amount", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("expense_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="recorded"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_owner_expenses_owner_id", "owner_expenses", ["owner_id"])
    op.create_index("ix_owner_expenses_property_id", "owner_expenses", ["property_id"])

    op.create_table(
        "provider_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("maintenance_id", sa.Integer(), sa.ForeignKey("maintenance.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_number", sa.String(80), nullable=False, unique=True),
        sa.Column("amount", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="submitted"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_provider_invoices_provider_id", "provider_invoices", ["provider_id"])
    op.create_index("ix_provider_invoices_maintenance_id", "provider_invoices", ["maintenance_id"])

    op.create_table(
        "provider_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("maintenance_id", sa.Integer(), sa.ForeignKey("maintenance.id", ondelete="SET NULL"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_provider_ratings_provider_id", "provider_ratings", ["provider_id"])


def downgrade():
    op.drop_index("ix_provider_ratings_provider_id", table_name="provider_ratings")
    op.drop_table("provider_ratings")
    op.drop_index("ix_provider_invoices_maintenance_id", table_name="provider_invoices")
    op.drop_index("ix_provider_invoices_provider_id", table_name="provider_invoices")
    op.drop_table("provider_invoices")
    op.drop_index("ix_owner_expenses_property_id", table_name="owner_expenses")
    op.drop_index("ix_owner_expenses_owner_id", table_name="owner_expenses")
    op.drop_table("owner_expenses")
