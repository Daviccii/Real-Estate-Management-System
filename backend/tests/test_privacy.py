"""
Privacy / GDPR tests: data export, consent recording (anonymous and
authenticated), deletion request lifecycle, and admin erasure execution.
"""
from app.models import ConsentRecord, DataDeletionRequest, User

PASSWORD = "Str0ng!TestPass42"


def _register(client, email):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Privacy Tester"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_admin(db_session, email):
    user = db_session.query(User).filter(User.email == email).first()
    user.role = "admin"
    db_session.commit()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def test_export_requires_auth(client):
    assert client.get("/api/privacy/export").status_code == 401


def test_export_returns_profile_with_secrets_redacted(client, db_session):
    email = "export1@privacy.dev"
    _register(client, email)
    headers = _login(client, email)

    # Related data to verify the export picks it up.
    client.post(
        "/api/privacy/consent",
        json={"consent_type": "cookie_analytics", "granted": True},
        headers=headers,
    )

    resp = client.get("/api/privacy/export", headers=headers)
    assert resp.status_code == 200, resp.text
    assert "attachment" in resp.headers.get("content-disposition", "")

    data = resp.json()
    assert data["profile"]["email"] == email
    assert data["profile"]["hashed_password"] == "[REDACTED]"
    assert data["profile"]["mfa_secret"] == "[REDACTED]"
    assert len(data["related_data"]["consents"]) == 1
    assert data["related_data"]["consents"][0]["granted"] is True


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------

def test_consent_anonymous_and_authenticated(client, db_session):
    resp = client.post(
        "/api/privacy/consent",
        json={"consent_type": "cookie_analytics", "granted": True, "client_id": "anon-123"},
    )
    assert resp.status_code == 200
    assert resp.json()["recorded"] is True

    _register(client, "consent1@privacy.dev")
    headers = _login(client, "consent1@privacy.dev")
    resp = client.post(
        "/api/privacy/consent",
        json={"consent_type": "cookie_marketing", "granted": False},
        headers=headers,
    )
    assert resp.status_code == 200

    rows = db_session.query(ConsentRecord).order_by(ConsentRecord.id).all()
    assert len(rows) == 2
    assert rows[0].user_id is None and rows[0].client_id == "anon-123" and rows[0].granted is True
    assert rows[1].user_id is not None and rows[1].client_id is None and rows[1].granted is False


def test_consent_rejects_unknown_type(client):
    resp = client.post(
        "/api/privacy/consent",
        json={"consent_type": "definitely_not_a_type", "granted": True},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Deletion request lifecycle
# ---------------------------------------------------------------------------

def test_deletion_request_lifecycle(client, db_session):
    _register(client, "lifecycle@privacy.dev")
    headers = _login(client, "lifecycle@privacy.dev")

    assert client.get("/api/privacy/delete-request", headers=headers).json()["request"] is None

    resp = client.post("/api/privacy/delete-request", json={"reason": "testing"}, headers=headers)
    assert resp.status_code == 202
    assert resp.json()["created"] is True
    request_id = resp.json()["request"]["id"]

    # Idempotent: a second request while pending returns the same row.
    resp = client.post("/api/privacy/delete-request", json={}, headers=headers)
    assert resp.status_code == 202
    assert resp.json()["created"] is False
    assert resp.json()["request"]["id"] == request_id

    resp = client.delete("/api/privacy/delete-request", headers=headers)
    assert resp.status_code == 200
    assert client.delete("/api/privacy/delete-request", headers=headers).status_code == 404

    row = db_session.query(DataDeletionRequest).filter(DataDeletionRequest.id == request_id).first()
    assert row.status == "cancelled"


# ---------------------------------------------------------------------------
# Admin queue and execution
# ---------------------------------------------------------------------------

def _setup_admin_and_request(client, db_session, tag):
    _register(client, f"admin_{tag}@privacy.dev")
    _make_admin(db_session, f"admin_{tag}@privacy.dev")
    _register(client, f"user_{tag}@privacy.dev")
    admin_headers = _login(client, f"admin_{tag}@privacy.dev")
    user_headers = _login(client, f"user_{tag}@privacy.dev")
    resp = client.post("/api/privacy/delete-request", json={"reason": "gdpr"}, headers=user_headers)
    return admin_headers, user_headers, resp.json()["request"]["id"]


def test_non_admin_cannot_access_admin_queue(client, db_session):
    _register(client, "pleb@privacy.dev")
    headers = _login(client, "pleb@privacy.dev")
    assert client.get("/api/privacy/admin/deletion-requests", headers=headers).status_code == 403


def test_admin_lists_and_executes_deletion(client, db_session):
    admin_headers, user_headers, request_id = _setup_admin_and_request(client, db_session, "exec")
    user_email = "user_exec@privacy.dev"

    listing = client.get("/api/privacy/admin/deletion-requests", headers=admin_headers)
    assert listing.status_code == 200
    assert any(r["id"] == request_id and r["status"] == "pending" for r in listing.json()["requests"])

    resp = client.post(f"/api/privacy/admin/deletion-requests/{request_id}/execute", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"

    user = db_session.query(User).filter(User.email == user_email).first()
    assert user is None  # original email gone
    anon = db_session.query(User).filter(User.id == resp.json()["user_id"]).first()
    assert anon.email == f"deleted+{resp.json()['user_id']}@anonymized.invalid"
    assert anon.full_name == "Deleted User"
    assert anon.is_active is False

    # Old credentials no longer authenticate.
    assert client.post("/api/auth/login", json={"email": user_email, "password": PASSWORD}).status_code != 200

    # Executing twice is rejected.
    assert client.post(f"/api/privacy/admin/deletion-requests/{request_id}/execute", headers=admin_headers).status_code == 400


def test_admin_can_decline_request(client, db_session):
    admin_headers, _, request_id = _setup_admin_and_request(client, db_session, "decline")
    resp = client.post(
        f"/api/privacy/admin/deletion-requests/{request_id}/decline",
        json={"notes": "Active lease with financial obligations"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["request"]["status"] == "declined"
    assert "lease" in resp.json()["request"]["notes"]


def test_execute_with_missing_user_declines(client, db_session):
    _register(client, "ghost_admin@privacy.dev")
    _make_admin(db_session, "ghost_admin@privacy.dev")
    admin_headers = _login(client, "ghost_admin@privacy.dev")

    _register(client, "vanishing@privacy.dev")
    user_headers = _login(client, "vanishing@privacy.dev")
    request_id = client.post("/api/privacy/delete-request", json={}, headers=user_headers).json()["request"]["id"]

    user = db_session.query(User).filter(User.email == "vanishing@privacy.dev").first()
    user_id = user.id
    db_session.delete(user)
    db_session.commit()

    resp = client.post(f"/api/privacy/admin/deletion-requests/{request_id}/execute", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"
