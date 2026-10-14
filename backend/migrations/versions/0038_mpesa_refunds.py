"""m-pesa refund records

Adds the mpesa_refunds table: one row per refund issued against a succeeded
M-Pesa collection. Refunds are a distinct ledger — the collection row is
never mutated; only the linked rent obligation's settlement status is
recomputed to the net collected amount. No money is moved by the app: each
row documents a reversal the landlord performed through their own M-Pesa
channels (reversal_reference = their statement's transaction code), so the
feature requires no Daraja B2C credentials.

Portable across PostgreSQL (production) and SQLite (dev/tests).

Revision ID: 0038_mpesa_refunds
Revises: 0037_mpesa_transactions
Create Date: 2026-10-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0038_mpesa_refunds"
down_revision = "0037_mpesa_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mpesa_refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mpesa_transaction_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("reversal_reference", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mpesa_transaction_id"], ["mpesa_transactions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mpesa_refunds_id", "mpesa_refunds", ["id"])
    op.create_index(
        "ix_mpesa_refunds_mpesa_transaction_id",
        "mpesa_refunds",
        ["mpesa_transaction_id"],
    )
    op.create_index("ix_mpesa_refunds_payment_id", "mpesa_refunds", ["payment_id"])
    op.create_index("ix_mpesa_refunds_status", "mpesa_refunds", ["status"])
    op.create_index("ix_mpesa_refunds_recorded_by", "mpesa_refunds", ["recorded_by"])


def downgrade() -> None:
    op.drop_table("mpesa_refunds")
