from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class ProviderRating(Base):
    __tablename__ = "provider_ratings"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id", ondelete="SET NULL"), nullable=True)
    work_order_id = Column(Integer, ForeignKey("maintenance_work_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    provider = relationship("User", foreign_keys=[provider_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    maintenance = relationship("Maintenance", foreign_keys=[maintenance_id])
