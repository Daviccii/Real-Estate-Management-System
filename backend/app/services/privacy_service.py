"""
Privacy / GDPR service.

Implements the three data-subject capabilities the frontend exposes:

- record_consent: append-only consent log (Art. 7(1) demonstrable consent)
- export_user_data: machine-readable copy of everything linked to the user
  (Art. 15 access / Art. 20 portability)
- request / cancel / execute account deletion (Art. 17 erasure)

Erasure is implemented as irreversible anonymization of the user row rather
than row deletion: lease, payment, application, and audit records carry
foreign keys to users.id and are retained under the legal-obligation /
contract exemption (Art. 17(3)(b)). Identity fields are replaced with
non-identifying values so the retained rows no longer reference a person.
"""
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

from sqlalchemy.orm import Session

from app.models import (
    ConsentRecord,
    DataDeletionRequest,
    Favorite,
    Notification,
    EmailVerification,
    PasswordResetToken,
    PasswordHistory,
    RecoveryCode,
    SmsChallenge,
    User,
)
from app.models.base import Base
from app.services.audit_service import log_audit_event
from app.services.email_service import email_service
from app.utils.security import hash_unusable_password
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

ANONYMIZED_NAME = "Deleted User"
REDACTED_FIELDS = {"hashed_password", "mfa_secret"}

# (model, fk attribute on the model, section label in the export)
EXPORT_RELATIONS: List[Tuple[Type[Base], str, str]] = [
    (Favorite, "user_id", "favorites"),
    (Notification, "recipient_id", "notifications"),
    (ConsentRecord, "user_id", "consents"),
]


def _serialize_row(obj: Any) -> Dict[str, Any]:
    result = {}
    for key, value in vars(obj).items():
        if key == "_sa_instance_state":
            continue
        if isinstance(value, datetime):
            value = value.isoformat()
        result[key] = value
    return result


def record_consent(
    db: Session,
    consent_type: str,
    granted: bool,
    user: Optional[User] = None,
    client_id: Optional[str] = None,
    policy_version: str = "1.0",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> ConsentRecord:
    """Append one consent decision. Never updates prior rows: history is the proof."""
    record = ConsentRecord(
        user_id=user.id if user else None,
        client_id=(client_id or None)[:64] if not user else None,
        consent_type=consent_type[:50],
        granted=bool(granted),
        policy_version=policy_version[:20],
        ip_address=ip_address,
        user_agent=(user_agent or None)[:255],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def export_user_data(db: Session, user: User) -> Dict[str, Any]:
    """Build the full machine-readable export for one user."""
    data = {
        "profile": _serialize_row(user),
        "related_data": {},
        "generated_at": utc_now().isoformat(),
    }
    # Secrets never leave the database, even in the owner's own export.
    for field in REDACTED_FIELDS:
        data["profile"][field] = "[REDACTED]"

    for model, fk_column, label in EXPORT_RELATIONS:
        rows = db.query(model).filter(getattr(model, fk_column) == user.id).all()
        data["related_data"][label] = [_serialize_row(r) for r in rows]
    return data


def get_active_deletion_request(db: Session, user_id: int) -> Optional[DataDeletionRequest]:
    return (
        db.query(DataDeletionRequest)
        .filter(DataDeletionRequest.user_id == user_id, DataDeletionRequest.status == "pending")
        .first()
    )


def request_account_deletion(
    db: Session,
    user: User,
    reason: Optional[str] = None,
) -> Tuple[DataDeletionRequest, bool]:
    """Create a pending erasure request. Idempotent while one is already pending."""
    existing = get_active_deletion_request(db, user.id)
    if existing:
        return existing, False

    request = DataDeletionRequest(user_id=user.id, reason=reason)
    db.add(request)
    db.commit()
    db.refresh(request)

    log_audit_event(db, user.id, "DELETION_REQUESTED", entity_type="user", entity_id=user.id)
    email_service.send_notification_email(
        email=user.email,
        subject="Account deletion request received",
        message=(
            "We received your request to delete your account. Our team will process it "
            "shortly. You can cancel the request from your profile page until it is executed."
        ),
        user_name=user.full_name,
    )
    return request, True


def cancel_account_deletion(db: Session, user: User) -> bool:
    """Withdraw a pending request. Returns False when nothing is pending."""
    request = get_active_deletion_request(db, user.id)
    if not request:
        return False
    request.status = "cancelled"
    request.processed_at = utc_now()
    db.commit()
    log_audit_event(db, user.id, "DELETION_CANCELLED", entity_type="user", entity_id=user.id)
    return True


def _wipe_auth_data(db: Session, user_id: int) -> None:
    for model in (PasswordResetToken, EmailVerification, RecoveryCode, SmsChallenge):
        db.query(model).filter(model.user_id == user_id).delete()
    # Password history rows contain old hashes of the deleted identity.
    db.query(PasswordHistory).filter(PasswordHistory.user_id == user_id).delete()


def execute_account_deletion(
    db: Session,
    request: DataDeletionRequest,
    admin: User,
) -> Dict[str, Any]:
    """Anonymize the user and close out the request. Irreversible."""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        request.status = "declined"
        request.notes = "User no longer exists"
        request.processed_at = utc_now()
        request.processed_by = admin.id
        db.commit()
        return {"status": "declined", "reason": "User no longer exists"}

    favorites_removed = (
        db.query(Favorite).filter(Favorite.user_id == user.id).delete(synchronize_session=False)
    )
    notifications_removed = (
        db.query(Notification)
        .filter(Notification.recipient_id == user.id)
        .delete(synchronize_session=False)
    )
    _wipe_auth_data(db, user.id)

    # Unique constraint on email requires a unique replacement value.
    user.full_name = ANONYMIZED_NAME
    user.email = f"deleted+{user.id}@anonymized.invalid"
    user.phone = None
    user.avatar_url = None
    user.roles_csv = None
    user.company_id = None
    user.mfa_enabled = False
    user.mfa_secret = None
    user.is_active = False
    user.is_verified = False
    # Unusable random password: the account can never authenticate again.
    user.hashed_password = hash_unusable_password(secrets.token_urlsafe(48))

    request.status = "completed"
    request.processed_at = utc_now()
    request.processed_by = admin.id

    db.commit()

    log_audit_event(
        db,
        admin.id,
        "DELETION_EXECUTED",
        entity_type="user",
        entity_id=user.id,
        details={"request_id": request.id, "favorites_removed": favorites_removed,
                 "notifications_removed": notifications_removed},
    )
    return {
        "status": "completed",
        "user_id": user.id,
        "favorites_removed": favorites_removed,
        "notifications_removed": notifications_removed,
    }


def decline_account_deletion(db: Session, request: DataDeletionRequest, admin: User, notes: Optional[str] = None) -> DataDeletionRequest:
    request.status = "declined"
    request.notes = notes
    request.processed_at = utc_now()
    request.processed_by = admin.id
    db.commit()
    log_audit_event(db, admin.id, "DELETION_DECLINED", entity_type="user", entity_id=request.user_id)
    return request
