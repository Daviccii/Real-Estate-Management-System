"""Comprehensive logging (#27): security event stream, request correlation, formatters."""
import json
import logging
import uuid

import pytest

from app.config.logging_config import JSONFormatter
from app.services.security_events import emit_security_event

PASSWORD = "Str0ng!TestPass42"


@pytest.fixture()
def unique_suffix():
    return uuid.uuid4().hex[:8]


def _register(client, email, full_name="Sec Log Tester"):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email, password=PASSWORD):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp


def _security_events(caplog):
    return [r.security for r in caplog.records if hasattr(r, "security")]


# ---------------------------------------------------------------------------
# emit_security_event / formatters
# ---------------------------------------------------------------------------

def test_emit_security_event_structures_record(caplog):
    with caplog.at_level(logging.WARNING, logger="security"):
        emit_security_event(
            "auth.login_failed",
            user_id=7,
            actor="someone@example.com",
            details={"attempt": 3},
        )
    payload = _security_events(caplog)[-1]
    assert payload["event"] == "auth.login_failed"
    assert payload["outcome"] == "denied"
    assert payload["user_id"] == 7
    assert payload["actor"] == "someone@example.com"
    assert payload["details"] == {"attempt": 3}
    assert "password" not in json.dumps(payload).lower()


def test_json_formatter_includes_security_payload():
    record = logging.LogRecord(
        "security", logging.WARNING, __file__, 1, "auth.login_failed", (), None
    )
    record.security = {"event": "auth.login_failed", "ip": "203.0.113.9"}
    data = json.loads(JSONFormatter().format(record))
    assert data["level"] == "WARNING"
    assert data["security"] == {"event": "auth.login_failed", "ip": "203.0.113.9"}


def test_json_formatter_includes_request_fields():
    record = logging.LogRecord(
        "app.request", logging.INFO, __file__, 1, "GET /x", (), None
    )
    record.method = "GET"
    record.path = "/x"
    record.status = 200
    record.duration_ms = 3.21
    record.request_id = "abcdef1234567890"
    data = json.loads(JSONFormatter().format(record))
    assert data["status"] == 200
    assert data["duration_ms"] == 3.21
    assert data["request_id"] == "abcdef1234567890"


# ---------------------------------------------------------------------------
# API-driven security events
# ---------------------------------------------------------------------------

def test_failed_login_emits_security_event(client, caplog, unique_suffix):
    email = f"sec_fail_{unique_suffix}@seclog.dev"
    _register(client, email)
    with caplog.at_level(logging.WARNING, logger="security"):
        resp = _login(client, email, password="Wr0ng!Password1")
    assert resp.status_code == 401
    payloads = [p for p in _security_events(caplog) if p["event"] == "auth.login_failed"]
    assert payloads, "expected an auth.login_failed security event"
    assert payloads[-1]["actor"] == email
    assert payloads[-1]["outcome"] == "denied"


def test_successful_login_emits_security_event(client, caplog, unique_suffix):
    email = f"sec_ok_{unique_suffix}@seclog.dev"
    _register(client, email)
    with caplog.at_level(logging.INFO, logger="security"):
        resp = _login(client, email)
    assert resp.status_code == 200
    payloads = [p for p in _security_events(caplog) if p["event"] == "auth.login_success"]
    assert payloads, "expected an auth.login_success security event"
    assert payloads[-1]["outcome"] == "allowed"


def test_mfa_verify_failure_emits_security_event(client, caplog):
    with caplog.at_level(logging.WARNING, logger="security"):
        resp = client.post(
            "/api/auth/mfa/verify",
            json={"mfa_token": "bogus-token", "method": "totp", "code": "123456"},
        )
    assert resp.status_code == 401
    payloads = [p for p in _security_events(caplog) if p["event"] == "auth.mfa_failed"]
    assert payloads
    assert payloads[-1]["details"]["reason"] == "invalid_mfa_token"


def test_password_reset_events(client, caplog, unique_suffix):
    with caplog.at_level(logging.INFO, logger="security"):
        client.post(
            "/api/auth/forgot-password",
            json={"email": f"sec_reset_{unique_suffix}@seclog.dev", "base_url": "http://localhost:5173"},
        )
        resp = client.post(
            "/api/auth/reset-password",
            json={"token": "bogus", "new_password": PASSWORD},
        )
    assert resp.status_code == 400
    events = [p["event"] for p in _security_events(caplog)]
    assert "auth.password_reset_requested" in events
    assert "auth.password_reset_rejected" in events


# ---------------------------------------------------------------------------
# Request correlation middleware
# ---------------------------------------------------------------------------

def test_request_id_generated_and_echoed(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id")


def test_request_id_incoming_value_is_echoed(client):
    resp = client.get("/health/live", headers={"X-Request-ID": "trace-abc-12345"})
    assert resp.headers["x-request-id"] == "trace-abc-12345"


def test_request_id_malformed_header_is_replaced(client):
    resp = client.get("/health/live", headers={"X-Request-ID": "drop table users;--"})
    request_id = resp.headers["x-request-id"]
    assert request_id != "drop table users;--"
    assert len(request_id) == 16


def test_malformed_request_id_never_reaches_security_events(client, caplog):
    with caplog.at_level(logging.WARNING, logger="security"):
        client.get("/health/live", headers={"X-Request-ID": "../etc/passwd"})
    for payload in _security_events(caplog):
        assert payload.get("request_id") != "../etc/passwd"
