"""The first start brings his old QMX data in (design 62 F step 4, guard 5). Every old folder here
is a synthetic old-layout home in pytest's tmp folder; nothing reads his profile, his ~/.qmx, his
browser or his Credential Manager, and the sync roots are the test's own."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import uuid
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.library import UNFINISHED, old_library
from qmx_home import pointer_file
from qmx_library.migrate.from_library_b import JUNK

from qmx_host.__main__ import main
from qmx_host.bring_in import Refused, bring_in, copy_file
from qmx_host.first_start import Places, bring_in_old, first_start_router

VAULT_KEY = b"\x01\x02 test vault key"


def items(db: sqlite3.Connection, home: Path, rows: list[tuple[str, str, str]]) -> None:
    """Library B rows as `library.db` held them (MIGRATION step 2's table): id, kind, title."""
    for item_id, kind, title in rows:
        body = json.dumps({"title": title}, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(body).hexdigest()
        (home / "artifacts" / digest).write_bytes(body)
        data: dict[str, object] = {
            "id": item_id,
            "kind": kind,
            "title": title,
            "tags": [],
            "source": "",
            "created": "2026-10-01T00:00:00+00:00",
            "root_id": item_id,
            "version": 1,
            "previous_id": None,
            "sha256": digest,
            "size": len(body),
            "ref": f"artifacts/{digest}",
            "fetched_date": None,
        }
        db.execute(
            "INSERT INTO items VALUES(?,?,?,?,?,?)",
            (item_id, json.dumps(data), item_id, 1, "", None),
        )


def old_home(at: Path, scratch: Path) -> Path:
    """A flat home in the old layout: the stores a PC host wrote, `library.db` with rows still in
    its `-wal` (taken while a connection held them), the test junk, a vault key, the host log,
    the old lock, and the relayed home's junction to the chats."""
    (at / "artifacts").mkdir(parents=True)
    (at / ".qmx").mkdir()
    (at / ".qmx" / "vault.key").write_bytes(VAULT_KEY)
    (at / "control.db").write_bytes(b"control store bytes")
    (at / "runs.db").write_bytes(b"run index bytes")
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
                    (str(uuid.uuid4()), "article", "Carry paper"),
                    (str(uuid.uuid4()), "backtest", "Rates"),
                    (str(uuid.uuid4()), "backtest", "Momentum"),
                    (JUNK[0], "workflow-result", "remote-flow"),
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
    assert (new / "data" / "control.db").read_bytes() == b"control store bytes"
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
    assert "Your Library: 3 items are in the new Library." in report.lines
    assert (
        "  1 test results named remote-flow, made by test runs and not by you. They stay in your "
        "old folder." in report.lines
    )
    assert "  engine.lock: the old QMX's lock file; QMX makes a new one." in report.lines
    assert (new / "data" / "migration" / "bring-in-report.txt").read_text(
        encoding="utf-8"
    ) == report.text
    pointer = pointer_file()
    assert pointer is not None
    assert f"home = {json.dumps(str(new))}" in pointer.read_text(encoding="utf-8")


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
        if target.name == "runs.db":
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

    assert stopped.value.code == 2
    assert capsys.readouterr().err.strip() == (
        f"{old} holds your old QMX data in the old layout. QMX does not start on it and never "
        "changes it. Bring it into a new QMX folder with the first start: python -m qmx_host "
        f"bring-in --home <new QMX folder> --old {old}"
    )
    assert snapshot(old) == before


def test_the_card_offers_the_bring_in_first_and_answers_each_choice(pc: Path) -> None:
    old = old_home(pc / "profile" / ".qmx", pc)
    onedrive = pc / "OneDrive"
    app = FastAPI()
    app.include_router(
        first_start_router(Places(places(pc).environ, (("OneDrive", onedrive),)), old, drives=[])
    )
    client = TestClient(app)

    card = client.get("/api/first-start").json()
    restore = client.post("/api/first-start/restore")
    refused = client.post("/api/first-start/bring-in", json={"folder": str(onedrive / "QMX")})
    brought = client.post("/api/first-start/bring-in", json={"folder": str(pc / "QMX")})

    assert (card["old"], card["chosen"], card["found"]) == (str(old), "bring-in", None)
    assert card["choices"] == ["bring-in", "new", "open", "restore"]
    assert restore.status_code == 501
    assert refused.status_code == 409
    assert "inside your OneDrive folder" in refused.json()["detail"]
    assert brought.status_code == 200
    assert brought.json()["finished"] is True
    assert client.get("/api/first-start").json()["found"] == str(pc / "QMX")
