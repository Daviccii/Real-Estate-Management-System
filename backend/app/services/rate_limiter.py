import logging
from datetime import datetime, timezone

from fastapi import Request

from app.config.settings import settings

logger = logging.getLogger(__name__)
_client = None


async def allow_request(request: Request) -> bool:
    """
    Use Redis for a process-independent fixed-window rate limit.
    
    Rate limits are applied at multiple levels:
    1. IP-based: Per client IP address
    2. User-based: Per authenticated user (if logged in)
    
    This prevents abuse while allowing legitimate users multiple sessions.
    """
    global _client
    if not settings.RATE_LIMIT_ENABLED:
        return True
    if not settings.REDIS_URL:
        raise RuntimeError("RATE_LIMIT_ENABLED requires REDIS_URL")
    if _client is None:
        from redis.asyncio import Redis
        _client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    window = int(datetime.now(timezone.utc).timestamp() // 60)
    
    # Check IP-based rate limit (always applied)
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"api-rate:ip:{client_ip}:{window}"
    ip_count = await _client.incr(ip_key)
    if ip_count == 1:
        await _client.expire(ip_key, 70)
    
    # Check user-based rate limit (if authenticated)
    # Extract user ID from Authorization header if present
    user_count = 0
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.auth.jwt import decode_token
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            user_id = payload.get("sub")
            if user_id:
                user_key = f"api-rate:user:{user_id}:{window}"
                user_count = await _client.incr(user_key)
                if user_count == 1:
                    await _client.expire(user_key, 70)
        except Exception:
            # If token is invalid, just rely on IP-based limiting
            pass
    
    # Allow request if both IP and user (if authenticated) are within limits
    # User limit is typically higher than IP limit to allow multiple devices
    user_limit = settings.RATE_LIMIT_PER_MINUTE * 2  # 2x for authenticated users
    return ip_count <= settings.RATE_LIMIT_PER_MINUTE and user_count <= user_limit
