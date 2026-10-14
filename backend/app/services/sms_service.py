"""
SMS Service

Pluggable SMS backend for MFA backup codes and high-priority alerts.
Three transports selected by SMS_BACKEND:
- console (default): log the message instead of delivering it - safe for dev/tests
- twilio: reserved production transport; fails closed until provider credentials
  are configured (from a secrets manager, never .env in production)
- africastalking: Africa's Talking SMS provider for Kenya/region
"""
import logging
from typing import Optional
import httpx
import xml.etree.ElementTree as ET

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

    if settings.SMS_BACKEND == "africastalking":
        return _send_africastalking(phone, message)

    logger.error("Unknown SMS_BACKEND '%s'; message not delivered", settings.SMS_BACKEND)
    return False


def _send_africastalking(phone: str, message: str) -> bool:
    """
    Send SMS via Africa's Talking API.

    Africa's Talking API: https://developers.africastalking.com/sms/send

    Returns:
        bool: True if the message was dispatched successfully
    """
    if not settings.AT_USERNAME or not settings.AT_API_KEY:
        logger.error(
            "SMS backend 'africastalking' is not configured; set AT_USERNAME "
            "and AT_API_KEY in .env to enable it"
        )
        return False

    # Normalize phone number to international format (e.g., +2547XXXXXXXX)
    if not phone.startswith("+"):
        # Assume Kenya if no country code
        if phone.startswith("0"):
            phone = "+254" + phone[1:]
        elif phone.startswith("7"):
            phone = "+254" + phone
        elif phone.startswith("1"):
            phone = "+1" + phone  # US fallback
        else:
            phone = "+" + phone

    # Africa's Talking sandbox vs production endpoint
    base_url = "https://api.sandbox.africastalking.com" if settings.AT_ENVIRONMENT == "sandbox" else "https://api.africastalking.com"
    url = f"{base_url}/version1/messaging"

    payload = {
        "username": settings.AT_USERNAME,
        "to": phone,
        "message": message[:_SMS_MAX_LENGTH],
    }

    if settings.AT_SENDER_ID:
        payload["from"] = settings.AT_SENDER_ID

    try:
        # Africa's Talking: API key in apiKey header
        headers = {
            "apiKey": settings.AT_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = httpx.post(
            url,
            data=payload,
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()

        # Africa's Talking returns XML, not JSON
        # Parse the XML response
        root = ET.fromstring(response.text)
        recipient = root.find(".//Recipient")
        if recipient is not None:
            status = recipient.find("status")
            if status is not None and status.text in ("Success", "Sent", "Queued"):
                logger.info("[SMS:africastalking] to=%s status=%s", phone, status.text)
                return True
            else:
                status_text = status.text if status is not None else "Unknown"
                logger.warning("[SMS:africastalking] to=%s status=%s", phone, status_text)
                return False
        else:
            logger.warning("[SMS:africastalking] to=%s no recipient in response", phone)
            return False

    except httpx.HTTPStatusError as e:
        logger.error("[SMS:africastalking] HTTP error to=%s: %s", phone, e.response.text)
        logger.error("[SMS:africastalking] Status code: %s", e.response.status_code)
        logger.error("[SMS:africastalking] Response headers: %s", dict(e.response.headers))
        return False
    except httpx.RequestError as e:
        logger.error("[SMS:africastalking] request error to=%s: %s", phone, str(e))
        return False
    except Exception as e:
        logger.error("[SMS:africastalking] unexpected error to=%s: %s", phone, str(e))
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
