from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PlatformSettingsBase(BaseModel):
    enable_user_registration: bool = True
    require_email_verification: bool = False
    enable_property_moderation: bool = False
    session_timeout_minutes: int = 60
    password_min_length: int = 8
    notify_new_users: bool = False
    notify_new_inquiries: bool = False
    notify_property_updates: bool = False


class PlatformSettingsUpdate(BaseModel):
    enable_user_registration: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    enable_property_moderation: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    password_min_length: Optional[int] = None
    notify_new_users: Optional[bool] = None
    notify_new_inquiries: Optional[bool] = None
    notify_property_updates: Optional[bool] = None


class PlatformSettingsOut(PlatformSettingsBase):
    id: int
    updated_at: datetime
    updated_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
