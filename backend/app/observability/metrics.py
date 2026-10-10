import os
import platform
import sys
import threading
import time
from collections import Counter

from fastapi import Request

_lock = threading.Lock()
_counters = Counter()
_request_durations_ms = Counter()
_process_started_at = time.time()


def increment(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] += value


def observe_request(request: Request, status_code: int, duration_ms: float) -> None:
    route = request.scope.get("route")
    route_name = getattr(route, "path", request.url.path)
    bucket = int(duration_ms // 100) * 100
    with _lock:
        _counters["requests_total"] += 1
        if status_code >= 500:
            _counters["errors_5xx_total"] += 1
        elif status_code >= 400:
            _counters["errors_4xx_total"] += 1
        _counters[f"requests_total|{request.method}|{route_name}|{status_code}"] += 1
        _request_durations_ms[f"request_duration_ms|{request.method}|{route_name}|{bucket}"] += 1


def snapshot() -> dict[str, dict]:
    memory_bytes = 0
    try:
        import psutil
        memory_bytes = psutil.Process().memory_info().rss
    except Exception:
        pass
    with _lock:
        total_requests = _counters["requests_total"]
        errors_5xx = _counters["errors_5xx_total"]
        return {
            "counters": dict(_counters),
            "request_duration_buckets": dict(_request_durations_ms),
            "process": {"rss_bytes": memory_bytes, "pid": os.getpid()},
            "summary": {
                "uptime_seconds": round(time.time() - _process_started_at, 1),
                "total_requests": total_requests,
                "errors_4xx": _counters["errors_4xx_total"],
                "errors_5xx": errors_5xx,
                "error_rate_percent": round(errors_5xx / total_requests * 100, 2) if total_requests else 0.0,
            },
            "system": {
                "app_version": _app_version(),
                "python_version": sys.version.split()[0],
                "platform": platform.system().lower(),
            },
        }


def _app_version() -> str:
    try:
        from app.config.settings import settings
        return settings.APP_VERSION
    except Exception:
        return "unknown"


async def timed_call(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        increment("requests_errors_total")
        raise
    finally:
        duration_ms = (time.perf_counter() - started) * 1000
        status_code = locals().get("response").status_code if "response" in locals() else 500
        observe_request(request, status_code, duration_ms)
    return response
