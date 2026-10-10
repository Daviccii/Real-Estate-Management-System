"""
Password Reset Endpoints

Forgot-password and reset-password flows.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.auth.roles import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.services.account_lockout import clear_failed_login_attempts
from app.services.password_reset_service import (
    password_in_history,
    record_password_history,
    reset_password,
    send_password_reset,
)
from app.services.security_events import emit_security_event
from app.services.token_revocation import revoke_all_user_tokens
from app.utils.security import get_password_hash, validate_password_strength, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    base_url: str = "http://localhost:5173"


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password", mode="before")
    @classmethod
    def check_password_length(cls, v):
        if not isinstance(v, str):
            v = str(v)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be 72 bytes or fewer")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password", mode="before")
    @classmethod
    def check_password_length(cls, v):
        if not isinstance(v, str):
            v = str(v)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be 72 bytes or fewer")
        return v


GENERIC_RESET_MESSAGE = "If an account exists for that email, a reset link has been sent."


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Start a password reset. Always returns the same response, whether or not
    the email exists, to avoid account enumeration.
    """
    emit_security_event(
        "auth.password_reset_requested",
        request=request,
        actor=payload.email,
        severity="info",
    )
    try:
        send_password_reset(db, payload.email, payload.base_url)
    except Exception as exc:
        # Never leak internals; the user still sees the generic message.
        # Ops still see the failure (type only - exception text may contain relay data).
        emit_security_event(
            "auth.password_reset_delivery_failed",
            request=request,
            actor=payload.email,
            details={"error_type": type(exc).__name__},
        )
    return {"message": GENERIC_RESET_MESSAGE}


@router.post("/reset-password")
async def reset_password_endpoint(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Complete a password reset using a emailed token."""
    success, error_message, user = reset_password(db, payload.token, payload.new_password)

    if not success:
        emit_security_event("auth.password_reset_rejected", request=request, details={"reason": error_message})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    # Force re-authentication everywhere and clear any failed-login lockout.
    await revoke_all_user_tokens(user.id)
    await clear_failed_login_attempts(user.email)
    emit_security_event(
        "auth.password_reset_completed",
        request=request,
        user_id=user.id,
        actor=user.email,
        outcome="allowed",
        severity="info",
    )
    return {"message": "Password reset successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change password while authenticated. Enforces strength and history checks,
    then revokes all sessions so the change takes effect immediately.
    """
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    is_valid, error_message = validate_password_strength(payload.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    if password_in_history(db, current_user.id, payload.new_password) or verify_password(
        payload.new_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have used this password before. Please choose a new one",
        )

    previous_hash = current_user.hashed_password
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    # Archive the password being replaced so it counts toward the reuse block.
    record_password_history(db, current_user.id, previous_hash)

    await revoke_all_user_tokens(current_user.id)
    return {"message": "Password changed successfully"}
