"""One copy of a folder's data (design 62 C1): what is in it, how a live store is copied, and
the order that keeps a copy from ever being mixed. Every folder is synthetic, in pytest's tmp
folder."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Generator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
from backup_fixtures import LEFT_OUT, MONTH, SECRETS, filled_folder, rows
from qmf.core import is_ok
from qmf.data.series import SeriesKey, SeriesStore
from qmx_engine.ledger import redact
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_home import resolve
from qmx_home.backup import snapshot
from qmx_home.backup.repository import FolderRepository, Manifest
from qmx_home.backup.snapshot import make

STAMP = "20261027T030000000000Z"


def quick_pool(manifest: Manifest, home: Path, path: str) -> Path:
    entry = next(e for e in manifest.entries if e.path == path)
    return FolderRepository(home / "backups" / "quick").pool_path(entry.sha256)


def test_a_copy_holds_every_file_but_the_left_out_the_secret_and_the_links(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX")

    copy = make(filled.layout, previous=None, stamp=STAMP)

    paths = {entry.path for entry in copy.entries}
    assert len(paths) == 65
    assert not paths & {*LEFT_OUT, *SECRETS}
    assert not [p for p in paths if p.startswith("claude-relayed/")]
    assert {
        "library/checkout/main/i0/.checkout.json",
        "claude/projects/p/chat.jsonl",
        f"{MONTH}/2026-02/open.parquet",
        f"{MONTH}/2026-02/state.json",
    } <= paths
    assert filled.long in paths
    assert len(str(filled.layout.data / str(filled.long))) > 300
    once = {e.path for e in copy.entries if e.at == "live"}
    assert once == set(filled.written_once)
    log = quick_pool(copy, filled.layout.root, "library/refs/log.jsonl").read_bytes()
    assert log.count(b"\n") == 3
    assert log.endswith(b'"item": "i2"}\n')


def test_each_store_is_copied_as_committed_with_its_row_counts_and_never_checkpointed(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", stores=1, secrets=False)
    ledger = filled.layout.data / "engine" / "engine.sqlite"
    with closing(sqlite3.connect(ledger, isolation_level=None)) as writer:
        writer.execute("PRAGMA journal_mode = WAL")
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        writer.execute("INSERT INTO events (at, body) VALUES ('committed', x'00')")
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("INSERT INTO events (at, body) VALUES ('not yet', x'00')")
        wal = ledger.with_name("engine.sqlite-wal")
        before = (wal.stat().st_size, wal.stat().st_mtime_ns, ledger.stat().st_mtime_ns)

        copy = make(filled.layout, previous=None, stamp=STAMP)

        after = (wal.stat().st_size, wal.stat().st_mtime_ns, ledger.stat().st_mtime_ns)
        writer.execute("ROLLBACK")
    entry = next(e for e in copy.entries if e.path == "engine/engine.sqlite")
    assert entry.tables == {"events": 65, "qmx_meta": 1}
    assert (entry.version, entry.min_reader) == (1, 1)
    assert rows(quick_pool(copy, filled.layout.root, "engine/engine.sqlite")) == entry.tables
    assert after == before, "the copy never checkpoints the live store"


def test_a_second_copy_of_an_unchanged_folder_reads_no_file_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX")
    first = make(filled.layout, previous=None, stamp=STAMP)
    pool = FolderRepository(filled.layout.backups / "quick")
    pooled = sorted(p.name for p in pool.pool.rglob("*") if p.is_file())
    opened: list[str] = []
    real_shared, real_connect = snapshot.open_shared, sqlite3.connect

    def shared(path: Path):
        opened.append(str(path))
        return real_shared(path)

    def connect(*args: object, **kwargs: object) -> sqlite3.Connection:
        opened.append(str(args[0]))
        return real_connect(*args, **kwargs)  # type: ignore[arg-type]

    from qmx_home import files

    monkeypatch.setattr(files, "open_shared", shared)
    monkeypatch.setattr(snapshot, "open_shared", shared)
    monkeypatch.setattr(sqlite3, "connect", connect)

    second = make(filled.layout, previous=first, stamp="20261027T040000000000Z")

    assert opened == []
    assert second.files == first.files
    assert sorted(p.name for p in pool.pool.rglob("*") if p.is_file()) == pooled


OPERATOR = Principal("operator")


@contextmanager
def ledger_writer(path: Path) -> Generator[threading.Event]:
    """A second thread committing rows to the engine ledger in a loop until the block ends."""
    stop = threading.Event()

    def write() -> None:
        with closing(sqlite3.connect(path, isolation_level=None, check_same_thread=False)) as db:
            db.execute("PRAGMA journal_mode = WAL")
            n = 0
            while not stop.is_set():
                db.execute("INSERT INTO events (at, body) VALUES (?, x'00')", (f"loop {n}",))
                n += 1

    thread = threading.Thread(target=write)
    thread.start()
    try:
        yield stop
    finally:
        stop.set()
        thread.join()


def test_writes_at_every_step_never_leave_a_copied_ref_or_price_state_naming_a_missing_file(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    ledger = layout.data / "engine" / "engine.sqlite"
    ledger.parent.mkdir(parents=True)
    with closing(sqlite3.connect(ledger, isolation_level=None)) as db:
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, at TEXT, body BLOB)")
    wall = [datetime(2024, 1, 15, tzinfo=UTC)]
    prices = SeriesStore(layout.data / "market" / "series", wall=lambda: wall[0])
    steps: list[str] = []
    with Store.open(layout.data / "library", redactor=redact) as library:

        def commit(month: int, *, settled: bool) -> None:
            key = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2024, month, "")
            assert is_ok(key)
            start = int(datetime(2024, month, 1, 9, tzinfo=UTC).timestamp() * 1000)
            ticks = [(start + i * 1000, 108_000 + i, 108_012 + i, 0.5, 0.25) for i in range(5)]
            wall[0] = (
                datetime(2026, 10, 1, tzinfo=UTC)
                if settled
                else datetime(2024, month, 2, tzinfo=UTC)
            )
            assert is_ok(prices.commit(key.value, ticks))

        def between(step: str) -> None:
            n = len(steps)
            steps.append(step)
            library.put(
                OPERATOR,
                Draft("note", None, title=f"put {n}", blobs={"body.md": f"n{n}".encode()}),
                on="main",
                expected_head=None,
            )
            commit(n + 1, settled=True)

        for month in range(1, 7):
            commit(month, settled=False)
        between("before the copy")
        with ledger_writer(ledger):
            copy = make(layout, previous=None, stamp=STAMP, progress=between)

    assert steps[1:] == ["stores", "library logs", "files", "price months", "files written once"]
    listed = {entry.path for entry in copy.entries}
    refs = quick_pool(copy, layout.root, "library/refs/log.jsonl").read_text(encoding="utf-8")
    heads = [json.loads(line)["new_head"] for line in refs.splitlines()]
    assert len(heads) >= 2
    for head in heads:
        hexdigest = head.rsplit(":", 1)[-1]
        assert f"library/objects/{hexdigest[:2]}/{hexdigest[2:4]}/{hexdigest}.json" in listed
    states = [e for e in copy.entries if e.path.endswith("/state.json")]
    assert len(states) >= 3
    for entry in states:
        state = json.loads(quick_pool(copy, layout.root, entry.path).read_bytes())
        named = f"{state['fingerprint']}.parquet" if state["frozen"] else "open.parquet"
        assert f"{entry.path.rpartition('/')[0]}/{named}" in listed
    store = quick_pool(copy, layout.root, "engine/engine.sqlite")
    with closing(sqlite3.connect(store)) as copied:
        assert copied.execute("PRAGMA quick_check").fetchone() == ("ok",)
    ledger_entry = next(e for e in copy.entries if e.path == "engine/engine.sqlite")
    assert rows(store) == ledger_entry.tables
    assert ledger_entry.tables["events"] > 0


def test_a_month_that_freezes_while_its_files_are_copied_is_copied_again_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    wall = [datetime(2024, 3, 2, tzinfo=UTC)]
    prices = SeriesStore(layout.data / "market" / "series", wall=lambda: wall[0])
    key = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2024, 3, "")
    assert is_ok(key)
    start = int(datetime(2024, 3, 1, 9, tzinfo=UTC).timestamp() * 1000)
    ticks = [(start + i * 1000, 108_000 + i, 108_012 + i, 0.5, 0.25) for i in range(5)]
    assert is_ok(prices.commit(key.value, ticks))
    listed = snapshot._month_files  # pyright: ignore[reportPrivateUsage]
    frozen: list[str] = []

    def then_freeze(folder: Path) -> list[str]:
        names = listed(folder)
        if not frozen:
            wall[0] = datetime(2026, 10, 1, tzinfo=UTC)
            commit = prices.commit(key.value, ticks)
            assert is_ok(commit)
            frozen.append(commit.value.fingerprint)
        return names

    monkeypatch.setattr(snapshot, "_month_files", then_freeze)

    copy = make(layout, previous=None, stamp=STAMP)

    month = "market/series/dukascopy/EURUSD/ticks/-/2024-03"
    assert sorted(e.path for e in copy.entries) == [
        f"{month}/{frozen[0]}.parquet",
        f"{month}/state.json",
    ]
    state = json.loads(quick_pool(copy, layout.root, f"{month}/state.json").read_bytes())
    assert (state["frozen"], state["fingerprint"]) == (True, frozen[0])
