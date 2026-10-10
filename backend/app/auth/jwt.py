from datetime import datetime, timedelta
from app.utils.time import utc_now
from typing import Optional
import uuid

from jose import JWTError, jwt

from app.config.settings import settings


def _expire_time(minutes: Optional[int] = None, days: Optional[int] = None) -> datetime:
    if minutes is not None:
        return utc_now() + timedelta(minutes=minutes)
    if days is not None:
        return utc_now() + timedelta(days=days)
    return utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = _expire_time(minutes=(expires_delta and int(expires_delta.total_seconds() // 60)))
    # FIX: tag the token type so a leaked/stolen refresh token cannot be used
    # directly as an access token (they previously shared the same shape).
    # Also add JTI (JWT ID) for token revocation support
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "iat": int(utc_now().timestamp())  # Issued at timestamp
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, days: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = _expire_time(days=(days or settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "iat": int(utc_now().timestamp())  # Issued at timestamp
    })
    # use same secret and algorithm for simplicity; consider using a separate secret in production
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise
