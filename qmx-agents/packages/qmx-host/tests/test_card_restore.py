"""The first-start card restores a copy (design 62 F step 2, C3 and B4; plan B4). Every folder,
backup place and profile is in pytest's tmp folder; no host, browser, Credential Manager or pg0 is
started."""

from __future__ import annotations

import platform
import sqlite3
import sys
import threading
import time
import tomllib
import uuid
from collections.abc import Iterator, Mapping
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_engine.ledger.store import Ledger
from qmx_home import LABEL, RESTORE_UNFINISHED, Label, Layout, pointer_file, resolve
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan, Storage
from qmx_home.backup.repository import FolderRepository, Manifest
from qmx_home.backup.round import run_round
from test_bring_in import old_home

from qmx_host import first_start
from qmx_host.__main__ import main
from qmx_host.bring_in import Report
from qmx_host.first_start import Places, first_start_router, offer

BEFORE = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
COPY_AT = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
AFTER = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)


@pytest.fixture
def pc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    profile = tmp_path / "profile"
    for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (profile / part).mkdir(parents=True)
        monkeypatch.setenv(name, str(profile / part))
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("HOME", str(profile))
    monkeypatch.delenv("QMX_HOME", raising=False)
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    monkeypatch.setattr(first_start, "_fixed_drives", list)
    yield tmp_path


def places(pc: Path, **kind: Any) -> Places:
    return Places({"APPDATA": str(pc / "profile" / "Roaming")}, **kind)


def removable(_root: str) -> int:
    return 2


def runs(layout: Layout, count: int, at: datetime) -> None:
    with Ledger.open(layout.home) as ledger:
        for _ in range(count):
            ledger.append(
                f"run-{uuid.uuid4()}", "run_created", {"workflow": "w"}, at=at.isoformat()
            )


def folder(root: Path) -> Layout:
    """A labelled QMX folder with five notes and a run ledger holding one run."""
    layout = resolve(root, create=True)
    notes = layout.data / "notes"
    notes.mkdir(parents=True)
    for number in range(5):
        (notes / f"{number}.txt").write_text(f"note {number}", encoding="utf-8")
    runs(layout, 1, BEFORE)
    return layout


def sent(layout: Layout, usb: Path, now: datetime = COPY_AT) -> str:
    """A round to a folder target at `usb`; the copy's stamp there."""
    report = run_round(
        layout, Plan(storages=(Storage("usb", "usb", "folder", usb),)), now=now, floor=0
    )
    stamp = report.places[1].stamp
    assert stamp is not None, report.lines
    return stamp


def source(usb: Path) -> dict[str, str]:
    return {"kind": "folder", "path": str(usb)}


def notes(layout: Layout) -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in (layout.data / "notes").iterdir()}


def home_id(root: Path) -> str:
    return Label.parse((root / LABEL).read_text(encoding="utf-8")).home_id


def pointed() -> Path | None:
    """The folder the pointer file names, or None."""
    pointer = pointer_file()
    if pointer is None or not pointer.is_file():
        return None
    return Path(tomllib.loads(pointer.read_text(encoding="utf-8"))["home"])


def card(pc: Path, place: Places | None = None, handed: list[Path] | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(
        first_start_router(
            place or places(pc),
            pc / "no-old",
            drives=[],
            port=8799,
            on_handover=None if handed is None else handed.append,
        )
    )
    return TestClient(app)


def ended(client: TestClient, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        job = client.get(f"/api/first-start/jobs/{job_id}").json()
        if job["state"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} still running")


def restored(client: TestClient, body: Mapping[str, object]) -> dict[str, Any]:
    asked = client.post("/api/first-start/restore", json={**body, "confirmed": True})
    assert asked.status_code == 202, asked.text
    return ended(client, asked.json()["id"])


def test_the_card_lists_a_places_copies_and_says_what_each_restore_replaces(pc: Path) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    runs(layout, 2, AFTER)
    place = FolderRepository(usb / "QMX-backup" / home_id(layout.root))
    held = place.manifest(stamp)
    partial = "20261027T040000000000Z"
    place.put_copy(
        Manifest(
            {**held.header, "stamp": partial, "partial": True, "unread": ["notes/4.txt (denied)"]},
            tuple(e for e in held.entries if e.path != "notes/4.txt"),
        )
    )
    client = card(pc)

    listed = client.post("/api/first-start/copies", json={"source": source(usb)})
    here = client.post(
        "/api/first-start/restore/check",
        json={"folder": str(layout.root), "source": source(usb), "copy": stamp},
    )
    new = client.post(
        "/api/first-start/restore/check",
        json={"folder": str(pc / "New"), "source": source(usb), "copy": partial},
    )
    nowhere = client.post("/api/first-start/copies", json={"source": source(pc / "empty")})

    copies = listed.json()["copies"]
    assert [(c["stamp"], c["why"], c["files"], c["partial"], c["lacks"]) for c in copies] == [
        (partial, "round", len(held.entries) - 1, True, ["notes/4.txt (denied)"]),
        (stamp, "round", len(held.entries), False, []),
    ]
    assert here.json()["newer"] == {"runs": 2, "ref_moves": 0, "chats": 0, "price_months": 0}
    assert here.json()["line"] == (
        f"Restoring the copy {stamp} into {layout.root} replaces what the folder holds now: since "
        "this copy the folder holds 2 runs started, 0 Library saves, 0 chats and 0 price months. "
        f"The folder's data is set aside whole in {layout.backups} first."
    )
    assert (new.json()["new"], new.json()["line"]) == (
        True,
        f"Restoring the copy {partial} makes a new QMX folder at {pc / 'New'} from it. This copy "
        "is partial: it lacks notes/4.txt (denied).",
    )
    assert not (pc / "New").exists(), "a check writes nothing"
    assert (nowhere.status_code, nowhere.json()["detail"]) == (
        409,
        f"{pc / 'empty'} holds no QMX copies",
    )


def test_a_restore_into_a_new_folder_takes_the_copys_home_id_and_is_handed_over(
    pc: Path,
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    handed: list[Path] = []
    client = card(pc, handed=handed)
    body = {"folder": str(pc / "New"), "source": source(usb), "copy": stamp}

    unconfirmed = client.post("/api/first-start/restore", json=body)
    loosely = client.post("/api/first-start/restore", json={**body, "confirmed": "yes"})
    before = (pc / "New").exists()
    job = restored(client, body)
    handover = client.post("/api/first-start/handover")

    new = resolve(pc / "New")
    assert (unconfirmed.status_code, unconfirmed.json()["detail"]) == (
        400,
        "a restore needs confirmed: true, after you saw what it replaces; nothing was changed",
    )
    assert loosely.status_code == 422
    assert not before, "an unconfirmed restore writes nothing"
    assert job["state"] == "finished", job["line"]
    assert job["result"]["folder"] == str(new.root)
    assert job["result"]["line"].startswith(f"QMX restored the copy {stamp} from ")
    assert home_id(new.root) == home_id(layout.root)
    assert notes(new) == notes(layout)
    assert not (new.data / RESTORE_UNFINISHED).exists()
    assert pointed() == new.root
    assert handover.json() == {"folder": str(new.root), "port": 8799}
    assert handed == [new.root]


def test_a_restore_that_fails_leaves_the_new_folder_marked_unpointed_and_offered_again(
    pc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    place = FolderRepository(usb / "QMX-backup" / home_id(layout.root))
    note = next(e for e in place.manifest(stamp).entries if e.path == "notes/0.txt")
    place.local_pack(place.index().good(note.sha256)[0].pack).unlink()
    client = card(pc)
    default = pc / "profile" / "QMX"
    body = {"folder": str(default), "source": source(usb), "copy": stamp}

    failed = restored(client, body)
    after_failure = pointed()
    offered = offer(pc / "no-old", places(pc), drives=[]).document()
    capsys.readouterr()
    with pytest.raises(SystemExit) as serve:
        main(["serve", "--home", str(default)])
    said = capsys.readouterr().err
    sent(layout, usb, AFTER)
    again = restored(client, body)

    new = default.resolve()
    assert failed["state"] == "stopped"
    assert failed["line"].startswith(f"the copy {stamp} in {place.where} lacks ")
    assert after_failure is None, "no pointer to a folder whose restore failed"
    assert offered["restore_unfinished"] == {
        "folder": str(new),
        "line": f"Restoring a copy into {new} did not finish. Restore it again into the same "
        "folder; nothing of yours was in it.",
    }
    assert offered["choices"] == ["restore", "open"]
    assert serve.value.code == 3
    assert said == (
        f"QMX did not start: restoring a copy into {new} did not finish. Start the first start "
        "and restore it again into the same folder.\n"
    )
    assert again["state"] == "finished", again["line"]
    assert not (new / "data" / RESTORE_UNFINISHED).exists()
    assert pointed() == new


def test_a_new_folder_whose_restore_staged_but_never_finished_is_restored_again(
    pc: Path,
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    place = FolderRepository(usb / "QMX-backup" / home_id(layout.root))
    new = first_start.restore_into(pc / "New", places(pc), make=True).layout
    restore.stage(new, place, stamp, replace=True, keep_free=0)

    job = restored(card(pc), {"folder": str(new.root), "source": source(usb), "copy": stamp})

    assert job["state"] == "finished", job["line"]
    assert notes(new) == notes(layout)
    assert not (new.backups / "restore.json").exists()
    assert pointed() == new.root


def test_a_folder_refused_for_a_newer_format_is_offered_the_restore_and_opens_after_it(
    pc: Path,
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    first_start.write_pointer(layout.root)
    newer = Label(home_id(layout.root), 3, "9.0.0", "9.0.0", min_reader=3)
    layout.label.write_text(newer.dump(), encoding="utf-8")
    client = card(pc)

    shown = client.get("/api/first-start").json()
    job = restored(client, {"folder": str(layout.root), "source": source(usb), "copy": stamp})

    assert (shown["refused"]["folder"], shown["choices"]) == (str(layout.root), ["open", "restore"])
    assert "or restore a copy from before the upgrade" in shown["refused"]["line"]
    assert job["state"] == "finished", job["line"]
    assert resolve(layout.root).root == layout.root
    assert notes(layout) == {f"{n}.txt": f"note {n}" for n in range(5)}


def test_a_folder_with_a_refused_store_is_offered_the_restore(pc: Path) -> None:
    layout = folder(pc / "QMX")
    first_start.write_pointer(layout.root)
    with closing(sqlite3.connect(layout.data / "engine" / "engine.sqlite")) as db:
        db.execute("PRAGMA user_version = 99")
        db.execute("UPDATE meta SET value = '99' WHERE key = 'min_reader'")
        db.commit()

    shown = offer(pc / "no-old", places(pc), drives=[])

    assert (shown.found, shown.choices) == (None, ("open", "restore"))
    assert shown.refused is not None
    assert shown.refused["folder"] == str(layout.root)
    assert str(shown.refused["line"]).endswith(
        "Install that QMX, or restore a copy from before the upgrade, with Restore from a backup "
        f"on the start screen or python -m qmx_host restore --home {layout.root} --from "
        f"{layout.backups / 'quick'}."
    )


def test_another_folders_copy_is_409_by_name_and_restores_with_replace(pc: Path) -> None:
    mine, theirs, usb = folder(pc / "QMX"), folder(pc / "Other"), pc / "usb"
    (theirs.data / "notes" / "0.txt").write_text("theirs", encoding="utf-8")
    stamp = sent(theirs, usb)
    before = notes(mine)
    client = card(pc)
    body = {
        "folder": str(mine.root),
        "source": {**source(usb), "home_id": home_id(theirs.root)},
        "copy": stamp,
    }

    refused = client.post("/api/first-start/restore", json={**body, "confirmed": True})
    untouched = sorted(p.name for p in mine.backups.iterdir())
    job = restored(client, {**body, "replace": True})

    assert refused.status_code == 409
    assert refused.json()["detail"] == (
        f"the copy {stamp} in {usb / 'QMX-backup' / home_id(theirs.root)} is of another QMX "
        f"folder ({theirs.root} on {platform.node()}), not of {mine.root}. Choose replace to "
        "restore it here: this folder's data is set aside whole first"
    )
    assert untouched == [], "nothing was written before the refusal"
    assert job["state"] == "finished", job["line"]
    assert notes(mine)["0.txt"] == "theirs"
    assert home_id(mine.root) == home_id(theirs.root)
    (aside,) = mine.backups.glob("before-restore-*")
    set_aside = {
        p.name: p.read_text(encoding="utf-8") for p in (aside / "data" / "notes").iterdir()
    }
    assert set_aside == before


def test_a_host_on_the_folder_or_a_running_restore_is_409_by_name(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    me = psutil.Process()
    record = layout.data / "control-process.json"
    record.write_text(f'{{"pid": {me.pid}, "created": {me.create_time()}}}', encoding="utf-8")
    client = card(pc)
    body = {"folder": str(layout.root), "source": source(usb), "copy": stamp, "confirmed": True}

    hosted = client.post("/api/first-start/restore", json=body)
    record.unlink()
    gate, entered = threading.Event(), threading.Event()
    staging = first_start.stage

    def held(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        gate.wait(30)
        return staging(*args, **kwargs)

    monkeypatch.setattr(first_start, "stage", held)
    first = client.post("/api/first-start/restore", json={**body, "folder": str(pc / "New")})
    assert entered.wait(30)
    second = client.post("/api/first-start/restore", json=body)
    bring = client.post("/api/first-start/bring-in", json={"folder": str(pc / "Other")})
    handover = client.post("/api/first-start/handover")
    shown = client.get("/api/first-start").json()
    gate.set()
    done = ended(client, first.json()["id"])

    job = first.json()["id"]
    assert (hosted.status_code, hosted.json()["detail"]) == (
        409,
        f"QMX is running on {layout.root} (PID {me.pid}); close it, then restore",
    )
    assert (second.status_code, second.json()["detail"]) == (
        409,
        f"a restore is already running (job {job}); wait for it to end",
    )
    assert (bring.status_code, bring.json()["detail"]) == (
        409,
        f"a restore is already running (job {job}); wait for it to end",
    )
    assert (handover.status_code, handover.json()["detail"]) == (
        409,
        f"the restore (job {job}) is still running",
    )
    assert (shown["running"], shown["job"]["kind"]) == (str((pc / "New").resolve()), "restore")
    assert done["state"] == "finished", done["line"]


def test_the_card_reads_no_store_of_the_folder_while_its_restore_runs(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    first_start.write_pointer(layout.root)
    read: list[Path] = []
    checking, finishing = first_start.check_open, first_start.finish
    gate, entered = threading.Event(), threading.Event()

    def counted(at: Layout) -> Any:
        read.append(at.root)
        return checking(at)

    def held(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        gate.wait(30)
        return finishing(*args, **kwargs)

    monkeypatch.setattr(first_start, "check_open", counted)
    monkeypatch.setattr(first_start, "finish", held)
    client = card(pc)
    body = {"folder": str(layout.root), "source": source(usb), "copy": stamp, "confirmed": True}

    asked = client.post("/api/first-start/restore", json=body)
    assert entered.wait(30)
    before = len(read)
    shown = client.get("/api/first-start").json()
    during = len(read) - before
    gate.set()
    job = ended(client, asked.json()["id"])

    assert during == 0, "the card read the folder's stores while its restore ran"
    assert (shown["found"], shown["running"]) == (str(layout.root), str(layout.root))
    assert job["state"] == "finished", job["line"]


def test_a_restore_while_a_bring_in_runs_is_409_naming_it(
    pc: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    old = old_home(pc / ".qmx", pc)
    gate = threading.Event()
    real = first_start.bring_in_old

    def held_back(*args: Any, **kwargs: Any) -> Report:
        gate.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(first_start, "bring_in_old", held_back)
    app = FastAPI()
    app.include_router(first_start_router(places(pc), old, drives=[], port=8799))
    client = TestClient(app)
    body = {"folder": str(pc / "New"), "source": source(usb), "copy": stamp, "confirmed": True}

    running = client.post("/api/first-start/bring-in", json={"folder": str(pc / "Brought")}).json()
    refused = client.post("/api/first-start/restore", json=body)
    gate.set()
    brought = ended(client, running["id"])

    assert (refused.status_code, refused.json()["detail"]) == (
        409,
        f"a bring-in is already running (job {running['id']}); wait for it to end",
    )
    assert not (pc / "New").exists()
    assert brought["state"] == "finished", brought["line"]


def test_a_never_place_is_refused_and_a_removable_drive_is_warned(pc: Path) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    inside = pc / "profile" / "Roaming" / "QMX folder"
    client = card(pc, places(pc, drive_type=removable))
    body = {"source": source(usb), "copy": stamp, "confirmed": True}

    never = client.post("/api/first-start/restore", json={**body, "folder": str(inside)})
    usb_drive = client.post("/api/first-start/restore", json={**body, "folder": str(pc / "New")})
    job = ended(client, usb_drive.json()["id"])

    assert never.status_code == 409
    assert never.json()["detail"] == (
        f"{inside} is inside Windows' app folder AppData\\Roaming ({pc / 'profile' / 'Roaming'}), "
        "where a QMX folder never goes: an uninstall or an app package can empty it. Pick "
        "another folder"
    )
    assert not inside.exists()
    if sys.platform == "win32":
        assert usb_drive.json()["warning"] == (
            f"{pc.drive} is a removable drive: QMX stops working whenever it is unplugged"
        )
    assert job["state"] == "finished", job["line"]
