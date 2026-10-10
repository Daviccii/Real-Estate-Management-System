"""Security event logging (SIEM-ready structured events).

Emits one structured record per security-relevant occurrence on the
dedicated `security` logger so aggregators can filter on
`logger == "security"` and query the `security.*` fields directly.
Secrets (passwords, tokens, codes) are never included; `actor` carries
only the attempted identifier such as an email address.
"""
import logging
import re
from typing import Any, Dict, Optional

from fastapi import Request

security_logger = logging.getLogger("security")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def client_ip(request: Optional[Request]) -> Optional[str]:
    """Best-effort client IP: first X-Forwarded-For hop, else the peer address."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def request_id_of(request: Optional[Request]) -> Optional[str]:
    """The correlation ID assigned by the logging middleware, when present."""
    if request is None:
        return None
    value = getattr(request.state, "request_id", None)
    return value if value and _REQUEST_ID_RE.fullmatch(str(value)) else None


def emit_security_event(
    event: str,
    *,
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    actor: Optional[str] = None,
    outcome: str = "denied",
    severity: str = "warning",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit a structured security event to the `security` log stream."""
    payload: Dict[str, Any] = {"event": event, "outcome": outcome}
    ip = client_ip(request)
    if ip:
        payload["ip"] = ip
    if user_id is not None:
        payload["user_id"] = user_id
    if actor:
        payload["actor"] = actor
    if request is not None:
        payload["path"] = request.url.path
        correlation_id = request_id_of(request)
        if correlation_id:
            payload["request_id"] = correlation_id
    if details:
        payload["details"] = details
    level = getattr(logging, severity.upper(), logging.WARNING)
    security_logger.log(level, event, extra={"security": payload})
