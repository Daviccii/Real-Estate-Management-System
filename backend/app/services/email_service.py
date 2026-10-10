"""
Email Service

Transactional email delivery with two transports selected by EMAIL_BACKEND:
- console (default): log the email instead of delivering it - safe for dev/tests
- smtp: deliver via any SMTP relay (SES/Mailgun SMTP, Mailhog, Gmail, ...)

Security emails (verification, password reset, deletion receipts) are always
sent regardless of user preferences; only in-app notification fan-out is
preference-gated (see notification_repo).
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config.settings import settings
from app.services.email_templates import render_email

logger = logging.getLogger(__name__)


def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Deliver a multipart/alternative message over SMTP. Returns True on success."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS
        ) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to_email], message.as_string())
        return True
    except Exception as exc:
        logger.error("SMTP delivery to %s failed: %s", to_email, exc, exc_info=True)
        return False


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send (or log) one email through the configured backend."""
    if settings.EMAIL_BACKEND == "smtp":
        return _send_via_smtp(to_email, subject, html_body, text_body)

    logger.info(
        "[EMAIL:console] to=%s subject=%s\n%s",
        to_email,
        subject,
        text_body,
    )
    return True


class EmailService:
    """Template-rendered transactional emails; safe, non-raising call API."""

    @staticmethod
    def send_verification_email(email: str, verification_url: str, user_name: str = None) -> bool:
        """Send the email-verification link. Transactional: ignores user preferences."""
        subject, html_body, text_body = render_email(
            "verify_email",
            {"user_name": user_name or "there", "verification_url": verification_url},
            button_url=verification_url,
            button_label="Verify my email",
            app_name=settings.APP_NAME,
        )
        return send_email(email, subject, html_body, text_body)

    @staticmethod
    def send_password_reset_email(email: str, reset_url: str, user_name: str = None) -> bool:
        """Send the single-use password reset link. Transactional: ignores user preferences."""
        subject, html_body, text_body = render_email(
            "password_reset",
            {"user_name": user_name or "there", "reset_url": reset_url},
            button_url=reset_url,
            button_label="Reset password",
            app_name=settings.APP_NAME,
        )
        return send_email(email, subject, html_body, text_body)

    @staticmethod
    def send_notification_email(
        email: str,
        subject: str,
        message: str,
        user_name: str = None,
        title: Optional[str] = None,
    ) -> bool:
        """
        Send a generic notification email with an optional in-app-style title.

        Transactional receipts (e.g. deletion-request confirmation) call this
        directly; the preference-gated in-app fan-out lives in notification_repo.
        """
        _, html_body, text_body = render_email(
            "notification",
            {"subject": subject, "title": title or subject, "message": message,
             "user_name": user_name or "there"},
            app_name=settings.APP_NAME,
        )
        return send_email(email, subject, html_body, text_body)


# Global email service instance
email_service = EmailService()
