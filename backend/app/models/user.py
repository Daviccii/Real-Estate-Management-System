from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.utils.time import utc_now

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    roles_csv = Column(String, default="user", nullable=True)  # Comma-separated roles for multi-role users
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(64), nullable=True)  # base32 TOTP secret
    created_at = Column(DateTime, nullable=True, default=utc_now)
    updated_at = Column(DateTime, nullable=True, default=utc_now, onupdate=utc_now)
    company = relationship("Company", back_populates="users")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    mfa_recovery_codes = relationship("RecoveryCode", back_populates="user", cascade="all, delete-orphan")
    mfa_sms_challenges = relationship("SmsChallenge", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    password_histories = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")

    def has_role(self, target_role: str) -> bool:
        if self.role == target_role:
            return True
        if self.roles_csv:
            return target_role in [r.strip() for r in self.roles_csv.split(",")]
        return False
