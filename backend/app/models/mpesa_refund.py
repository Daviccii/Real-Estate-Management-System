from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class MpesaRefund(Base):
    """
    A refund issued against a succeeded M-Pesa collection.

    Deliberately a separate ledger from collections: the mpesa_transactions
    row (what Safaricom collected) is never mutated or deleted by a refund,
    and payment rows only get their settlement status recomputed — every
    refund is its own auditable record with its own reason.

    The integration does NOT move money: sending funds back to a tenant's
    phone requires the Daraja B2C API and Safaricom-issued initiator
    credentials, which are not part of this deployment. A refund recorded
    here documents a reversal the landlord performed through their own M-Pesa
    channels (app reversal, *334# transaction reversal, or agent visit) —
    `reversal_reference` is the transaction code of that reversal as it
    appears on the landlord's M-Pesa statement. Recording one adjusts the
    rent ledger honestly: the credited obligation is reopened to the net
    amount still collected.
    """

    __tablename__ = "mpesa_refunds"

    id = Column(Integer, primary_key=True, index=True)
    mpesa_transaction_id = Column(
        Integer, ForeignKey("mpesa_transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Denormalized from the transaction; SET NULL keeps the audit trail if
    # the obligation is later removed.
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="KES")
    reason = Column(String(500), nullable=False)
    # M-Pesa transaction code of the landlord-side reversal (their statement).
    reversal_reference = Column(String(64), nullable=True)
    # "recorded" — a documented manual reversal. Future B2C integrations may
    # add processing/completed states; the column exists so that addition
    # needs no schema change.
    status = Column(String(30), nullable=False, default="recorded", index=True)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    transaction = relationship("MpesaTransaction", foreign_keys=[mpesa_transaction_id])
    recorded_by_user = relationship("User", foreign_keys=[recorded_by])
