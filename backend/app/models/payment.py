from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(String(100), nullable=False)
    payment_type = Column(String(50), nullable=True, index=True)
    payment_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    reference = Column(String(255), nullable=True)
    payment_method = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    tenant = relationship("User", foreign_keys=[tenant_id])
    lease = relationship("Lease", backref="payments")
    property = relationship("Property", backref="payments")
    unit = relationship("Unit", backref="payments")