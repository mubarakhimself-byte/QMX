"""`/api/backups` behind the host's bearer, and a round that never holds a request (B3)."""

from __future__ import annotations

import secrets
import socket
import statistics
import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.server import create_app
from qmx_home.backup.plan import NO_SECOND_DRIVE
from qmx_home.files import hold
from test_backups_service import Clock, connect, folder, proposing, service, target

from qmx_host import backups as module
from qmx_host.backups import Backups, backups_router

TOKEN = secrets.token_urlsafe(32)
BEARER = {"Authorization": f"Bearer {TOKEN}"}


def app_of(backups: Backups) -> FastAPI:
    return create_app(backups.control, TOKEN, extra_routers=[backups_router(backups)])


def ended(rest: TestClient | httpx.Client, job_id: str) -> dict[str, object]:
    for _ in range(1200):
        job = cast(
            "dict[str, object]", rest.get(f"/api/backups/jobs/{job_id}", headers=BEARER).json()
        )
        if job["state"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError("the round did not end within 60 s")


@contextmanager
def held_rounds(monkeypatch: pytest.MonkeyPatch) -> Generator[threading.Event]:
    """Rounds that wait until the test lets them go, then run as written."""
    go = threading.Event()
    real = module.run_round

    def waiting(*args: object, **kwargs: object) -> object:
        go.wait(30)
        return cast("Callable[..., object]", real)(*args, **kwargs)

    monkeypatch.setattr(module, "run_round", waiting)
    try:
        yield go
    finally:
        go.set()


def test_every_backup_route_answers_401_without_the_bearer(tmp_path: Path) -> None:
    backups = service(folder(tmp_path / "QMX"), Clock())
    with TestClient(app_of(backups)) as rest:
        answers = [
            rest.get("/api/backups").status_code,
            rest.get("/api/backups/targets/quick/copies").status_code,
            rest.post("/api/backups/run").status_code,
            rest.get("/api/backups/jobs/x").status_code,
            rest.post("/api/backups/targets/usb/carry-on").status_code,
            rest.post("/api/backups/targets/default/accept").status_code,
        ]
    assert answers == [401] * 6


def test_a_round_asked_for_while_one_runs_is_409_naming_it_and_after_it_is_202(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    connect(backups, target(tmp_path / "usb"))
    with TestClient(app_of(backups)) as rest, held_rounds(monkeypatch) as go:
        scheduled = backups.sweep()
        assert scheduled is not None
        refused = rest.post("/api/backups/run", headers=BEARER, json={"target": "usb"})
        assert (refused.status_code, refused.json()) == (
            409,
            {
                "detail": f"a backup round is already running (job {scheduled.id}, the schedule "
                "started it); it ends by itself, then ask again"
            },
        )
        go.set()
        assert ended(rest, scheduled.id)["state"] == "finished"

        asked = rest.post("/api/backups/run", headers=BEARER, json={"target": "usb"})
        assert asked.status_code == 202
        job = ended(rest, str(asked.json()["id"]))
        places = cast("list[dict[str, object]]", cast("dict[str, object]", job["result"])["places"])
        assert [(p["id"], p["result"]) for p in places] == [
            ("quick", "unchanged"),
            ("usb", "unchanged"),
        ]
        assert all(str(p["line"]).startswith("nothing changed since the last copy") for p in places)

        unknown = rest.post("/api/backups/run", headers=BEARER, json={"target": "tape"})
        assert (unknown.status_code, unknown.json()) == (
            404,
            {"detail": "there is no storage 'tape' in Settings"},
        )


def test_the_view_shows_each_place_with_its_last_copy_and_lists_its_copies(
    tmp_path: Path,
) -> None:
    layout, clock = folder(tmp_path / "QMX"), Clock()
    backups = service(layout, clock)
    connect(backups, target(tmp_path / "usb"))
    with TestClient(app_of(backups)) as rest:
        started = rest.post("/api/backups/run", headers=BEARER)
        assert ended(rest, str(started.json()["id"]))["state"] == "finished"
        view = rest.get("/api/backups", headers=BEARER).json()
        copies = rest.get("/api/backups/targets/usb/copies", headers=BEARER).json()
        missing = rest.get("/api/backups/targets/tape/copies", headers=BEARER)
        accept = rest.post("/api/backups/targets/default/accept", headers=BEARER)

    places = view["places"]
    assert [(p["id"], p["last"]["result"], p["concern"]) for p in places] == [
        ("quick", "copied", None),
        ("usb", "copied", None),
    ]
    assert places[1]["newest_complete"] == places[1]["last"]["stamp"]
    assert (view["line"], view["proposal"], view["running"]) == (None, None, None)
    assert [(c["readable"], c["why"], c["partial"]) for c in copies["copies"]] == [
        (True, "round", False)
    ]
    assert copies["copies"][0]["stamp"] == places[1]["newest_complete"]
    assert missing.status_code == 404
    assert (accept.status_code, accept.json()) == (
        409,
        {"detail": "you already connected a storage; change it in Settings, Sync to my storage"},
    )


def test_accepting_with_no_drive_to_propose_is_409_with_the_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "proposal", proposing(None))
    backups = service(folder(tmp_path / "QMX"), Clock())
    with TestClient(app_of(backups)) as rest:
        refused = rest.post("/api/backups/targets/default/accept", headers=BEARER)
    assert (refused.status_code, refused.json()) == (409, {"detail": NO_SECOND_DRIVE})


@contextmanager
def serving(app: FastAPI) -> Generator[str]:
    """The app on a real loopback socket in this process, as the host serves it."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    for _ in range(400):
        if server.started:
            break
        time.sleep(0.025)
    try:
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        server.should_exit = True
        thread.join(30)
        sock.close()


def test_health_answers_in_under_a_second_all_through_a_round(tmp_path: Path) -> None:
    layout = folder(tmp_path / "QMX", files=400, store_rows=20_000)
    backups = service(layout, Clock())
    connect(backups, target(tmp_path / "usb"))
    with serving(app_of(backups)) as url, httpx.Client(base_url=url, timeout=10) as rest:
        started = rest.post("/api/backups/run", headers=BEARER)
        assert started.status_code == 202
        job_id = str(started.json()["id"])
        waits: list[float] = []
        while rest.get(f"/api/backups/jobs/{job_id}", headers=BEARER).json()["state"] == "running":
            asked = time.perf_counter()
            assert rest.get("/api/health", headers=BEARER).status_code == 200
            waits.append(time.perf_counter() - asked)
            time.sleep(0.05)
        job = ended(rest, job_id)

    assert job["state"] == "finished", job["line"]
    assert len(waits) >= 10, f"the round took too little time to prove anything: {len(waits)}"
    assert max(waits) < 1.0, (
        f"slowest health {max(waits):.3f} s, median {statistics.median(waits):.3f} s"
    )


def test_a_round_asked_for_while_the_command_line_round_holds_the_folder_is_409(
    tmp_path: Path,
) -> None:
    layout = folder(tmp_path / "QMX")
    backups = service(layout, Clock())
    with TestClient(app_of(backups)) as rest, hold(layout.backups / "backups.lock", "busy"):
        refused = rest.post("/api/backups/run", headers=BEARER)
        swept = backups.sweep()
    assert (refused.status_code, refused.json()) == (
        409,
        {
            "detail": "a backup round from the command line (python -m qmx_host backup) is "
            f"copying {layout.root}; it ends by itself, then ask again"
        },
    )
    assert (swept, backups.jobs.latest("backup")) == (None, None)
