"""
Kenyan phone-number normalization for M-Pesa (Safaricom Daraja).

Daraja STK Push expects the MSISDN in the 2547XXXXXXXX / 2541XXXXXXXX
international format. Tenants type every local variant, so every entry path
funnels through normalize_kenyan_phone:

    07XXXXXXXX   -> 2547XXXXXXXX
    01XXXXXXXX   -> 2541XXXXXXXX
    2547XXXXXXXX -> unchanged
    2541XXXXXXXX -> unchanged
    +254..., 00254..., and 7XXXXXXXX/1XXXXXXXX also accepted.

Anything else raises ValueError; callers turn that into a 422.
"""
import re

_NATIONAL_RE = re.compile(r"^[71]\d{8}$")


def normalize_kenyan_phone(value) -> str:
    """Return the Daraja-format MSISDN (254XXXXXXXXX) or raise ValueError."""
    if value is None:
        raise ValueError("Phone number is required")

    compact = re.sub(r"[\s\-().]+", "", str(value).strip())
    if compact.startswith("+"):
        compact = compact[1:]
    if compact.startswith("00"):
        compact = compact[2:]
    if not compact.isdigit():
        raise ValueError("Phone number must contain digits only")

    if compact.startswith("254") and len(compact) == 12:
        national = compact[3:]
    elif compact.startswith("0") and len(compact) == 10:
        national = compact[1:]
    elif len(compact) == 9:
        # Bare national number without the trunk 0 (common on forms).
        national = compact
    else:
        raise ValueError(
            "Enter a valid Kenyan phone number (07XXXXXXXX, 01XXXXXXXX or 2547XXXXXXXX)"
        )

    if not _NATIONAL_RE.match(national):
        raise ValueError(
            "Enter a valid Kenyan mobile number starting with 07 or 01"
        )
    return f"254{national}"


def mask_phone(value) -> str:
    """Mask an MSISDN for API responses: 254712345678 -> 2547****678."""
    text = str(value or "")
    if len(text) < 7:
        return "***"
    return f"{text[:4]}****{text[-3:]}"
