from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # user, agent, owner, property, document, service_provider
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Status: unverified, pending, verified, rejected, expired
    status = Column(String(50), nullable=False, default="pending", index=True)
    
    verification_type = Column(String(100), nullable=False)  # government_id, license, title_deed, business_permit
    submitted_data_json = Column(Text, nullable=True)  # Document links, registration numbers, etc.
    
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    evidence = relationship("VerificationEvidence", back_populates="verification", cascade="all, delete-orphan")
