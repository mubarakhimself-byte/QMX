from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import cast

import duckdb
import pytest

from qmx_apps.backup import BackupSettings, backup, checksum, restore
from qmx_apps.backup_schedule import BackupSchedule
from qmx_apps.cache import ReadCache
from qmx_apps.errors import AppError
from qmx_apps.store import analytics, open_store
from qmx_apps.volume import Volume, VolumeLease


@pytest.fixture
def volume(tmp_path: Path) -> Volume:
    value = Volume(tmp_path, "storage-app")
    value.create(agents=True)
    with closing(open_store(value)) as db, db:
        db.execute("CREATE TABLE readings (id INTEGER PRIMARY KEY, value INTEGER)")
        db.execute("INSERT INTO readings VALUES(1,42)")
    (value.root / "blobs/result.txt").write_text("saved result")
    return value


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> BackupSettings:
    # Use the real rclone executable and a key-free local backend, not a fake transfer.
    assert shutil.which("rclone"), "Install rclone on PATH for the backup integration tests."
    config = tmp_path / "rclone.conf"
    config.write_text("[fixture]\ntype = local\n")
    monkeypatch.setenv("RCLONE_CONFIG", str(config))
    return BackupSettings(remote="fixture", bucket=(tmp_path / "remote").as_posix())


def test_migrations_atomic_numbered_and_immutable(volume: Volume, tmp_path: Path) -> None:
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "2-cache.sql").write_text("CREATE TABLE cached (value TEXT, fetched_at TEXT);")
    (directory / "10-index.sql").write_text("CREATE INDEX cache_time ON cached(fetched_at);")
    with closing(open_store(volume, directory)) as db:
        assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        assert db.execute("PRAGMA busy_timeout").fetchone() == (5000,)
        assert db.execute("SELECT number FROM _qmx_migrations ORDER BY number").fetchall() == [
            (2,),
            (10,),
        ]
    with closing(open_store(volume, directory)) as db:
        assert db.execute("SELECT COUNT(*) FROM _qmx_migrations").fetchone() == (2,)
    (directory / "11-broken.sql").write_text("CREATE TABLE broken (id INTEGER); SELECT no_column;")
    with pytest.raises(sqlite3.Error), closing(open_store(volume, directory)):
        pass
    with closing(open_store(volume)) as db:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='broken'").fetchall()
    (directory / "11-broken.sql").unlink()
    (directory / "2-cache.sql").write_text("DROP TABLE cached;")
    with pytest.raises(AppError, match="cannot change"), closing(open_store(volume, directory)):
        pass


def test_migration_cannot_commit_partial_work(volume: Volume, tmp_path: Path) -> None:
    (tmp_path / "1.sql").write_text("CREATE TABLE partial (id INTEGER); COMMIT;")
    with pytest.raises(sqlite3.Error), closing(open_store(volume, tmp_path)):
        pass
    with closing(open_store(volume)) as db:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='partial'").fetchall()


def test_analytics_joins_sqlite_and_parquet_read_only(volume: Volume) -> None:
    path = (volume.root / "data/bars.parquet").as_posix().replace("'", "''")
    with duckdb.connect() as db:
        db.execute(f"COPY (SELECT 1 AS id, 8 AS amount) TO '{path}' (FORMAT PARQUET)")
    with analytics(volume) as db:
        assert db.execute(
            "SELECT value + amount FROM app.readings JOIN parquet USING(id)"
        ).fetchall() == [(50,)]
        with pytest.raises(duckdb.Error):
            db.execute("INSERT INTO app.readings VALUES(2,0)")


def test_snapshot_during_writes_and_round_trip(
    volume: Volume, settings: BackupSettings, tmp_path: Path
) -> None:
    started = threading.Event()
    stop = threading.Event()
    errors: list[Exception] = []

    def write() -> None:
        try:
            with closing(open_store(volume)) as db:
                while not stop.is_set():
                    with db:
                        db.execute("INSERT INTO readings(value) VALUES(43)")
                    started.set()
                    stop.wait(0.01)
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=write)
    thread.start()
    assert started.wait(5)
    try:
        first = backup(volume, settings)
    finally:
        stop.set()
        thread.join(5)
    assert not errors and not thread.is_alive()
    assert first["restore_test"] == {"passed": True}
    snapshot_id = str(first["snapshot_id"])
    snapshot = Path(settings.bucket) / settings.node / "storage-app" / snapshot_id
    with closing(sqlite3.connect(snapshot / "app.db")) as db:
        assert db.execute("SELECT COUNT(*) FROM readings").fetchone()[0] >= 2
    assert not list(snapshot.rglob("*-wal"))
    (volume.root / "data/stale.parquet").write_bytes(b"stale")
    (volume.root / "blobs/result.txt").write_text("changed")
    restored = restore(tmp_path, "storage-app", settings, snapshot_id)
    assert restored["checksums"] == first["checksums"]
    for name, digest in cast(dict[str, str], first["checksums"]).items():
        assert checksum(volume.root / name) == digest
    assert not (volume.root / "data/stale.parquet").exists()


def test_corruption_and_active_volume_refuse_restore(
    volume: Volume, settings: BackupSettings, tmp_path: Path
) -> None:
    manifest = backup(volume, settings)
    snapshot_id = str(manifest["snapshot_id"])
    lease = VolumeLease(tmp_path, "storage-app")
    try:
        with pytest.raises(AppError) as caught:
            restore(tmp_path, "storage-app", settings, snapshot_id)
        assert caught.value.code == "volume_busy"
    finally:
        lease.close()
    original = checksum(volume.root / "app.db")
    remote = Path(settings.bucket) / settings.node / "storage-app" / snapshot_id
    (remote / "app.db").write_bytes(b"corrupt")
    with pytest.raises(AppError, match="checksums"):
        restore(tmp_path, "storage-app", settings, snapshot_id)
    assert checksum(volume.root / "app.db") == original


def test_missing_rclone_clear_error(
    volume: Volume, settings: BackupSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(command: str) -> None:
        return None

    monkeypatch.setattr(shutil, "which", missing)
    with pytest.raises(AppError, match="Install rclone") as caught:
        backup(volume, settings)
    assert caught.value.code == "rclone_missing"


def test_restore_failed_swap_keeps_previous(
    volume: Volume, settings: BackupSettings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = backup(volume, settings)
    (volume.root / "blobs/result.txt").write_text("current")
    replace = os.replace

    def fail_stage(source: str | Path, destination: str | Path) -> None:
        if Path(source).name == "volume":
            raise OSError("swap failed")
        replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_stage)
    with pytest.raises(OSError, match="swap failed"):
        restore(tmp_path, "storage-app", settings, str(manifest["snapshot_id"]))
    assert (volume.root / "blobs/result.txt").read_text() == "current"


def test_schedule_reloads_settings_and_records_failures() -> None:
    settings = BackupSettings(remote="fixture", bucket="bucket")
    runs: list[str] = []
    failures: list[str] = []

    def fail(app_id: str) -> None:
        runs.append(app_id)
        raise AppError("failed", "failed")

    schedule = BackupSchedule(
        lambda: settings, lambda: ["app"], fail, lambda app, error: failures.append(app)
    )
    schedule.close()
    schedule.sweep(0)
    schedule.sweep(86399)
    assert not runs
    schedule.sweep(86400)
    assert runs == failures == ["app"]
    settings.interval_seconds = 10
    schedule.sweep(86410)
    assert len(runs) == 2
    settings.enabled = False
    schedule.sweep(99999)
    assert len(runs) == 2


def test_read_cache_expiry_and_invalidation() -> None:
    cache = ReadCache[str, int](ttl=0.01)
    assert cache.get("key", lambda: 42) == 42
    assert cache.get("key", lambda: 99) == 42
    time.sleep(0.02)
    assert cache.get("key", lambda: 99) == 99
    cache.invalidate()
    assert cache.get("key", lambda: 12) == 12


def test_backup_manifest_is_persisted(volume: Volume, settings: BackupSettings) -> None:
    manifest = backup(volume, settings)
    assert json.loads((volume.root / "backup.json").read_text()) == manifest
