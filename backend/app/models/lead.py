from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prospect_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Lead pipeline stages:
    # new -> contacted -> interested -> viewing -> applied -> approved -> closed (or lost)
    stage = Column(String(50), nullable=False, default="new", index=True)
    
    prospect_name = Column(String(255), nullable=True)
    prospect_email = Column(String(255), nullable=True)
    prospect_phone = Column(String(100), nullable=True)
    
    estimated_budget = Column(String(100), nullable=True)
    preferred_location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    commission_amount = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    agent = relationship("User", foreign_keys=[agent_id], backref="agent_leads")
    prospect = relationship("User", foreign_keys=[prospect_id], backref="prospect_leads")
    property = relationship("Property", foreign_keys=[property_id], backref="property_leads")
    inquiry = relationship("Inquiry", foreign_keys=[inquiry_id])
