"""
Run the data retention jobs and print the report.

One-shot (safe to schedule via cron / Task Scheduler):

    python scripts/run_retention.py --once

Long-running daemon (used by the docker-compose `retention` service):

    python scripts/run_retention.py --daemon    # every RETENTION_INTERVAL_HOURS

Legal hold (if enabled) suspends the destructive jobs automatically. The
daemon keeps running after a failure - the emitted error log is the alert.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.logging_config import setup_logging, get_logger  # noqa: E402
from app.config.settings import settings  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.services.retention_service import run_retention  # noqa: E402

setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT, app_name=settings.APP_NAME)
logger = get_logger("scripts.run_retention")


def run_once() -> bool:
    db = SessionLocal()
    try:
        report = run_retention(db)
        logger.info("Retention complete: %s", report)
        print(json.dumps(report, default=str))
        return True
    except Exception:
        logger.error("Retention run failed", exc_info=True)
        return False
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="PropNoxa data retention jobs")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="run one retention cycle and exit")
    mode.add_argument("--daemon", action="store_true", help="keep running on RETENTION_INTERVAL_HOURS")
    args = parser.parse_args()

    if args.once:
        return 0 if run_once() else 1

    interval = max(1, settings.RETENTION_INTERVAL_HOURS) * 3600
    while True:
        run_once()
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
