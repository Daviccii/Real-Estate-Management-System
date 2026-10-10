"""
Tamper-evident audit chain tests: chained writes (including batched flushes),
verification of intact chains, detection of edited/deleted/forged entries,
retention-prune anchors, tip tracking, and the admin verify endpoint.
"""
import hashlib
import hmac
import json
from datetime import timedelta
from uuid import uuid4

import sqlalchemy as sa

from app.models import AuditChainState, AuditLog, User
from app.services.audit_chain import ANCHOR_ACTION, verify_audit_chain
from app.services.audit_service import log_audit_event
from app.services.retention_service import run_retention
from app.utils.audit_hash import GENESIS_PREV, entry_payload
from app.utils.time import utc_now


def _mk_entry(db, *, action="TEST_EVENT", details=None, created_at=None):
    entry = AuditLog(
        action=action, entity_type="test", details_json=details, created_at=created_at
    )
    db.add(entry)
    return entry


def _entries(db):
    return db.query(AuditLog).order_by(AuditLog.id.asc()).all()


def _seed_three(db):
    e1 = _mk_entry(db, action="ONE")
    e2 = _mk_entry(db, action="TWO")
    e3 = _mk_entry(db, action="THREE")
    db.commit()
    return e1, e2, e3


def _ago(days):
    return utc_now() - timedelta(days=days)


# ---------------------------------------------------------------------------
# Chained writes
# ---------------------------------------------------------------------------

def test_writes_are_chained_and_verify_pass(db_session):
    _mk_entry(db_session, action="ONE")
    db_session.commit()
    _mk_entry(db_session, action="TWO")
    db_session.commit()
    _mk_entry(db_session, action="THREE")
    db_session.commit()

    rows = _entries(db_session)
    assert [r.action for r in rows] == ["ONE", "TWO", "THREE"]
    assert rows[0].prev_hash == GENESIS_PREV
    assert rows[1].prev_hash == rows[0].entry_hash
    assert rows[2].prev_hash == rows[1].entry_hash
    assert all(r.entry_hash and len(r.entry_hash) == 64 for r in rows)

    report = verify_audit_chain(db_session)
    assert report["verified"] is True
    assert report["entries_checked"] == 3
    assert report["root"] == {"kind": "genesis"}
    assert report["first_broken"] is None
    assert report["tip_hash"] == rows[-1].entry_hash


def test_batch_insert_in_one_flush_preserves_chain(db_session):
    # Regression guard: all before_insert events for a batched flush fire
    # before any INSERT, so a naive "read the last row" hook would fork the
    # chain here. The tip-table design must keep it linear.
    for i in range(5):
        _mk_entry(db_session, action=f"BATCH_{i}")
    db_session.commit()

    rows = _entries(db_session)
    assert len(rows) == 5
    for prev, cur in zip(rows, rows[1:]):
        assert cur.prev_hash == prev.entry_hash
    assert verify_audit_chain(db_session)["verified"] is True


def test_service_written_events_are_chained(db_session):
    first = log_audit_event(db_session, None, "SERVICE_ONE")
    second = log_audit_event(db_session, None, "SERVICE_TWO")
    assert first is not None and second is not None

    rows = _entries(db_session)
    assert rows[0].prev_hash == GENESIS_PREV
    assert rows[1].prev_hash == rows[0].entry_hash
    assert verify_audit_chain(db_session)["verified"] is True


def test_empty_chain_verifies(db_session):
    report = verify_audit_chain(db_session)
    assert report["verified"] is True
    assert report["entries_checked"] == 0
    assert report["root"] is None
    assert report["tip_hash"] is None


# ---------------------------------------------------------------------------
# Tampering detection
# ---------------------------------------------------------------------------

def test_edited_entry_is_detected(db_session):
    _seed_three(db_session)
    target = _entries(db_session)[1]

    db_session.execute(
        sa.update(AuditLog)
        .where(AuditLog.id == target.id)
        .values(details_json='{"tampered": 1}')
    )
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == target.id
    assert "modified" in report["first_broken"]["reason"]


def test_deleted_middle_entry_is_detected(db_session):
    _seed_three(db_session)
    rows = _entries(db_session)
    victim, successor = rows[1], rows[2]

    db_session.execute(sa.delete(AuditLog).where(AuditLog.id == victim.id))
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == successor.id
    assert "broken link" in report["first_broken"]["reason"]


def test_deleted_tail_entry_is_detected(db_session):
    _seed_three(db_session)
    rows = _entries(db_session)
    db_session.execute(sa.delete(AuditLog).where(AuditLog.id == rows[-1].id))
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == rows[-2].id
    assert "tip mismatch" in report["first_broken"]["reason"]


def test_deleted_prefix_entry_is_detected(db_session):
    _seed_three(db_session)
    rows = _entries(db_session)
    db_session.execute(sa.delete(AuditLog).where(AuditLog.id == rows[0].id))
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == rows[1].id
    assert "missing chain root" in report["first_broken"]["reason"]


def test_forged_rehash_without_key_is_detected(db_session):
    # An attacker with database access but without AUDIT_CHAIN_SECRET cannot
    # rebuild a modified row: recomputing with any other key fails.
    _seed_three(db_session)
    target = _entries(db_session)[1]

    payload = entry_payload(target)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    forged = hmac.new(
        b"attacker-key", f"{target.prev_hash}:{canonical}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    db_session.execute(
        sa.update(AuditLog).where(AuditLog.id == target.id).values(entry_hash=forged)
    )
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == target.id
    assert "mismatch" in report["first_broken"]["reason"]


def test_entry_without_hash_is_flagged(db_session):
    _seed_three(db_session)
    target = _entries(db_session)[1]
    db_session.execute(
        sa.update(AuditLog).where(AuditLog.id == target.id).values(entry_hash=None)
    )
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == target.id
    assert "no chain hash" in report["first_broken"]["reason"]


def test_timestamp_normalization_round_trips(db_session):
    # The hook hashes the storage form (naive UTC); a payload built via the
    # public helper must match what verification recomputes after read-back.
    _mk_entry(db_session, action="STAMPED", created_at=_ago(3))
    db_session.commit()
    report = verify_audit_chain(db_session)
    assert report["verified"] is True


# ---------------------------------------------------------------------------
# Retention pruning vs. the chain
# ---------------------------------------------------------------------------

def test_prefix_prune_records_anchor_and_still_verifies(db_session):
    old = _mk_entry(db_session, action="OLD", created_at=_ago(400))
    retained1 = _mk_entry(db_session, action="RETAINED_1")
    retained2 = _mk_entry(db_session, action="RETAINED_2")
    db_session.commit()
    old_id, old_hash = old.id, old.entry_hash
    r1_id = retained1.id
    r2_id = retained2.id

    report = run_retention(db_session)
    assert report["audit_logs_pruned"] == 1

    anchor_row = db_session.query(AuditLog).filter_by(action=ANCHOR_ACTION).one()
    details = json.loads(anchor_row.details_json)
    assert details["pruned_count"] == 1
    assert details["links"] == [
        {
            "predecessor_id": old_id,
            "predecessor_hash": old_hash,
            "successor_id": r1_id,
        }
    ]
    assert "tail_pruned_from_id" not in details

    result = verify_audit_chain(db_session)
    assert result["verified"] is True
    assert result["root"] == {"kind": "anchor", "anchor_id": anchor_row.id}
    assert db_session.query(AuditLog).filter_by(id=r2_id).first() is not None
    # The tip follows the newest entry (the run payload written last).
    tip = db_session.query(AuditChainState).first().last_entry_hash
    run_entry = db_session.query(AuditLog).filter_by(action="RETENTION_RUN").one()
    assert tip == run_entry.entry_hash


def test_middle_prune_records_link_and_still_verifies(db_session):
    _mk_entry(db_session, action="A", created_at=_ago(10))
    b = _mk_entry(db_session, action="B", created_at=_ago(400))
    c = _mk_entry(db_session, action="C", created_at=_ago(10))
    db_session.commit()
    b_id, b_hash, c_id = b.id, b.entry_hash, c.id

    report = run_retention(db_session)
    assert report["audit_logs_pruned"] == 1

    details = json.loads(
        db_session.query(AuditLog).filter_by(action=ANCHOR_ACTION).one().details_json
    )
    assert details["links"] == [
        {"predecessor_id": b_id, "predecessor_hash": b_hash, "successor_id": c_id}
    ]
    assert "tail_pruned_from_id" not in details

    result = verify_audit_chain(db_session)
    assert result["verified"] is True
    assert result["root"] == {"kind": "genesis"}


def test_prune_then_edit_still_detected(db_session):
    _mk_entry(db_session, action="A", created_at=_ago(10))
    _mk_entry(db_session, action="B", created_at=_ago(400))
    survivor = _mk_entry(db_session, action="C", created_at=_ago(10))
    db_session.commit()

    run_retention(db_session)
    assert verify_audit_chain(db_session)["verified"] is True

    db_session.execute(
        sa.update(AuditLog)
        .where(AuditLog.id == survivor.id)
        .values(details_json='{"tampered": 1}')
    )
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == survivor.id


def test_deletion_after_prune_not_vouched_by_anchor(db_session):
    _mk_entry(db_session, action="OLD", created_at=_ago(400))
    retained1 = _mk_entry(db_session, action="RETAINED_1")
    retained2 = _mk_entry(db_session, action="RETAINED_2")
    db_session.commit()
    run_retention(db_session)

    # The anchor only vouches for the pruned entry; deleting a retained one
    # afterwards must still be flagged.
    db_session.execute(sa.delete(AuditLog).where(AuditLog.id == retained1.id))
    db_session.commit()

    report = verify_audit_chain(db_session)
    assert report["verified"] is False
    assert report["first_broken"]["id"] == retained2.id


def test_tail_prune_moves_tip(db_session):
    fine = _mk_entry(db_session, action="FINE", created_at=_ago(10))
    tail_old = _mk_entry(db_session, action="TAIL_OLD", created_at=_ago(400))
    db_session.commit()
    tail_id = tail_old.id
    fine_hash = fine.entry_hash

    report = run_retention(db_session)
    assert report["audit_logs_pruned"] == 1

    anchor_row = db_session.query(AuditLog).filter_by(action=ANCHOR_ACTION).one()
    details = json.loads(anchor_row.details_json)
    assert details["tail_pruned_from_id"] == tail_id
    assert details["links"] == []
    # The anchor chains directly onto the last survivor.
    assert anchor_row.prev_hash == fine_hash

    result = verify_audit_chain(db_session)
    assert result["verified"] is True
    assert result["entries_checked"] == 3  # FINE, anchor, RETENTION_RUN

    # New appends chain onto the moved tip.
    appended = log_audit_event(db_session, None, "AFTER_TAIL_PRUNE")
    assert appended is not None
    result = verify_audit_chain(db_session)
    assert result["verified"] is True
    assert result["entries_checked"] == 4
    state = db_session.query(AuditChainState).first()
    assert state.last_entry_hash == appended.entry_hash


def test_full_prune_resets_chain(db_session):
    only = _mk_entry(db_session, action="ONLY", created_at=_ago(400))
    db_session.commit()
    only_id = only.id

    report = run_retention(db_session)
    assert report["audit_logs_pruned"] == 1

    anchor_row = db_session.query(AuditLog).filter_by(action=ANCHOR_ACTION).one()
    details = json.loads(anchor_row.details_json)
    assert details["tail_pruned_from_id"] == only_id
    assert details["links"] == []

    result = verify_audit_chain(db_session)
    assert result["verified"] is True
    assert result["root"] == {"kind": "genesis"}
    assert result["first_entry_id"] == anchor_row.id
    assert result["entries_checked"] == 2
    # Pruned entry is gone (SQLite may reuse its rowid for the anchor row,
    # so assert on the action, not the id).
    assert db_session.query(AuditLog).filter_by(action="ONLY").first() is None


def test_prune_with_legal_hold_keeps_everything(db_session, monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "LEGAL_HOLD_ENABLED", True)
    _mk_entry(db_session, action="ANCIENT", created_at=_ago(4000))
    db_session.commit()

    report = run_retention(db_session)
    assert report["audit_logs_pruned"] == 0
    assert db_session.query(AuditLog).filter_by(action=ANCHOR_ACTION).count() == 0
    assert verify_audit_chain(db_session)["verified"] is True


# ---------------------------------------------------------------------------
# Admin verify endpoint
# ---------------------------------------------------------------------------

PASSWORD = "Str0ng!TestPass42"


def _register(client, email):
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()


def test_chain_verify_endpoint_requires_auth(client):
    assert client.get("/api/v1/audit-logs/chain/verify").status_code == 401


def test_chain_verify_endpoint_forbids_non_admin(client, db_session):
    email = f"chain_nonadmin_{uuid4().hex[:8]}@chain.dev"
    _register(client, email)
    headers = _login(client, email)
    assert client.get("/api/v1/audit-logs/chain/verify", headers=headers).status_code == 403


def test_chain_verify_endpoint_reports_status(client, db_session):
    email = f"chain_admin_{uuid4().hex[:8]}@chain.dev"
    _register(client, email)
    _promote(db_session, email, "admin")
    headers = _login(client, email)

    # Auth flows emit structured security events, not audit_logs rows, so
    # seed chain entries directly to give the endpoint something to verify.
    _mk_entry(db_session, action="PRE_VERIFY_ONE")
    _mk_entry(db_session, action="PRE_VERIFY_TWO")
    db_session.commit()

    resp = client.get("/api/v1/audit-logs/chain/verify", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verified"] is True
    assert body["entries_checked"] >= 2
    assert body["first_broken"] is None
    assert body["checked_at"]


def test_audit_log_list_exposes_chain_fields(client, db_session):
    email = f"chain_reader_{uuid4().hex[:8]}@chain.dev"
    _register(client, email)
    _promote(db_session, email, "admin")
    headers = _login(client, email)

    _mk_entry(db_session, action="LISTED_ONE")
    _mk_entry(db_session, action="LISTED_TWO")
    db_session.commit()

    resp = client.get("/api/v1/audit-logs/", headers=headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert items, "expected seeded audit entries"
    assert all(item["entry_hash"] for item in items)
    assert any(item["prev_hash"] == GENESIS_PREV for item in items)
