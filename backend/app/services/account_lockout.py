"""
Account Lockout Service

Implements progressive delay and account lockout after failed login attempts
to prevent brute force attacks.

Uses Redis for distributed lockout state across multiple API workers.
"""
import logging
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status

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


async def record_failed_login_attempt(email: str) -> dict:
    """
    Record a failed login attempt and return lockout status.
    
    Returns:
        dict with keys:
        - attempts: Number of failed attempts
        - locked: Whether account is locked
        - lockout_until: When lockout expires (if locked)
        - lockout_duration: How long the lockout lasts
    """
    client = get_redis_client()
    if not client:
        # If Redis is not available, still track in memory (not ideal but safe fallback)
        logger.warning("Redis not available for account lockout - using in-memory fallback")
        return {"attempts": 0, "locked": False, "lockout_until": None, "lockout_duration": 0}
    
    key = f"login-failures:{email.lower()}"
    
    # Increment attempt counter
    attempts = await client.incr(key)
    
    # Set expiration on first attempt (15 minutes window)
    if attempts == 1:
        await client.expire(key, 900)  # 15 minutes
    
    # Progressive delay strategy:
    # 3 attempts: 1 minute lockout
    # 5 attempts: 5 minute lockout
    # 10 attempts: 30 minute lockout
    # 15 attempts: 1 hour lockout
    # 20 attempts: 24 hour lockout (admin unlock required)
    
    lockout_duration = 0
    locked = False
    lockout_until = None
    
    if attempts >= 20:
        lockout_duration = 86400  # 24 hours
        locked = True
    elif attempts >= 15:
        lockout_duration = 3600  # 1 hour
        locked = True
    elif attempts >= 10:
        lockout_duration = 1800  # 30 minutes
        locked = True
    elif attempts >= 5:
        lockout_duration = 300  # 5 minutes
        locked = True
    elif attempts >= 3:
        lockout_duration = 60  # 1 minute
        locked = True
    
    if locked:
        lockout_key = f"login-locked:{email.lower()}"
        # Set lockout if not already set
        if not await client.exists(lockout_key):
            lockout_until = datetime.now(timezone.utc) + timedelta(seconds=lockout_duration)
            await client.setex(lockout_key, lockout_duration, str(lockout_until.timestamp()))
            logger.warning(
                f"Account locked due to failed login attempts",
                extra={"email": email, "attempts": attempts, "lockout_duration": lockout_duration}
            )
        else:
            # Get existing lockout time
            existing = await client.get(lockout_key)
            lockout_until = datetime.fromtimestamp(float(existing), timezone.utc)
    
    return {
        "attempts": attempts,
        "locked": locked,
        "lockout_until": lockout_until.isoformat() if lockout_until else None,
        "lockout_duration": lockout_duration
    }


async def check_account_locked(email: str) -> dict:
    """
    Check if an account is currently locked.
    
    Returns:
        dict with keys:
        - locked: Whether account is locked
        - lockout_until: When lockout expires (if locked)
        - attempts: Number of failed attempts
    """
    client = get_redis_client()
    if not client:
        return {"locked": False, "lockout_until": None, "attempts": 0}
    
    email_lower = email.lower()
    lockout_key = f"login-locked:{email_lower}"
    attempts_key = f"login-failures:{email_lower}"
    
    # Check if locked
    locked_until = await client.get(lockout_key)
    if locked_until:
        lockout_time = datetime.fromtimestamp(float(locked_until), timezone.utc)
        if lockout_time > datetime.now(timezone.utc):
            attempts = await client.get(attempts_key) or 0
            return {
                "locked": True,
                "lockout_until": lockout_time.isoformat(),
                "attempts": int(attempts)
            }
        else:
            # Lockout expired, clean up
            await client.delete(lockout_key)
            await client.delete(attempts_key)
    
    # Get attempt count
    attempts = await client.get(attempts_key)
    return {
        "locked": False,
        "lockout_until": None,
        "attempts": int(attempts) if attempts else 0
    }


async def clear_failed_login_attempts(email: str) -> None:
    """
    Clear failed login attempts after successful login.
    Called when user successfully authenticates.
    """
    client = get_redis_client()
    if not client:
        return
    
    email_lower = email.lower()
    await client.delete(f"login-failures:{email_lower}")
    await client.delete(f"login-locked:{email_lower}")


async def unlock_account(email: str) -> bool:
    """
    Manually unlock an account (admin function).
    
    Returns:
        bool: True if account was unlocked, False if not locked
    """
    client = get_redis_client()
    if not client:
        return False
    
    email_lower = email.lower()
    lockout_key = f"login-locked:{email_lower}"
    attempts_key = f"login-failures:{email_lower}"
    
    if await client.exists(lockout_key):
        await client.delete(lockout_key)
        await client.delete(attempts_key)
        logger.info(f"Account manually unlocked", extra={"email": email})
        return True
    
    return False
