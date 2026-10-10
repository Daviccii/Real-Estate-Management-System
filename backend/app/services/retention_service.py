"""
Data retention jobs (storage limitation, GDPR Art. 5(1)(e)).

Each job deletes rows past their retention window and returns the count
removed. Destructive jobs are suspended while LEGAL_HOLD_ENABLED is set;
ephemeral auth artifacts (expired/used one-time tokens) are purged regardless
because they have no evidentiary value and are a liability.

Run via the admin endpoint (POST /api/v1/admin/retention/run) or the CLI
(scripts/run_retention.py, suitable for cron). Every run is recorded in the
audit log as RETENTION_RUN with the per-category counts.

Audit pruning would otherwise sever the tamper-evident chain (see
services/audit_chain.py), so it reports exactly which links its deletions
broke; run_retention records that as an AUDIT_CHAIN_ANCHOR entry in the same
transaction, and verification then accepts those specific breaks.
"""
import json
import logging
from datetime import timedelta
from typing import Optional

from sqlalchemy import and_, insert, or_, update
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models import (
    AuditChainState,
    AuditLog,
    EmailVerification,
    Notification,
    PasswordResetToken,
    SmsChallenge,
)
from app.services.audit_chain import ANCHOR_ACTION
from app.utils.audit_hash import normalize_created_at
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


def purge_stale_auth_tokens(db: Session, now=None) -> int:
    """Delete expired or used one-time tokens past the grace window.

    Always runs, even under legal hold: these are single-use secrets that are
    already dead (expired/consumed), not records of anything.
    """
    now = now or utc_now()
    grace_cutoff = now - timedelta(days=settings.RETENTION_TOKEN_GRACE_DAYS)
    removed = 0

    for expired_at, used_at, model in (
        (PasswordResetToken.expires_at, PasswordResetToken.used_at, PasswordResetToken),
        (EmailVerification.expires_at, EmailVerification.verified_at, EmailVerification),
        (SmsChallenge.expires_at, SmsChallenge.used_at, SmsChallenge),
    ):
        query = db.query(model).filter(
            or_(
                expired_at < grace_cutoff,
                and_(used_at.isnot(None), used_at < grace_cutoff),
            )
        )
        removed += query.delete(synchronize_session="fetch")
    return removed


def prune_audit_logs(db: Session, now=None) -> dict:
    """Delete audit entries older than RETENTION_AUDIT_LOG_DAYS (0 = never).

    Returns ``{"removed": int, "anchor": dict | None}``. The anchor lists every
    chain link the deletion breaks - for each surviving entry that follows a
    pruned run, the id and hash of the last pruned entry before it - plus
    ``tail_pruned_from_id`` when the newest entries were pruned (the tip row
    is moved to the last survivor, or to NULL when nothing survives). The
    caller writes the anchor as an AUDIT_CHAIN_ANCHOR audit entry in the same
    transaction; without it, verification treats the breaks as tampering.
    """
    if settings.LEGAL_HOLD_ENABLED or settings.RETENTION_AUDIT_LOG_DAYS <= 0:
        return {"removed": 0, "anchor": None}
    now = now or utc_now()
    cutoff = now - timedelta(days=settings.RETENTION_AUDIT_LOG_DAYS)
    # Stored timestamps read back naive on both SQLite and Postgres; compare
    # in the storage form so aware/naive never collide.
    cutoff_naive = normalize_created_at(cutoff)

    links = []
    pruned_count = 0
    pending = None  # (id, entry_hash) of the last pruned entry awaiting a survivor
    run_start = None  # first id of the pruned run pending on
    last_survivor_hash = None
    is_tail_pruned = False
    rows = (
        db.query(AuditLog.id, AuditLog.entry_hash, AuditLog.created_at)
        .order_by(AuditLog.id.asc())
        .yield_per(1000)
    )
    for row in rows:
        if normalize_created_at(row.created_at) < cutoff_naive:
            if pending is None:
                run_start = row.id
            pending = (row.id, row.entry_hash)
            pruned_count += 1
        else:
            if pending is not None:
                links.append(
                    {
                        "predecessor_id": pending[0],
                        "predecessor_hash": pending[1],
                        "successor_id": row.id,
                    }
                )
                pending = None
                run_start = None
            last_survivor_hash = row.entry_hash

    if pruned_count == 0:
        return {"removed": 0, "anchor": None}

    removed = (
        db.query(AuditLog)
        .filter(AuditLog.created_at < cutoff)
        .delete(synchronize_session="fetch")
    )
    is_tail_pruned = pending is not None
    if is_tail_pruned:
        # Raw Core update: the tip must never sit as a dirty ORM attribute,
        # or its later flush could clobber the value the insert hook writes.
        result = db.execute(
            update(AuditChainState)
            .where(AuditChainState.id == 1)
            .values(last_entry_hash=last_survivor_hash)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount == 0:
            db.execute(
                insert(AuditChainState).values(id=1, last_entry_hash=last_survivor_hash)
            )

    anchor = {
        "pruned_count": removed,
        "cutoff": cutoff_naive.isoformat(),
        "links": links,
    }
    if is_tail_pruned:
        anchor["tail_pruned_from_id"] = run_start
    return {"removed": removed, "anchor": anchor}


def prune_notifications(db: Session, now=None) -> int:
    """Delete read notifications past the window; unread get double the window."""
    if settings.LEGAL_HOLD_ENABLED:
        return 0
    now = now or utc_now()
    read_cutoff = now - timedelta(days=settings.RETENTION_NOTIFICATIONS_DAYS)
    unread_cutoff = now - timedelta(days=settings.RETENTION_NOTIFICATIONS_DAYS * 2)
    removed = 0
    removed += (
        db.query(Notification)
        .filter(and_(Notification.read_at.isnot(None), Notification.read_at < read_cutoff))
        .delete(synchronize_session="fetch")
    )
    removed += (
        db.query(Notification)
        .filter(
            and_(
                Notification.read_at.is_(None),
                Notification.created_at < unread_cutoff,
            )
        )
        .delete(synchronize_session="fetch")
    )
    return removed


def run_retention(db: Session, *, now=None, actor_id: Optional[int] = None) -> dict:
    """Run all retention jobs, commit, and return the report."""
    now = now or utc_now()
    auth_tokens_purged = purge_stale_auth_tokens(db, now)
    prune = prune_audit_logs(db, now)
    notifications_pruned = prune_notifications(db, now)
    report = {
        "ran_at": now.isoformat(),
        "legal_hold": settings.LEGAL_HOLD_ENABLED,
        "auth_tokens_purged": auth_tokens_purged,
        "audit_logs_pruned": prune["removed"],
        "notifications_pruned": notifications_pruned,
    }
    if prune["anchor"] is not None:
        db.add(
            AuditLog(
                actor_id=actor_id,
                action=ANCHOR_ACTION,
                entity_type="audit_log",
                details_json=json.dumps(prune["anchor"], sort_keys=True),
            )
        )
        # Flush before adding the run entry so the anchor is chained first
        # and the RETENTION_RUN entry links onto it deterministically.
        db.flush()
    db.add(
        AuditLog(
            actor_id=actor_id,
            action="RETENTION_RUN",
            entity_type="retention",
            details_json=json.dumps(report, sort_keys=True),
        )
    )
    db.commit()
    logger.info("Retention run: %s", report)
    return report
