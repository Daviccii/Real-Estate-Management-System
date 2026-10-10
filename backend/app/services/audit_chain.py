"""Verification of the tamper-evident audit chain.

Walks the audit_logs table in id order, recomputes every entry_hash, and
checks that each row's prev_hash matches its predecessor. Any edited row,
deleted row, reordered row, or row inserted outside the chained write path
surfaces as the first deviation, with enough context to locate it.

Retention pruning deletes the oldest rows by design, which breaks the links
around the deleted segments. Before deleting, retention records an
AUDIT_CHAIN_ANCHOR entry listing every such break (the id and hash of the
last pruned row before each surviving segment) plus any tip move. Those
anchor entries are chained like any other, so - unlike a bare "skip the
check" - they cannot be forged without the HMAC key; verification accepts a
link only when an anchor entry vouches for that exact predecessor hash, so an
undeclared deletion is still flagged.

The newest entry is additionally cross-checked against the audit_chain_state
tip row, which catches deletions at the tail of the table (nothing else links
forward to the last entry).

Known limitation (documented in SECURITY_IMPROVEMENTS.md): an attacker with
simultaneous database write access AND the HMAC key can rebuild the entire
chain consistently. The chain's guarantee is against database-only tampering.
"""
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditChainState, AuditLog
from app.utils.audit_hash import GENESIS_PREV, compute_entry_hash, entry_payload
from app.utils.time import utc_now

ANCHOR_ACTION = "AUDIT_CHAIN_ANCHOR"


def _anchor_index(db: Session) -> dict:
    """Map predecessor_hash -> anchor entry id for every recorded prune link.

    Those predecessors are rows that were deleted by retention under a
    recorded anchor; a surviving entry whose prev_hash matches one is a
    legitimate, declared break rather than tampering.
    """
    anchors: dict = {}
    rows = db.query(AuditLog).filter(AuditLog.action == ANCHOR_ACTION).all()
    for row in rows:
        try:
            details = json.loads(row.details_json or "")
        except (TypeError, ValueError):
            continue
        links = details.get("links") if isinstance(details, dict) else None
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            predecessor_hash = link.get("predecessor_hash")
            if isinstance(predecessor_hash, str) and predecessor_hash:
                anchors[predecessor_hash] = row.id
    return anchors


def verify_audit_chain(db: Session) -> dict:
    """Recompute the chain and report the first deviation, if any."""
    anchors = _anchor_index(db)

    checked = 0
    first_broken: Optional[dict] = None
    root: Optional[dict] = None
    first_entry_id: Optional[int] = None
    expected_prev = GENESIS_PREV
    last_row: Any = None

    for row in db.query(AuditLog).order_by(AuditLog.id.asc()).yield_per(500):
        checked += 1
        if checked == 1:
            first_entry_id = row.id
            if row.prev_hash == GENESIS_PREV:
                root = {"kind": "genesis"}
            elif row.prev_hash in anchors:
                root = {"kind": "anchor", "anchor_id": anchors[row.prev_hash]}
            else:
                first_broken = {
                    "id": row.id,
                    "reason": (
                        "missing chain root: the oldest retained entry links to an "
                        "unknown predecessor (possible prefix deletion)"
                    ),
                }
                break
        elif row.prev_hash != expected_prev:
            if row.prev_hash in anchors:
                # A recorded retention prune removed the predecessor; the
                # anchor entry vouches for exactly this break.
                pass
            else:
                first_broken = {
                    "id": row.id,
                    "reason": "broken link: prev_hash does not match the previous entry",
                    "expected_prev_hash": expected_prev,
                    "actual_prev_hash": row.prev_hash,
                }
                break

        if row.entry_hash is None:
            first_broken = {
                "id": row.id,
                "reason": "entry has no chain hash (inserted outside the chained write path)",
            }
            break

        computed = compute_entry_hash(row.prev_hash, entry_payload(row))
        if row.entry_hash != computed:
            first_broken = {
                "id": row.id,
                "reason": "entry hash mismatch: the row was modified after it was written",
                "stored_entry_hash": row.entry_hash,
                "computed_entry_hash": computed,
            }
            break

        expected_prev = row.entry_hash
        last_row = row

    state = db.query(AuditChainState).filter(AuditChainState.id == 1).first()
    tip_hash = state.last_entry_hash if state else None

    if first_broken is None:
        if last_row is None:
            if tip_hash is not None:
                first_broken = {
                    "id": None,
                    "reason": "chain is empty but the recorded tip hash is not (entries were deleted)",
                    "recorded_tip_hash": tip_hash,
                }
        elif tip_hash != last_row.entry_hash:
            first_broken = {
                "id": last_row.id,
                "reason": (
                    "chain tip mismatch: the recorded tip does not match the newest "
                    "entry (possible tail deletion or bypassed write)"
                ),
                "recorded_tip_hash": tip_hash,
                "newest_entry_hash": last_row.entry_hash,
            }

    return {
        "verified": first_broken is None,
        "entries_checked": checked,
        "root": root,
        "first_entry_id": first_entry_id,
        "last_entry_id": last_row.id if last_row is not None else None,
        "tip_hash": tip_hash,
        "first_broken": first_broken,
        "checked_at": utc_now().isoformat(),
    }
