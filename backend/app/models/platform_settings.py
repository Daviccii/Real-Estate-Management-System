"""
Singleton table holding platform-wide configuration that admins can toggle
from the Settings page. Only one row ever exists (id=1) — see
platform_settings_repo.get_or_create_settings() for the singleton pattern.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Platform settings
    enable_user_registration = Column(Boolean, nullable=False, default=True)
    require_email_verification = Column(Boolean, nullable=False, default=False)
    enable_property_moderation = Column(Boolean, nullable=False, default=False)

    # Security settings
    session_timeout_minutes = Column(Integer, nullable=False, default=60)
    password_min_length = Column(Integer, nullable=False, default=8)

    # Notification settings
    notify_new_users = Column(Boolean, nullable=False, default=False)
    notify_new_inquiries = Column(Boolean, nullable=False, default=False)
    notify_property_updates = Column(Boolean, nullable=False, default=False)

    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by = relationship("User", foreign_keys=[updated_by_id])