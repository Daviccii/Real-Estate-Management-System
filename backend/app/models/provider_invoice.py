from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class ProviderInvoice(Base):
    __tablename__ = "provider_invoices"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_number = Column(String(80), nullable=False, unique=True)
    amount = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="submitted")
    description = Column(Text, nullable=True)
    issued_at = Column(DateTime, nullable=False, default=utc_now)
    due_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    provider = relationship("User", foreign_keys=[provider_id])
    maintenance = relationship("Maintenance", foreign_keys=[maintenance_id])
