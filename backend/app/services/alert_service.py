"""
Alerting service

Fan-out for operational alerts (unhandled 5xx, critical security events)
to pluggable backends selected by ALERT_BACKENDS:

- console (default): log the alert - safe for dev/tests
- pagerduty: PagerDuty Events API v2; needs PAGERDUTY_ROUTING_KEY
- datadog: Datadog Events API; needs DATADOG_API_KEY (+ DATADOG_SITE)
- sentry: Sentry store API; needs SENTRY_DSN

Provider backends fail closed (log an error, skip) until their credentials
are configured from a secrets manager. emit_alert never raises and never
blocks request handling for longer than a short HTTP timeout: alerting is
best-effort, the request path must not depend on it.
"""
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

ALERT_TIMEOUT_SECONDS = 5.0

# Internal severities admitted by every backend; "high" is accepted as an
# alias and mapped to "error" for providers with a fixed severity scale.
_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2, "high": 2, "critical": 3}


def _normalize_severity(severity: str) -> str:
    value = (severity or "error").strip().lower()
    return "error" if value == "high" else value


def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
    """Single transport used by every provider backend. Never raises."""
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=ALERT_TIMEOUT_SECONDS)
        return 200 <= response.status_code < 300
    except Exception as exc:  # transport errors must never surface to callers
        logger.error("Alert delivery failed (%s): %s", url, exc)
        return False


def _send_pagerduty(title: str, severity: str, details: Optional[Dict[str, Any]], dedup_key: Optional[str]) -> bool:
    routing_key = settings.PAGERDUTY_ROUTING_KEY
    if not routing_key:
        logger.error("PagerDuty alerting selected but PAGERDUTY_ROUTING_KEY is not configured")
        return False
    payload: Dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": title[:1024],
            "source": settings.APP_NAME,
            "severity": _normalize_severity(severity),
            "custom_details": details or {},
        },
    }
    if dedup_key:
        payload["dedup_key"] = dedup_key[:255]
    return _post_json("https://events.pagerduty.com/v2/enqueue", {}, payload)


def _send_datadog(title: str, severity: str, details: Optional[Dict[str, Any]], dedup_key: Optional[str]) -> bool:
    api_key = settings.DATADOG_API_KEY
    if not api_key:
        logger.error("Datadog alerting selected but DATADOG_API_KEY is not configured")
        return False
    alert_type = "error" if _SEVERITY_ORDER.get(_normalize_severity(severity), 2) >= 2 else _normalize_severity(severity)
    payload: Dict[str, Any] = {
        "title": title[:100],
        "text": json.dumps(details or {}, default=str),
        "alert_type": alert_type,
        "source_type_name": "python",
    }
    if dedup_key:
        payload["aggregation_key"] = dedup_key[:100]
    url = f"https://api.{settings.DATADOG_SITE}/api/v1/events"
    return _post_json(url, {"DD-API-KEY": api_key}, payload)


def _send_sentry(title: str, severity: str, details: Optional[Dict[str, Any]], dedup_key: Optional[str]) -> bool:
    dsn = settings.SENTRY_DSN
    if not dsn:
        logger.error("Sentry alerting selected but SENTRY_DSN is not configured")
        return False
    parsed = urlparse(dsn)
    public_key = parsed.username
    project_id = (parsed.path or "").strip("/").split("/")[-1]
    if not public_key or not parsed.hostname or not project_id.isdigit():
        logger.error("SENTRY_DSN is malformed; expected https://<key>@<host>/<project_id>")
        return False
    level = {"critical": "fatal", "high": "error"}.get(_normalize_severity(severity), _normalize_severity(severity))
    payload: Dict[str, Any] = {
        "message": title[:1024],
        "level": level if level in ("fatal", "error", "warning", "info") else "error",
        "platform": "python",
        "tags": {"dedup_key": dedup_key} if dedup_key else {},
        "extra": details or {},
    }
    store_url = f"{parsed.scheme}://{parsed.hostname}/api/{project_id}/store/"
    auth = f"Sentry sentry_version=7, sentry_key={public_key}, sentry_client=propnoxa/1.0"
    return _post_json(store_url, {"X-Sentry-Auth": auth}, payload)


def emit_alert(
    title: str,
    *,
    severity: str = "error",
    details: Optional[Dict[str, Any]] = None,
    dedup_key: Optional[str] = None,
) -> bool:
    """
    Fan one alert out to every configured backend. Never raises.

    Returns True when at least one backend accepted the alert.
    """
    delivered = False
    for backend in settings.ALERT_BACKENDS:
        try:
            if backend == "console":
                logger.warning(
                    "[ALERT:console] severity=%s title=%s dedup=%s details=%s",
                    _normalize_severity(severity), title, dedup_key, details or {},
                )
                delivered = True
            elif backend == "pagerduty":
                delivered |= _send_pagerduty(title, severity, details, dedup_key)
            elif backend == "datadog":
                delivered |= _send_datadog(title, severity, details, dedup_key)
            elif backend == "sentry":
                delivered |= _send_sentry(title, severity, details, dedup_key)
            else:
                logger.error("Unknown ALERT_BACKENDS entry '%s' ignored", backend)
        except Exception:
            logger.exception("Alert backend '%s' crashed while emitting '%s'", backend, title)
    return delivered
