"""Database backup CLI.

Examples:
    python scripts/backup_database.py --once                 # one verified dump
    python scripts/backup_database.py --daemon               # run on BACKUP_INTERVAL_HOURS
    python scripts/backup_database.py --list
    python scripts/backup_database.py --verify path/to/backup.sqlite.gz
    python scripts/backup_database.py --prune
    python scripts/backup_database.py --status
    python scripts/backup_database.py --pitr-plan 2026-10-09T12:00:00Z --recovery-dir /var/lib/postgresql/data
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings  # noqa: E402
from app.services import backup_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="PropNoxa database backups")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="run one backup cycle and exit")
    mode.add_argument("--daemon", action="store_true", help="keep running on BACKUP_INTERVAL_HOURS")
    mode.add_argument("--list", action="store_true", help="list stored backups")
    mode.add_argument("--verify", metavar="PATH", help="verify a stored artefact")
    mode.add_argument("--prune", action="store_true", help="apply the retention policy now")
    mode.add_argument("--status", action="store_true", help="show archive/retention status")
    mode.add_argument("--pitr-plan", metavar="UTC_TIME", help="print the point-in-time recovery plan")
    parser.add_argument("--recovery-dir", default="./pgdata-recovery", help="target PGDATA for --pitr-plan")
    args = parser.parse_args()

    if args.once:
        print(json.dumps(backup_service.run_backup_cycle(), indent=2, default=str))
        return 0

    if args.daemon:
        interval = max(1, settings.BACKUP_INTERVAL_HOURS) * 3600
        while True:
            try:
                result = backup_service.run_backup_cycle()
                print(json.dumps({"status": "ok", **result}, default=str))
            except Exception as exc:  # keep the scheduler alive; the failure is the alert
                print(json.dumps({"status": "error", "error": str(exc)}))
            time.sleep(interval)

    if args.list:
        for kind in (backup_service.LOGICAL, backup_service.PHYSICAL):
            entries = backup_service.list_backups(kind)
            print(f"{kind}: {len(entries)} artefact(s) in {settings.backup_root / kind}")
            for entry in entries:
                verified = "verified" if entry.get("verified") else "UNVERIFIED"
                print(f"  {entry['name']}  {entry.get('size_bytes', 0)} bytes  {verified}")
        return 0

    if args.verify:
        outcome = backup_service.verify_backup(Path(args.verify))
        print(json.dumps(outcome, indent=2))
        return 0 if outcome["ok"] else 1

    if args.prune:
        removed = backup_service.prune() + backup_service.prune(backup_service.PHYSICAL)
        print(json.dumps({"removed": removed}))
        return 0

    if args.status:
        print(json.dumps({
            "primary_dir": str(settings.backup_root),
            "secondary_dir": str(settings.backup_secondary_root) if settings.backup_secondary_root else None,
            "retention_days": settings.BACKUP_RETENTION_DAYS,
            "keep_minimum": settings.BACKUP_KEEP_MINIMUM,
            "interval_hours": settings.BACKUP_INTERVAL_HOURS,
            "wal_archive": backup_service.wal_archive_status(),
            "counts": {
                kind: len(backup_service.list_backups(kind))
                for kind in (backup_service.LOGICAL, backup_service.PHYSICAL)
            },
        }, indent=2))
        return 0

    if args.pitr_plan:
        plan = backup_service.pitr_recovery_plan(args.pitr_plan, args.recovery_dir)
        print(json.dumps(plan, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except backup_service.BackupError as error:
        print(json.dumps({"status": "error", "error": str(error)}))
        raise SystemExit(1)
