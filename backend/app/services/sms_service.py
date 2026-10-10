"""
SMS Service

Pluggable SMS backend for MFA backup codes and high-priority alerts.
Two transports selected by SMS_BACKEND:
- console (default): log the message instead of delivering it - safe for dev/tests
- twilio: reserved production transport; fails closed until provider credentials
  are configured (from a secrets manager, never .env in production)
"""
import logging
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Twilio's hard single-message limit; guards against runaway notification bodies.
_SMS_MAX_LENGTH = 1600


def send_message(phone: str, message: str) -> bool:
    """
    Send (or log) one SMS through the configured backend. Never raises.

    Returns:
        bool: True if the message was dispatched (or logged in console mode)
    """
    if not phone or not message:
        logger.warning("SMS skipped: missing phone number or message body")
        return False

    if settings.SMS_BACKEND == "console":
        logger.info("[SMS:console] to=%s\n%s", phone, message[:_SMS_MAX_LENGTH])
        return True

    if settings.SMS_BACKEND == "twilio":
        logger.error(
            "SMS backend 'twilio' is not configured; set TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER (from a secrets manager) "
            "to enable it"
        )
        return False

    logger.error("Unknown SMS_BACKEND '%s'; message not delivered", settings.SMS_BACKEND)
    return False


class SmsService:
    """Facade kept for existing callers (`sms_service.send_otp`)."""

    @staticmethod
    def send_otp(phone: str, code: str, user_name: Optional[str] = None) -> bool:
        """
        Send a one-time code via SMS.

        Args:
            phone: Destination phone number (E.164 preferred)
            code: The one-time code
            user_name: Recipient name (optional)

        Returns:
            bool: True if the message was dispatched
        """
        if not phone:
            logger.warning("SMS OTP skipped: no phone number on account")
            return False
        name = f" for {user_name}" if user_name else ""
        return send_message(
            phone,
            f"PropNoxa: your verification code{name} is {code}. "
            f"It expires in {settings.MFA_SMS_CODE_EXPIRE_MINUTES} minutes.",
        )


# Global SMS service instance
sms_service = SmsService()
