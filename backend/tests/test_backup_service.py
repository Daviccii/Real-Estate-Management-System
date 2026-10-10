"""Backup service: verified archives, checksums, retention and mirroring."""
import os
import time
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.models.base import Base
from app.services import backup_service


@pytest.fixture()
def file_db(tmp_path, monkeypatch):
    """A real on-disk SQLite database with the full schema, pointed at by settings."""
    db_file = tmp_path / "app.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    monkeypatch.setattr(backup_service.settings, "DATABASE_URL", url)
    monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setattr(backup_service.settings, "BACKUP_SECONDARY_DIR", None)
    return db_file


def test_create_logical_backup_writes_verified_checksummed_archive(file_db):
    artifact = backup_service.create_logical_backup()

    path = Path(artifact.path)
    assert path.exists()
    assert artifact.kind == backup_service.LOGICAL
    assert artifact.db_type == "sqlite"
    assert artifact.verified is True
    assert len(artifact.sha256) == 64
    assert path.with_suffix(path.suffix + ".sha256").exists()
    assert path.with_suffix(path.suffix + ".meta.json").exists()
    # gzip'd snapshot, not the raw file: a real dump is smaller than the live DB header set
    assert path.read_bytes()[:2] == b"\x1f\x8b"


def test_verify_backup_detects_tampering(file_db):
    artifact = backup_service.create_logical_backup()
    path = Path(artifact.path)
    # corrupt a byte past the gzip header so the checksum no longer matches
    data = bytearray(path.read_bytes())
    data[-5] ^= 0xFF
    path.write_bytes(bytes(data))

    outcome = backup_service.verify_backup(path)
    assert outcome["ok"] is False
    assert "checksum mismatch" in outcome["detail"]


def test_verify_backup_rejects_truncated_archive(file_db):
    artifact = backup_service.create_logical_backup()
    path = Path(artifact.path)
    path.with_suffix(path.suffix + ".sha256").unlink()  # no checksum to lean on
    path.write_bytes(path.read_bytes()[:6])

    outcome = backup_service.verify_backup(path)
    assert outcome["ok"] is False


def test_in_memory_database_is_not_backed_up(file_db, monkeypatch):
    monkeypatch.setattr(backup_service.settings, "DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(backup_service.BackupError):
        backup_service.create_logical_backup()


def test_mirror_to_secondary_copies_artefact(file_db, tmp_path, monkeypatch):
    secondary = tmp_path / "offsite"
    monkeypatch.setattr(backup_service.settings, "BACKUP_SECONDARY_DIR", str(secondary))

    artifact = backup_service.create_logical_backup()

    mirrored = secondary / Path(artifact.path).name
    assert mirrored.exists()
    assert mirrored.read_bytes() == Path(artifact.path).read_bytes()
    assert artifact.mirrored_to == str(mirrored)


def test_prune_removes_expired_but_keeps_floor(file_db):
    directory = backup_service.settings.backup_root / backup_service.LOGICAL
    directory.mkdir(parents=True, exist_ok=True)

    stale = []
    now = time.time()
    for index in range(4):
        path = directory / f"propnoxa-00000000T0000{index}Z-logical.sqlite.gz"
        path.write_bytes(b"placeholder")
        # all 40 days old, but with a clear newest-to-oldest ordering
        mtime = now - 40 * 86400 + index
        os.utime(path, (mtime, mtime))
        stale.append(path.name)

    removed = backup_service.prune(retention_days=30, keep_minimum=2)

    # retention says everything is expired, the floor says the two newest stay
    assert sorted(removed) == sorted(stale[:2])
    assert (directory / stale[2]).exists()
    assert (directory / stale[3]).exists()


def test_run_backup_cycle_reports_and_prunes(file_db):
    result = backup_service.run_backup_cycle(include_physical=False)

    assert result["logical"]["verified"] is True
    assert result["physical"] is None
    assert result["pruned"] == []
    assert len(backup_service.list_backups(backup_service.LOGICAL)) == 1


def test_verify_flags_garbage_archive(file_db):
    artifact = backup_service.create_logical_backup()
    path = Path(artifact.path)
    path.write_bytes(b"not an archive")

    outcome = backup_service.verify_backup(path)
    assert outcome["ok"] is False


def test_physical_backup_requires_postgres(file_db):
    with pytest.raises(backup_service.BackupError):
        backup_service.create_physical_backup()


def test_wal_archive_status_reports_configuration(file_db, tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service.settings, "BACKUP_WAL_ARCHIVE_DIR", None)
    assert backup_service.wal_archive_status()["enabled"] is False

    archive = tmp_path / "wal"
    archive.mkdir()
    (archive / "000000010000000000000001").write_bytes(b"x")
    monkeypatch.setattr(backup_service.settings, "BACKUP_WAL_ARCHIVE_DIR", str(archive))

    status = backup_service.wal_archive_status()
    assert status["enabled"] is True
    assert status["segment_count"] == 1
