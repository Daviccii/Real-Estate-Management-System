"""
SMS notification tests.
Covers the pluggable SMS backend (console/twilio) and the high-priority
notification fan-out to recipients with a phone number on file.
"""
import uuid

import pytest

from app.config.settings import settings
from app.models.user import User
from app.repositories import notification_repo as notification_repo_module
from app.repositories.notification_repo import create_notification
from app.services import sms_service as sms_service_module
from app.services.sms_service import send_message, sms_service

SMS_LOGGER = "app.services.sms_service"


def _make_user(db_session, phone=None):
    user = User(
        email=f"sms_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="not-a-real-hash",
        full_name="SMS Tester",
        phone=phone,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_console_backend_logs_and_succeeds(caplog):
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        ok = send_message("+15551230000", "Your rent is due")
    assert ok is True
    assert "[SMS:console]" in caplog.text
    assert "+15551230000" in caplog.text
    assert "Your rent is due" in caplog.text


def test_send_otp_includes_code_and_expiry(caplog):
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        ok = sms_service.send_otp("+15551230001", "123456", "Ada")
    assert ok is True
    assert "123456" in caplog.text
    assert str(settings.MFA_SMS_CODE_EXPIRE_MINUTES) in caplog.text


def test_missing_phone_or_body_returns_false():
    assert send_message("", "hello") is False
    assert send_message("+15551230000", "") is False
    assert sms_service.send_otp("", "123456") is False


def test_twilio_backend_fails_closed(monkeypatch, caplog):
    monkeypatch.setattr(settings, "SMS_BACKEND", "twilio")
    with caplog.at_level("ERROR", logger=SMS_LOGGER):
        ok = send_message("+15551230002", "should not deliver")
    assert ok is False
    assert "TWILIO_ACCOUNT_SID" in caplog.text


def test_unknown_backend_fails_closed(monkeypatch, caplog):
    monkeypatch.setattr(settings, "SMS_BACKEND", "carrier-pigeon")
    with caplog.at_level("ERROR", logger=SMS_LOGGER):
        ok = send_message("+15551230003", "should not deliver")
    assert ok is False


def test_long_message_is_truncated(caplog):
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        ok = send_message("+15551230004", "x" * 2000)
    assert ok is True
    assert sms_service_module._SMS_MAX_LENGTH == 1600
    assert ("x" * 1600) in caplog.text
    assert ("x" * 1601) not in caplog.text


def test_high_priority_notification_fans_out_sms(db_session, caplog):
    user = _make_user(db_session, phone="+15551230005")
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        create_notification(
            db_session,
            recipient_id=user.id,
            notification_type="PAYMENT",
            title="Payment Overdue",
            message="Payment of $1200.00 is OVERDUE",
            priority="HIGH",
        )
    assert "[SMS:console]" in caplog.text
    assert "+15551230005" in caplog.text
    assert "Payment Overdue" in caplog.text


def test_normal_priority_notification_skips_sms(db_session, caplog):
    user = _make_user(db_session, phone="+15551230006")
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        create_notification(
            db_session,
            recipient_id=user.id,
            notification_type="PAYMENT",
            title="Payment Due",
            message="Payment of $1200.00 is due soon",
            priority="NORMAL",
        )
    assert "[SMS:console]" not in caplog.text


def test_notification_without_phone_skips_sms(db_session, caplog):
    user = _make_user(db_session, phone=None)
    with caplog.at_level("INFO", logger=SMS_LOGGER):
        create_notification(
            db_session,
            recipient_id=user.id,
            notification_type="SECURITY",
            title="Security Alert",
            message="New sign-in detected",
            priority="CRITICAL",
        )
    assert "[SMS:console]" not in caplog.text


def test_sms_fan_out_failure_never_breaks_notification(db_session, monkeypatch, caplog):
    user = _make_user(db_session, phone="+15551230007")

    def _boom(phone, message):
        raise RuntimeError("provider down")

    monkeypatch.setattr(notification_repo_module, "send_message", _boom)
    with caplog.at_level("WARNING", logger="app.repositories.notification_repo"):
        notification = create_notification(
            db_session,
            recipient_id=user.id,
            notification_type="PAYMENT",
            title="Payment Overdue",
            message="still created",
            priority="HIGH",
        )
    assert notification.id is not None
    assert "SMS fan-out failed" in caplog.text
