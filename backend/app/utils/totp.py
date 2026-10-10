"""
TOTP (RFC 6238) utility - dependency-free, for Google Authenticator compatibility.

Uses the same HMAC-SHA1 / 30-second / 6-digit scheme as RFC 6238 and
authenticator apps. No third-party library required.
"""
import base64
import hashlib
import hmac
import os
import secrets
import struct
import time


def generate_totp_secret(length: int = 20) -> str:
    """Generate a random shared secret, returned as base32 (no padding)."""
    raw = os.urandom(length)
    return base64.b32encode(raw).decode("utf-8").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    """Decode a base32 secret, tolerating missing padding and spaces."""
    cleaned = secret.replace(" ", "").upper()
    padding = "=" * ((8 - len(cleaned) % 8) % 8)
    return base64.b32decode(cleaned + padding)


def compute_totp(secret: str, at_time: float | None = None, digits: int = 6, period: int = 30) -> str:
    """Compute the TOTP code for a given time (defaults to now)."""
    timestamp = int((at_time if at_time is not None else time.time()) // period)
    counter = struct.pack(">Q", timestamp)
    digest = hmac.new(_decode_secret(secret), counter, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    code = truncated % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp(
    secret: str,
    token: str,
    window: int = 1,
    digits: int = 6,
    period: int = 30,
    at_time: float | None = None,
) -> bool:
    """
    Verify a TOTP token, allowing +/- `window` time steps for clock drift.
    Uses constant-time comparison.
    """
    if token is None:
        return False
    token = token.strip()
    if len(token) != digits or not token.isdigit():
        return False
    now = at_time if at_time is not None else time.time()
    for step in range(-window, window + 1):
        candidate = compute_totp(secret, at_time=now + step * period, digits=digits, period=period)
        if hmac.compare_digest(candidate, token):
            return True
    return False


def build_provisioning_uri(secret: str, account_name: str, issuer: str) -> str:
    """
    Build an otpauth:// URI for provisioning an authenticator app.
    The issuer appears both in the label and the query string, which is what
    Google Authenticator / Authy expect.
    """
    from urllib.parse import quote

    label = quote(f"{issuer}:{account_name}")
    query = (
        f"secret={quote(secret)}"
        f"&issuer={quote(issuer)}"
        f"&algorithm=SHA1"
        f"&digits=6"
        f"&period=30"
    )
    return f"otpauth://totp/{label}?{query}"


def generate_recovery_codes(count: int = 10) -> list[str]:
    """Generate human-friendly single-use recovery codes (groups of XXXXX-XXXXX)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Crockford-ish, no ambiguous chars

    def block() -> str:
        return "".join(secrets.choice(alphabet) for _ in range(5))

    return [f"{block()}-{block()}" for _ in range(count)]
