"""
Data retention jobs (storage limitation, GDPR Art. 5(1)(e)).

Each job deletes rows past their retention window and returns the count
removed. Destructive jobs are suspended while LEGAL_HOLD_ENABLED is set;
ephemeral auth artifacts (expired/used one-time tokens) are purged regardless
because they have no evidentiary value and are a liability.

Run via the admin endpoint (POST /api/v1/admin/retention/run) or the CLI
(scripts/run_retention.py, suitable for cron). Every run is recorded in the
audit log as RETENTION_RUN with the per-category counts.
"""
import logging
from datetime import timedelta
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models import (
    AuditLog,
    EmailVerification,
    Notification,
    PasswordResetToken,
    SmsChallenge,
)
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


def prune_audit_logs(db: Session, now=None) -> int:
    """Delete audit entries older than RETENTION_AUDIT_LOG_DAYS (0 = never)."""
    if settings.LEGAL_HOLD_ENABLED or settings.RETENTION_AUDIT_LOG_DAYS <= 0:
        return 0
    now = now or utc_now()
    cutoff = now - timedelta(days=settings.RETENTION_AUDIT_LOG_DAYS)
    return (
        db.query(AuditLog)
        .filter(AuditLog.created_at < cutoff)
        .delete(synchronize_session="fetch")
    )


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
    report = {
        "ran_at": now.isoformat(),
        "legal_hold": settings.LEGAL_HOLD_ENABLED,
        "auth_tokens_purged": purge_stale_auth_tokens(db, now),
        "audit_logs_pruned": prune_audit_logs(db, now),
        "notifications_pruned": prune_notifications(db, now),
    }
    db.add(
        AuditLog(
            actor_id=actor_id,
            action="RETENTION_RUN",
            entity_type="retention",
            details_json=str(report),
        )
    )
    db.commit()
    logger.info("Retention run: %s", report)
    return report
