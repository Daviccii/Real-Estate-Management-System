from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Time, Index
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Viewing(Base):
    __tablename__ = "viewings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True)
    prospect_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    host_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # agent or manager
    
    # Timing
    viewing_date = Column(String(50), nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String(20), nullable=False)  # HH:MM
    end_time = Column(String(20), nullable=False)    # HH:MM
    
    # Status: requested, confirmed, completed, cancelled, rescheduled
    status = Column(String(50), nullable=False, default="requested", index=True)
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    property = relationship("Property", backref="viewings")
    unit = relationship("Unit", backref="viewings")
    prospect = relationship("User", foreign_keys=[prospect_id], backref="requested_viewings")
    host_user = relationship("User", foreign_keys=[host_user_id], backref="hosted_viewings")

    __table_args__ = (
        Index("ix_viewing_host_schedule", "host_user_id", "viewing_date", "start_time"),
    )
