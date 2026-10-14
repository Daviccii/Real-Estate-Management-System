from sqlalchemy import (
    Boolean,
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


class MpesaTransaction(Base):
    """
    One M-Pesa STK Push collection attempt for a rent obligation.

    The `payments` table stays the rent ledger (what is owed); this table is
    the collection attempt trail (what was asked of Safaricom and what came
    back). A successful transaction is applied to its Payment exactly once —
    guarded by the atomic status claim in mpesa_service.process_callback and
    the `applied_to_payment` flag — so replays and concurrent callbacks can
    never double-credit the same obligation.

    Status lifecycle (terminal states never transition again):
        pending           request being submitted to Daraja
        awaiting_callback STK accepted; waiting for the customer to enter PIN
        succeeded         ResultCode 0, receipt recorded, ledger credited
        failed            definite rejection (insufficient funds, wrong PIN, ...)
        cancelled         customer cancelled the prompt (ResultCode 1032)
        timed_out         no response from the customer (ResultCode 1037)
        expired           request expired before completion (ResultCode 1019)
        unknown           outcome unverifiable (network timeout after submit,
                          amount mismatch) — resolve via reconciliation
    """

    __tablename__ = "mpesa_transactions"

    id = Column(Integer, primary_key=True, index=True)
    # Human-readable internal reference (MPX-XXXXXXXX) for support and receipts.
    reference = Column(String(40), nullable=False, unique=True, index=True)

    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    # Allocation snapshot: whose collection this payment belongs to. SET NULL so
    # the audit trail survives account removal without dangling references.
    landlord_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="KES")
    channel = Column(String(30), nullable=False, default="mpesa_stk")
    # Normalized Daraja format (2547XXXXXXXX). Masked in every API response.
    phone_number = Column(String(20), nullable=False)

    status = Column(String(30), nullable=False, default="pending", index=True)
    result_code = Column(Integer, nullable=True)
    result_description = Column(String(500), nullable=True)
    failure_reason = Column(String(255), nullable=True)

    merchant_request_id = Column(String(64), nullable=True, index=True)
    # Unique nullable column: reconciliation and callback matching key on this.
    checkout_request_id = Column(String(64), nullable=True, unique=True)
    # Safaricom receipt code (e.g. "SJK3X1ABC"); unique so one receipt can
    # never be recorded against two transactions.
    mpesa_receipt_number = Column(String(64), nullable=True, unique=True, index=True)

    # True once the linked Payment ledger row was credited by this transaction.
    applied_to_payment = Column(Boolean, nullable=False, default=False)
    # Counts callback deliveries (including replays) for audit/investigation.
    callback_attempts = Column(Integer, nullable=False, default=0)

    initiated_at = Column(DateTime, nullable=False, default=utc_now)
    callback_received_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    payment = relationship("Payment", foreign_keys=[payment_id])
    tenant = relationship("User", foreign_keys=[tenant_id])
    lease = relationship("Lease", foreign_keys=[lease_id])
    property = relationship("Property", foreign_keys=[property_id])
    unit = relationship("Unit", foreign_keys=[unit_id])
    landlord = relationship("User", foreign_keys=[landlord_id])
