import re
from passlib.context import CryptContext

# prefer pbkdf2_sha256 (pure-Python) and keep bcrypt as a fallback
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength against security requirements.
    
    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common passwords (basic check)
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    password_lower = password.lower()
    common_passwords = [
        "password", "123456", "qwerty", "admin", "welcome",
        "letmein", "monkey", "dragon", "master", "hello"
    ]
    if any(common in password_lower for common in common_passwords):
        return False, "Password contains common patterns. Please choose a stronger password"
    
    # Check for sequential characters
    if any(str(i) * 3 in password for i in range(10)):
        return False, "Password must not contain sequential characters"
    
    return True, ""


def get_password_hash(password: str) -> str:
    """
    Hash a password after validating its strength.
    
    Raises:
        ValueError: If password is too long or fails strength validation
    """
    # Validate password strength before hashing
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)
    
    try:
        return pwd_context.hash(password)
    except ValueError:
        # propagate a clear error for callers to convert to HTTP 400
        raise
    except Exception as exc:
        # wrap unexpected errors
        raise ValueError(f"password hashing failed: {exc}")


def hash_unusable_password(password: str) -> str:
    """
    Hash a machine-generated credential without applying the user password policy.

    Random tokens (e.g. secrets.token_urlsafe) frequently lack a special
    character and would fail validate_password_strength nondeterministically.
    """
    try:
        return pwd_context.hash(password)
    except Exception as exc:
        raise ValueError(f"password hashing failed: {exc}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
