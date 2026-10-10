"""Performance (#25): cache-aside service, property cache invalidation, media caching."""
import fnmatch
import uuid

import pytest

from app.config.settings import settings  # the pydantic instance cache_service reads
from app.models.user import User
from app.services import cache_service

PASSWORD = "Str0ng!TestPass42"


@pytest.fixture()
def unique_suffix():
    return uuid.uuid4().hex[:8]


class FakeRedis:
    """In-memory stand-in for the cache client (TTLs not needed in tests)."""

    def __init__(self):
        self.store = {}
        self.set_calls = 0

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value
        self.set_calls += 1

    def scan_iter(self, match=None, count=None):
        for key in list(self.store):
            if fnmatch.fnmatch(key, match):
                yield key

    def delete(self, *keys):
        for key in keys:
            self.store.pop(key, None)


class BrokenRedis:
    """Simulates a Redis outage — every call raises."""

    def get(self, key):
        raise ConnectionError("redis down")

    def set(self, *args, **kwargs):
        raise ConnectionError("redis down")

    def scan_iter(self, *args, **kwargs):
        raise ConnectionError("redis down")

    def delete(self, *keys):
        raise ConnectionError("redis down")


@pytest.fixture()
def cache(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(cache_service, "_client", fake)
    return fake


# ---------------------------------------------------------------------------
# Service-level behavior
# ---------------------------------------------------------------------------

def test_cache_roundtrip(cache):
    cache_service.cache_set_json("k", {"a": 1})
    assert cache_service.cache_get_json("k") == {"a": 1}


def test_get_returns_none_when_unset(cache):
    assert cache_service.cache_get_json("missing") is None


def test_cache_disabled_without_redis_url(monkeypatch):
    monkeypatch.setattr(cache_service, "_client", None)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    assert cache_service.cache_get_json("k") is None
    cache_service.cache_set_json("k", {"a": 1})
    assert cache_service.cache_delete_pattern("k") == 0


def test_redis_outage_never_breaks_callers(monkeypatch):
    monkeypatch.setattr(cache_service, "_client", BrokenRedis())
    assert cache_service.cache_get_json("k") is None
    cache_service.cache_set_json("k", {"a": 1})
    assert cache_service.cache_delete_pattern("props:*") == 0


def test_invalidate_property_cache_hits_only_property_keys(cache):
    cache_service.cache_set_json("props:v1:list?limit=10", [1])
    cache_service.cache_set_json("props:v1:detail:3", {"id": 3})
    cache_service.cache_set_json("api-rate:ip:1.2.3.4:1", 7)
    removed = cache_service.invalidate_property_cache()
    assert removed == 2
    assert cache_service.cache_get_json("api-rate:ip:1.2.3.4:1") == 7


def test_property_list_key_is_order_independent():
    assert (
        cache_service.property_list_key(city="Nairobi", limit=10)
        == cache_service.property_list_key(limit=10, city="Nairobi")
    )


# ---------------------------------------------------------------------------
# End-to-end: public property list served from cache, flushed on mutation
# ---------------------------------------------------------------------------

def _register_admin(client, db_session, email):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Cache Admin"},
    )
    assert resp.status_code == 200, resp.text
    user = db_session.query(User).filter_by(email=email).first()
    user.role = "admin"
    db_session.commit()
    db_session.refresh(user)
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_public_list_uses_cache_and_invalidation_flushes_it(
    client, db_session, cache, unique_suffix
):
    email = f"cache_admin_{unique_suffix}@cache.dev"
    headers = _register_admin(client, db_session, email)

    create = client.post(
        "/api/properties/",
        json={"name": f"Cache Villa {unique_suffix}", "city": "Nairobi"},
        headers=headers,
    )
    assert create.status_code == 201, create.text
    property_id = create.json()["id"]

    listed = client.get("/api/properties/public?limit=10")
    assert listed.status_code == 200
    assert any(p["id"] == property_id for p in listed.json())
    assert cache.set_calls >= 1

    list_key = cache_service.property_list_key(
        city=None, limit=10, property_type=None, purpose=None,
        search=None, skip=0, sort=None, status=None, verified_only=False,
    )
    assert list_key in cache.store

    # A poisoned cache entry is served back verbatim: proof the read came
    # from Redis, not the database.
    cache.store[list_key] = "[]"
    listed_again = client.get("/api/properties/public?limit=10")
    assert listed_again.json() == []

    # Mutation flushes the poisoned entry; the row is gone, so the fresh DB
    # read no longer contains the property.
    deleted = client.delete(f"/api/properties/{property_id}", headers=headers)
    assert deleted.status_code == 204
    assert list_key not in cache.store
    listed_after = client.get("/api/properties/public?limit=10")
    assert listed_after.status_code == 200
    assert all(p["id"] != property_id for p in listed_after.json())
