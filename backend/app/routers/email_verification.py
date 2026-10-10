"""
Email Verification Endpoints

API endpoints for email verification functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.auth.roles import get_current_user
from app.models.user import User
from app.services.email_verification_service import (
    verify_email,
    resend_verification_email,
    send_verification_on_registration
)

router = APIRouter(prefix="/email-verification", tags=["email-verification"])


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    base_url: str = "http://localhost:5173"


@router.post("/verify")
def verify_email_endpoint(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify email using a token.
    
    This endpoint is called when a user clicks the verification link in their email.
    """
    success, error_message, user = verify_email(db, request.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Verification failed"
        )
    
    return {
        "message": "Email verified successfully",
        "user_id": user.id,
        "email": user.email
    }


@router.post("/resend")
async def resend_verification(
    request: ResendVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend verification email to the current user.
    
    Users can request a new verification email if the previous one expired
    or was not received.
    """
    success, error_message = resend_verification_email(
        db,
        current_user.id,
        request.base_url
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Failed to resend verification email"
        )
    
    return {"message": "Verification email sent successfully"}


@router.get("/status")
def get_verification_status(current_user: User = Depends(get_current_user)):
    """
    Get the current user's email verification status.
    """
    return {
        "is_verified": current_user.is_verified,
        "email": current_user.email
    }
