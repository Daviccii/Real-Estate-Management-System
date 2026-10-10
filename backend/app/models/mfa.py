"""
MFA Models

- RecoveryCode: single-use backup codes issued when MFA is enabled
- SmsChallenge: short-lived hashed SMS OTP codes (backup second factor)
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class RecoveryCode(Base):
    __tablename__ = "mfa_recovery_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(64), unique=True, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="mfa_recovery_codes")


class SmsChallenge(Base):
    __tablename__ = "mfa_sms_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    code_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="mfa_sms_challenges")
