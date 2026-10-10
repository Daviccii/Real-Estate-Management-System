"""
Data retention tests: expired/used one-time token purging, audit log and
notification pruning windows, legal-hold suspension, and the admin trigger
endpoint (auth, authorization, audit trail).
"""
from datetime import timedelta
from uuid import uuid4

from app.config.settings import settings
from app.models import (
    AuditLog,
    EmailVerification,
    Notification,
    PasswordResetToken,
    SmsChallenge,
    User,
)
from app.services.retention_service import purge_stale_auth_tokens, run_retention
from app.utils.time import utc_now


def _mk_user(db_session, email=None):
    user = User(
        email=email or f"ret_{uuid4().hex[:8]}@retention.dev",
        hashed_password="x",
        full_name="Retention Tester",
        role="tenant",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _expired(days_ago):
    return utc_now() - timedelta(days=days_ago)


def _mk_reset_token(db_session, user, *, expires_at=None, used_at=None):
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=uuid4().hex,
        expires_at=expires_at or utc_now() + timedelta(days=1),
        used_at=used_at,
    )
    db_session.add(token)
    db_session.commit()
    return token


def _mk_email_verification(db_session, user, *, expires_at=None, verified_at=None):
    verification = EmailVerification(
        user_id=user.id,
        email=user.email,
        token=uuid4().hex,
        expires_at=expires_at or utc_now() + timedelta(days=1),
        verified_at=verified_at,
    )
    db_session.add(verification)
    db_session.commit()
    return verification


def _mk_sms_challenge(db_session, user, *, expires_at=None, used_at=None):
    challenge = SmsChallenge(
        user_id=user.id,
        phone="+254700000000",
        code_hash=uuid4().hex,
        expires_at=expires_at or utc_now() + timedelta(minutes=5),
        used_at=used_at,
    )
    db_session.add(challenge)
    db_session.commit()
    return challenge


def _mk_notification(db_session, user, *, created_at=None, read_at=None):
    notification = Notification(
        recipient_id=user.id,
        notification_type="PAYMENT",
        title="t",
        message="m",
        created_at=created_at,
        read_at=read_at,
        is_read=read_at is not None,
    )
    db_session.add(notification)
    db_session.commit()
    return notification


# ---------------------------------------------------------------------------
# Ephemeral auth tokens (purged even under legal hold)
# ---------------------------------------------------------------------------

def test_expired_and_stale_used_tokens_are_purged(db_session):
    user = _mk_user(db_session)
    fresh = _mk_reset_token(db_session, user)
    expired = _mk_reset_token(db_session, user, expires_at=_expired(60))
    used_long_ago = _mk_reset_token(db_session, user, used_at=_expired(60))
    used_recently = _mk_reset_token(db_session, user, used_at=_expired(1))
    old_verified = _mk_email_verification(db_session, user, verified_at=_expired(60))
    fresh_verification = _mk_email_verification(db_session, user)
    old_sms = _mk_sms_challenge(db_session, user, expires_at=_expired(31))
    fresh_sms = _mk_sms_challenge(db_session, user)
    fresh_id, expired_id, used_long_ago_id, used_recently_id = (
        fresh.id, expired.id, used_long_ago.id, used_recently.id
    )
    fresh_verification_id, old_verified_id = fresh_verification.id, old_verified.id
    fresh_sms_id, old_sms_id = fresh_sms.id, old_sms.id

    removed = purge_stale_auth_tokens(db_session)
    db_session.commit()

    assert removed >= 4
    remaining_tokens = {t.id for t in db_session.query(PasswordResetToken).all()}
    assert fresh_id in remaining_tokens
    assert used_recently_id in remaining_tokens
    assert expired_id not in remaining_tokens
    assert used_long_ago_id not in remaining_tokens
    remaining_verifications = {v.id for v in db_session.query(EmailVerification).all()}
    assert fresh_verification_id in remaining_verifications
    assert old_verified_id not in remaining_verifications
    remaining_sms = {c.id for c in db_session.query(SmsChallenge).all()}
    assert fresh_sms_id in remaining_sms
    assert old_sms_id not in remaining_sms


def test_tokens_are_purged_even_under_legal_hold(db_session, monkeypatch):
    monkeypatch.setattr(settings, "LEGAL_HOLD_ENABLED", True)
    user = _mk_user(db_session)
    expired = _mk_reset_token(db_session, user, expires_at=_expired(60))
    expired_id = expired.id

    purge_stale_auth_tokens(db_session)
    db_session.commit()

    assert db_session.query(PasswordResetToken).filter_by(id=expired_id).first() is None


# ---------------------------------------------------------------------------
# Audit log + notification pruning (suspended by legal hold)
# ---------------------------------------------------------------------------

def test_audit_logs_pruned_after_window(db_session):
    user = _mk_user(db_session)
    old = AuditLog(actor_id=user.id, action="LOGIN", created_at=_expired(400))
    recent = AuditLog(actor_id=user.id, action="LOGIN", created_at=_expired(10))
    db_session.add_all([old, recent])
    db_session.commit()
    old_id, recent_id = old.id, recent.id

    assert run_retention(db_session)["audit_logs_pruned"] == 1

    remaining = {a.id for a in db_session.query(AuditLog).all()}
    assert recent_id in remaining
    assert old_id not in remaining


def test_audit_log_retention_disabled_keeps_everything(db_session, monkeypatch):
    monkeypatch.setattr(settings, "RETENTION_AUDIT_LOG_DAYS", 0)
    user = _mk_user(db_session)
    ancient = AuditLog(actor_id=user.id, action="LOGIN", created_at=_expired(4000))
    db_session.add(ancient)
    db_session.commit()

    assert run_retention(db_session)["audit_logs_pruned"] == 0
    assert db_session.query(AuditLog).filter_by(id=ancient.id).first() is not None


def test_notifications_pruned_by_read_window(db_session):
    user = _mk_user(db_session)
    old_read = _mk_notification(db_session, user, created_at=_expired(200), read_at=_expired(190))
    recent_read = _mk_notification(db_session, user, created_at=_expired(2), read_at=_expired(1))
    old_unread = _mk_notification(db_session, user, created_at=_expired(400))
    recent_unread = _mk_notification(db_session, user, created_at=_expired(200))
    recent_read_id, recent_unread_id = recent_read.id, recent_unread.id
    old_read_id, old_unread_id = old_read.id, old_unread.id

    assert run_retention(db_session)["notifications_pruned"] == 2

    remaining = {n.id for n in db_session.query(Notification).all()}
    assert remaining == {recent_read_id, recent_unread_id}
    assert old_read_id not in remaining
    assert old_unread_id not in remaining


def test_legal_hold_suspends_business_record_purges(db_session, monkeypatch):
    monkeypatch.setattr(settings, "LEGAL_HOLD_ENABLED", True)
    user = _mk_user(db_session)
    ancient_audit = AuditLog(actor_id=user.id, action="LOGIN", created_at=_expired(4000))
    ancient_notification = _mk_notification(
        db_session, user, created_at=_expired(4000), read_at=_expired(3900)
    )
    db_session.add(ancient_audit)
    db_session.commit()

    report = run_retention(db_session)

    assert report["legal_hold"] is True
    assert report["audit_logs_pruned"] == 0
    assert report["notifications_pruned"] == 0
    assert db_session.query(AuditLog).filter_by(id=ancient_audit.id).first() is not None
    assert (
        db_session.query(Notification).filter_by(id=ancient_notification.id).first()
        is not None
    )


def test_run_writes_retention_audit_trail(db_session):
    user = _mk_user(db_session)
    before = db_session.query(AuditLog).filter_by(action="RETENTION_RUN").count()

    run_retention(db_session, actor_id=user.id)

    entry = (
        db_session.query(AuditLog)
        .filter_by(action="RETENTION_RUN")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert entry is not None
    assert entry.actor_id == user.id
    assert db_session.query(AuditLog).filter_by(action="RETENTION_RUN").count() == before + 1


# ---------------------------------------------------------------------------
# Admin trigger endpoint
# ---------------------------------------------------------------------------

PASSWORD = "Str0ng!TestPass42"


def _register(client, email):
    resp = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(db_session, email, role):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = role
    db_session.commit()
    db_session.refresh(user)


def test_retention_endpoint_requires_auth(client):
    assert client.post("/api/admin/retention/run").status_code == 401


def test_retention_endpoint_forbids_non_admin(client, db_session):
    email = f"ret_nonadmin_{uuid4().hex[:8]}@retention.dev"
    _register(client, email)
    headers = _login(client, email)
    assert client.post("/api/admin/retention/run", headers=headers).status_code == 403


def test_retention_endpoint_runs_and_reports(client, db_session):
    email = f"ret_admin_{uuid4().hex[:8]}@retention.dev"
    admin_id = _register(client, email)
    _promote(db_session, email, "admin")
    headers = _login(client, email)

    resp = client.post("/api/admin/retention/run", headers=headers)
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["legal_hold"] is False
    assert {"auth_tokens_purged", "audit_logs_pruned", "notifications_pruned", "ran_at"} <= set(report)

    entry = (
        db_session.query(AuditLog)
        .filter_by(action="RETENTION_RUN")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert entry is not None and entry.actor_id == admin_id
