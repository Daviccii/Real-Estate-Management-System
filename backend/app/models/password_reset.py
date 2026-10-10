"""
Password Reset & History Models

Stores single-use, expiring password reset tokens and a rolling history of
previously used password hashes so old passwords cannot be reused.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # SHA-256 hash of the token; the raw token only ever exists in the email link
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="password_reset_tokens")


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="password_histories")
