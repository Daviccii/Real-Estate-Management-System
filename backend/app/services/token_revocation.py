"""
Token Revocation Service

Implements token blacklist for revoking access and refresh tokens.
Uses Redis for distributed token revocation across multiple API workers.
"""
import logging
from datetime import datetime, timezone, timedelta

from app.config.settings import settings

logger = logging.getLogger(__name__)
_redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None and settings.REDIS_URL:
        from redis.asyncio import Redis
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def revoke_token(token_jti: str, token_type: str = "access", user_id: int = None) -> bool:
    """
    Revoke a token by adding it to the blacklist.
    
    Args:
        token_jti: JWT ID of the token to revoke
        token_type: Type of token ("access" or "refresh")
        user_id: User ID for additional tracking
    
    Returns:
        bool: True if token was revoked successfully
    """
    client = get_redis_client()
    if not client:
        logger.warning("Redis not available for token revocation - token revocation will not work")
        return False
    
    # Calculate TTL based on token type
    # Access tokens expire in 60 minutes, refresh tokens in 7 days
    if token_type == "access":
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 60  # Add 1 minute buffer
    else:  # refresh
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600 + 3600  # Add 1 hour buffer
    
    key = f"revoked:{token_type}:{token_jti}"
    
    # Store token metadata
    metadata = {
        "revoked_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id) if user_id else None,
        "token_type": token_type
    }
    
    await client.setex(key, ttl, str(metadata))
    logger.info(f"Token revoked", extra={"token_type": token_type, "user_id": user_id})
    
    return True


async def is_token_revoked(token_jti: str, token_type: str = "access") -> bool:
    """
    Check if a token has been revoked.
    
    Args:
        token_jti: JWT ID of the token to check
        token_type: Type of token ("access" or "refresh")
    
    Returns:
        bool: True if token is revoked
    """
    client = get_redis_client()
    if not client:
        # If Redis is not available, assume token is not revoked (safe default)
        return False
    
    key = f"revoked:{token_type}:{token_jti}"
    return await client.exists(key) > 0


async def revoke_all_user_tokens(user_id: int) -> int:
    """
    Revoke all tokens for a user (logout from all devices).
    
    This requires a different approach since we don't have a list of all valid tokens.
    Instead, we add a user-level revocation marker that will be checked during token validation.
    
    Args:
        user_id: User ID whose tokens should be revoked
    
    Returns:
        int: Timestamp when revocation was set
    """
    client = get_redis_client()
    if not client:
        logger.warning("Redis not available for token revocation")
        return 0
    
    # Set a user-level revocation timestamp
    # Any token issued before this timestamp will be considered revoked
    revocation_time = datetime.now(timezone.utc).timestamp()
    key = f"user-revoked:{user_id}"
    
    # Store for 30 days (longer than refresh token lifetime)
    await client.setex(key, 30 * 24 * 3600, str(revocation_time))
    
    logger.info(f"All tokens revoked for user", extra={"user_id": user_id})
    
    return int(revocation_time)


async def get_user_revocation_time(user_id: int) -> float:
    """
    Get the timestamp when a user's tokens were revoked.
    
    Args:
        user_id: User ID to check
    
    Returns:
        float: Revocation timestamp, or 0 if not revoked
    """
    client = get_redis_client()
    if not client:
        return 0
    
    key = f"user-revoked:{user_id}"
    revocation_str = await client.get(key)
    
    if revocation_str:
        return float(revocation_str)
    
    return 0


async def revoke_token_by_jti(token_jti: str, user_id: int = None) -> bool:
    """
    Revoke a specific token by its JWT ID.
    
    This is used when we have the full token and can extract its JTI.
    
    Args:
        token_jti: JWT ID from the token
        user_id: User ID for tracking
    
    Returns:
        bool: True if revoked successfully
    """
    return await revoke_token(token_jti, "access", user_id)
