"""
Run the data retention jobs and print the report.

Safe to schedule via cron / Task Scheduler (daily). Legal hold (if enabled)
suspends the destructive jobs automatically. Exits non-zero on failure so
schedulers surface the error.
"""
import sys

from app.config.logging_config import setup_logging, get_logger
from app.config.settings import settings
from app.database.database import SessionLocal
from app.services.retention_service import run_retention

setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT, app_name=settings.APP_NAME)
logger = get_logger("scripts.run_retention")


def main() -> int:
    db = SessionLocal()
    try:
        report = run_retention(db)
        logger.info("Retention complete: %s", report)
        return 0
    except Exception:
        logger.error("Retention run failed", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
