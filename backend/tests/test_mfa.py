"""
MFA tests: TOTP enroll -> challenge -> verify, recovery codes (single-use),
SMS backup, disable, and mandatory-for-admin enforcement.
"""
from app.config.settings import settings
from app.models.user import User
from app.utils.security import get_password_hash
from app.utils.totp import compute_totp

PASSWORD = "Str0ng!TestPass42"


def _register_and_bearer(client, email, phone=None, db_session=None):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "MFA Tester"},
    )
    assert resp.status_code == 200, resp.text
    if phone and db_session is not None:
        user = db_session.query(User).filter(User.id == resp.json()["id"]).first()
        user.phone = phone
        db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return login.json()["access_token"], resp.json()["id"]


def _enroll_totp(client, bearer):
    headers = {"Authorization": f"Bearer {bearer}"}
    setup = client.post("/api/v1/auth/mfa/setup", json={}, headers=headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    assert setup.json()["provisioning_uri"].startswith("otpauth://totp/")
    code = compute_totp(secret)
    enable = client.post("/api/v1/auth/mfa/enable", json={"code": code}, headers=headers)
    assert enable.status_code == 200, enable.text
    return secret, enable.json()["recovery_codes"]


def test_enroll_then_login_challenge_and_totp_verify(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa1@mfatest.dev")
    _enroll_totp(client, bearer)

    login = client.post("/api/auth/login", json={"email": "mfa1@mfatest.dev", "password": PASSWORD})
    body = login.json()
    assert login.status_code == 200
    assert body["mfa_required"] is True
    assert body["access_token"] == ""
    assert body["mfa_token"]

    # Wrong TOTP rejected
    bad = client.post("/api/v1/auth/mfa/verify", json={"mfa_token": body["mfa_token"], "method": "totp", "code": "000000"})
    assert bad.status_code == 401

    user = db_session.query(User).filter(User.email == "mfa1@mfatest.dev").first()
    # Correct TOTP accepted
    code = compute_totp(user.mfa_secret)
    ok = client.post("/api/v1/auth/mfa/verify", json={"mfa_token": body["mfa_token"], "method": "totp", "code": code})
    assert ok.status_code == 200, ok.text
    access = ok.json()["access_token"]
    assert access
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200


def test_mfa_token_cannot_be_used_as_access_token(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa2@mfatest.dev")
    _enroll_totp(client, bearer)
    login = client.post("/api/auth/login", json={"email": "mfa2@mfatest.dev", "password": PASSWORD})
    mfa_token = login.json()["mfa_token"]

    # The challenge token must not grant access to protected endpoints
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {mfa_token}"})
    assert me.status_code == 401


def test_recovery_code_single_use(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa3@mfatest.dev")
    _, recovery_codes = _enroll_totp(client, bearer)
    code = recovery_codes[0]

    login = client.post("/api/auth/login", json={"email": "mfa3@mfatest.dev", "password": PASSWORD})
    mfa_token = login.json()["mfa_token"]
    ok = client.post("/api/v1/auth/mfa/verify", json={"mfa_token": mfa_token, "method": "recovery", "code": code})
    assert ok.status_code == 200

    # Same recovery code cannot be reused
    login2 = client.post("/api/auth/login", json={"email": "mfa3@mfatest.dev", "password": PASSWORD})
    reuse = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": login2.json()["mfa_token"], "method": "recovery", "code": code},
    )
    assert reuse.status_code == 401


def test_sms_backup_flow(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa4@mfatest.dev", phone="+254700111222", db_session=db_session)
    _enroll_totp(client, bearer)

    login = client.post("/api/auth/login", json={"email": "mfa4@mfatest.dev", "password": PASSWORD})
    mfa_token = login.json()["mfa_token"]
    assert "sms" in login.json()["allowed_methods"]

    sent = client.post("/api/v1/auth/mfa/send-sms", json={"mfa_token": mfa_token})
    assert sent.status_code == 200, sent.text
    sms_code = sent.json()["dev_code"]

    ok = client.post("/api/v1/auth/mfa/verify", json={"mfa_token": mfa_token, "method": "sms", "code": sms_code})
    assert ok.status_code == 200, ok.text


def test_disable_mfa(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa5@mfatest.dev")
    secret, _ = _enroll_totp(client, bearer)

    disabled = client.post(
        "/api/v1/auth/mfa/disable",
        json={"code": compute_totp(secret)},
        headers={"Authorization": f"Bearer {bearer}"},
    )
    assert disabled.status_code == 200, disabled.text

    # Login is a plain session again
    login = client.post("/api/auth/login", json={"email": "mfa5@mfatest.dev", "password": PASSWORD})
    assert login.json()["mfa_required"] is False
    assert login.json()["access_token"]


def test_status_endpoint(client, db_session):
    bearer, _ = _register_and_bearer(client, "mfa6@mfatest.dev")
    status_before = client.get("/api/v1/auth/mfa/status", headers={"Authorization": f"Bearer {bearer}"}).json()
    assert status_before["mfa_enabled"] is False

    _enroll_totp(client, bearer)
    status_after = client.get("/api/v1/auth/mfa/status", headers={"Authorization": f"Bearer {bearer}"}).json()
    assert status_after["mfa_enabled"] is True
    assert status_after["recovery_codes_remaining"] == settings.MFA_RECOVERY_CODE_COUNT


def test_admin_mfa_mandatory_flow(client, db_session, monkeypatch):
    """With MFA_MANDATORY_FOR_ADMIN on, admins must enroll during login."""
    monkeypatch.setattr(settings, "MFA_MANDATORY_FOR_ADMIN", True)

    admin = User(
        email="admin001@mfatest.dev",
        hashed_password=get_password_hash(PASSWORD),
        full_name="Forced Admin",
        role="admin",
        roles_csv="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()

    # Step 1: password only -> setup challenge, no session
    login = client.post("/api/auth/login", json={"email": "admin001@mfatest.dev", "password": PASSWORD})
    body = login.json()
    assert body["mfa_required"] is True
    assert body["mfa_setup_required"] is True
    mfa_token = body["mfa_token"]

    # Step 2: enroll with the mfa_token
    setup = client.post("/api/v1/auth/mfa/setup", json={"mfa_token": mfa_token})
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    enable = client.post("/api/v1/auth/mfa/enable", json={"mfa_token": mfa_token, "code": compute_totp(secret)})
    assert enable.status_code == 200, enable.text

    # Step 3: challenge -> verify -> real session
    login2 = client.post("/api/auth/login", json={"email": "admin001@mfatest.dev", "password": PASSWORD})
    assert login2.json()["mfa_setup_required"] is False  # now enrolled
    ok = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": login2.json()["mfa_token"], "method": "totp", "code": compute_totp(secret)},
    )
    assert ok.status_code == 200, ok.text
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {ok.json()['access_token']}"})
    assert me.status_code == 200


def test_admin_not_challenged_when_mandatory_off(client, db_session):
    """Default (flag off): admins log in with password only."""
    assert settings.MFA_MANDATORY_FOR_ADMIN is False
    admin = User(
        email="admin002@mfatest.dev",
        hashed_password=get_password_hash(PASSWORD),
        role="admin",
        roles_csv="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": "admin002@mfatest.dev", "password": PASSWORD})
    assert login.json()["mfa_required"] is False
    assert login.json()["access_token"]
