from typing import Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.utils.time import utc_now
from app.models.platform_settings import PlatformSettings


def get_or_create_settings(db: Session) -> PlatformSettings:
    """Singleton getter for platform settings."""
    settings = db.query(PlatformSettings).filter(PlatformSettings.id == 1).first()
    if not settings:
        settings = PlatformSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, settings_obj: PlatformSettings, updated_by_id: Optional[int] = None, **kwargs: Any) -> PlatformSettings:
    for key, value in kwargs.items():
        if hasattr(settings_obj, key) and value is not None:
            setattr(settings_obj, key, value)
    settings_obj.updated_at = utc_now()
    if updated_by_id:
        settings_obj.updated_by_id = updated_by_id
    db.commit()
    db.refresh(settings_obj)
    return settings_obj
