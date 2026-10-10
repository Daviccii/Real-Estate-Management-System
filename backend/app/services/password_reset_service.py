"""
Password Reset Service

Implements secure, token-based password reset:
- Single-use, expiring reset tokens (only the SHA-256 hash is stored)
- Password history so recently used passwords cannot be reused
- Sessions revoked after a successful reset
"""
import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.password_reset import PasswordHistory, PasswordResetToken
from app.models.user import User
from app.services.email_service import email_service
from app.utils.security import get_password_hash, verify_password
from app.utils.time import as_utc, utc_now

logger = logging.getLogger(__name__)


def _hash_token(token: str) -> str:
    """Hash a reset token so a database leak cannot be used to reset passwords."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def record_password_history(db: Session, user_id: int, hashed_password: str) -> None:
    """Store a password hash in the rolling history and trim to PASSWORD_HISTORY_LIMIT."""
    db.add(PasswordHistory(user_id=user_id, hashed_password=hashed_password))
    db.commit()

    all_history = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc(), PasswordHistory.id.desc())
        .all()
    )
    for stale in all_history[settings.PASSWORD_HISTORY_LIMIT:]:
        db.delete(stale)
    db.commit()


def password_in_history(db: Session, user_id: int, new_password: str) -> bool:
    """Check whether the candidate password matches any stored history hash."""
    entries = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc(), PasswordHistory.id.desc())
        .limit(settings.PASSWORD_HISTORY_LIMIT)
        .all()
    )
    return any(verify_password(new_password, entry.hashed_password) for entry in entries)


def create_reset_token(db: Session, user_id: int) -> str:
    """
    Invalidate outstanding tokens for the user and issue a new one.

    Returns the raw token (only its hash is persisted); the caller embeds it
    in the emailed reset link.
    """
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used_at == None,  # noqa: E711
    ).delete()

    raw_token = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    db.add(
        PasswordResetToken(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
    )
    db.commit()
    return raw_token


def send_password_reset(db: Session, email: str, base_url: str = "http://localhost:5173") -> bool:
    """
    Issue and email a reset link for the account matching `email`.

    Returns True if a reset email was dispatched. Callers should not reveal
    whether the account exists; treat False as the same user-facing outcome.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.info("Password reset requested for unknown email", extra={"email": email})
        return False

    raw_token = create_reset_token(db, user.id)
    reset_url = f"{base_url}/reset-password?token={raw_token}"
    return email_service.send_password_reset_email(
        email=user.email,
        reset_url=reset_url,
        user_name=user.full_name,
    )


def reset_password(
    db: Session,
    token: str,
    new_password: str,
) -> tuple[bool, Optional[str], Optional[User]]:
    """
    Consume a reset token and set a new password.

    Returns:
        (success, error_message, user)
    """
    token_hash = _hash_token(token)
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None,  # noqa: E711
    ).first()

    if not reset:
        return False, "Invalid or expired reset token", None
    if as_utc(reset.expires_at) < utc_now():
        return False, "Reset token has expired", None

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        return False, "User not found", None

    if password_in_history(db, user.id, new_password) or verify_password(new_password, user.hashed_password):
        return False, "You have used this password before. Please choose a new one", None

    # get_password_hash validates strength and raises ValueError on failure
    try:
        new_hash = get_password_hash(new_password)
    except ValueError as exc:
        return False, str(exc), None

    # Archive the password being replaced so it counts toward the reuse block.
    record_password_history(db, user.id, user.hashed_password)
    user.hashed_password = new_hash

    reset.used_at = utc_now()
    # Invalidate any other outstanding tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at == None,  # noqa: E711
    ).update({PasswordResetToken.used_at: utc_now()}, synchronize_session=False)

    db.commit()
    logger.info("Password reset completed", extra={"user_id": user.id})
    return True, None, user
