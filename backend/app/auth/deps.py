from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.auth.jwt import decode_token
from app.database.database import get_db
from app.models.user import User
from app.services.token_revocation import is_token_revoked, get_user_revocation_time

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        # FIX: reject refresh tokens presented as access tokens. Without this,
        # the httpOnly refresh cookie value could be copied out (e.g. via the
        # browser devtools) and used directly as a long-lived Bearer token.
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if token has been revoked
        token_jti = payload.get("jti")
        if token_jti and await is_token_revoked(token_jti, "access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = int(payload.get("sub"))
        
        # Check if user's tokens have been revoked (logout from all devices)
        token_issued_at = payload.get("iat")
        if token_issued_at:
            revocation_time = await get_user_revocation_time(user_id)
            if revocation_time and token_issued_at < revocation_time:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user(
    token: Optional[str] = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Resolve the caller when a valid token is present; anonymous otherwise.

    Used by endpoints that behave for both states, e.g. consent recording.
    An invalid or expired token degrades to anonymous instead of erroring,
    because consent must still be recordable from a logged-out browser.
    """
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        token_jti = payload.get("jti")
        if token_jti and await is_token_revoked(token_jti, "access"):
            return None
        user_id = int(payload.get("sub"))
        token_issued_at = payload.get("iat")
        if token_issued_at:
            revocation_time = await get_user_revocation_time(user_id)
            if revocation_time and token_issued_at < revocation_time:
                return None
    except Exception:
        return None
    return db.query(User).filter(User.id == user_id).first()
