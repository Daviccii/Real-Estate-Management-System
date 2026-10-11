"""
Alerting service tests: console fan-out, provider payload shapes
(PagerDuty / Datadog / Sentry), fail-closed without credentials, transport
failures never raising, the global 5xx handler emitting an alert, and
critical security events forwarding to the alerting backends.
"""
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.config.settings import settings
from app.main import app
from app.services import alert_service
from app.services.alert_service import emit_alert


def _capture_transport(monkeypatch):
    sent = []

    def fake_post(url, headers, payload):
        sent.append({"url": url, "headers": headers, "payload": payload})
        return True

    monkeypatch.setattr(alert_service, "_post_json", fake_post)
    return sent


# ---------------------------------------------------------------------------
# Console default
# ---------------------------------------------------------------------------

def test_console_backend_default_succeeds(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["console"])
    assert emit_alert("db latency spike", severity="warning") is True


def test_unknown_backend_never_raises(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["bogus-backend"])
    assert emit_alert("whatever") is False


def test_transport_failure_never_raises(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["pagerduty"])
    monkeypatch.setattr(settings, "PAGERDUTY_ROUTING_KEY", "rk-test")

    def boom(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr(alert_service.httpx, "post", boom)
    assert emit_alert("pager test") is False


# ---------------------------------------------------------------------------
# PagerDuty
# ---------------------------------------------------------------------------

def test_pagerduty_fails_closed_without_key(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["pagerduty"])
    monkeypatch.setattr(settings, "PAGERDUTY_ROUTING_KEY", None)
    assert emit_alert("no key") is False


def test_pagerduty_payload_shape(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["pagerduty"])
    monkeypatch.setattr(settings, "PAGERDUTY_ROUTING_KEY", "rk-123")
    sent = _capture_transport(monkeypatch)

    assert emit_alert("audit chain broken", severity="high", details={"entry": 7}, dedup_key="chain:7") is True
    assert len(sent) == 1
    body = sent[0]["payload"]
    assert sent[0]["url"] == "https://events.pagerduty.com/v2/enqueue"
    assert body["routing_key"] == "rk-123"
    assert body["event_action"] == "trigger"
    assert body["dedup_key"] == "chain:7"
    assert body["payload"]["severity"] == "error"  # "high" maps onto PD's scale
    assert body["payload"]["summary"] == "audit chain broken"
    assert body["payload"]["custom_details"] == {"entry": 7}


# ---------------------------------------------------------------------------
# Datadog
# ---------------------------------------------------------------------------

def test_datadog_fails_closed_without_key(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["datadog"])
    monkeypatch.setattr(settings, "DATADOG_API_KEY", None)
    assert emit_alert("no key") is False


def test_datadog_payload_shape(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["datadog"])
    monkeypatch.setattr(settings, "DATADOG_API_KEY", "dd-key")
    monkeypatch.setattr(settings, "DATADOG_SITE", "datadoghq.eu")
    sent = _capture_transport(monkeypatch)

    assert emit_alert("5xx spike", severity="error", dedup_key="exc:RuntimeError:/x") is True
    assert sent[0]["url"] == "https://api.datadoghq.eu/api/v1/events"
    assert sent[0]["headers"]["DD-API-KEY"] == "dd-key"
    assert sent[0]["payload"]["title"] == "5xx spike"
    assert sent[0]["payload"]["alert_type"] == "error"
    assert sent[0]["payload"]["aggregation_key"] == "exc:RuntimeError:/x"


# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------

def test_sentry_fails_closed_without_dsn(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["sentry"])
    monkeypatch.setattr(settings, "SENTRY_DSN", None)
    assert emit_alert("no dsn") is False


def test_sentry_malformed_dsn_refused(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["sentry"])
    monkeypatch.setattr(settings, "SENTRY_DSN", "not-a-dsn")
    assert emit_alert("bad dsn") is False


def test_sentry_payload_shape(monkeypatch):
    monkeypatch.setattr(settings, "ALERT_BACKENDS", ["sentry"])
    monkeypatch.setattr(settings, "SENTRY_DSN", "https://abc123@o1.ingest.sentry.io/4242")
    sent = _capture_transport(monkeypatch)

    assert emit_alert("db down", severity="critical", details={"db": "primary"}) is True
    assert sent[0]["url"] == "https://o1.ingest.sentry.io/api/4242/store/"
    assert "sentry_key=abc123" in sent[0]["headers"]["X-Sentry-Auth"]
    assert sent[0]["payload"]["level"] == "fatal"  # critical maps to fatal
    assert sent[0]["payload"]["message"] == "db down"
    assert sent[0]["payload"]["extra"] == {"db": "primary"}


# ---------------------------------------------------------------------------
# Wiring: 5xx handler + security events
# ---------------------------------------------------------------------------

def test_global_exception_handler_emits_alert(test_engine, monkeypatch):
    from app.database.database import get_db, get_read_db

    def raiser():
        raise RuntimeError("boom")

    app.dependency_overrides[get_db] = raiser
    app.dependency_overrides[get_read_db] = raiser

    calls = []

    def recorder(title, **kwargs):
        calls.append((title, kwargs))
        return True

    monkeypatch.setattr("app.main.emit_alert", recorder)

    try:
        # raise_server_exceptions=False so the 500 travels through
        # ServerErrorMiddleware's custom handler instead of re-raising here.
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/v1/properties")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 500
    assert calls, "expected the global handler to emit an alert"
    title, kwargs = calls[0]
    assert "RuntimeError" in title
    assert kwargs["severity"] == "error"
    # FastAPI's redirect_slashes sends /api/v1/properties -> /api/v1/properties/,
    # so the handler sees the post-redirect path.
    assert kwargs["dedup_key"] == "exc:RuntimeError:/api/v1/properties/"


def test_critical_security_event_forwards_to_alerting(monkeypatch):
    from app.services import security_events

    calls = []
    monkeypatch.setattr(
        "app.services.security_events.emit_alert",
        lambda title, **kwargs: calls.append((title, kwargs)) or True,
    )

    security_events.emit_security_event("audit_chain_broken", severity="critical")
    assert calls and calls[0][0] == "audit_chain_broken"
    assert calls[0][1]["severity"] == "critical"
    assert calls[0][1]["dedup_key"] == "security:audit_chain_broken"


def test_info_security_event_does_not_page(monkeypatch):
    from app.services import security_events

    calls = []
    monkeypatch.setattr(
        "app.services.security_events.emit_alert",
        lambda title, **kwargs: calls.append((title, kwargs)) or True,
    )

    security_events.emit_security_event("login_succeeded", severity="info", outcome="allowed")
    assert calls == []
