"""
Email notification tests: template rendering (incl. HTML escaping of
user-derived values), console transport logging, SMTP transport delivery,
per-user email preferences, and the preference-gated notification fan-out.
"""
import smtplib

import pytest

import app.repositories.notification_repo as notification_repo
import app.services.email_service as email_service_module
from app.services.email_preference_service import set_preference
from app.services.email_service import send_email
from app.services.email_templates import render_email
from app.models import User

PASSWORD = "Str0ng!TestPass42"


def _register(client, email, full_name="Email Tester"):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def _login(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def test_verify_email_template_includes_link_and_recipient():
    subject, html_body, text_body = render_email(
        "verify_email",
        {"user_name": "Ada", "verification_url": "https://app.dev/verify-email?token=abc"},
        button_url="https://app.dev/verify-email?token=abc",
    )
    assert "Verify your email" in subject
    assert "https://app.dev/verify-email?token=abc" in html_body
    assert "Hi Ada" in text_body


def test_user_supplied_values_are_escaped_in_html_only():
    _, html_body, text_body = render_email(
        "notification",
        {"subject": "s", "title": "t", "message": "<script>x()</script>",
         "user_name": "<b>Bob</b>"},
    )
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
    # The text alternative keeps the raw value (no HTML context to escape).
    assert "<script>x()</script>" in text_body


def test_unknown_template_name_raises():
    with pytest.raises(KeyError):
        render_email("does_not_exist", {})


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------

def test_console_backend_logs_and_succeeds(caplog):
    with caplog.at_level("INFO", logger="app.services.email_service"):
        sent = send_email("a@b.dev", "Hello", "<p>body</p>", "body")
    assert sent is True
    assert "[EMAIL:console]" in caplog.text
    assert "a@b.dev" in caplog.text


class _FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.ended_tls = False
        self.logged_in = None
        self.sent = None
        _FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        pass

    def starttls(self):
        self.ended_tls = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def sendmail(self, from_addr, to_addrs, payload):
        self.sent = (from_addr, to_addrs, payload)


def test_smtp_backend_delivers_multipart_message(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.local")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "mailer")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(email_service_module.smtplib, "SMTP", _FakeSMTP)
    _FakeSMTP.instances = []

    sent = send_email("dest@b.dev", "Subj", "<p>html</p>", "text")

    assert sent is True
    server = _FakeSMTP.instances[-1]
    assert server.host == "smtp.test.local" and server.port == 587
    assert server.ended_tls is True
    assert server.logged_in == ("mailer", "secret")
    from_addr, to_addrs, payload = server.sent
    assert to_addrs == ["dest@b.dev"]
    assert from_addr == settings.EMAIL_FROM

    import email as email_lib

    parsed = email_lib.message_from_string(payload)
    assert parsed["Subject"] == "Subj"
    assert parsed.get_content_type() == "multipart/alternative"
    bodies = {
        part.get_content_type(): part.get_payload(decode=True).decode("utf-8")
        for part in parsed.walk()
        if part.get_content_type() in ("text/plain", "text/html")
    }
    assert "<p>html</p>" in bodies["text/html"]
    assert "text" in bodies["text/plain"]


def test_smtp_backend_returns_false_on_delivery_failure(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.local")

    class _FailingSMTP(_FakeSMTP):
        def sendmail(self, from_addr, to_addrs, payload):
            raise smtplib.SMTPException("relay refused")

    monkeypatch.setattr(email_service_module.smtplib, "SMTP", _FailingSMTP)

    assert send_email("dest@b.dev", "Subj", "<p>html</p>", "text") is False


# ---------------------------------------------------------------------------
# Preferences API
# ---------------------------------------------------------------------------

def test_email_preferences_require_auth(client):
    assert client.get("/api/notifications/email-preferences").status_code == 401


def test_preferences_default_to_opted_in(client):
    email = "prefs1@email.dev"
    _register(client, email)
    headers = _login(client, email)

    resp = client.get("/api/notifications/email-preferences", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"notifications_enabled": True}


def test_preferences_can_be_opted_out_and_persist(client, db_session):
    email = "prefs2@email.dev"
    _register(client, email)
    headers = _login(client, email)

    resp = client.put(
        "/api/notifications/email-preferences",
        json={"notifications_enabled": False},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"notifications_enabled": False}

    reread = client.get("/api/notifications/email-preferences", headers=headers)
    assert reread.json() == {"notifications_enabled": False}

    user = db_session.query(User).filter(User.email == email).first()
    assert user.email_preference.notifications_enabled is False


# ---------------------------------------------------------------------------
# Preference-gated fan-out
# ---------------------------------------------------------------------------

def test_notification_fan_out_emails_opted_in_user(client, db_session, monkeypatch):
    email = "fanout1@email.dev"
    user_id = _register(client, email)

    sent = []
    monkeypatch.setattr(
        email_service_module.email_service,
        "send_notification_email",
        lambda **kwargs: sent.append(kwargs) or True,
    )

    notification_repo.create_notification(
        db_session,
        recipient_id=user_id,
        notification_type="PAYMENT",
        title="Payment Due",
        message="You owe money",
    )
    assert len(sent) == 1
    assert sent[0]["subject"] == "Payment Due"
    assert sent[0]["message"] == "You owe money"


def test_notification_fan_out_respects_opt_out(client, db_session, monkeypatch):
    email = "fanout2@email.dev"
    user_id = _register(client, email)
    set_preference(db_session, user_id, notifications_enabled=False)

    sent = []
    monkeypatch.setattr(
        email_service_module.email_service,
        "send_notification_email",
        lambda **kwargs: sent.append(kwargs) or True,
    )

    notification_repo.create_notification(
        db_session,
        recipient_id=user_id,
        notification_type="LEASE",
        title="Lease signed",
        message="Congrats",
    )
    assert sent == []


def test_fan_out_swallows_delivery_errors(client, db_session, monkeypatch):
    email = "fanout3@email.dev"
    user_id = _register(client, email)

    def _boom(**kwargs):
        raise RuntimeError("smtp exploded")

    monkeypatch.setattr(email_service_module.email_service, "send_notification_email", _boom)

    notification = notification_repo.create_notification(
        db_session,
        recipient_id=user_id,
        notification_type="SYSTEM",
        title="Still created",
        message="Email failure must not lose the in-app notification",
    )
    assert notification.id is not None
