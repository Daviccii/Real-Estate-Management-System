"""Redis-backed cache-aside helpers.

A cache must never take a read down: every function swallows Redis errors
(logs at debug) and callers fall through to the database. Keys are namespaced
(`props:v1:*`) so an invalidation is one SCAN+DEL.
"""
import json
import logging
from typing import Any, Dict, Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client = None

PROPERTY_CACHE_PREFIX = "props:v1"
DEFAULT_TTL_SECONDS = 60


def _get_client():
    global _client
    if _client is None:
        if not settings.REDIS_URL:
            return None
        import redis

        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def cache_get_json(key: str) -> Optional[Any]:
    try:
        client = _get_client()
        if client is None:
            return None
        raw = client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        logger.debug("Cache get failed for %s", key, exc_info=True)
        return None


def cache_set_json(key: str, value: Any, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    try:
        client = _get_client()
        if client is None:
            return
        client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        logger.debug("Cache set failed for %s", key, exc_info=True)


def cache_delete_pattern(pattern: str) -> int:
    try:
        client = _get_client()
        if client is None:
            return 0
        keys = list(client.scan_iter(match=pattern, count=200))
        if keys:
            client.delete(*keys)
        return len(keys)
    except Exception:
        logger.debug("Cache invalidation failed for %s", pattern, exc_info=True)
        return 0


def build_key(namespace: str, **params) -> str:
    """Deterministic cache key from a namespace plus its filter parameters."""
    flat = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return f"{namespace}?{flat}"


def invalidate_property_cache() -> int:
    return cache_delete_pattern(f"{PROPERTY_CACHE_PREFIX}:*")


def property_list_key(**filters) -> str:
    return build_key(f"{PROPERTY_CACHE_PREFIX}:list", **filters)


def property_detail_key(property_id: int) -> str:
    return f"{PROPERTY_CACHE_PREFIX}:detail:{property_id}"
