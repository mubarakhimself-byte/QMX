"""The mini-app catalogue `apps.db` under design 62 B2: a catalogue written before stores carried
versions is marked as version 1 and keeps its rows; a newer one whose min_reader is raised is
refused by name and left as it was."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from qmx_home import resolve
from qmx_home.stores import APPLICATION_ID
from qmx_home.versions import StoreRefused

from qmx_apps.supervisor import Supervisor


def home_of(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def test_a_catalogue_from_before_versions_is_marked_and_keeps_its_rows(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = home / "apps.db"
    with closing(sqlite3.connect(path, isolation_level=None)) as old:
        old.execute("CREATE TABLE definitions (id TEXT, version TEXT, hash TEXT PRIMARY KEY)")
        old.execute("CREATE TABLE selected (id TEXT PRIMARY KEY, hash TEXT)")
        old.execute("INSERT INTO selected VALUES ('notes', 'h1')")

    Supervisor(home)

    with closing(sqlite3.connect(path)) as db:
        marks = (
            db.execute("PRAGMA application_id").fetchone()[0],
            db.execute("PRAGMA user_version").fetchone()[0],
        )
        rows = db.execute("SELECT id, hash FROM selected").fetchall()
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master")}
    assert (marks, rows) == ((APPLICATION_ID, 1), [("notes", "h1")])
    assert {"runtime", "active", "homes", "qmx_meta"} <= tables


def test_a_catalogue_whose_min_reader_is_raised_is_refused_by_name(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    Supervisor(home)
    path = home / "apps.db"
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        db.execute("PRAGMA user_version = 3")
        db.execute("UPDATE qmx_meta SET value = '3' WHERE key = 'min_reader'")
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        Supervisor(home)

    assert str(refused.value).startswith(
        "This QMX folder's mini-app catalogue was written by QMX 0.1.0 as mini-app catalogue "
        "version 3. This QMX reads mini-app catalogue version 1, and this one needs a QMX that "
        "reads version 3 or newer."
    )
    assert path.read_bytes() == before
