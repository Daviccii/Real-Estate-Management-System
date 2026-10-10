"""
MFA Service

TOTP enrollment/verification, single-use recovery codes, and SMS backup
codes. Also issues the short-lived "mfa" token used between password
verification and full session issuance at login.
"""
import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.config.settings import settings
from app.models.mfa import RecoveryCode, SmsChallenge
from app.models.user import User
from app.services.sms_service import sms_service
from app.utils.time import as_utc, utc_now
from app.utils.totp import (
    build_provisioning_uri,
    generate_recovery_codes,
    generate_totp_secret,
    verify_totp,
)

logger = logging.getLogger(__name__)

ALLOWED_MFA_METHODS = {"totp", "sms", "recovery"}


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Login challenge token (type="mfa"): proves the password was correct but
# grants nothing until the second factor is verified.
# ---------------------------------------------------------------------------

def create_mfa_token(user_id: int) -> str:
    expire = utc_now() + timedelta(minutes=settings.MFA_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "mfa",
        "exp": expire,
        "iat": int(utc_now().timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def resolve_mfa_user(db: Session, mfa_token: str) -> Optional[User]:
    """Return the user for a valid, unused mfa_token, else None."""
    try:
        payload = decode_token(mfa_token)
    except Exception:
        return None
    if payload.get("type") != "mfa":
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    return user


# ---------------------------------------------------------------------------
# TOTP enrollment
# ---------------------------------------------------------------------------

def setup_totp_secret(db: Session, user: User) -> tuple[str, str]:
    """
    Generate and store a new TOTP secret (does NOT enable MFA yet).

    Returns (secret, provisioning_uri).
    """
    secret = generate_totp_secret()
    user.mfa_secret = secret
    db.commit()
    uri = build_provisioning_uri(secret, user.email, settings.MFA_ISSUER_NAME)
    return secret, uri


def enable_mfa(db: Session, user: User, code: str) -> tuple[bool, Optional[str], list[str]]:
    """
    Enable MFA after the user proves possession with a valid TOTP code.

    Returns (success, error_message, recovery_codes).
    """
    if not user.mfa_secret:
        return False, "MFA setup not started. Call the setup endpoint first.", []
    if user.mfa_enabled:
        return False, "MFA is already enabled on this account.", []
    if not verify_totp(user.mfa_secret, code):
        return False, "Invalid verification code", []

    user.mfa_enabled = True
    db.commit()
    recovery_codes = _issue_recovery_codes(db, user.id)
    logger.info("MFA enabled", extra={"user_id": user.id})
    return True, None, recovery_codes


def disable_mfa(db: Session, user: User, code: str) -> tuple[bool, Optional[str]]:
    """Disable MFA after verifying a current factor (TOTP, recovery, or SMS-free
    password confirmation is intentionally excluded to keep this a factor check)."""
    if not user.mfa_enabled:
        return False, "MFA is not enabled"
    if not verify_totp(user.mfa_secret or "", code) and not verify_recovery_code(db, user.id, code):
        return False, "Invalid verification code"

    user.mfa_enabled = False
    user.mfa_secret = None
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user.id).delete()
    db.commit()
    logger.info("MFA disabled", extra={"user_id": user.id})
    return True, None


# ---------------------------------------------------------------------------
# Recovery codes
# ---------------------------------------------------------------------------

def _issue_recovery_codes(db: Session, user_id: int) -> list[str]:
    db.query(RecoveryCode).filter(RecoveryCode.user_id == user_id).delete()
    raw_codes = generate_recovery_codes(settings.MFA_RECOVERY_CODE_COUNT)
    for raw in raw_codes:
        db.add(RecoveryCode(user_id=user_id, code_hash=_hash_code(raw)))
    db.commit()
    return raw_codes


def regenerate_recovery_codes(db: Session, user: User) -> list[str]:
    return _issue_recovery_codes(db, user.id)


def verify_recovery_code(db: Session, user_id: int, code: str) -> bool:
    """Verify and consume a single-use recovery code."""
    record = db.query(RecoveryCode).filter(
        RecoveryCode.user_id == user_id,
        RecoveryCode.code_hash == _hash_code(code),
        RecoveryCode.used_at == None,  # noqa: E711
    ).first()
    if not record:
        return False
    record.used_at = utc_now()
    db.commit()
    return True


# ---------------------------------------------------------------------------
# SMS backup codes
# ---------------------------------------------------------------------------

def create_sms_challenge(db: Session, user: User) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Generate a 6-digit SMS code, store its hash, and dispatch it.

    Returns (sent, error_message, raw_code) - raw_code is only safe to surface
    in development (see the router); the stored record keeps just the hash.
    """
    if not user.phone:
        return False, "No phone number on this account for SMS delivery", None

    db.query(SmsChallenge).filter(
        SmsChallenge.user_id == user.id,
        SmsChallenge.used_at == None,  # noqa: E711
    ).delete()

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = utc_now() + timedelta(minutes=settings.MFA_SMS_CODE_EXPIRE_MINUTES)
    db.add(
        SmsChallenge(
            user_id=user.id,
            phone=user.phone,
            code_hash=_hash_code(code),
            expires_at=expires_at,
        )
    )
    db.commit()

    sent = sms_service.send_otp(user.phone, code, user.full_name)
    return sent, None if sent else "SMS delivery failed", code


def verify_sms_code(db: Session, user_id: int, code: str) -> bool:
    """Verify and consume an SMS code."""
    challenge = db.query(SmsChallenge).filter(
        SmsChallenge.user_id == user_id,
        SmsChallenge.code_hash == _hash_code(code),
        SmsChallenge.used_at == None,  # noqa: E711
    ).first()
    if not challenge:
        return False
    if as_utc(challenge.expires_at) < utc_now():
        return False
    challenge.used_at = utc_now()
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Verification dispatcher (used by the login challenge)
# ---------------------------------------------------------------------------

def verify_second_factor(db: Session, user: User, method: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Verify a second factor for a user.

    Returns (success, error_message).
    """
    if method not in ALLOWED_MFA_METHODS:
        return False, f"Invalid method. Expected one of: {', '.join(sorted(ALLOWED_MFA_METHODS))}"

    if method == "recovery":
        ok = verify_recovery_code(db, user.id, code)
        return (True, None) if ok else (False, "Invalid or already-used recovery code")

    if method == "sms":
        ok = verify_sms_code(db, user.id, code)
        return (True, None) if ok else (False, "Invalid or expired SMS code")

    # totp
    if not user.mfa_secret or not verify_totp(user.mfa_secret, code):
        return False, "Invalid authenticator code"
    return True, None
