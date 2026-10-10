"""
Verify the tamper-evident audit chain and print the JSON report.

Safe to run any time (read-only); exits non-zero when verification fails so
cron / monitoring surfaces tampering. Pair with scripts/run_retention.py: run
verification right after pruning to confirm the recorded anchors keep the
chain intact.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.logging_config import setup_logging, get_logger
from app.config.settings import settings
from app.database.database import SessionLocal
from app.services.audit_chain import verify_audit_chain

setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT, app_name=settings.APP_NAME)
logger = get_logger("scripts.verify_audit_chain")


def main() -> int:
    db = SessionLocal()
    try:
        report = verify_audit_chain(db)
        print(json.dumps(report, indent=2))
        if report["verified"]:
            logger.info("Audit chain verified: %s entries", report["entries_checked"])
            return 0
        logger.error("Audit chain verification FAILED: %s", report["first_broken"])
        return 1
    except Exception:
        logger.error("Audit chain verification crashed", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
