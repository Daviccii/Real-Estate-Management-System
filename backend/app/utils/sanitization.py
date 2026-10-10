"""
Input Sanitization Utilities

Provides functions to sanitize user-generated content to prevent XSS attacks
and other injection vulnerabilities.
"""
import re
from typing import Optional
from html import escape


def sanitize_html(text: Optional[str], allow_tags: Optional[list[str]] = None) -> str:
    """
    Sanitize HTML content by escaping all HTML tags except explicitly allowed ones.
    
    For maximum security, we default to escaping ALL HTML. If specific tags are needed,
    they must be explicitly whitelisted.
    
    Args:
        text: Input text to sanitize
        allow_tags: List of allowed HTML tags (e.g., ['p', 'br', 'strong'])
    
    Returns:
        Sanitized text with HTML escaped
    
    Note:
        For production, consider using a library like bleach or nh3 for more
        sophisticated HTML sanitization. This is a basic implementation.
    """
    if not text:
        return ""
    
    # If no tags are allowed, escape everything
    if not allow_tags:
        return escape(text)
    
    # If tags are allowed, use a more sophisticated approach
    # For now, we'll escape everything for security
    # TODO: Implement proper HTML sanitization with bleach library
    return escape(text)


def sanitize_string(text: Optional[str], max_length: int = 10000) -> str:
    """
    Sanitize a string by removing null bytes and limiting length.
    
    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.
    
    Args:
        filename: Input filename
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove path traversal attempts
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    
    # Remove null bytes
    filename = filename.replace("\x00", "")
    
    # Keep only safe characters (alphanumeric, underscore, hyphen, dot)
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def sanitize_url(url: Optional[str]) -> str:
    """
    Sanitize a URL by ensuring it starts with http:// or https://.
    
    Args:
        url: Input URL
    
    Returns:
        Sanitized URL or empty string if invalid
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Ensure URL starts with http:// or https://
    if not url.startswith(("http://", "https://")):
        return ""
    
    # Remove newlines and other dangerous characters
    url = re.sub(r"[\r\n\t]", "", url)
    
    return url


def sanitize_email(email: Optional[str]) -> str:
    """
    Sanitize an email address by removing dangerous characters.
    
    Args:
        email: Input email address
    
    Returns:
        Sanitized email or empty string if invalid
    """
    if not email:
        return ""
    
    email = email.strip().lower()
    
    # Basic email validation (prevent injection)
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return ""
    
    # Remove null bytes and newlines
    email = email.replace("\x00", "").replace("\n", "").replace("\r", "")
    
    return email


def sanitize_sql_like_pattern(pattern: Optional[str]) -> str:
    """
    Sanitize a SQL LIKE pattern by escaping special characters.
    
    Args:
        pattern: Input LIKE pattern
    
    Returns:
        Sanitized pattern with wildcards escaped
    """
    if not pattern:
        return ""
    
    # Escape SQL LIKE wildcards
    pattern = pattern.replace("%", "\\%").replace("_", "\\_")
    
    return pattern


def sanitize_json_field(value: any, max_length: int = 10000) -> any:
    """
    Sanitize a JSON field value recursively.
    
    Args:
        value: JSON value to sanitize
        max_length: Maximum string length
    
    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        return sanitize_string(value, max_length)
    elif isinstance(value, list):
        return [sanitize_json_field(item, max_length) for item in value]
    elif isinstance(value, dict):
        return {k: sanitize_json_field(v, max_length) for k, v in value.items()}
    else:
        return value


def detect_xss_attack(text: str) -> bool:
    """
    Detect potential XSS attack patterns in text.
    
    Args:
        text: Text to check
    
    Returns:
        True if XSS pattern detected
    """
    if not text:
        return False
    
    # Common XSS patterns
    xss_patterns = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"onclick=",
        r"onmouseover=",
        r"onfocus=",
        r"onblur=",
        r"eval\(",
        r"fromCharCode",
        r"document\.cookie",
        r"window\.location",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    text_lower = text.lower()
    for pattern in xss_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False


def sanitize_user_input(text: Optional[str], field_name: str = "input") -> str:
    """
    Comprehensive sanitization for user input.
    
    Args:
        text: User input to sanitize
        field_name: Name of the field (for logging)
    
    Returns:
        Sanitized text
    
    Raises:
        ValueError: If XSS attack detected
    """
    if not text:
        return ""
    
    # Check for XSS attacks
    if detect_xss_attack(text):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Potential XSS attack detected in field: {field_name}")
        raise ValueError("Invalid input detected")
    
    # Sanitize the text
    return sanitize_string(text)
