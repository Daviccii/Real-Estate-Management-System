"""
MFA Endpoints

TOTP enrollment/verification, SMS backup codes, recovery codes, and the
post-login second-factor challenge.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.config.settings import settings
from app.database.database import get_db
from app.models.mfa import RecoveryCode
from app.schemas.role_profiles import AuthLoginResponse
from app.models.user import User
from app.observability.metrics import increment
from app.routers.auth import build_user_summary, get_dashboard_path
from app.services.security_events import emit_security_event
from app.services.mfa_service import (
    create_sms_challenge,
    disable_mfa,
    enable_mfa,
    regenerate_recovery_codes,
    resolve_mfa_user,
    setup_totp_secret,
    verify_second_factor,
)
from app.utils.totp import verify_totp

router = APIRouter(prefix="/auth/mfa", tags=["auth"])

# Optional bearer: MFA endpoints accept either a full session (management)
# or the short-lived mfa_token issued by login (challenge/enrollment).
bearer_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class MfaCodeRequest(BaseModel):
    code: str
    mfa_token: Optional[str] = None


class SendSmsRequest(BaseModel):
    mfa_token: Optional[str] = None


class MfaVerifyRequest(BaseModel):
    mfa_token: str
    method: str = "totp"
    code: str

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"totp", "sms", "recovery"}
        if v not in allowed:
            raise ValueError(f"Invalid method. Must be one of: {', '.join(sorted(allowed))}")
        return v


def _user_from_bearer(token: str, db: Session) -> Optional[User]:
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None


def resolve_user(db: Session, bearer_token: Optional[str], mfa_token: Optional[str]) -> User:
    """Resolve the acting user from either a valid access token or an mfa_token."""
    if bearer_token:
        user = _user_from_bearer(bearer_token, db)
        if user:
            return user
    if mfa_token:
        user = resolve_mfa_user(db, mfa_token)
        if user:
            return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a valid session token or MFA challenge token",
    )


@router.get("/status")
def mfa_status(
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    if not bearer_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    current_user = resolve_user(db, bearer_token, None)
    remaining = (
        db.query(RecoveryCode)
        .filter(RecoveryCode.user_id == current_user.id, RecoveryCode.used_at == None)  # noqa: E711
        .count()
    )
    return {
        "mfa_enabled": bool(current_user.mfa_enabled),
        "has_secret": bool(current_user.mfa_secret),
        "sms_available": bool(current_user.phone),
        "recovery_codes_remaining": remaining,
        "mandatory_for_admin": settings.MFA_MANDATORY_FOR_ADMIN,
    }


@router.post("/setup")
def mfa_setup(
    payload: SendSmsRequest,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    """Generate a TOTP secret + provisioning URI. Does not enable MFA yet."""
    current_user = resolve_user(db, bearer_token, payload.mfa_token)
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it first to re-enroll.",
        )
    secret, provisioning_uri = setup_totp_secret(db, current_user)
    increment("mfa_setups_total")
    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "issuer": settings.MFA_ISSUER_NAME,
        "account": current_user.email,
        "message": "Add this account to Google Authenticator (or scan the URI as a QR), then POST /auth/mfa/enable with the 6-digit code.",
    }


@router.post("/enable")
def mfa_enable(
    payload: MfaCodeRequest,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    """Verify a TOTP code to activate MFA. Returns recovery codes exactly once."""
    current_user = resolve_user(db, bearer_token, payload.mfa_token)
    success, error_message, recovery_codes = enable_mfa(db, current_user, payload.code)
    if not success:
        increment("mfa_failures_total")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    increment("mfa_enabled_total")
    return {
        "message": "MFA enabled",
        "recovery_codes": recovery_codes,
        "warning": "Store these recovery codes safely. Each works once if you lose your authenticator.",
    }


@router.post("/disable")
def mfa_disable(
    payload: MfaCodeRequest,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    """Disable MFA after verifying a current factor."""
    if not bearer_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    current_user = resolve_user(db, bearer_token, payload.mfa_token)
    success, error_message = disable_mfa(db, current_user, payload.code)
    if not success:
        increment("mfa_failures_total")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    increment("mfa_disabled_total")
    return {"message": "MFA disabled"}


@router.post("/recovery-codes/regenerate")
def mfa_regenerate_recovery(
    payload: MfaCodeRequest,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    """Issue a fresh set of recovery codes (old ones are invalidated). Requires a current TOTP code."""
    if not bearer_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    current_user = resolve_user(db, bearer_token, payload.mfa_token)
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")
    if not current_user.mfa_secret or not verify_totp(current_user.mfa_secret, payload.code):
        increment("mfa_failures_total")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authenticator code")
    codes = regenerate_recovery_codes(db, current_user)
    return {"recovery_codes": codes, "warning": "Previous recovery codes are no longer valid."}


@router.post("/send-sms")
def mfa_send_sms(
    payload: SendSmsRequest,
    db: Session = Depends(get_db),
    bearer_token: Optional[str] = Depends(bearer_scheme),
):
    """Send a backup 6-digit SMS code (in dev this is logged to console)."""
    current_user = resolve_user(db, bearer_token, payload.mfa_token)
    success, error_message, dev_code = create_sms_challenge(db, current_user)
    if not success:
        increment("mfa_sms_send_failures_total")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message or "SMS delivery failed")
    increment("mfa_sms_sent_total")
    result = {"message": f"SMS code sent to the phone ending {current_user.phone[-4:]}"}
    # Development-only convenience (mirrors dev email logging); never present in production.
    if settings.is_development and dev_code:
        result["dev_code"] = dev_code
    return result


@router.post("/verify", response_model=AuthLoginResponse)
def mfa_verify(
    payload: MfaVerifyRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Complete the login challenge: exchange the mfa_token plus a valid second
    factor for a full session (access token + refresh cookie).
    """
    current_user = resolve_mfa_user(db, payload.mfa_token)
    if not current_user:
        increment("mfa_failures_total")
        emit_security_event("auth.mfa_failed", request=request, details={"reason": "invalid_mfa_token"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired MFA token")

    success, error_message = verify_second_factor(db, current_user, payload.method, payload.code)
    if not success:
        increment("mfa_failures_total")
        emit_security_event(
            "auth.mfa_failed",
            request=request,
            user_id=current_user.id,
            actor=current_user.email,
            details={"method": payload.method},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
    increment("mfa_verified_total")

    access = create_access_token({"sub": str(current_user.id), "role": current_user.role})
    refresh = create_refresh_token({"sub": str(current_user.id)})
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/",
    )
    return {
        "access_token": access,
        "token_type": "bearer",
        "redirect_url": get_dashboard_path(current_user.role),
        "user": build_user_summary(current_user, db),
    }
