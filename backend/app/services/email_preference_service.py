"""
Email preference store: single opt-out toggle for notification emails.

No row means opted in - absence must not silently suppress mail, so callers
ask notifications_opted_in() rather than reading the model directly.
"""
from sqlalchemy.orm import Session

from app.models.email_preference import EmailPreference
from app.utils.time import utc_now


def get_preference(db: Session, user_id: int) -> EmailPreference | None:
    return db.query(EmailPreference).filter(EmailPreference.user_id == user_id).first()


def set_preference(db: Session, user_id: int, *, notifications_enabled: bool) -> EmailPreference:
    preference = get_preference(db, user_id)
    if preference is None:
        preference = EmailPreference(user_id=user_id, notifications_enabled=notifications_enabled)
        db.add(preference)
    else:
        preference.notifications_enabled = notifications_enabled
        preference.updated_at = utc_now()
    db.commit()
    db.refresh(preference)
    return preference


def notifications_opted_in(db: Session, user_id: int) -> bool:
    preference = get_preference(db, user_id)
    return True if preference is None else preference.notifications_enabled
