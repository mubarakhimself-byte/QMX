"""The first start brings his old QMX data in (design 62 F step 4, guard 5). Every old folder here
is a synthetic old-layout home in pytest's tmp folder; nothing reads his profile, his ~/.qmx, his
browser or his Credential Manager, and the sync roots are the test's own."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Generator, Iterator, Sequence
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from typing import Any

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.library import UNFINISHED, old_library
from qmx_control.service import ControlService
from qmx_engine.ledger import redact
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.store import Ledger
from qmx_home import FLAT, LABEL, Label, pointer_file, resolve
from qmx_library.migrate import OPERATOR, from_library_b, place
from qmx_library.migrate.from_library_b import JUNK, resolve_alias
from qmx_library.migrate.snapshot import snapshot as freeze
from qmx_library.port import Draft
from qmx_library.store import Store

from qmx_host import first_start
from qmx_host.__main__ import main
from qmx_host.bring_in import (
    PARTIAL,
    REPORT,
    REPORT_TEXT,
    Refused,
    Report,
    again,
    bring_in,
    brought_from,
    copy_file,
    long_path,
)
from qmx_host.first_start import Places, bring_in_old, first_start_router, offer
from qmx_host.host import recheck_test_runs

VAULT_KEY = b"\x01\x02 test vault key"


def items(db: sqlite3.Connection, home: Path, rows: list[tuple[str, str, str, int]]) -> None:
    """Library B rows as `library.db` held them (MIGRATION step 2's table): for each item its
    root id, kind, title and number of versions, each version one row."""
    for root, kind, title, versions in rows:
        previous: str | None = None
        for version in range(1, versions + 1):
            item_id = root if version == 1 else str(uuid.uuid4())
            content = {"title": title} if version == 1 else {"title": title, "version": version}
            body = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
            digest = hashlib.sha256(body).hexdigest()
            (home / "artifacts" / digest).write_bytes(body)
            data: dict[str, object] = {
                "id": item_id,
                "kind": kind,
                "title": title,
                "tags": [],
                "source": "",
                "created": "2026-10-01T00:00:00+00:00",
                "root_id": root,
                "version": version,
                "previous_id": previous,
                "sha256": digest,
                "size": len(body),
                "ref": f"artifacts/{digest}",
                "fetched_date": None,
            }
            db.execute(
                "INSERT INTO items VALUES(?,?,?,?,?,?)",
                (item_id, json.dumps(data), root, version, "", None),
            )
            previous = item_id


def old_home(
    at: Path,
    scratch: Path,
    made_by_tests: Sequence[str] = (),
    *,
    count: int = 3,
    versions: int = 1,
) -> Path:
    """A flat home in the old layout, labelled format 1 the way LF1's `--create` labelled one: the
    control store and run index from the control service's own openers, a run ledger at schema
    version 3 (the parent's own steps 1 to 3) with one event, `library.db` with rows still in
    its `-wal` (taken while a connection held them), the test junk, a vault key, the host log,
    the old lock, and the relayed home's junction to the chats. The Library holds `count` items of
    his (an article, then backtests). `made_by_tests` names more `remote-flow` results, written
    after the junk list was taken. The first of his items and each test run's item have
    `versions` versions."""
    mine = [("article", "Carry paper"), ("backtest", "Rates"), ("backtest", "Momentum")]
    mine += [("backtest", f"Study {n}") for n in range(len(mine), count)]
    (at / "artifacts").mkdir(parents=True)
    (at / LABEL).write_text(Label.mint(FLAT).dump(), encoding="utf-8")
    (at / ".qmx").mkdir()
    (at / ".qmx" / "vault.key").write_bytes(VAULT_KEY)
    ControlService(at, secret_getter=lambda _s, _u: None).close()
    (at / "engine").mkdir()
    with closing(sqlite3.connect(at / "engine" / "engine.sqlite", isolation_level=None)) as db:
        for statement in (*STEPS[0], *STEPS[1], *STEPS[2]):
            db.execute(statement)
        db.execute("INSERT INTO meta VALUES ('schema_version', '3')")
        db.execute(
            "INSERT INTO events VALUES ('run-1', 1, '2026-10-01T00:00:00Z', 'run_created', '{}')"
        )
    (at / "control.log").write_text("host started\n", encoding="utf-8")
    (at / "engine.lock").write_bytes(b"")
    (at / "claude" / "projects" / "p").mkdir(parents=True)
    (at / "claude" / "projects" / "p" / "chat.jsonl").write_text("{}\n", encoding="utf-8")
    (at / "claude-relayed").mkdir()
    link(at / "claude-relayed" / "projects", at / "claude" / "projects")
    (at / "empty-folder").mkdir()
    live = scratch / "live"
    live.mkdir()
    with closing(sqlite3.connect(live / "library.db")) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE items(id TEXT PRIMARY KEY, data TEXT NOT NULL, root TEXT NOT NULL,
                version INTEGER NOT NULL, source TEXT NOT NULL, fetched_date TEXT,
                UNIQUE(root,version));
            CREATE TABLE links(source TEXT,target TEXT,relation TEXT,
                PRIMARY KEY(source,target,relation));
            CREATE TABLE memo(key TEXT PRIMARY KEY,item_id TEXT NOT NULL);
        """)
        db.execute("PRAGMA wal_autocheckpoint=0")
        with db:
            items(
                db,
                at,
                [
                    *(
                        (str(uuid.uuid4()), kind, title, versions if n == 0 else 1)
                        for n, (kind, title) in enumerate(mine[:count])
                    ),
                    (JUNK[0], "workflow-result", "remote-flow", 1),
                    *((i, "workflow-result", "remote-flow", versions) for i in made_by_tests),
                ],
            )
        for name in ("library.db", "library.db-wal"):
            shutil.copyfile(live / name, at / name)
    return at


def link(path: Path, target: Path) -> None:
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(path))
    else:
        path.symlink_to(target, target_is_directory=True)


def snapshot(folder: Path) -> list[tuple[str, int, int, str]]:
    """Every entry of `folder` with its size, modified time and hash: what "unchanged" means."""
    found: list[tuple[str, int, int, str]] = []
    for path in sorted(folder.rglob("*")):
        record = path.lstat()
        is_file = path.is_file() and not path.is_junction() and not path.is_symlink()
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if is_file else ""
        found.append(
            (path.relative_to(folder).as_posix(), record.st_size, record.st_mtime_ns, digest)
        )
    return found


@pytest.fixture
def pc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A scratch profile: the pointer and the first start's lock land under it, never in his."""
    profile = tmp_path / "profile"
    for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (profile / part).mkdir(parents=True)
        monkeypatch.setenv(name, str(profile / part))
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("HOME", str(profile))
    monkeypatch.delenv("QMX_HOME", raising=False)
    yield tmp_path


def places(pc: Path, **sync: Path) -> Places:
    environ = {
        "APPDATA": str(pc / "profile" / "Roaming"),
        "LOCALAPPDATA": str(pc / "profile" / "Local"),
    }
    return Places(environ, tuple((client, root) for client, root in sync.items()))


def test_the_old_folder_is_copied_switched_and_left_exactly_as_it_was(pc: Path) -> None:
    old = old_home(pc / "old" / ".qmx", pc)
    before = snapshot(old)

    report = bring_in_old(old, pc / "QMX", places(pc))

    new = pc / "QMX"
    assert report.finished, report.text
    assert snapshot(old) == before, "not one byte, time or name of the old folder changed"
    assert (new / "keys" / "vault.key").read_bytes() == VAULT_KEY
    assert (new / "logs" / "host.log").read_text(encoding="utf-8") == "host started\n"
    assert not (new / "data" / LABEL).exists(), "the old label never lands inside data/"
    assert Label.parse((new / LABEL).read_text(encoding="utf-8")).format_version == 2
    assert (new / "data" / "claude" / "projects" / "p" / "chat.jsonl").is_file()
    assert (new / "data" / "empty-folder").is_dir()
    assert not (new / "data" / "claude-relayed" / "projects").exists(), "a link is never copied"
    assert not (new / "data" / "library.db").exists()
    assert (new / "data" / "migration" / "retired" / "library.db").is_file()
    assert old_library(new / "data") is None
    assert not (new / "data" / UNFINISHED).exists()
    library = report.facts["library"]
    assert isinstance(library, dict)
    assert library["kinds"] == {"article": 1, "backtest": 2}
    assert library["report"]["junk"] == [JUNK[0]]
    assert report.lines[0] == f"Your old QMX data is in {new} now."
    assert "Your Library: 3 items in the new Library." in report.lines
    assert (
        "  1 test result named remote-flow, made by test runs and not by you, left in your old "
        "folder." in report.lines
    )
    assert "  engine.lock: the old QMX's lock file; QMX makes a new one." in report.lines
    assert (new / "data" / "migration" / "bring-in-report.txt").read_text(
        encoding="utf-8"
    ) == report.text
    assert "  qmx-home.toml: the old folder's own label; the new folder has its own." in (
        report.lines
    )
    pointer = pointer_file()
    assert pointer is not None
    assert f"home = {json.dumps(str(new))}" in pointer.read_text(encoding="utf-8")
    assert sorted(p.name for p in pointer.parent.iterdir()) == ["home.toml"]
    (copy,) = (new / "backups").glob("pre-engine-3-5-*")
    assert (copy / "data" / "engine" / "engine.sqlite").is_file()
    with Ledger.open(new / "data") as ledger:
        assert ledger.applied == []
    uri = f"{(new / 'data' / 'engine' / 'engine.sqlite').as_uri()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        marks = db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        events = db.execute("SELECT run_id FROM events").fetchall()
    assert (marks, events) == (("5",), [("run-1",)])


def test_a_store_the_new_folder_would_refuse_fails_the_bring_in_by_name(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    with closing(sqlite3.connect(old / "control.db", isolation_level=None)) as db:
        db.execute("PRAGMA user_version = 9")
        db.execute("UPDATE qmx_meta SET value = '9' WHERE key = 'min_reader'")

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert not report.finished
    assert str(report.facts["why"]).startswith(
        "the control store would not open in the new folder: "
    )
    assert (pc / "QMX" / "data" / UNFINISHED).is_file()


def test_a_rerun_after_a_finished_bring_in_returns_its_report_and_copies_nothing(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    first = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)
    written = snapshot(pc / "QMX")

    again = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert again.lines == first.lines
    assert snapshot(pc / "QMX") == written


def test_a_corrupted_copy_leaves_the_new_folder_unfinished_and_the_old_one_untouched(
    pc: Path,
) -> None:
    old = old_home(pc / ".qmx", pc)
    before = snapshot(old)

    def corrupting(source: Path, target: Path) -> str:
        digest = copy_file(source, target)
        if target.name == f"runs.db{PARTIAL}":
            target.write_bytes(b"not what was copied")
        return digest

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal, copy=corrupting)

    assert not report.finished
    assert report.facts["why"] == "the copy of runs.db does not match your old folder"
    assert snapshot(old) == before
    assert (pc / "QMX" / "data" / UNFINISHED).read_text(encoding="utf-8") == report.facts["why"]
    refusal = old_library(pc / "QMX" / "data")
    assert refusal is not None and refusal.startswith(
        f"bringing your old QMX data into {pc / 'QMX' / 'data'} did not finish: the copy of runs.db"
    )
    assert refusal.endswith(
        "Bring it in again into the same folder from the first start, which clears only QMX's "
        f"own unfinished copy there: python -m qmx_host bring-in --again --home {pc / 'QMX'} "
        "--old <old folder>"
    ), "never a second folder beside the unfinished one"
    with pytest.raises(Refused, match="did not finish"):
        bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)


def test_a_file_that_changes_while_it_is_copied_stops_the_bring_in(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)

    def meddling(source: Path, target: Path) -> str:
        digest = copy_file(source, target)
        if source.name == "vault.key":
            (old / "control.db").write_bytes(b"written by a QMX still running")
        return digest

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal, copy=meddling)

    assert not report.finished
    assert report.facts["why"] == (
        "your old folder changed while it was copied (control.db changed)"
    )


def test_a_folder_under_a_sync_client_or_an_app_folder_is_refused_by_name(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    onedrive = pc / "OneDrive - Home"
    dropbox = pc / "Dropbox"
    (pc / "profile" / "Local" / "Dropbox").mkdir()
    (pc / "profile" / "Local" / "Dropbox" / "info.json").write_text(
        json.dumps({"personal": {"path": str(dropbox), "host": 1}}), encoding="utf-8"
    )
    from qmx_host.first_start import sync_roots

    environ = {**places(pc).environ, "OneDriveConsumer": str(onedrive)}
    here = Places(environ, sync_roots(environ))

    with pytest.raises(Refused) as under_onedrive:
        bring_in_old(old, onedrive / "QMX", here)
    with pytest.raises(Refused) as under_dropbox:
        bring_in_old(old, dropbox / "Work" / "QMX", here)
    with pytest.raises(Refused) as in_app_data:
        bring_in_old(old, pc / "profile" / "Local" / "QMX", here)

    assert str(under_onedrive.value).startswith(
        f"{onedrive / 'QMX'} is inside your OneDrive folder {onedrive}, where a QMX folder never "
        "goes: OneDrive syncs it live"
    )
    assert f"inside your Dropbox folder {dropbox}" in str(under_dropbox.value)
    assert "inside Windows' app folder AppData\\Local" in str(in_app_data.value)
    assert not (onedrive / "QMX").exists() and not (dropbox / "Work").exists()


def test_old_folders_lf2_refuses_and_overlapping_targets_are_refused(pc: Path) -> None:
    profile = pc / "someone"
    profile.mkdir()
    (profile / "NTUSER.DAT").write_bytes(b"hive")
    (profile / "control.db").write_bytes(b"x")
    notes = pc / "notes"
    (notes / "vault").mkdir(parents=True)
    old = old_home(pc / ".qmx", pc)
    refusal = places(pc).refusal

    with pytest.raises(Refused, match="it is a user profile"):
        bring_in(profile, pc / "A", place_refusal=refusal)
    with pytest.raises(Refused, match=r"has no qmx-home\.toml and none of a QMX home's own files"):
        bring_in(notes, pc / "B", place_refusal=refusal)
    with pytest.raises(Refused, match="overlap"):
        bring_in(old, old / "QMX", place_refusal=refusal)
    assert not (pc / "A").exists() and not (pc / "B").exists() and not (old / "QMX").exists()


def test_two_first_starts_at_once_refuse_the_second(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    lock = pc / "profile" / "Roaming" / "QMX" / "first-start.lock"
    lock.parent.mkdir(parents=True)
    with lock.open("a+b") as held:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(Refused, match="another first start is running"):
            bring_in_old(old, pc / "QMX", places(pc))
    assert not (pc / "QMX").exists()


def test_too_little_room_is_refused_before_anything_is_written(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / ".qmx", pc)

    def ten_megabytes_free(_path: object) -> SimpleNamespace:
        return SimpleNamespace(free=10 << 20)

    monkeypatch.setattr("qmx_host.bring_in.shutil.disk_usage", ten_megabytes_free)

    with pytest.raises(Refused, match=r"has 10\.0 MB free; QMX keeps at least 1\.0 GB free there"):
        bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)
    assert not (pc / "QMX").exists()


def test_the_host_refuses_the_old_folder_and_names_the_first_start(
    pc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = old_home(pc / ".qmx", pc)
    before = snapshot(old)

    with pytest.raises(SystemExit) as stopped:
        main(["serve", "--home", str(old)])

    assert stopped.value.code == 3, "a first start is due"
    assert capsys.readouterr().err.strip() == (
        f"{old} holds your old QMX data in the old layout. QMX does not start on it and never "
        "changes it. Bring it into a new QMX folder with the first start: python -m qmx_host "
        f"bring-in --home <new QMX folder> --old {old}"
    )
    assert snapshot(old) == before


def card_client(place: Places, old: Path, handed: list[Path] | None = None) -> TestClient:
    """The card's routes on a test client, on no machine drive, handing over into `handed`."""
    app = FastAPI()
    on_handover = handed.append if handed is not None else None
    app.include_router(
        first_start_router(place, old, drives=[], port=8799, on_handover=on_handover)
    )
    return TestClient(app)


def ended(client: TestClient, job_id: str) -> dict[str, Any]:
    """The job's view once it is no longer running."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        job = client.get(f"/api/first-start/jobs/{job_id}").json()
        if job["state"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} still running")


def test_the_card_offers_the_bring_in_first_and_answers_each_choice(pc: Path) -> None:
    old = old_home(pc / "profile" / ".qmx", pc)
    onedrive = pc / "OneDrive"
    client = card_client(Places(places(pc).environ, (("OneDrive", onedrive),)), old)

    card = client.get("/api/first-start").json()
    restore = client.post("/api/first-start/restore")
    refused = client.post("/api/first-start/bring-in", json={"folder": str(onedrive / "QMX")})
    after_refusal = client.get("/api/first-start").json()["job"]
    brought = client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")})
    job = ended(client, brought.json()["id"])

    assert (card["old"], card["chosen"], card["found"], card["job"]) == (
        str(old),
        "bring-in",
        None,
        None,
    )
    assert card["choices"] == ["bring-in", "new", "open", "restore"]
    assert restore.status_code == 501
    assert refused.status_code == 409
    assert "inside your OneDrive folder" in refused.json()["detail"]
    assert after_refusal is None, "a refused bring-in starts no job"
    assert brought.status_code == 202
    assert (brought.json()["kind"], brought.json()["state"]) == ("bring-in", "running")
    assert (job["state"], job["line"], job["step"]) == (
        "finished",
        "",
        "opening the new folder's stores",
    )
    assert job["result"]["finished"] is True
    assert job["result"]["report"][0] == f"Your old QMX data is in {pc / 'QMX'} now."
    progress = job["progress"]
    assert progress["files_hashed"] == progress["files_total"]
    assert progress["files_copied"] == progress["files_total"] - 2, "the old lock and label stay"
    assert (progress["versions_switched"], progress["versions_total"]) == (3, 3)
    reloaded = client.get("/api/first-start").json()
    assert (reloaded["found"], reloaded["job"]) == (str(pc / "QMX"), job)


def test_an_old_folder_a_host_still_serves_is_refused_by_its_process_record(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    me = psutil.Process()
    (old / "control-process.json").write_text(
        json.dumps({"pid": me.pid, "port": 1, "created": me.create_time()}), encoding="utf-8"
    )

    with pytest.raises(Refused, match=rf"a QMX host is still running on .* \(PID {me.pid}\)"):
        bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)
    assert not (pc / "QMX").exists()


def test_the_same_old_folder_is_never_brought_into_a_second_folder(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    assert bring_in_old(old, pc / "QMX", places(pc)).finished

    with pytest.raises(Refused, match="was already brought into"):
        bring_in_old(old, pc / "Second", places(pc))
    assert not (pc / "Second").exists()


def test_an_old_folder_that_is_a_link_is_read_through_it_and_said_so(pc: Path) -> None:
    real = old_home(pc / "elsewhere" / ".qmx", pc)
    old = pc / "profile-link"
    link(old, real)

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert report.finished, report.text
    assert report.lines[1] == f"Your old folder {old} is a link; its files were read from {real}."
    assert old.is_junction() or old.is_symlink()


def test_a_rerun_naming_another_old_folder_is_refused_not_answered_with_the_first_report(
    pc: Path,
) -> None:
    first = old_home(pc / "first" / ".qmx", pc / "first")
    other = old_home(pc / "other" / ".qmx", pc / "other")
    assert bring_in(first, pc / "QMX", place_refusal=places(pc).refusal).finished

    with pytest.raises(Refused) as refused:
        bring_in(other, pc / "QMX", place_refusal=places(pc).refusal)

    assert str(refused.value) == (
        f"{pc / 'QMX'} already holds the old data brought in from {first}, not {other}; bring "
        f"{other} into another new folder"
    )


def test_a_stale_frozen_copy_in_the_old_folder_hides_no_row(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    earlier = pc / "earlier"
    (earlier / "artifacts").mkdir(parents=True)
    with (
        closing(sqlite3.connect(old / "library.db")) as source,
        closing(sqlite3.connect(earlier / "library.db")) as kept,
    ):
        source.backup(kept)
        with kept:
            kept.execute("DELETE FROM items WHERE json_extract(data, '$.kind') = 'backtest'")
    freeze(earlier)
    shutil.copytree(earlier / "migration", old / "migration")

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert report.finished, report.text
    library = report.facts["library"]
    assert isinstance(library, dict)
    assert library["kinds"] == {"article": 1, "backtest": 2}
    assert str(report.facts["set_aside"]).startswith("migration/pre-from-the-old-folder-")
    assert any(line.startswith("  Your old folder held the frozen copy") for line in report.lines)


def test_any_error_ends_with_an_unfinished_report_naming_it(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)

    def failing(source: Path, target: Path) -> str:
        raise RuntimeError("the copier broke")

    report = bring_in_old(old, pc / "QMX", places(pc), copy=failing)

    assert not report.finished
    assert report.facts["why"] == "it stopped with an error: the copier broke"
    assert report.lines[0] == (
        "Bringing your old QMX data in did not finish: it stopped with an error: the copier broke."
    )
    assert (pc / "QMX" / "data" / UNFINISHED).read_text(encoding="utf-8") == report.facts["why"]
    assert not (pc / "profile" / "Roaming" / "QMX").exists(), "no lock is left in AppData"


MADE_BY_TESTS = (
    "  2 items made by test runs, not by you, are in the new Library but archived: search and "
    "recall leave them out, and nothing was deleted."
)


def searched(data: Path) -> tuple[int, int]:
    """Items Library search finds for `remote-flow`, then with the archived ones."""
    with Store.open(data / "library", redactor=redact, name="pc") as store:
        return (
            len(store.search(OPERATOR, "remote-flow")),
            len(store.search(OPERATOR, "remote-flow", include_archived=True)),
        )


def test_test_runs_in_the_old_library_are_counted_apart_and_archived_not_deleted(
    pc: Path,
) -> None:
    tests = sorted(str(uuid.uuid4()) for _ in range(2))
    old = old_home(pc / "old" / ".qmx", pc, made_by_tests=tests)
    before = snapshot(old)

    report = bring_in_old(old, pc / "QMX", places(pc))

    assert report.finished, report.text
    assert snapshot(old) == before, "not one byte, time or name of the old folder changed"
    library = report.facts["library"]
    assert isinstance(library, dict)
    assert library["kinds"] == {"article": 1, "backtest": 2}
    assert (report.facts["test_runs"], report.facts["test_rule"]) == (tests, 1)
    assert "Your Library: 3 items in the new Library." in report.lines
    assert MADE_BY_TESTS in report.lines
    assert (
        "  1 test result named remote-flow, made by test runs and not by you, left in your old "
        "folder." in report.lines
    )
    assert searched(pc / "QMX" / "data") == (0, 2)


def brought_in_before_the_rule(pc: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, list[str]]:
    """A folder brought in the way a release before the test rule did: the two test runs active
    in the new Library and no `test_rule` stamp in the report. Returns its data folder and the
    test runs' old ids."""
    tests = sorted(str(uuid.uuid4()) for _ in range(2))
    old = old_home(pc / "old" / ".qmx", pc, made_by_tests=tests)
    with monkeypatch.context() as earlier:
        earlier.setattr(from_library_b, "TEST_LANES", ())
        bring_in_old(old, pc / "QMX", places(pc))
    data = pc / "QMX" / "data"
    saved = json.loads((data / REPORT).read_text(encoding="utf-8"))
    for stamp in ("test_rule", "test_runs"):
        del saved[stamp]
    (data / REPORT).write_text(json.dumps(saved), encoding="utf-8")
    return data, tests


def test_a_folder_brought_in_before_the_rule_is_archived_once_at_host_start(
    pc: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data, _ = brought_in_before_the_rule(pc, monkeypatch)
    assert searched(data) == (2, 2)

    for _ in range(2):
        with Store.open(data / "library", redactor=redact, name="pc") as store:
            recheck_test_runs(data, store)

    text = (data / REPORT_TEXT).read_text(encoding="utf-8").splitlines()
    facts = json.loads((data / REPORT).read_text(encoding="utf-8"))
    assert searched(data) == (0, 2)
    assert [line for line in text if "made by test runs, not by you" in line] == [
        f"Checked again when QMX started on {datetime.now(UTC):%Y-%m-%d}: "
        + MADE_BY_TESTS.removeprefix("  ")
    ]
    assert (facts["test_rule"], len(facts["test_runs"])) == (1, 2)
    assert capsys.readouterr().err == "library: 2 old items made by test runs archived\n"


def test_an_item_he_added_a_version_to_since_the_bring_in_stays_his_at_host_start(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data, tests = brought_in_before_the_rule(pc, monkeypatch)
    with Store.open(data / "library", redactor=redact, name="pc") as store:
        first = store.get(OPERATOR, str(resolve_alias(store, tests[0])))
        place(
            store,
            Draft(
                "artifact",
                first.item,
                title="remote-flow",
                blobs={"content": b"my notes on the remote flow"},
                parents=[first.object_id],
            ),
        )
        recheck_test_runs(data, store)
        found = {hit.item for hit in store.search(OPERATOR, "remote-flow")}

    facts = json.loads((data / REPORT).read_text(encoding="utf-8"))
    assert found == {first.item}, "the item with his version is still found"
    assert facts["test_runs"] == [tests[1]]


def test_an_unreadable_frozen_library_leaves_the_report_unstamped_and_the_host_starting(
    pc: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data, _ = brought_in_before_the_rule(pc, monkeypatch)
    frozen = data / "migration" / "pre" / "library.db"
    frozen.write_bytes(b"not a database " * 100)

    with Store.open(data / "library", redactor=redact, name="pc") as store:
        recheck_test_runs(data, store)

    facts = json.loads((data / REPORT).read_text(encoding="utf-8"))
    assert "test_rule" not in facts
    assert capsys.readouterr().err == (
        f"library: test runs from the old Library not checked in {frozen}: file is not a database\n"
    )
    assert searched(data) == (2, 2)


def test_the_report_counts_items_not_versions(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc, made_by_tests=[str(uuid.uuid4())], versions=2)

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert report.finished, report.text
    library = report.facts["library"]
    assert isinstance(library, dict)
    assert library["kinds"] == {"article": 1, "backtest": 2}
    assert "Your Library: 3 items in the new Library." in report.lines
    assert (
        "  1 item made by test runs, not by you, is in the new Library but archived: search and "
        "recall leave them out, and nothing was deleted." in report.lines
    )


@pytest.mark.skipif(sys.platform != "win32", reason="the 260-character limit is Windows' own")
def test_a_file_at_a_path_over_260_characters_is_copied_and_hashed(pc: Path) -> None:
    old = old_home(pc / ".qmx", pc)
    deep = long_path(old / "environments" / ("e" * 120) / ("f" * 120))
    deep.mkdir(parents=True)
    (deep / "model.bin").write_bytes(b"weights" * 1000)
    copied_path = "cache/envs/" + "e" * 120 + "/" + "f" * 120 + "/model.bin"
    assert len(str(pc / "QMX" / copied_path)) > 260

    report = bring_in(old, pc / "QMX", place_refusal=places(pc).refusal)

    assert report.finished, report.text
    copied = long_path(pc / "QMX" / copied_path)
    assert (
        hashlib.sha256(copied.read_bytes()).hexdigest()
        == hashlib.sha256(b"weights" * 1000).hexdigest()
    )
    assert not any("\\\\?\\" in line for line in report.lines)
    assert long_path(Path("D:/QMX/a")) == Path("\\\\?\\D:\\QMX\\a")


def test_an_error_before_the_copy_stops_the_job_with_one_line_and_no_marker(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / ".qmx", pc)
    client = card_client(places(pc), old)

    def unready(_path: object) -> object:
        raise OSError(errno.EIO, "The device is not ready")

    def denied(flag: Path, **_: object) -> object:
        raise PermissionError(errno.EACCES, "Access is denied", str(flag))

    with monkeypatch.context() as broken:
        broken.setattr("qmx_host.bring_in.shutil.disk_usage", unready)
        first = ended(
            client,
            client.post("/api/first-start/bring-in", json={"folder": str(pc / "A")}).json()["id"],
        )
    with monkeypatch.context() as broken:
        broken.setattr("qmx_host.bring_in.resolve", denied)
        second = ended(
            client,
            client.post("/api/first-start/bring-in", json={"folder": str(pc / "B")}).json()["id"],
        )

    assert (first["state"], first["line"]) == (
        "stopped",
        "the bring-in did not start: The device is not ready. Nothing was copied; fix that, then "
        "bring your old data in again",
    )
    assert (second["state"], second["line"]) == (
        "stopped",
        f"the bring-in did not start: Access is denied ({pc / 'B'}). Nothing was copied; fix "
        "that, then bring your old data in again",
    )
    assert not (pc / "A").exists()
    assert not (pc / "B").exists()


def test_a_bring_in_while_one_runs_is_refused_naming_it_and_so_are_new_and_open(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / ".qmx", pc)
    client = card_client(places(pc), old)
    gate = threading.Event()
    real = first_start.bring_in_old

    def held_back(*args: Any, **kwargs: Any) -> Report:
        gate.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(first_start, "bring_in_old", held_back)

    running = client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")}).json()
    second = client.post("/api/first-start/bring-in", json={"folder": str(pc / "Other")})
    made = client.post("/api/first-start/new", json={"folder": str(pc / "New")})
    opened = client.post("/api/first-start/open", json={"folder": str(pc / "QMX")})
    handover = client.post("/api/first-start/handover")
    gate.set()
    job = ended(client, running["id"])

    assert second.status_code == 409
    assert second.json()["detail"] == (
        f"a bring-in is already running (job {running['id']}); wait for it to end"
    )
    assert (made.status_code, opened.status_code, handover.status_code) == (409, 409, 409)
    assert made.json()["detail"] == "another first start is running on this PC; wait for it to end"
    assert job["state"] == "finished"
    assert not (pc / "New").exists() and not (pc / "Other").exists()


@contextmanager
def locked(path: Path) -> Generator[None]:
    """`path` locked the way another process's first start holds it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as held:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def test_a_first_start_in_another_process_makes_the_card_answer_409_even_with_no_appdata(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / ".qmx", pc)
    client = card_client(places(pc), old)
    beside_the_pointer = pc / "profile" / "Roaming" / "QMX" / "first-start.lock"

    with locked(beside_the_pointer):
        with_pointer = client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")})
    monkeypatch.setattr(first_start, "pointer_file", lambda: None)
    monkeypatch.setattr(tempfile, "tempdir", str(pc / "temp"))
    with locked(pc / "temp" / "qmx-first-start.lock"):
        without = client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")})

    for answer in (with_pointer, without):
        assert answer.status_code == 409
        assert answer.json()["detail"] == (
            "another first start is running on this PC; wait for it to end"
        )
    assert client.get("/api/first-start").json()["job"] is None
    assert not (pc / "QMX").exists()


def test_a_bring_in_stopped_mid_copy_is_offered_again_into_the_same_folder(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    old = old_home(pc / "old" / ".qmx", pc)
    other = old_home(pc / "other" / ".qmx", pc / "other")
    target = pc / "profile" / "QMX"
    before = snapshot(old)
    calls: list[Path] = []

    def killed(source: Path, written: Path) -> str:
        calls.append(source)
        if len(calls) == 5:
            raise KeyboardInterrupt
        return copy_file(source, written)

    with pytest.raises(KeyboardInterrupt):
        bring_in(old, target, place_refusal=places(pc).refusal, copy=killed)
    facts = json.loads((target / "data" / REPORT).read_text(encoding="utf-8"))
    finished_facts = brought_from(target)
    offered = offer(pc / "profile" / ".qmx", places(pc), drives=[])
    with pytest.raises(SystemExit) as serve:
        main(["serve", "--home", str(target)])
    with pytest.raises(Refused, match="not") as wrong_old:
        again(other, target, place_refusal=places(pc).refusal)
    report = again(old, target, place_refusal=places(pc).refusal)

    assert (facts["old"], facts["folder"], facts["finished"]) == (str(old), str(target), False)
    assert finished_facts is None, "the start facts do not read as a finished bring-in"
    assert offered.unfinished is not None
    assert offered.unfinished["folder"] == str(target)
    assert offered.unfinished["line"].startswith(
        f"Bringing your old QMX data into {target} did not finish: it stopped while copying."
    )
    assert (offered.found, offered.old, offered.choices) == (
        None,
        str(old),
        ("bring-in", "open", "restore"),
    )
    assert serve.value.code == 3
    assert str(wrong_old.value) == (
        f"{target} holds an unfinished copy of {old}, not of {other}; nothing was cleared"
    )
    assert report.finished, report.text
    assert snapshot(old) == before
    with pytest.raises(Refused, match="holds no unfinished bring-in"):
        again(old, target, place_refusal=places(pc).refusal)


def test_the_host_exits_3_when_a_first_start_is_due_and_2_for_a_folder_it_refuses(
    pc: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    codes: dict[str, object] = {}
    for command in ("serve", "start", "status", "stop"):
        with pytest.raises(SystemExit) as stopped:
            main([command])
        codes[command] = stopped.value.code
    newer = pc / "newer"
    newer.mkdir()
    label = Label("0193aaaa-0000-7000-8000-000000000000", 3, "9.0.0", "9.0.0", min_reader=3)
    (newer / LABEL).write_text(label.dump(), encoding="utf-8")
    first_start.write_pointer(newer)
    capsys.readouterr()
    with pytest.raises(SystemExit) as refused:
        main(["serve"])
    line = capsys.readouterr().err.strip()
    offered = offer(pc / "profile" / ".qmx", places(pc), drives=[]).document()

    assert codes == {"serve": 3, "start": 3, "status": 3, "stop": 3}
    assert refused.value.code == 2
    assert line.startswith(f"{newer} was written by QMX 9.0.0 (folder format 3).")
    assert offered["refused"] == {"folder": str(newer.resolve()), "line": line}
    assert (offered["found"], offered["choices"]) == (None, ["open"])


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters are Windows' own")
def test_the_card_warns_of_a_removable_drive_on_the_default_folder_and_the_chosen_one(
    pc: Path,
) -> None:
    removable = Places(places(pc).environ, drive_type=lambda _root: 2)
    client = card_client(removable, pc / "no-old-folder")
    drive = PureWindowsPath(pc).drive

    card = client.get("/api/first-start").json()
    made = client.post("/api/first-start/new", json={"folder": str(pc / "QMX")}).json()

    warning = f"{drive} is a removable drive: QMX stops working whenever it is unplugged"
    assert (card["warning"], made["warning"]) == (warning, warning)
    assert made["folder"] == str(pc / "QMX")


def stopped_mid_copy(pc: Path, old: Path, target: Path) -> None:
    """A bring-in of `old` into `target` killed at its fifth copy."""
    calls: list[Path] = []

    def killed(source: Path, written: Path) -> str:
        calls.append(source)
        if len(calls) == 5:
            raise KeyboardInterrupt
        return copy_file(source, written)

    with pytest.raises(KeyboardInterrupt):
        bring_in(old, target, place_refusal=places(pc).refusal, copy=killed)


def still_unfinished(pc: Path, target: Path) -> bool:
    """Whether QMX still refuses `target` and the card still offers its bring-in again."""
    offered = offer(pc / "profile" / ".qmx", places(pc), drives=[])
    return (
        old_library(target / "data") is not None
        and offered.unfinished is not None
        and offered.unfinished["folder"] == str(target)
        and offered.found is None
    )


def test_an_again_refused_or_killed_after_its_clear_leaves_the_folder_unfinished(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / "old" / ".qmx", pc)
    target = pc / "profile" / "QMX"
    stopped_mid_copy(pc, old, target)

    def killed_while_clearing(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    with monkeypatch.context() as killing:
        killing.setattr("qmx_host.bring_in.shutil.rmtree", killed_while_clearing)
        with pytest.raises(KeyboardInterrupt):
            again(old, target, place_refusal=places(pc).refusal)
    after_the_kill = still_unfinished(pc, target)

    def ten_megabytes_free(_path: object) -> SimpleNamespace:
        return SimpleNamespace(free=10 << 20)

    with monkeypatch.context() as full:
        full.setattr("qmx_host.bring_in.shutil.disk_usage", ten_megabytes_free)
        with pytest.raises(Refused, match="needs"):
            again(old, target, place_refusal=places(pc).refusal)
    after_the_refusal = still_unfinished(pc, target)
    report = again(old, target, place_refusal=places(pc).refusal)

    assert after_the_refusal, "a refused again leaves the folder unfinished, never empty and his"
    assert after_the_kill, "a kill during the clear leaves the folder unfinished"
    assert report.finished, report.text


def test_a_copy_killed_halfway_leaves_no_partial_file_and_the_next_again_finishes(
    pc: Path,
) -> None:
    old = old_home(pc / "old" / ".qmx", pc)
    before = snapshot(old)
    target = pc / "profile" / "QMX"

    def killed_halfway(source: Path, written: Path) -> str:
        if source.name == "vault.key":
            written.write_bytes(source.read_bytes()[: len(VAULT_KEY) // 2])
            raise KeyboardInterrupt
        return copy_file(source, written)

    with pytest.raises(KeyboardInterrupt):
        bring_in(old, target, place_refusal=places(pc).refusal, copy=killed_halfway)
    partial_at_the_key = (target / "keys" / "vault.key").exists()
    mine = target / "keys" / "my-notes.txt"
    mine.write_text("his own file", encoding="utf-8")

    report = again(old, target, place_refusal=places(pc).refusal)

    assert not partial_at_the_key, "a cut copy never sits at its destination"
    assert report.finished, report.text
    assert (target / "keys" / "vault.key").read_bytes() == VAULT_KEY
    assert mine.read_text(encoding="utf-8") == "his own file", "nothing of his is removed"
    assert not list(target.rglob("*.qmx-copying"))
    assert snapshot(old) == before


def test_a_marker_with_no_facts_is_brought_in_again_not_a_dead_end(pc: Path) -> None:
    old = old_home(pc / "old" / ".qmx", pc)
    copied = pc / "profile" / "QMX"
    stopped_mid_copy(pc, old, copied)
    (copied / "data" / REPORT).unlink()
    marker = resolve(pc / "Marked", create=True, drives=[]).data / UNFINISHED
    marker.parent.mkdir(parents=True)
    marker.write_text("it stopped while copying", encoding="utf-8")
    marked = pc / "Marked"
    other = old_home(pc / "other" / ".qmx", pc / "other")

    with pytest.raises(Refused, match="nothing was cleared"):
        again(other, copied, place_refusal=places(pc).refusal)
    from_the_list = again(old, copied, place_refusal=places(pc).refusal)
    from_nothing_copied = again(old, marked, place_refusal=places(pc).refusal)

    assert from_the_list.finished, "the saved list names the old folder the copy came from"
    assert from_nothing_copied.finished, "a marker alone means nothing was copied yet"


def test_the_card_shows_a_running_bring_in_as_running_not_unfinished(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_host import bring_in as module

    old = old_home(pc / "old" / ".qmx", pc)
    target = pc / "profile" / "QMX"
    client = card_client(places(pc), old)
    copying = threading.Event()
    gate = threading.Event()
    real = module._carry  # pyright: ignore[reportPrivateUsage]

    def held(*args: Any, **kwargs: Any) -> str | None:
        copying.set()
        gate.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(module, "_carry", held)
    job = client.post("/api/first-start/bring-in", json={"folder": str(target)}).json()
    copying.wait(30)
    card = client.get("/api/first-start").json()
    gate.set()
    ended(client, job["id"])

    assert (card["unfinished"], card["running"], card["job"]["state"]) == (
        None,
        str(target),
        "running",
    )


def test_a_handover_waits_for_a_bring_in_that_is_starting(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = old_home(pc / "old" / ".qmx", pc)
    client = card_client(places(pc), old, handed=[])
    assert client.post("/api/first-start/new", json={"folder": str(pc / "Made")}).status_code == 200
    checking = threading.Event()
    gate = threading.Event()
    refusal = first_start._bring_in_refusal  # pyright: ignore[reportPrivateUsage]
    real = first_start.bring_in_old

    def slow_refusal(*args: Any, **kwargs: Any) -> str | None:
        checking.set()
        gate.wait(30)
        return refusal(*args, **kwargs)

    def held_back(*args: Any, **kwargs: Any) -> Report:
        gate.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(first_start, "_bring_in_refusal", slow_refusal)
    monkeypatch.setattr(first_start, "bring_in_old", held_back)
    answers: dict[str, Any] = {}
    posting = threading.Thread(
        target=lambda: answers.setdefault(
            "bring-in", client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")})
        )
    )
    posting.start()
    checking.wait(30)
    handing = threading.Thread(
        target=lambda: answers.setdefault("handover", client.post("/api/first-start/handover"))
    )
    handing.start()
    handing.join(0.5)
    waited = handing.is_alive()
    gate.set()
    posting.join(30)
    handing.join(30)
    ended(client, answers["bring-in"].json()["id"])

    assert waited, "the handover waits while a bring-in is starting"
    assert answers["handover"].status_code == 409
    assert answers["handover"].json()["detail"].startswith("the bring-in (job ")


def test_a_pointer_to_a_folder_that_is_gone_is_refused_not_offered_a_new_one(
    pc: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    old = old_home(pc / "old" / ".qmx", pc)
    usb = pc / "usb" / "QMX"
    assert bring_in_old(old, usb, places(pc)).finished
    (pc / "usb").rename(pc / "unplugged")
    capsys.readouterr()

    with pytest.raises(SystemExit) as serve:
        main(["serve"])
    line = capsys.readouterr().err.strip()
    offered = offer(old, places(pc), drives=[])

    assert serve.value.code == 2
    assert line.startswith(f"the QMX folder {usb.resolve()} is not there")
    assert (offered.choices, offered.refused) == (
        ("open",),
        {"folder": str(usb.resolve()), "line": line},
    )
