from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Lease(Base):
    __tablename__ = "leases"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    rent_amount = Column(String(100), nullable=False)
    deposit = Column(String(100), nullable=True)
    payment_due_date = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    tenant = relationship("User", foreign_keys=[tenant_id])
    unit = relationship("Unit", backref="leases")
    property = relationship("Property", backref="leases")