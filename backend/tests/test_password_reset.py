"""
Password reset flow tests: forgot-password, token reset, expiration,
single-use tokens, password history, and change-password.
"""
from datetime import timedelta

from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.password_reset_service import create_reset_token, record_password_history
from app.utils.security import get_password_hash
from app.utils.time import utc_now

STRONG_OLD = "Str0ng!TestPass42"
STRONG_NEW = "N3w!RotatedSeed99"
STRONG_THIRD = "Th1rd!RotatedSeed77"


def _register(client, email, password=STRONG_OLD):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Reset Tester"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _issue_token(db_session, user_id):
    return create_reset_token(db_session, user_id)


def test_forgot_password_is_enumeration_safe(client):
    resp = client.post("/api/auth/forgot-password", json={"email": "ghost@nowhere.resetapp.dev"})
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


def test_forgot_password_creates_token(client, db_session):
    user_id = _register(client, "forgot1@resetapp.dev")
    resp = client.post("/api/auth/forgot-password", json={"email": "forgot1@resetapp.dev"})
    assert resp.status_code == 200
    outstanding = (
        db_session.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at == None)
        .count()
    )
    assert outstanding == 1


def test_reset_password_success_and_login_switch(client, db_session):
    user_id = _register(client, "reset1@resetapp.dev")
    token = _issue_token(db_session, user_id)

    resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": STRONG_NEW})
    assert resp.status_code == 200, resp.text

    assert client.post("/api/auth/login", json={"email": "reset1@resetapp.dev", "password": STRONG_OLD}).status_code != 200
    assert client.post("/api/auth/login", json={"email": "reset1@resetapp.dev", "password": STRONG_NEW}).status_code == 200


def test_reset_token_is_single_use(client, db_session):
    user_id = _register(client, "reset2@resetapp.dev")
    token = _issue_token(db_session, user_id)
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": STRONG_NEW}).status_code == 200
    reuse = client.post("/api/auth/reset-password", json={"token": token, "new_password": STRONG_THIRD})
    assert reuse.status_code == 400


def test_expired_reset_token_rejected(client, db_session):
    user_id = _register(client, "reset3@resetapp.dev")
    token = _issue_token(db_session, user_id)
    record = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).first()
    record.expires_at = utc_now() - timedelta(minutes=1)
    db_session.commit()

    resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": STRONG_NEW})
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_reset_rejects_weak_password(client, db_session):
    user_id = _register(client, "reset4@resetapp.dev")
    token = _issue_token(db_session, user_id)
    resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "weak"})
    assert resp.status_code == 400


def test_password_history_blocks_reuse(client, db_session):
    user_id = _register(client, "reset5@resetapp.dev")
    token = _issue_token(db_session, user_id)
    assert client.post("/api/auth/reset-password", json={"token": token, "new_password": STRONG_NEW}).status_code == 200

    # Try to go back to the original password
    token2 = _issue_token(db_session, user_id)
    resp = client.post("/api/auth/reset-password", json={"token": token2, "new_password": STRONG_OLD})
    assert resp.status_code == 400
    assert "used this password before" in resp.json()["detail"]


def test_change_password_requires_current(client, db_session):
    _register(client, "change1@resetapp.dev")
    login = client.post("/api/auth/login", json={"email": "change1@resetapp.dev", "password": STRONG_OLD})
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    bad = client.post(
        "/api/auth/change-password",
        json={"current_password": "Wr0ng!SeedPass11", "new_password": STRONG_NEW},
        headers=headers,
    )
    assert bad.status_code == 400

    good = client.post(
        "/api/auth/change-password",
        json={"current_password": STRONG_OLD, "new_password": STRONG_NEW},
        headers=headers,
    )
    assert good.status_code == 200, good.text


def test_change_password_blocks_history_reuse(client, db_session):
    _register(client, "change2@resetapp.dev")
    login = client.post("/api/auth/login", json={"email": "change2@resetapp.dev", "password": STRONG_OLD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.post(
        "/api/auth/change-password",
        json={"current_password": STRONG_OLD, "new_password": STRONG_NEW},
        headers=headers,
    ).status_code == 200

    blocked = client.post(
        "/api/auth/change-password",
        json={"current_password": STRONG_NEW, "new_password": STRONG_OLD},
        headers=headers,
    )
    assert blocked.status_code == 400
