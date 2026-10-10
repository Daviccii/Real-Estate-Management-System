from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=False, default="medium", index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    cost = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("User", foreign_keys=[tenant_id])
    property = relationship("Property", backref="maintenance_requests")
    unit = relationship("Unit", backref="maintenance_requests")
    assigned_manager = relationship("User", foreign_keys=[assigned_manager_id])