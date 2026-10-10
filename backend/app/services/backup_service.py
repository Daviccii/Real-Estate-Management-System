"""Database backup, verification, retention and point-in-time recovery support.

Two artefact kinds are produced, because they answer different questions:

* ``logical``  - ``pg_dump`` / SQLite snapshot. Small, portable, restorable into a
  fresh cluster. This is the daily "did we keep the data" copy.
* ``physical`` - ``pg_basebackup`` of the running cluster. Required as the starting
  point for write-ahead-log replay, i.e. point-in-time recovery (PITR).
  A logical dump cannot be replayed forward, so enabling PITR without physical
  base backups gives a false sense of safety.
"""

import gzip
import os
import hashlib
import json
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from app.config.settings import settings
from app.observability.metrics import increment
from app.utils.time import utc_now


class BackupError(RuntimeError):
    pass


LOGICAL = "logical"
PHYSICAL = "physical"


@dataclass
class BackupArtifact:
    name: str
    path: str
    kind: str
    db_type: str
    size_bytes: int
    sha256: str
    created_at: str
    verified: bool = False
    verification_detail: str = ""
    mirrored_to: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def db_type(url: Optional[str] = None) -> str:
    target = url or settings.DATABASE_URL
    if target.startswith(("postgresql://", "postgres://")):
        return "postgresql"
    if target.startswith("sqlite:///"):
        return "sqlite"
    raise BackupError(f"Unsupported DATABASE_URL scheme for backups: {target[:30]}")


def sqlite_db_path() -> Path:
    raw = settings.DATABASE_URL.removeprefix("sqlite:///")
    raw = unquote(raw)
    if not raw or raw == ":memory:":
        raise BackupError("In-memory SQLite databases cannot be backed up")
    return Path(raw)


def postgres_info() -> dict:
    parsed = urlparse(settings.DATABASE_URL)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": (parsed.path or "/").lstrip("/"),
    }


def find_binary(configured: Optional[str], name: str) -> str:
    path = configured or shutil.which(name)
    if not path:
        raise BackupError(
            f"{name} was not found. Install the PostgreSQL client tools that match the "
            f"server version, or point BACKUP_*_PATH at the binary."
        )
    return path


def run_command(cmd: list[str], env: Optional[dict] = None) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, env=env, capture_output=True)
    if result.returncode != 0:
        raise BackupError(
            f"Command failed ({' '.join(part for part in cmd if not part.startswith('-F'))}): "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result


def stamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def _mtime_path(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _scratch_path(suffix: str) -> Path:
    # mkstemp hands back a live descriptor; leaving it open keeps the file locked on Windows.
    handle, name = tempfile.mkstemp(suffix=suffix)
    os.close(handle)
    return Path(name)


def _artifact_dir(kind: str, dest_dir: Optional[Path]) -> Path:
    base = Path(dest_dir) if dest_dir else (settings.backup_root / kind)
    base.mkdir(parents=True, exist_ok=True)
    return base


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_sidecars(artifact: BackupArtifact) -> None:
    path = Path(artifact.path)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{artifact.sha256}  {path.name}\n")


def _write_meta(artifact: BackupArtifact) -> None:
    Path(artifact.path).with_suffix(Path(artifact.path).suffix + ".meta.json").write_text(
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )


def _make_artifact(path: Path, kind: str, engine: str, extra: Optional[dict] = None) -> BackupArtifact:
    return BackupArtifact(
        name=path.name,
        path=str(path),
        kind=kind,
        db_type=engine,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
        created_at=utc_now().isoformat(),
        extra=extra or {},
    )


def create_logical_backup(dest_dir: Optional[Path] = None) -> BackupArtifact:
    """Snapshot the database into a compressed, checksummed archive."""
    engine = db_type()
    directory = _artifact_dir(LOGICAL, dest_dir)

    if engine == "sqlite":
        target = directory / f"propnoxa-{stamp()}-logical.sqlite.gz"
        _dump_sqlite(target)
    else:
        target = directory / f"propnoxa-{stamp()}-logical.dump.gz"
        _dump_postgres(target)

    artifact = _make_artifact(target, LOGICAL, engine)
    _write_sidecars(artifact)

    if settings.BACKUP_VERIFY_AFTER_CREATE:
        outcome = verify_backup(target)
        artifact.verified = outcome["ok"]
        artifact.verification_detail = outcome["detail"]

    mirror_path = mirror_to_secondary(artifact)
    artifact.mirrored_to = mirror_path
    _write_meta(artifact)

    if not artifact.verified and settings.BACKUP_VERIFY_AFTER_CREATE:
        increment("backup_failed_total")
        raise BackupError(f"Backup verification failed: {artifact.verification_detail}")

    increment("backup_created_total")
    return artifact


def _dump_sqlite(target: Path) -> None:
    source_path = sqlite_db_path()
    if not source_path.exists():
        raise BackupError(f"SQLite database file not found: {source_path}")

    # The backup API is used instead of copying the file so a consistent snapshot is
    # taken even while the API process is writing.
    source = sqlite3.connect(str(source_path))
    scratch = _scratch_path(".sqlite")
    try:
        destination = sqlite3.connect(str(scratch))
        with destination:
            source.backup(destination)
        destination.close()
        with scratch.open("rb") as raw, gzip.open(target, "wb") as compressed:
            shutil.copyfileobj(raw, compressed)
    finally:
        source.close()
        scratch.unlink(missing_ok=True)


def _dump_postgres(target: Path) -> None:
    info = postgres_info()
    pg_dump = find_binary(settings.BACKUP_PG_DUMP_PATH, "pg_dump")
    env = {"PGPASSWORD": info["password"], "PGSSLMODE": "prefer"}
    scratch = _scratch_path(".dump")
    try:
        run_command(
            [pg_dump, "--format=custom", "--compress=0", "--no-owner", "--no-privileges",
             f"--host={info['host']}", f"--port={info['port']}", f"--username={info['user']}",
             f"--dbname={info['dbname']}", f"--file={scratch}"],
            env=env,
        )
        with scratch.open("rb") as raw, gzip.open(target, "wb") as compressed:
            shutil.copyfileobj(raw, compressed)
    finally:
        scratch.unlink(missing_ok=True)


def create_physical_backup(dest_dir: Optional[Path] = None) -> BackupArtifact:
    """Take a physical base backup, the anchor point WAL replay restores from."""
    if db_type() != "postgresql":
        raise BackupError("Physical base backups require PostgreSQL")

    info = postgres_info()
    directory = _artifact_dir(PHYSICAL, dest_dir)
    target = directory / f"propnoxa-{stamp()}-physical.tar.gz"
    pg_basebackup = find_binary(settings.BACKUP_PG_BASEBACKUP_PATH, "pg_basebackup")
    env = {"PGPASSWORD": info["password"], "PGSSLMODE": "prefer"}

    result = subprocess.run(
        [pg_basebackup, f"--host={info['host']}", f"--port={info['port']}",
         f"--username={info['user']}", f"--dbname={info['dbname']}",
         "--format=tar", "--gzip=no", "-D", "-"],
        env=env,
        capture_output=True,
    )
    if result.returncode != 0:
        raise BackupError(f"pg_basebackup failed: {result.stderr.decode(errors='replace').strip()}")

    with gzip.open(target, "wb") as compressed:
        compressed.write(result.stdout)

    artifact = _make_artifact(target, PHYSICAL, "postgresql")
    _write_sidecars(artifact)
    outcome = verify_backup(target)
    artifact.verified = outcome["ok"]
    artifact.verification_detail = outcome["detail"]
    artifact.mirrored_to = mirror_to_secondary(artifact)
    _write_meta(artifact)
    if not outcome["ok"]:
        increment("backup_failed_total")
        raise BackupError(f"Physical backup verification failed: {outcome['detail']}")
    increment("backup_physical_created_total")
    return artifact


def readable_archive(path: Path) -> Path:
    """Return an uncompressed path for archives stored as ``*.gz``."""
    if path.name.endswith(".gz"):
        scratch = _scratch_path(path.suffix[:-3] or ".dump")
        with gzip.open(path, "rb") as compressed, scratch.open("wb") as raw:
            shutil.copyfileobj(compressed, raw)
        return scratch
    return path


def verify_backup(path: Path) -> dict:
    """Prove the artefact is intact, not just present.

    An unverified backup directory is a liability: files can be truncated, or the
    disk copy can succeed while the archive itself is unreadable.
    """
    path = Path(path)
    if not path.exists():
        return {"ok": False, "detail": f"missing file: {path.name}"}

    checksum_file = path.with_suffix(path.suffix + ".sha256")
    if checksum_file.exists():
        expected = checksum_file.read_text().split()[0]
        actual = sha256_file(path)
        if expected != actual:
            return {"ok": False, "detail": f"checksum mismatch ({path.name})"}

    kind = "physical" if "-physical." in path.name else "logical"
    try:
        extracted = readable_archive(path)
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        return {"ok": False, "detail": f"archive is not readable ({exc})"}
    try:
        if kind == "physical":
            return _verify_physical(extracted)
        if path.name.endswith(".sqlite.gz"):
            return _verify_sqlite(extracted)
        return _verify_pg_logical(extracted)
    finally:
        if extracted != path:
            extracted.unlink(missing_ok=True)


def _verify_sqlite(extracted: Path) -> dict:
    conn = sqlite3.connect(str(extracted))
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            return {"ok": False, "detail": f"integrity_check returned {integrity}"}
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not tables:
            return {"ok": False, "detail": "backup contains no tables"}
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] if "alembic_version" in tables else "unmanaged"
        users = conn.execute("SELECT count(*) FROM users").fetchone()[0] if "users" in tables else 0
        return {
            "ok": True,
            "detail": f"integrity ok, schema {version}, {users} user rows",
        }
    except sqlite3.Error as exc:
        return {"ok": False, "detail": f"unreadable sqlite backup: {exc}"}
    finally:
        conn.close()


def _verify_pg_logical(extracted: Path) -> dict:
    pg_restore = find_binary(settings.BACKUP_PG_RESTORE_PATH, "pg_restore")
    result = subprocess.run([pg_restore, "--list", str(extracted)], capture_output=True)
    if result.returncode != 0:
        return {"ok": False, "detail": f"pg_restore could not read the archive: {result.stderr.decode(errors='replace').strip()}"}
    listing = result.stdout.decode(errors="replace")
    data_entries = sum(1 for line in listing.splitlines() if "TABLE DATA" in line)
    if data_entries == 0:
        return {"ok": False, "detail": "archive contains no table data"}
    return {"ok": True, "detail": f"archive readable, {data_entries} table-data entries"}


def _verify_physical(extracted: Path) -> dict:
    try:
        with tarfile.open(extracted, "r:") as archive:
            names = {member.name.rstrip("/") for member in archive.getmembers()}
    except tarfile.TarError as exc:
        return {"ok": False, "detail": f"unreadable base backup tar: {exc}"}
    if "PG_VERSION" not in names and "backup_label" not in names:
        return {"ok": False, "detail": "base backup is missing PG_VERSION/backup_label"}
    return {"ok": True, "detail": f"base backup readable, {len(names)} entries"}


def mirror_to_secondary(artifact: BackupArtifact) -> Optional[str]:
    """Copy the artefact to a second location (mounted bucket / replicated volume)."""
    secondary = settings.backup_secondary_root
    if not secondary:
        return None
    secondary.mkdir(parents=True, exist_ok=True)
    destination = secondary / Path(artifact.path).name
    shutil.copy2(artifact.path, destination)
    checksum_file = Path(artifact.path).with_suffix(Path(artifact.path).suffix + ".sha256")
    if checksum_file.exists():
        shutil.copy2(checksum_file, destination.with_suffix(destination.suffix + ".sha256"))
    increment("backup_mirrored_total")
    return str(destination)


def list_backups(kind: str = LOGICAL) -> list[dict]:
    directory = settings.backup_root / kind
    if not directory.exists():
        return []
    artefacts = []
    for path in sorted(directory.glob("*"), key=lambda item: item.name):
        if path.name.endswith((".sha256", ".meta.json")):
            continue
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.exists():
            artefacts.append(json.loads(meta_path.read_text(encoding="utf-8")))
        else:
            artefacts.append({
                "name": path.name,
                "path": str(path),
                "kind": kind,
                "size_bytes": path.stat().st_size,
                "created_at": None,
                "verified": False,
            })
    return artefacts


def prune(kind: str = LOGICAL, retention_days: Optional[int] = None, keep_minimum: Optional[int] = None) -> list[str]:
    """Delete expired artefacts, never dropping below a safety floor."""
    directory = settings.backup_root / kind
    if not directory.exists():
        return []

    days = retention_days if retention_days is not None else settings.BACKUP_RETENTION_DAYS
    floor = keep_minimum if keep_minimum is not None else settings.BACKUP_KEEP_MINIMUM
    cutoff = utc_now() - timedelta(days=days)

    artefacts = sorted(
        (path for path in directory.glob("*") if not path.name.endswith((".sha256", ".meta.json"))),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    removed = []
    for index, path in enumerate(artefacts):
        expired = _mtime_path(path) < cutoff
        if expired and index + 1 > floor:
            _delete_with_sidecars(path)
            removed.append(path.name)

    if kind == PHYSICAL:
        for path in artefacts[settings.BACKUP_PHYSICAL_KEEP_COUNT:]:
            if path.name not in removed:
                _delete_with_sidecars(path)
                removed.append(path.name)

    if removed:
        increment("backup_pruned_total", len(removed))
    return removed


def _delete_with_sidecars(path: Path) -> None:
    for sibling in (
        path,
        path.with_suffix(path.suffix + ".sha256"),
        path.with_suffix(path.suffix + ".meta.json"),
    ):
        sibling.unlink(missing_ok=True)


def run_backup_cycle(include_physical: Optional[bool] = None) -> dict:
    physical_enabled = settings.BACKUP_PHYSICAL_ENABLED if include_physical is None else include_physical
    result = {"logical": None, "physical": None, "pruned": [], "pruned_physical": []}

    artifact = create_logical_backup()
    result["logical"] = artifact.to_dict()
    if physical_enabled and db_type() == "postgresql":
        result["physical"] = create_physical_backup().to_dict()
        result["pruned_physical"] = prune(PHYSICAL)
    result["pruned"] = prune(LOGICAL)
    return result


def wal_archive_status() -> dict:
    """Report how much WAL history is retained, since PITR cannot go back further."""
    archive = settings.backup_wal_archive_root
    if not archive or not archive.exists():
        return {"enabled": False, "detail": "no WAL archive directory configured"}
    segments = [path for path in archive.glob("*") if path.is_file() and not path.name.endswith("history")]
    oldest_path = min(segments, key=lambda item: item.stat().st_mtime, default=None)
    return {
        "enabled": True,
        "directory": str(archive),
        "segment_count": len(segments),
        "oldest_segment": _mtime_path(oldest_path).isoformat() if oldest_path else None,
    }


def pitr_recovery_plan(target_time: str, recovery_dir: str) -> dict:
    """Build the configuration needed to replay WAL up to a point in time.

    PITR is a physical-backup operation: the base backup is extracted into PGDATA,
    then ``restore_command`` feeds archived WAL segments until the target time.
    """
    if db_type() != "postgresql":
        raise BackupError("Point-in-time recovery requires PostgreSQL with WAL archiving")

    archive = settings.backup_wal_archive_root
    if not archive:
        raise BackupError("BACKUP_WAL_ARCHIVE_DIR must be set to replay archived WAL")

    bases = sorted((settings.backup_root / PHYSICAL).glob("*")) if (settings.backup_root / PHYSICAL).exists() else []
    if not bases:
        raise BackupError("No physical base backup available - restore_command has nothing to start from")

    return {
        "base_backup": str(bases[-1]),
        "recovery_target_directory": str(Path(recovery_dir).resolve()),
        "postgresql_conf": {
            "restore_command": f"cp {archive}/%f %p",
            "recovery_target_time": target_time,
            "recovery_target_action": "promote",
            "archive_mode": "on",
        },
        "signal_file": "recovery.signal",
        "steps": [
            f"tar -xzf {bases[-1]} -C {recovery_dir}",
            f"touch {recovery_dir}/recovery.signal",
            f"append the postgresql_conf entries to {recovery_dir}/postgresql.conf",
            "start PostgreSQL and watch the log until 'consistent recovery state reached'",
        ],
    }
