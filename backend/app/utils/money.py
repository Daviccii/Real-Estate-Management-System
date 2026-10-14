"""
Money parsing for the free-text amount strings stored across the app.

`Payment.amount` and `Lease.rent_amount` are String columns that hold values
like "1200", "1,200", "KSh 45,000" or "45000/Month". Any arithmetic on them
must go through parse_amount, which strips currency noise and commas and
returns a Decimal quantized to cents (None when unparseable) — SQL casts on
the raw strings silently mis-handle these formats.
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

_CURRENCY_NOISE = re.compile(
    r"(?i)(ksh|kes|shs|sh|/month|/mo|per\s+month|monthly)"
)
_NUMERIC_RE = re.compile(r"^\d+(?:\.\d+)?$")
_CENTS = Decimal("0.01")


def parse_amount(value) -> Optional[Decimal]:
    """Parse a human-entered amount into Decimal (2dp), or None if invalid."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value.quantize(_CENTS)
    if isinstance(value, bool):  # bool is an int subclass; never an amount
        return None
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value)).quantize(_CENTS)
        except InvalidOperation:
            return None

    text = _CURRENCY_NOISE.sub("", str(value))
    text = text.replace(",", "").replace("\u00a0", " ").strip()
    if not _NUMERIC_RE.match(text):
        return None
    try:
        return Decimal(text).quantize(_CENTS)
    except InvalidOperation:
        return None


def format_amount(value) -> str:
    """Two-decimal string for API responses ("" when unparseable)."""
    parsed = parse_amount(value)
    return f"{parsed:.2f}" if parsed is not None else ""
