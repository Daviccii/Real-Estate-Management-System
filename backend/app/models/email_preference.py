"""
Per-user email delivery preference.

Only *non-transactional* email is gated by this row: the in-app notification
fan-out in notification_repo checks it before emailing. Security and account
emails (verification, password reset, deletion receipts) are always sent.
No row means opted in (default True) - absence must not silently suppress mail.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship

from app.models.base import Base
from app.utils.time import utc_now


class EmailPreference(Base):
    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", backref=backref("email_preference", uselist=False))
