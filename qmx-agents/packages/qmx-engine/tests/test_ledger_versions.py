"""The run ledger opens a newer ledger that still allows it, refuses one that does not by name, and
copies an older one into backups/ before its first step (design 62 B2, B3)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from qmx_home import resolve
from qmx_home.versions import StoreRefused

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.store import Ledger, Reader

AT = "2026-10-26T12:00:00.000000+00:00"


def home_of(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def written_by_a_newer_release(home: Path, *, version: int, min_reader: int) -> Path:
    """This release's ledger, then what a newer release adds: a table, a column and its marks."""
    with Ledger.open(home) as ledger:
        ledger.append("run-1", "run_created", {"workflow": "wf"}, at=AT)
    path = home / "engine" / "engine.sqlite"
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        db.execute("CREATE TABLE lineage (run_id TEXT PRIMARY KEY, parent TEXT)")
        db.execute("ALTER TABLE events ADD COLUMN origin TEXT")
        db.execute("INSERT INTO lineage VALUES ('run-1', 'run-0')")
        db.execute(f"PRAGMA user_version = {version}")
        db.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(version),))
        db.execute("UPDATE meta SET value = ? WHERE key = 'min_reader'", (str(min_reader),))
    return path


def test_a_ledger_one_version_newer_opens_and_keeps_what_the_newer_release_added(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    path = written_by_a_newer_release(home, version=5, min_reader=4)

    with Ledger.open(home) as ledger:
        applied = ledger.applied
        ledger.append("run-1", "run_finished", {"outcome": "done"}, at=AT)
    with Reader.open(home) as reader:
        kinds = [event.kind for event in reader.events("run-1")]
    with closing(sqlite3.connect(path)) as db:
        kept = db.execute("SELECT parent FROM lineage").fetchall()
        marks = db.execute("SELECT key, value FROM meta WHERE key != 'sqlite_version'").fetchall()

    assert (applied, kinds, kept) == ([], ["run_created", "run_finished"], [("run-0",)])
    assert sorted(marks) == [("min_reader", "4"), ("schema_version", "5")]


def test_a_ledger_whose_min_reader_is_raised_is_refused_by_name_and_left_as_it_was(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    path = written_by_a_newer_release(home, version=7, min_reader=5)
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as writer:
        Ledger.open(home)
    with pytest.raises(StoreRefused) as reader:
        Reader.open(home)

    assert str(writer.value) == str(reader.value)
    assert str(writer.value) == (
        "This QMX folder's run ledger was written by QMX 0.1.0 as run ledger version 7. This "
        "QMX reads run ledger version 4, and this one needs a QMX that reads version 5 or "
        f"newer. Install that QMX, or restore the copy taken before the upgrade from "
        f"{home.parent / 'backups'}."
    )
    assert path.read_bytes() == before


def test_a_version_2_ledger_is_copied_into_backups_before_its_steps(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = home / "engine" / "engine.sqlite"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as old:
        for statement in (*STEPS[0], *STEPS[1]):
            old.execute(statement)
        old.execute("INSERT INTO meta VALUES ('schema_version', '2')")

    with Ledger.open(home) as ledger:
        applied = ledger.applied
    (copy,) = (home.parent / "backups").glob("pre-engine-2-4-*")
    with closing(sqlite3.connect(copy / "data" / "engine" / "engine.sqlite")) as kept:
        before = kept.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    with Reader.open(home) as reader:
        after = reader.stats().schema_version

    assert (applied, before, after) == ([3, 4], ("2",), 4)


def test_an_inbox_that_is_not_qmxs_is_refused_and_left_as_it_was(tmp_path: Path) -> None:
    home = home_of(tmp_path)
    path = home / "engine" / "inbox.sqlite"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as foreign:
        foreign.execute("CREATE TABLE songs (title TEXT)")
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        InboxTable.open(home)

    assert str(refused.value).startswith(f"{path} is not a QMX inbox: it holds none of")
    assert path.read_bytes() == before
