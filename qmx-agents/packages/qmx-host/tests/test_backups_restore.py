"""A restore from Settings (B5): checked, then staged as a job while the host answers, refused or
cancelled with its line, and the drill once a month on each place in turn."""

from __future__ import annotations

import hashlib
import re
import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from qmx_control.models import Document
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_home import Layout
from qmx_home.backup import restore as restoring
from test_backups_routes import BEARER, app_of, ended, held_rounds
from test_backups_service import Clock, connect, finished, folder, service, target

from qmx_host.backups import Backups

ASIDE = re.compile(r"backups/before-restore-\d{8}T\d{12}Z")


def clock_now() -> Clock:
    """A clock at the wall's time, since the log stamps its own lines with it."""
    clock = Clock()
    clock.now = datetime.now().astimezone() - timedelta(minutes=5)
    return clock


def copied(tmp_path: Path) -> tuple[Layout, Backups, Clock, str]:
    """A folder with one whole copy at the place `usb`, and that copy's date."""
    layout, clock = folder(tmp_path / "QMX"), clock_now()
    backups = service(layout, clock)
    connect(backups, target(tmp_path / "usb"))
    assert finished(backups, backups.start("usb", asked=True).job).state == "finished"
    (stamp,) = [c["stamp"] for c in backups.copies("usb")]
    return layout, backups, clock, str(stamp)


def digest(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def test_the_check_counts_what_a_copy_replaces_and_a_confirmed_restore_is_a_job_naming_the_restart(
    tmp_path: Path,
) -> None:
    layout, backups, _clock, stamp = copied(tmp_path)
    (layout.data / "chats").mkdir()
    (layout.data / "chats" / "since.json").write_text("{}", encoding="utf-8")
    body = {"target": "usb", "copy": stamp}

    with TestClient(app_of(backups)) as rest:
        check = rest.post("/api/backups/restore/check", headers=BEARER, json=body)
        unconfirmed = rest.post("/api/backups/restore", headers=BEARER, json=body)
        staged = rest.post("/api/backups/restore", headers=BEARER, json={**body, "confirmed": True})
        job = ended(rest, str(staged.json()["id"]))
        view = rest.get("/api/backups", headers=BEARER).json()

    result = cast("dict[str, object]", job["result"])
    aside = str(result["aside"])
    assert check.status_code == 200
    assert check.json()["newer"] == {"runs": 0, "ref_moves": 0, "chats": 1, "price_months": 0}
    assert check.json()["line"] == (
        "since this copy the folder holds 0 runs started, 0 Library saves, 1 chat and 0 price "
        f"months; restoring the copy {stamp} sets the folder's data aside whole in "
        f"{layout.backups} first, and QMX finishes the restore when it next starts"
    )
    assert (unconfirmed.status_code, unconfirmed.json()) == (
        400,
        {
            "detail": "a restore replaces this folder's data, so it needs confirmed: true, sent "
            "once you have seen what it replaces (POST /api/backups/restore/check)"
        },
    )
    assert (staged.status_code, staged.json()["kind"]) == (202, "restore")
    assert ASIDE.fullmatch(aside), aside
    assert (job["state"], result["restart"], result["line"]) == (
        "finished",
        True,
        f"Restart QMX to finish the restore; the work it replaces is set aside in {aside}",
    )
    assert view["restore"]["staged"] == {
        "copy": stamp,
        "where": check.json()["where"],
        "aside": aside,
        "finishing": False,
    }
    assert (layout.backups / f"restoring-{stamp}" / "data" / "notes" / "0000.txt").is_file()


def test_a_stage_during_a_round_a_second_stage_and_a_cancel_each_answer_with_their_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, backups, _clock, stamp = copied(tmp_path)
    before = digest(layout.data / "notes")
    body = {"target": "usb", "copy": stamp, "confirmed": True}

    with TestClient(app_of(backups)) as rest:
        nothing = rest.post("/api/backups/restore/cancel", headers=BEARER)
        where = rest.post(
            "/api/backups/restore/check", headers=BEARER, json={"target": "usb", "copy": stamp}
        ).json()["where"]
        with held_rounds(monkeypatch) as go:
            round_job = backups.start(None, asked=True).job
            during_round = rest.post("/api/backups/restore", headers=BEARER, json=body)
            go.set()
            finished(backups, round_job)
        first = rest.post("/api/backups/restore", headers=BEARER, json=body)
        assert ended(rest, str(first.json()["id"]))["state"] == "finished"
        second = rest.post("/api/backups/restore", headers=BEARER, json=body)
        cancelled = rest.post("/api/backups/restore/cancel", headers=BEARER)
        view = rest.get("/api/backups", headers=BEARER).json()

    assert (nothing.status_code, nothing.json()) == (
        404,
        {"detail": f"no restore is staged for {layout.root}"},
    )
    assert (during_round.status_code, during_round.json()) == (
        409,
        {
            "detail": f"a backup round is already running (job {round_job.id}, you started it); "
            "it ends by itself, then ask again"
        },
    )
    assert (second.status_code, second.json()) == (
        409,
        {
            "detail": f"a restore of the copy {stamp} from {where} is staged and waits; QMX "
            f"finishes it when {layout.root} next starts, or cancel it first"
        },
    )
    assert (cancelled.status_code, cancelled.json()) == (
        200,
        {
            "line": f"the restore of the copy {stamp} from {where} is cancelled; nothing in "
            f"{layout.root} changed"
        },
    )
    assert not (layout.backups / f"restoring-{stamp}").exists()
    assert not (layout.backups / "restore.json").exists()
    assert view["restore"]["staged"] is None
    assert digest(layout.data / "notes") == before


def test_a_round_while_a_restore_stages_waits_for_the_next_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _layout, backups, clock, stamp = copied(tmp_path)
    go, real = threading.Event(), restoring.stage

    def waiting(*args: object, **kwargs: object) -> object:
        go.wait(30)
        return cast("Callable[..., object]", real)(*args, **kwargs)

    monkeypatch.setattr(restoring, "stage", waiting)
    with TestClient(app_of(backups)) as rest:
        staged = rest.post(
            "/api/backups/restore",
            headers=BEARER,
            json={"target": "usb", "copy": stamp, "confirmed": True},
        ).json()
        clock.advance(hours=2)
        swept = backups.sweep()
        asked = rest.post("/api/backups/run", headers=BEARER)
        go.set()
        assert ended(rest, str(staged["id"]))["state"] == "finished"
        after = backups.sweep()

    assert swept is None
    assert (asked.status_code, asked.json()) == (
        409,
        {
            "detail": f"a restore is being staged (job {staged['id']}); it ends by itself, then "
            "ask again"
        },
    )
    assert after is not None
    assert finished(backups, after).kind == "backup"


def test_the_restore_routes_need_the_bearer_and_a_body_that_is_not_json_is_400(
    tmp_path: Path,
) -> None:
    backups = service(folder(tmp_path / "QMX"), clock_now())
    routes = ("check", "", "cancel", "carry-on")
    with TestClient(app_of(backups)) as rest:
        answers = [rest.post(f"/api/backups/restore/{r}".rstrip("/")).status_code for r in routes]
        bad = rest.post(
            "/api/backups/restore/check",
            headers={**BEARER, "Content-Type": "application/json"},
            content=b"{not json",
        )
        nothing = rest.post("/api/backups/restore/carry-on", headers=BEARER)

    assert answers == [401] * 4
    assert (bad.status_code, bad.json()) == (
        400,
        {"detail": "send the backup place and the copy's date as {target, copy}"},
    )
    assert (nothing.status_code, nothing.json()["detail"]) == (
        404,
        f"no restore of {backups.layout.root} waits for you to carry on; server sync and fires "
        "already run",
    )


def damage(place: Path) -> int:
    """Overwrite the start of every pack at a place; how many."""
    damaged = 0
    for path in place.rglob("*.pack"):
        path.write_bytes(b"damaged" + path.read_bytes()[7:])
        damaged += 1
    return damaged


def test_the_drill_runs_once_a_month_on_each_place_in_turn_and_a_failed_one_opens_an_incident(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), clock_now()
    backups = service(layout, clock)
    places: list[Document] = [
        target(tmp_path / "one", place="one"),
        target(tmp_path / "two", place="two"),
    ]
    connect(backups, *places)
    assert finished(backups, backups.sweep()).kind == "backup"
    assert backups.sweep() is None, "the first copy is not a month old"

    drilled: list[tuple[str, object, object]] = []
    for _ in range(3):
        if len(drilled) == 2:
            assert damage(tmp_path / "one") > 0
        clock.advance(days=31)
        assert finished(backups, backups.sweep()).kind == "backup"
        job = finished(backups, backups.sweep())
        assert job.result is not None
        drilled.append((job.kind, job.result["place"], job.result["passed"]))
    with InboxTable.open(layout.home) as inbox:
        failed = inbox.open_incident("backup-drill:one")
        other = inbox.open_incident("backup-drill:two")
    row = backups.doctor_line()

    assert drilled == [("drill", "one", True), ("drill", "two", True), ("drill", "one", False)]
    assert not (layout.cache / "restore-drill").exists()
    assert failed is not None
    assert (failed.signature, failed.title) == (
        "drill-failed",
        "Backups: the restore drill of one found damage",
    )
    assert other is None
    assert not row.ok
    assert re.search(r"the restore drill of two checked the copy \w+ \d+ days ago", row.detail)
    assert re.search(
        r"the restore drill of one \d+ days ago found the copy \w+ damaged, and it needs you: ",
        row.detail,
    )


def test_a_drill_short_of_room_does_not_run_and_the_doctor_row_says_so(tmp_path: Path) -> None:
    layout, clock = folder(tmp_path / "QMX"), clock_now()
    backups = service(layout, clock)
    assert finished(backups, backups.sweep()).kind == "backup"
    clock.advance(days=31)
    assert finished(backups, backups.sweep()).kind == "backup"
    backups.floor = 1 << 60

    job = finished(backups, backups.sweep())
    assert job.result is not None
    line = str(job.result["line"])

    assert (job.kind, job.result["place"], job.result["passed"]) == ("drill", "quick", None)
    assert line.startswith(f"the drill of {layout.backups / 'quick'} needs ")
    assert line.endswith("free; it runs when there is room")
    assert line in backups.doctor_line().detail
    assert not (layout.cache / "restore-drill").exists()
