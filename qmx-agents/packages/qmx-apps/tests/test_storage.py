from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from pathlib import Path

import duckdb
import pytest

from qmx_apps.cache import ReadCache
from qmx_apps.errors import AppError
from qmx_apps.store import analytics, open_store
from qmx_apps.volume import Volume, checksum, snapshot


@pytest.fixture
def volume(tmp_path: Path) -> Volume:
    value = Volume(tmp_path, "storage-app")
    value.create(agents=True)
    with closing(open_store(value)) as db, db:
        db.execute("CREATE TABLE readings (id INTEGER PRIMARY KEY, value INTEGER)")
        db.execute("INSERT INTO readings VALUES(1,42)")
    (value.root / "blobs/result.txt").write_text("saved result")
    return value


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


def test_read_cache_expiry_and_invalidation() -> None:
    cache = ReadCache[str, int](ttl=0.01)
    assert cache.get("key", lambda: 42) == 42
    assert cache.get("key", lambda: 99) == 42
    time.sleep(0.02)
    assert cache.get("key", lambda: 99) == 99
    cache.invalidate()
    assert cache.get("key", lambda: 12) == 12


def test_a_snapshot_copies_a_live_store_whole_and_checksums_name_its_bytes(
    volume: Volume, tmp_path: Path
) -> None:
    (volume.root / "data" / "heartbeat-1").write_text("beat")
    copied = tmp_path / "copied"

    snapshot(volume, copied)

    with closing(sqlite3.connect(copied / "app.db")) as db:
        assert db.execute("SELECT value FROM readings").fetchall() == [(42,)]
    assert not list(copied.rglob("*-wal")) and not (copied / "data" / "heartbeat-1").exists()
    assert checksum(copied / "blobs" / "result.txt") == checksum(volume.root / "blobs/result.txt")
