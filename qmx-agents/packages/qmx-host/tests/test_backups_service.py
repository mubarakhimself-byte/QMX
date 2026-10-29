"""The host's backup service: its sweep, its incidents and its doctor row (B3)."""

from __future__ import annotations

import dataclasses
import os
import re
import sqlite3
import string
import subprocess
import sys
import time
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.models import Document
from qmx_control.service import ControlService
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_home import Label, Layout, resolve
from qmx_home.backup.plan import NO_SECOND_DRIVE, Proposal
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import carry_on, run_round
from qmx_home.files import hold
from qmx_home.versions import log_line, log_lines

from qmx_host import backups as module
from qmx_host.backups import Backups
from qmx_host.jobs import Job

ZONE = timezone(timedelta(hours=1))
START = datetime(2026, 10, 28, 9, 30, tzinfo=ZONE)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **span: float) -> None:
        self.now += timedelta(**span)


def folder(root: Path, *, files: int = 20, store_rows: int = 200) -> Layout:
    """A labelled QMX folder with plain files and one SQLite store in `data/`."""
    layout = resolve(root, create=True)
    notes = layout.data / "notes"
    notes.mkdir(parents=True)
    for number in range(files):
        (notes / f"{number:04}.txt").write_bytes(os.urandom(2048))
    (layout.data / "engine").mkdir(exist_ok=True)
    with closing(sqlite3.connect(layout.data / "engine" / "engine.sqlite")) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, body BLOB)")
        db.executemany(
            "INSERT INTO events (body) VALUES (?)", [(os.urandom(512),) for _ in range(store_rows)]
        )
        db.commit()
    return layout


def service(layout: Layout, clock: Clock, *, floor: int = 0) -> Backups:
    control = ControlService(layout.home, secret_getter=lambda _service, _name: None)
    return Backups(layout, control, clock=clock, floor=floor)


def proposing(found: Proposal | None) -> Callable[[Layout], Proposal | None]:
    return lambda _layout: found


def target(path: Path, every: str = "1d", place: str = "usb") -> Document:
    """A folder storage: its `[engine]` row and its `[backup]` policy, as `connect` writes them."""
    return {"id": place, "path": str(path), "every": every}


def connect(backups: Backups, *storages: Document) -> None:
    """Each storage as the connect dialog leaves it: one `[engine]` row that can keep, and its
    policy by place id."""
    rows: Document = {
        str(s["id"]): {"id": s["id"], "via": "folder", "can": ["keep"], "path": s["path"]}
        for s in storages
    }
    policies: Document = {str(s["id"]): {"every": s["every"], "at": "03:00"} for s in storages}
    backups.control.settings_put(cast("Any", "engine"), {"placement": rows})
    backups.control.settings_put("backup", {"place": policies})


def ended(backups: Backups, job_id: str) -> Job:
    for _ in range(600):
        found = backups.jobs.get(job_id)
        assert found is not None
        if found.state != "running":
            return found
        time.sleep(0.05)
    raise AssertionError("the job did not end within 30 s")


def finished(backups: Backups, job: Job | None) -> Job:
    """A job once it ended; a round's with the places of each send it started, once each
    ended."""
    assert job is not None, "the sweep started no round"
    found = ended(backups, job.id)
    if found.result is None or "sends" not in found.result:
        return found
    places = list(cast("list[object]", found.result["places"]))
    for send_id in cast("dict[str, str]", found.result["sends"]).values():
        sent = ended(backups, send_id)
        if sent.result is not None:
            places += cast("list[object]", sent.result["places"])
    return dataclasses.replace(found, result={**found.result, "places": places})


def results(job: Job) -> dict[str, str]:
    assert job.state == "finished", job.line
    assert job.result is not None
    places = cast("list[dict[str, object]]", job.result["places"])
    return {str(place["id"]): str(place["result"]) for place in places}


def incident(layout: Layout, place: str) -> tuple[str, int, str] | None:
    with InboxTable.open(layout.home) as inbox:
        found = inbox.open_incident(f"backup:{place}")
    return None if found is None else (found.signature, found.count, found.cause)


def test_the_sweep_runs_a_round_when_the_quick_undo_is_due_and_not_otherwise(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)

    first = finished(backups, backups.sweep())
    assert (first.kind, results(first)) == ("backup", {"quick": "copied"})
    clock.advance(minutes=59)
    assert backups.sweep() is None
    clock.advance(minutes=2)
    assert results(finished(backups, backups.sweep())) == {"quick": "unchanged"}
    assert [line["why"] for line in log_lines(layout) if line["kind"] == "round"] == [
        "round",
        "round",
    ]


def test_with_no_target_only_the_quick_undo_is_written_and_the_proposal_is_shown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    offered = Proposal(tmp_path / "C" / "QMX-backup", "QMX proposes C:\\QMX-backup")
    monkeypatch.setattr(module, "proposal", proposing(offered))
    backups = service(layout, clock)

    finished(backups, backups.sweep())

    assert sorted(p.name for p in tmp_path.iterdir()) == ["QMX"]
    assert sorted(p.name for p in layout.backups.iterdir()) == [
        "backups.jsonl",
        "backups.lock",
        "quick",
    ]
    view = backups.view()
    assert (view["line"], view["proposal"]) == (
        NO_SECOND_DRIVE,
        {"path": str(offered.path), "line": "QMX proposes C:\\QMX-backup"},
    )
    row = backups.doctor_line()
    assert not row.ok
    assert row.detail.endswith(f"; {NO_SECOND_DRIVE}; QMX proposes C:\\QMX-backup")


def test_accepting_the_proposal_writes_one_target_row_and_the_next_round_sends_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    drive = tmp_path / "C" / "QMX-backup"
    monkeypatch.setattr(module, "proposal", proposing(Proposal(drive, "proposed")))
    backups = service(layout, clock)

    accepted = backups.accept()

    assert backups.control.settings_get(cast("Any", "engine")) == {
        "placement": {
            "second-drive": {
                "id": "second-drive",
                "via": "folder",
                "can": ["keep"],
                "path": str(drive),
            }
        }
    }
    assert accepted["line"] == (
        f"QMX copies your work to {drive} every day at 03:00; the first copy is made at the "
        "next round, within a few minutes"
    )
    assert results(finished(backups, backups.sweep())) == {
        "quick": "copied",
        "second-drive": "copied",
    }
    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    assert len(list((drive / home_id / "snapshots").iterdir())) == 1
    assert backups.doctor_line().ok


def test_a_full_target_opens_one_incident_that_the_next_copy_there_resolves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    usb = tmp_path / "usb"
    backups = service(layout, clock)
    connect(backups, target(usb, "1h"))
    room = FolderRepository.room

    def full(repo: FolderRepository) -> int | None:
        return 0 if usb in repo.root.parents else room(repo)

    monkeypatch.setattr(FolderRepository, "room", full)

    assert results(finished(backups, backups.sweep())) == {"quick": "copied", "usb": "refused"}
    first = incident(layout, "usb")
    assert first is not None
    assert first[:2] == ("refused", 1)
    assert re.search(r"has 0\.0 MB free; QMX keeps at least [\d,]+ MB free there", first[2])
    assert not backups.doctor_line().ok
    clock.advance(minutes=61)
    finished(backups, backups.sweep())
    assert incident(layout, "usb") == first

    monkeypatch.setattr(FolderRepository, "room", room)
    clock.advance(minutes=61)
    assert results(finished(backups, backups.sweep()))["usb"] == "copied"
    assert incident(layout, "usb") is None
    assert backups.doctor_line().ok


@pytest.mark.skipif(os.name != "nt", reason="an unplugged disk is a drive letter that is not there")
def test_an_unplugged_target_opens_its_incident_only_after_seven_intervals_with_no_copy(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    letter = next(c for c in reversed(string.ascii_uppercase) if not Path(f"{c}:\\").exists())
    backups = service(layout, clock)
    connect(backups, target(Path(f"{letter}:\\usb"), "1h"))

    for _hour in range(7):
        assert results(finished(backups, backups.sweep())) == {"quick": "copied", "usb": "skipped"}
        assert incident(layout, "usb") is None
        (layout.data / "notes" / "0000.txt").write_bytes(os.urandom(2048))
        clock.advance(minutes=61)
    finished(backups, backups.sweep())

    found = incident(layout, "usb")
    assert found is not None
    assert found[:2] == ("away", 1)
    assert found[2].startswith(f"{letter}:\\usb\\QMX-backup\\")
    assert "has had no copy for 7 hours: " in found[2]
    assert "is not there (is its drive plugged in?)" in found[2]


def test_a_copy_that_lacks_files_or_could_not_read_one_opens_its_incident_naming_them(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    usb = tmp_path / "usb"
    backups = service(layout, clock)
    connect(backups, target(usb))
    finished(backups, backups.sweep())
    key = cast("list[dict[str, object]]", log_lines(layout)[-1]["places"])[0]["key"]

    def logged(result: str, line: str, *, partial: bool) -> None:
        clock.advance(minutes=5)
        stamp = clock.now.astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        place = {"id": "usb", "key": key, "result": result, "line": line, "partial": partial}
        log_line(layout, {"kind": "round", "stamp": stamp, "places": [{**place, "stamp": stamp}]})
        assert backups.sweep() is None

    logged("copied", "copied 2 files; this copy lacks 1 file: notes/0003.txt", partial=True)
    assert incident(layout, "usb") == (
        "partial",
        1,
        "copied 2 files; this copy lacks 1 file: notes/0003.txt",
    )
    logged(
        "refused", "the copy stopped: Data error (D:\\QMX\\data\\notes\\0004.txt)", partial=False
    )
    assert incident(layout, "usb") == (
        "refused",
        1,
        "the copy stopped: Data error (D:\\QMX\\data\\notes\\0004.txt)",
    )
    logged("copied", "copied 1 file", partial=False)
    assert incident(layout, "usb") is None


def test_settings_it_cannot_read_open_the_settings_incident_until_they_are_fixed(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    settings = layout.home / "settings.toml"
    settings.write_text('[backup]\non = "yes"\n', encoding="utf-8")

    assert backups.sweep() is None
    assert incident(layout, "settings") == ("refused", 1, "[backup] on must be true or false")
    assert not backups.doctor_line().ok

    settings.write_text("", encoding="utf-8")
    finished(backups, backups.sweep())
    assert incident(layout, "settings") is None


def test_the_doctor_row_names_each_places_age_and_size_and_a_quick_undo_without_room(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    usb = tmp_path / "usb"
    backups = service(layout, clock)
    connect(backups, target(usb, "1h"))
    finished(backups, backups.sweep())
    clock.advance(hours=2, minutes=5)
    size = sum(p.stat().st_size for p in (layout.backups / "quick").rglob("*") if p.is_file())
    where = usb / "QMX-backup" / os.listdir(usb / "QMX-backup")[0]

    row = backups.doctor_line()

    assert (row.name, row.ok) == ("backups", True)
    assert row.detail == (
        f"This PC's copies: newest whole copy from 2 hours ago, {size / (1 << 20):,.1f} MB in "
        "all, a copy every 1h when something changed, kept 48 hours, 7 days; "
        f"usb ({where}): newest whole copy from 2 hours ago"
    )

    starved = service(layout, clock, floor=1 << 60)
    finished(starved, starved.sweep())
    clock.advance(minutes=1)
    assert starved.sweep() is None
    row = starved.doctor_line()
    assert not row.ok
    assert f"; the last round made no copy, so none went to {usb} either" in row.detail
    assert "This PC's copies: newest whole copy from 2 hours ago" in row.detail


def test_the_command_runs_one_round_exits_1_while_a_round_holds_the_lock_and_never_loads_the_host(
    tmp_path: Path,
) -> None:
    layout = folder(tmp_path / "QMX")
    script = (
        "import sys\n"
        "from qmx_host.__main__ import main\n"
        "code = main(sys.argv[1:])\n"
        "print('host loaded' if 'qmx_host.host' in sys.modules else 'host not loaded')\n"
        "raise SystemExit(code)\n"
    )
    command = [sys.executable, "-c", script, "backup", "--home", str(layout.root)]
    environment = {k: v for k, v in os.environ.items() if k != "QMX_HOME"}

    ran = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.splitlines()[0].startswith("copied ")
    assert ran.stdout.splitlines()[-1] == "host not loaded"

    with hold(layout.backups / "backups.lock", "busy"):
        held = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
    assert held.returncode == 1
    assert held.stderr.strip() == (
        f"refused: a backup round is already running for {layout.root}; it ends by itself"
    )
    assert held.stdout.strip() == "host not loaded"

    again = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
    assert again.returncode == 0
    assert again.stdout.splitlines()[0].startswith("nothing changed since the last copy")


def test_a_round_another_folder_sent_to_the_target_is_refused_until_he_carries_on(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    usb = tmp_path / "usb"
    backups = service(layout, clock)
    connect(backups, target(usb, "1h"))
    finished(backups, backups.sweep())
    twin = folder(tmp_path / "twin")
    twin.label.write_bytes(layout.label.read_bytes())
    carry_on(twin, backups.plan().sending[0])
    sent = run_round(twin, backups.plan(), now=clock.now + timedelta(minutes=1), floor=0)
    assert [place.result for place in sent.places] == ["copied", "copied"]

    clock.advance(minutes=61)
    assert results(finished(backups, backups.sweep()))["usb"] == "refused"
    assert incident(layout, "usb") is not None
    clock.advance(minutes=1)
    assert backups.sweep() is None

    backups.carry_on("usb")
    assert results(finished(backups, backups.sweep()))["usb"] == "copied"
    assert incident(layout, "usb") is None


def test_a_round_that_stops_with_an_unexpected_error_is_logged_raised_and_tried_an_hour_later(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    connect(backups, target(tmp_path / "usb"))

    def denied(*_args: object, **_kwargs: object) -> object:
        raise PermissionError(13, "Permission denied", "D:/QMX/data/notes")

    monkeypatch.setattr("qmx_home.backup.round.make", denied)

    stopped = finished(backups, backups.sweep())

    line = (
        "the round stopped with an error: PermissionError: [Errno 13] Permission denied: "
        "'D:/QMX/data/notes'; QMX tries again in an hour"
    )
    assert (stopped.state, stopped.line) == ("stopped", line)
    places = cast("list[dict[str, object]]", log_lines(layout)[-1]["places"])
    assert [(p["id"], p["result"]) for p in places] == [("quick", "refused"), ("usb", "skipped")]
    assert incident(layout, "quick") == ("refused", 1, line)
    clock.advance(minutes=1)
    assert backups.sweep() is None

    monkeypatch.undo()
    clock.advance(minutes=60)
    assert results(finished(backups, backups.sweep())) == {"quick": "copied"}
    assert incident(layout, "quick") is None


def test_after_a_restart_the_incident_of_a_place_no_longer_in_settings_is_resolved_saying_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    usb = tmp_path / "usb"
    backups = service(layout, clock)
    connect(backups, target(usb))
    room = FolderRepository.room

    def full(repo: FolderRepository) -> int | None:
        return 0 if usb in repo.root.parents else room(repo)

    monkeypatch.setattr(FolderRepository, "room", full)
    assert results(finished(backups, backups.sweep()))["usb"] == "refused"
    assert incident(layout, "usb") is not None
    backups.control.settings_put(cast("Any", "engine"), {"remove": ["placement.usb"]})

    restarted = service(layout, clock)
    clock.advance(minutes=5)
    restarted.sweep()

    with InboxTable.open(layout.home) as inbox:
        rows = inbox.connection.execute(
            "SELECT trigger_id, cause, resolved_at IS NOT NULL FROM incidents"
            " WHERE trigger_id = 'backup:usb'"
        ).fetchall()
    assert rows == [
        (
            "backup:usb",
            "the backup place usb is no longer in Settings, so QMX no longer copies there",
            1,
        )
    ]
