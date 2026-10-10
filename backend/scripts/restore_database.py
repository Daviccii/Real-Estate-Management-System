"""Restore the database from a verified backup artefact.

Restoring overwrites live data, so the default is a dry run and an explicit
``--confirm`` is required. The file currently in place is always kept alongside
as ``<name>.pre-restore-<stamp>`` so the operation can be undone.

Examples:
    python scripts/restore_database.py --from backups/database/logical/propnoxa-....sqlite.gz
    python scripts/restore_database.py --from ... --confirm
"""

import argparse
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings  # noqa: E402
from app.services import backup_service  # noqa: E402


def restore_sqlite(archive: Path, confirm: bool) -> int:
    target = backup_service.sqlite_db_path()
    outcome = backup_service.verify_backup(archive)
    if not outcome["ok"]:
        print(f"refusing to restore unverified backup: {outcome['detail']}")
        return 1

    print(f"backup:   {archive.name} ({outcome['detail']})")
    print(f"target:   {target}")
    if not confirm:
        print("dry run - pass --confirm to write the database file")
        return 0

    if target.exists():
        safety = target.with_name(f"{target.name}.pre-restore-{backup_service.stamp()}")
        shutil.copy2(target, safety)
        print(f"previous database kept at {safety}")

    scratch = target.with_name(target.name + ".restoring")
    try:
        if archive.name.endswith(".gz"):
            with gzip.open(archive, "rb") as compressed, scratch.open("wb") as raw:
                shutil.copyfileobj(compressed, raw)
        else:
            shutil.copy2(archive, scratch)
        scratch.replace(target)
    finally:
        scratch.unlink(missing_ok=True)
    print("restore complete")
    return 0


def restore_postgres(archive: Path, confirm: bool) -> int:
    outcome = backup_service.verify_backup(archive)
    if not outcome["ok"]:
        print(f"refusing to restore unverified backup: {outcome['detail']}")
        return 1

    info = backup_service.postgres_info()
    pg_restore = backup_service.find_binary(settings.BACKUP_PG_RESTORE_PATH, "pg_restore")
    extracted = backup_service.readable_archive(archive)
    command = [
        pg_restore, "--clean", "--if-exists", "--no-owner", "--no-privileges",
        f"--host={info['host']}", f"--port={info['port']}", f"--username={info['user']}",
        f"--dbname={info['dbname']}", str(extracted),
    ]
    print(f"target: postgres://{info['host']}:{info['port']}/{info['dbname']} ({outcome['detail']})")
    if not confirm:
        print("dry run - pass --confirm to run pg_restore against the live database")
        return 0

    env = {"PGPASSWORD": info["password"], "PGSSLMODE": "prefer"}
    try:
        subprocess.run(command, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"pg_restore failed: {exc}")
        return 1
    finally:
        if extracted != archive:
            extracted.unlink(missing_ok=True)
    print("restore complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a PropNoxa database backup")
    parser.add_argument("--from", dest="archive", required=True, help="path to a backup artefact")
    parser.add_argument("--confirm", action="store_true", help="actually overwrite the database")
    args = parser.parse_args()

    archive = Path(args.archive)
    if not archive.exists():
        print(f"no such file: {archive}")
        return 1

    if "-physical." in archive.name:
        print("physical base backups are restored with the PITR plan, not pg_restore:")
        print("  python scripts/backup_database.py --pitr-plan <UTC timestamp> --recovery-dir <PGDATA>")
        return 1

    if archive.name.endswith(".sqlite.gz") or archive.name.endswith(".sqlite"):
        return restore_sqlite(archive, args.confirm)
    return restore_postgres(archive, args.confirm)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except backup_service.BackupError as error:
        print(f"restore aborted: {error}")
        raise SystemExit(1)
