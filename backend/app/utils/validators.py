"""
Custom Pydantic validators for input sanitization.
"""
from pydantic import field_validator
from typing import Optional

from app.utils.sanitization import sanitize_string, sanitize_email, sanitize_url, detect_xss_attack


class SanitizedStringMixin:
    """
    Mixin class that provides sanitized string validators for Pydantic models.
    """
    
    @field_validator("*", mode="before")
    @classmethod
    def sanitize_string_fields(cls, v, info):
        """
        Automatically sanitize all string fields in the model.
        """
        if isinstance(v, str) and info.field_name:
            # Skip certain fields that should not be sanitized
            skip_fields = ["hashed_password", "password"]  # Passwords are handled separately
            if info.field_name in skip_fields:
                return v
            
            # Check for XSS attacks
            if detect_xss_attack(v):
                raise ValueError(f"Invalid characters detected in {info.field_name}")
            
            # Sanitize the string
            return sanitize_string(v, max_length=10000)
        
        return v


def sanitize_email_field(v: Optional[str]) -> Optional[str]:
    """Validator for email fields."""
    if v is None:
        return None
    return sanitize_email(v)


def sanitize_url_field(v: Optional[str]) -> Optional[str]:
    """Validator for URL fields."""
    if v is None:
        return None
    return sanitize_url(v)


def sanitize_description_field(v: Optional[str]) -> Optional[str]:
    """Validator for description/text fields with higher length limit."""
    if v is None:
        return None
    if detect_xss_attack(v):
        raise ValueError("Invalid characters detected in description")
    return sanitize_string(v, max_length=50000)
