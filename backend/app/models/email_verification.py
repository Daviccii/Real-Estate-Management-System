"""
Email Verification Model

Stores email verification tokens for user account verification.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.utils.time import utc_now


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    user = relationship("User", back_populates="email_verifications")
