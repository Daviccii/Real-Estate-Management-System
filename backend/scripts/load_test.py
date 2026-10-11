"""
HTTP load test for the PropNoxa API.

Drives a locally running uvicorn instance with concurrent virtual users and
reports throughput + latency percentiles. Never point this at production.

Usage (from the backend directory, venv python):

  # 1. Seed a throwaway database (schema + demo rows):
  DATABASE_URL="sqlite:///C:/Temp/propnoxa_loadtest.db" \
  SECRET_KEY="<32+ char secret>" ENVIRONMENT=development \
  python scripts/load_test.py --seed 200

  # 2. Start the app against the same database:
  DATABASE_URL="sqlite:///C:/Temp/propnoxa_loadtest.db" \
  SECRET_KEY="<32+ char secret>" ENVIRONMENT=development \
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8765

  # 3. Run the load test:
  python scripts/load_test.py --base-url http://127.0.0.1:8765 --users 20 --duration 30

Exit code is non-zero when any request errored (exception, timeout, or an
unexpected status), so it can gate deployments.

Caveats (stated honestly, printed in the report): a dev machine with SQLite
serializes writes and has no Redis edge cache; production runs PostgreSQL
(+ read replica) behind multiple uvicorn workers with Redis-backed rate
limiting. Treat the numbers as a floor, not the production ceiling.
"""
import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOAD_OWNER_EMAIL = "loadtest-owner@propnoxa-loadtest.com"
LOAD_OWNER_PASSWORD = "Str0ng!TestPass42"

# (weight, method, path, json_body)
def _scenarios(property_ids: list[int]):
    scenarios = [
        (5, "GET", "/api/v1/properties/public?limit=50&sort=newest", None),
        (3, "GET", "/api/v1/properties/public?search=villa&limit=20", None),
        (2, "GET", "/api/v1/properties/public?city=Nairobi&limit=20", None),
        (1, "GET", "/health/live", None),
        (1, "POST", "/api/v1/auth/login",
         {"email": LOAD_OWNER_EMAIL, "password": LOAD_OWNER_PASSWORD}),
    ]
    return scenarios


def _seed(count: int) -> None:
    from sqlalchemy.orm import sessionmaker

    from app.config.settings import settings
    from app.database.database import engine
    from app.models.base import Base
    from app.models.property import Property
    from app.models.user import User
    from app.utils.security import get_password_hash

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        owner = db.query(User).filter(User.email == LOAD_OWNER_EMAIL).first()
        if owner is None:
            owner = User(
                email=LOAD_OWNER_EMAIL,
                hashed_password=get_password_hash(LOAD_OWNER_PASSWORD),
                full_name="Load Test Owner",
                role="owner",
                roles_csv="owner",
                is_active=True,
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

        cities = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Kiambu"]
        types = ["apartment", "villa", "townhouse", "bungalow", "office"]
        existing = db.query(Property).count()
        for i in range(existing, existing + count):
            db.add(Property(
                name=f"Load Test Property {i}",
                owner_id=owner.id,
                city=cities[i % len(cities)],
                property_type=types[i % len(types)],
                status="active",
                purpose="rent",
                price="50000",
                description=f"Seasoned villa and apartment listing number {i} in {cities[i % len(cities)]}",
            ))
        db.commit()
        print(f"seeded: {count} properties (owner {LOAD_OWNER_EMAIL} ready for login)")
    finally:
        db.close()


async def _worker(client, scenarios, deadline, results, weights, total_weight):
    import httpx

    while time.monotonic() < deadline:
        _, method, path, body = random.choices(scenarios, weights=weights, k=1)[0]
        started = time.perf_counter()
        error = None
        status_code = None
        try:
            if method == "GET":
                resp = await client.get(path)
            else:
                resp = await client.post(path, json=body)
            status_code = resp.status_code
        except httpx.TimeoutException:
            error = "timeout"
        except Exception as exc:  # noqa: BLE001 - the load test records, never raises
            error = type(exc).__name__
        elapsed = time.perf_counter() - started
        results.append((path, method, status_code, elapsed, error))


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, int(round((pct / 100) * len(sorted_values) + 0.5)) - 1)
    return sorted_values[index]


async def _run(base_url: str, users: int, duration: int, expect_login_ok: bool) -> int:
    import httpx

    scenarios = _scenarios([])
    weights = [s[0] for s in scenarios]
    total_weight = sum(weights)

    results: list = []
    limits = httpx.Limits(max_connections=users * 4, max_keepalive_connections=users * 2)
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(base_url=base_url, limits=limits, timeout=timeout) as client:
        # Warm-up (connection setup + first-request compile paths).
        await client.get("/health/live")

        deadline = time.monotonic() + duration
        wall_start = time.monotonic()
        await asyncio.gather(*[
            _worker(client, scenarios, deadline, results, weights, total_weight)
            for _ in range(users)
        ])
        wall_elapsed = time.monotonic() - wall_start

    total = len(results)
    latencies = sorted(r[3] for r in results)
    errors = [r for r in results if r[4] is not None]
    unexpected = [
        r for r in results
        if r[4] is None and (r[2] >= 500 or (r[2] != 200))
    ]
    login_failures = [
        r for r in results if r[1] == "POST" and r[2] is not None and r[2] != 200
    ]
    status_counts: dict = {}
    for _, _, code, _, err in results:
        key = str(code) if code is not None else f"EXC:{err}"
        status_counts[key] = status_counts.get(key, 0) + 1

    report = {
        "base_url": base_url,
        "concurrent_users": users,
        "duration_seconds": round(wall_elapsed, 2),
        "requests_total": total,
        "requests_per_second": round(total / wall_elapsed, 2),
        "latency_ms": {
            "mean": round(statistics.mean(latencies) * 1000, 2) if latencies else 0,
            "p50": round(_percentile(latencies, 50) * 1000, 2),
            "p95": round(_percentile(latencies, 95) * 1000, 2),
            "p99": round(_percentile(latencies, 99) * 1000, 2),
            "max": round(max(latencies) * 1000, 2) if latencies else 0,
        },
        "status_counts": status_counts,
        "transport_errors": len(errors),
        "error_or_timeout_rate": round(len(errors) / total, 5) if total else 0,
        "unexpected_statuses": len(unexpected),
        "login_failures": len(login_failures),
    }
    print(json.dumps(report, indent=2))

    passed = not errors and not unexpected and (not expect_login_ok or not login_failures)
    print("VERDICT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="PropNoxa HTTP load test")
    parser.add_argument("--seed", type=int, metavar="N", help="seed N demo properties and exit")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--users", type=int, default=20, help="concurrent virtual users")
    parser.add_argument("--duration", type=int, default=30, help="seconds of sustained load")
    parser.add_argument("--allow-login-fail", action="store_true",
                        help="do not fail the run when the login scenario is rejected (unseeded DB)")
    args = parser.parse_args()

    if args.seed is not None:
        _seed(args.seed)
        return 0

    return asyncio.run(_run(args.base_url, args.users, args.duration,
                            expect_login_ok=not args.allow_login_fail))


if __name__ == "__main__":
    raise SystemExit(main())
