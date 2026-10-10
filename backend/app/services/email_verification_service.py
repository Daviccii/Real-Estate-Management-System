"""
Email Verification Service

Manages email verification tokens and verification process.
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.email_verification import EmailVerification
from app.utils.time import utc_now
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def create_email_verification(
    db: Session,
    user_id: int,
    email: str,
    expires_in_hours: int = 24
) -> EmailVerification:
    """
    Create an email verification token for a user.
    
    Args:
        db: Database session
        user_id: User ID
        email: Email address to verify
        expires_in_hours: Token expiration time in hours
    
    Returns:
        EmailVerification object
    """
    # Delete any existing unverified tokens for this user
    db.query(EmailVerification).filter(
        EmailVerification.user_id == user_id,
        EmailVerification.verified_at == None
    ).delete()
    
    # Generate new token
    token = generate_verification_token()
    expires_at = utc_now() + timedelta(hours=expires_in_hours)
    
    verification = EmailVerification(
        user_id=user_id,
        email=email,
        token=token,
        expires_at=expires_at
    )
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    return verification


def verify_email(db: Session, token: str) -> tuple[bool, Optional[str], Optional[User]]:
    """
    Verify an email using a verification token.
    
    Args:
        db: Database session
        token: Verification token
    
    Returns:
        (success: bool, error_message: str, user: User)
    """
    # Find verification record
    verification = db.query(EmailVerification).filter(
        EmailVerification.token == token,
        EmailVerification.verified_at == None
    ).first()
    
    if not verification:
        return False, "Invalid or expired verification token", None
    
    # Check if token is expired
    if verification.expires_at < utc_now():
        return False, "Verification token has expired", None
    
    # Get user
    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        return False, "User not found", None
    
    # Mark as verified
    verification.verified_at = utc_now()
    user.is_verified = True
    
    db.commit()
    
    logger.info(f"Email verified for user {user.email}", extra={"user_id": user.id})
    
    return True, None, user


def resend_verification_email(
    db: Session,
    user_id: int,
    base_url: str = "http://localhost:5173"
) -> tuple[bool, Optional[str]]:
    """
    Resend email verification email to a user.
    
    Args:
        db: Database session
        user_id: User ID
        base_url: Base URL for verification link
    
    Returns:
        (success: bool, error_message: str)
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, "User not found"
    
    # Check if already verified
    if user.is_verified:
        return False, "Email is already verified"
    
    # Create new verification token
    verification = create_email_verification(db, user_id, user.email)
    
    # Generate verification URL
    verification_url = f"{base_url}/verify-email?token={verification.token}"
    
    # Send email
    sent = email_service.send_verification_email(
        email=user.email,
        verification_url=verification_url,
        user_name=user.full_name
    )
    
    if not sent:
        return False, "Failed to send verification email"
    
    return True, None


def send_verification_on_registration(
    db: Session,
    user_id: int,
    base_url: str = "http://localhost:5173"
) -> bool:
    """
    Send verification email immediately after registration.
    
    Args:
        db: Database session
        user_id: User ID
        base_url: Base URL for verification link
    
    Returns:
        bool: True if email sent successfully
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    verification = create_email_verification(db, user_id, user.email)
    verification_url = f"{base_url}/verify-email?token={verification.token}"
    
    return email_service.send_verification_email(
        email=user.email,
        verification_url=verification_url,
        user_name=user.full_name
    )
