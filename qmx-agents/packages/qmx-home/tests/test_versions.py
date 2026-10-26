"""A store opens, upgrades after a copy, or refuses by name (design 62 B2 and B3)."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable, Iterator
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest

from qmx_home import Label, Layout, NoQmxFolder, resolve
from qmx_home.stores import APPLICATION_ID, STORES, Store, Version
from qmx_home.versions import Opened, StoreRefused, check_open, open_sqlite, too_new

DEMO = Store("demo", "demo ledger", "sqlite", Version(3, 2), "demo.sqlite", ("rows",))
STEPS = (
    ("CREATE TABLE rows (id INTEGER PRIMARY KEY, body TEXT NOT NULL)",),
    ("ALTER TABLE rows ADD COLUMN at TEXT",),
    ("CREATE TABLE notes (id INTEGER PRIMARY KEY)",),
)


@pytest.fixture
def folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Layout]:
    monkeypatch.setitem(STORES, "demo", DEMO)
    yield resolve(tmp_path / "QMX", create=True, drives=[])


def free_space(free: int) -> Callable[[object], SimpleNamespace]:
    """A drive with `free` bytes left, for `shutil.disk_usage`."""

    def usage(_path: object) -> SimpleNamespace:
        return SimpleNamespace(free=free)

    return usage


def connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path, isolation_level=None, timeout=10)


def made(path: Path, *, version: int, min_reader: int | None = None, rows: int = 2) -> Path:
    """A demo store at `version`, marked as QMX's, holding `rows` rows."""
    with closing(connect(path)) as db:
        for step in STEPS[:version]:
            for statement in step:
                db.execute(statement)
        db.executemany("INSERT INTO rows (body) VALUES (?)", [(f"row {n}",) for n in range(rows)])
        db.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        db.execute(f"PRAGMA user_version = {version}")
        db.execute("CREATE TABLE qmx_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO qmx_meta VALUES ('min_reader', ?)", (str(min_reader or version),))
    return path


def marks(path: Path) -> tuple[int, int, str, int]:
    with closing(connect(path)) as db:
        return (
            db.execute("PRAGMA application_id").fetchone()[0],
            db.execute("PRAGMA user_version").fetchone()[0],
            db.execute("SELECT value FROM qmx_meta WHERE key = 'min_reader'").fetchone()[0],
            db.execute("SELECT count(*) FROM rows").fetchone()[0],
        )


def opened(path: Path) -> Opened:
    with closing(connect(path)) as db:
        return open_sqlite(db, "demo", STEPS)


def test_a_store_one_version_newer_that_still_allows_this_one_opens_unchanged(
    folder: Layout,
) -> None:
    path = made(folder.data / "demo.sqlite", version=4, min_reader=3)
    before = path.read_bytes()

    result = opened(path)

    assert result.newer
    assert path.read_bytes() == before


def test_a_store_whose_min_reader_is_raised_is_refused_by_name_and_not_written(
    folder: Layout,
) -> None:
    path = made(folder.data / "demo.sqlite", version=7, min_reader=5)
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        opened(path)

    assert str(refused.value) == (
        "This QMX folder's demo ledger was written by QMX 0.1.0 as demo ledger version 7. This "
        "QMX reads demo ledger version 3, and this one needs a QMX that reads version 5 or "
        f"newer. Install that QMX, or restore the copy taken before the upgrade from "
        f"{folder.backups}."
    )
    assert path.read_bytes() == before


def test_an_older_store_is_copied_first_then_moved_forward_one_step_at_a_time(
    folder: Layout,
) -> None:
    path = made(folder.data / "demo.sqlite", version=1, rows=3)

    result = opened(path)

    assert (result.found, result.applied) == (Version(1, 1), (2, 3))
    assert marks(path) == (APPLICATION_ID, 3, "2", 3)
    copy = result.snapshot
    assert copy is not None
    assert copy.parent == folder.backups
    assert copy.name.startswith("pre-demo-1-3-")
    assert marks(copy / "data" / "demo.sqlite") == (APPLICATION_ID, 1, "1", 3)
    logged = json.loads((folder.backups / "backups.jsonl").read_text(encoding="utf-8"))
    assert (logged["kind"], logged["files"]) == ("pre-change", ["data/demo.sqlite"])


def test_a_step_that_fails_leaves_the_store_at_its_last_good_version_with_an_incident(
    folder: Layout,
) -> None:
    path = made(folder.data / "demo.sqlite", version=1)
    broken = (STEPS[0], STEPS[1], ("CREATE TABLE rows (id INTEGER)",))

    with closing(connect(path)) as db, pytest.raises(StoreRefused) as refused:
        open_sqlite(db, "demo", broken)

    assert str(refused.value).startswith(
        "The demo ledger could not be upgraded: step 3 (version 2 to 3) failed (SQLITE_ERROR). "
        "It stays at version 2, as it was, and the copy taken first is in "
    )
    assert marks(path)[1:] == (2, "2", 2)
    incident = json.loads(
        (folder.backups / "backups.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert (incident["kind"], incident["step"], incident["stays_at"]) == ("upgrade-failed", 3, 2)


def test_an_upgrade_whose_copy_would_fill_the_disk_changes_nothing(
    folder: Layout, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = made(folder.data / "demo.sqlite", version=1)
    before = path.read_bytes()
    monkeypatch.setattr("qmx_home.versions.shutil.disk_usage", free_space(100 << 20))

    with pytest.raises(StoreRefused) as refused:
        opened(path)

    assert "the copy QMX takes first could not be made" in str(refused.value)
    assert str(refused.value).endswith("Nothing changed.")
    assert path.read_bytes() == before
    assert list(folder.backups.iterdir()) == []


@pytest.mark.parametrize(
    ("shape", "why"),
    [
        ("other program", "it belongs to another program (application id 0x1234)"),
        ("not sqlite", "it is not a SQLite database"),
        ("foreign tables", "it holds none of a QMX demo ledger's tables"),
    ],
)
def test_a_file_that_is_not_qmxs_is_refused_and_left_as_it_is(
    folder: Layout, shape: str, why: str
) -> None:
    path = folder.data / "demo.sqlite"
    if shape == "not sqlite":
        path.write_text("my notes\n" * 200, encoding="utf-8")
    else:
        with closing(connect(path)) as db:
            db.execute("CREATE TABLE photos (id INTEGER)")
            if shape == "other program":
                db.execute("PRAGMA application_id = 4660")
    before = path.read_bytes()

    with pytest.raises(StoreRefused) as refused:
        opened(path)

    assert str(refused.value) == (
        f"{path} is not a QMX demo ledger: {why}. QMX leaves it as it is; move it aside and "
        "start QMX again to make a new one."
    )
    assert path.read_bytes() == before


def test_two_processes_opening_an_old_store_at_once_run_each_step_once(folder: Layout) -> None:
    path = made(folder.data / "demo.sqlite", version=1)
    start = threading.Barrier(2)
    applied: list[tuple[int, ...]] = []

    def open_it() -> None:
        with closing(connect(path)) as db:
            start.wait()
            applied.append(open_sqlite(db, "demo", STEPS).applied)

    threads = [threading.Thread(target=open_it) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(step for steps in applied for step in steps) == [2, 3]
    assert marks(path) == (APPLICATION_ID, 3, "2", 2)


def test_a_store_written_before_stores_carried_versions_is_marked_without_a_copy(
    folder: Layout,
) -> None:
    path = folder.data / "control.db"
    with closing(connect(path)) as db:
        db.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL)")

    with closing(connect(path)) as db:
        result = open_sqlite(db, "control", (("SELECT 1",),))

    assert (result.found, result.applied, result.snapshot) == (Version(1, 1), (), None)
    with closing(connect(path)) as db:
        assert db.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
    assert not folder.backups.joinpath("backups.jsonl").exists()


def write_label(layout: Layout, label: Label) -> None:
    layout.label.write_text(label.dump(), encoding="utf-8")


def read_label(layout: Layout) -> Label:
    return Label.parse(layout.label.read_text(encoding="utf-8"))


def test_check_open_names_each_held_back_store_and_rewrites_the_label_from_the_files(
    folder: Layout,
) -> None:
    made(folder.data / "demo.sqlite", version=2)
    label = read_label(folder)
    stores = {**label.stores, "library": {"version": 3, "min_reader": 2}, "lab": {"version": 9}}
    write_label(folder, Label(label.home_id, 2, "0.1.0", "0.3.0", stores=stores, extra={"x": 1}))

    opening = check_open(folder)

    lines = {verdict.store: (verdict.action, verdict.line) for verdict in opening.verdicts}
    assert lines["demo"] == (
        "upgrades",
        "demo ledger: version 2, upgraded to 3 when it next opens, after a copy into backups/",
    )
    assert lines["library"] == (
        "read-only",
        "This QMX folder's Library was written by QMX 0.3.0 as Library version 3. This QMX "
        "reads Library version 1, and this one needs a QMX that reads version 2 or newer. "
        f"Install that QMX, or restore the copy taken before the upgrade from {folder.backups}. "
        "The Library opens read-only until then.",
    )
    assert lines["engine"] == ("new", "run ledger: made at version 4 when first opened")
    assert [verdict.store for verdict in opening.held_back] == ["library"]
    written = read_label(folder)
    assert opening.label_written
    assert written.stores["demo"] == {"version": 2, "min_reader": 2}
    assert (written.stores["library"], written.stores["lab"]) == (stores["library"], {"version": 9})
    assert (written.extra, written.last_written_by) == ({"x": 1}, "0.3.0")
    assert too_new(folder.data / "library", "library") == lines["library"][1]
    assert too_new(folder.data / "market", "market") is None


def test_a_newer_folder_opens_when_it_allows_this_release_and_is_refused_by_name_otherwise(
    folder: Layout,
) -> None:
    label = read_label(folder)
    write_label(folder, Label(label.home_id, 3, "0.1.0", "0.4.0", min_reader=2))
    allowed = resolve(folder.root, drives=[])
    write_label(folder, Label(label.home_id, 3, "0.1.0", "0.4.0"))

    with pytest.raises(NoQmxFolder) as refused:
        resolve(folder.root, drives=[])

    assert allowed == folder
    assert str(refused.value) == (
        f"{folder.root} was written by QMX 0.4.0 (folder format 3). This QMX reads folder "
        "format 2, and this folder needs a QMX that reads format 3 or newer. Install that QMX, "
        f"or restore the copy taken before the upgrade from {folder.root / 'backups'}"
    )


def test_a_label_round_trip_keeps_what_a_newer_release_added() -> None:
    text = (
        'format = "qmx-home"\nformat_version = 2\nhome_id = "h"\ncreated_by = "0.1.0"\n'
        'last_written_by = "0.2.0"\nfeatures = ["sync", "lab"]\nwhen = 2026-10-26T12:00:00Z\n'
        '[stores]\nlibrary = { version = 1, min_reader = 1 }\n"pods v2" = { version = 2 }\n'
        "[stores.lab]\nversion = 4\nkinds = { model = 2 }\n"
    )

    again = Label.parse(Label.parse(text).dump())

    assert again == Label.parse(text)
    assert dict(again.extra) == {
        "features": ["sync", "lab"],
        "when": Label.parse(text).extra["when"],
    }
    assert again.stores["lab"] == {"version": 4, "kinds": {"model": 2}}


def test_the_label_check_reads_a_folder_with_no_label_as_this_releases(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()

    assert too_new(home / "library", "library") is None
