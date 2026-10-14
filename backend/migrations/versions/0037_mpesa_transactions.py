"""m-pesa (daraja) rent collection transactions

Adds the mpesa_transactions table: one row per STK Push collection attempt,
linking the rent obligation (payments), the tenant, lease, property, unit,
and the beneficiary landlord/company snapshot at initiation. Terminal states
are applied to the payments ledger exactly once (atomic status claim), and
unique constraints on the checkout request id and the Safaricom receipt
number make duplicate callbacks / duplicate receipts impossible to record.

Portable across PostgreSQL (production) and SQLite (dev/tests): plain
columns and constraints only, no dialect-specific SQL.

Revision ID: 0037_mpesa_transactions
Revises: 0036_audit_chain
Create Date: 2026-10-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0037_mpesa_transactions"
down_revision = "0036_audit_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mpesa_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=40), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("lease_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("landlord_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("result_code", sa.Integer(), nullable=True),
        sa.Column("result_description", sa.String(length=500), nullable=True),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("merchant_request_id", sa.String(length=64), nullable=True),
        sa.Column("checkout_request_id", sa.String(length=64), nullable=True),
        sa.Column("mpesa_receipt_number", sa.String(length=64), nullable=True),
        sa.Column("applied_to_payment", sa.Boolean(), nullable=False),
        sa.Column("callback_attempts", sa.Integer(), nullable=False),
        sa.Column("initiated_at", sa.DateTime(), nullable=False),
        sa.Column("callback_received_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["lease_id"], ["leases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["units.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["landlord_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference", name="uq_mpesa_transactions_reference"),
        sa.UniqueConstraint(
            "checkout_request_id", name="uq_mpesa_transactions_checkout_request_id"
        ),
        sa.UniqueConstraint(
            "mpesa_receipt_number", name="uq_mpesa_transactions_receipt"
        ),
    )
    op.create_index("ix_mpesa_transactions_id", "mpesa_transactions", ["id"])
    op.create_index(
        "ix_mpesa_transactions_payment_id", "mpesa_transactions", ["payment_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_tenant_id", "mpesa_transactions", ["tenant_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_lease_id", "mpesa_transactions", ["lease_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_property_id", "mpesa_transactions", ["property_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_unit_id", "mpesa_transactions", ["unit_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_landlord_id", "mpesa_transactions", ["landlord_id"]
    )
    op.create_index(
        "ix_mpesa_transactions_company_id", "mpesa_transactions", ["company_id"]
    )
    op.create_index("ix_mpesa_transactions_status", "mpesa_transactions", ["status"])
    op.create_index(
        "ix_mpesa_transactions_merchant_request_id",
        "mpesa_transactions",
        ["merchant_request_id"],
    )
    op.create_index(
        "ix_mpesa_transactions_receipt_number",
        "mpesa_transactions",
        ["mpesa_receipt_number"],
    )


def downgrade() -> None:
    op.drop_table("mpesa_transactions")
