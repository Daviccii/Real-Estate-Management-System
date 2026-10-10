"""Canonical serialization and hashing for the tamper-evident audit chain.

Every audit_logs row carries ``prev_hash`` (the ``entry_hash`` of the entry
that preceded it) and ``entry_hash`` = HMAC-SHA256(key, prev_hash + canonical
payload). HMAC rather than a plain hash means that an attacker with database
write access cannot recompute the chain after editing or deleting a row
without also stealing the server-side key - which lives in the environment,
never in the database.

The key derives from ``settings.AUDIT_CHAIN_SECRET`` when set, otherwise from
``SECRET_KEY``. It must stay stable across the deployment's lifetime: a
changed key invalidates verification of entries written under the old one.

Canonicalization rules (must round-trip through the database byte-for-byte):
- timestamps are stored and hashed as naive UTC ("2026-10-10T15:30:00[.uss]").
- every payload field is included explicitly, including nulls; keys are
  sorted and separators are compact so the JSON is deterministic.
- ``id`` and the hash fields themselves are excluded (the id is assigned by
  the database only after the hash is computed, and the links are hashed via
  ``prev_hash``).
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.config.settings import settings

#: prev_hash of the very first chained entry.
GENESIS_PREV = "0" * 64


def audit_chain_key() -> bytes:
    return (settings.AUDIT_CHAIN_SECRET or settings.SECRET_KEY).encode("utf-8")


def normalize_created_at(value: Optional[datetime]) -> Optional[datetime]:
    """Return the storage form of a timestamp: naive UTC."""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _iso(value: Optional[datetime]) -> Optional[str]:
    normalized = normalize_created_at(value)
    return normalized.isoformat() if normalized else None


def entry_payload(entry: Any) -> dict:
    """Build the canonical payload from an AuditLog instance or row.

    Duck-typed on purpose: the model module imports this helper at class
    definition time, so it must not import the model back.
    """
    return {
        "v": 1,
        "actor_id": entry.actor_id,
        "action": entry.action,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "ip_address": entry.ip_address,
        "user_agent": entry.user_agent,
        "details_json": entry.details_json,
        "created_at": _iso(entry.created_at),
    }


def compute_entry_hash(prev_hash: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    message = f"{prev_hash}:{canonical}".encode("utf-8")
    return hmac.new(audit_chain_key(), message, hashlib.sha256).hexdigest()
