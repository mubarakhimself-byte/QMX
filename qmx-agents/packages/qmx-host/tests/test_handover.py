"""The first-start card hands the folder of its own last finished choice to the desktop app and
stops, so the desktop app starts the host on it (loose strings P1, Appendix E). Every folder is in
pytest's tmp folder on a scratch profile; no host, browser or Credential Manager is started."""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_home import LABEL, Label

from qmx_host import first_start
from qmx_host.__main__ import main
from qmx_host.first_start import Places, first_start_app, first_start_router


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


def places(pc: Path) -> Places:
    return Places({"APPDATA": str(pc / "profile" / "Roaming")})


def test_the_handover_answers_only_the_folder_this_card_finished(pc: Path) -> None:
    elsewhere = pc / "Elsewhere"
    elsewhere.mkdir()
    (elsewhere / LABEL).write_text(Label.mint().dump(), encoding="utf-8")
    first_start.write_pointer(elsewhere)
    handed: list[Path] = []
    app = FastAPI()
    app.include_router(
        first_start_router(
            places(pc), pc / "no-old", drives=[], port=8799, on_handover=handed.append
        )
    )
    client = TestClient(app)

    before = client.post("/api/first-start/handover")
    made = client.post("/api/first-start/new", json={"folder": str(pc / "QMX")})
    first = client.post("/api/first-start/handover")
    second = client.post("/api/first-start/handover")

    assert before.status_code == 409, "an older pointer is never handed over"
    assert before.json()["detail"] == (
        "no QMX folder was chosen in this first start yet; make a new one, open one or bring "
        "your old data in first"
    )
    assert made.status_code == 200
    folder = str((pc / "QMX").resolve())
    assert (first.json(), second.json()) == ({"folder": folder, "port": 8799},) * 2
    assert handed == [Path(folder)] * 2


def test_the_handover_answer_reaches_the_client_before_the_card_stops(pc: Path) -> None:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server: list[uvicorn.Server] = []

    def stop(_folder: Path) -> None:
        server[0].should_exit = True

    app = first_start_app(places(pc), pc / "no-old", "", port=port, on_handover=stop)
    server.append(
        uvicorn.Server(uvicorn.Config(app, log_level="warning", timeout_graceful_shutdown=3))
    )
    running = threading.Thread(target=server[0].run, kwargs={"sockets": [sock]})
    running.start()
    try:
        base = f"http://127.0.0.1:{port}/api/first-start"
        while not server[0].started:
            running.join(0.05)
        made = httpx.post(f"{base}/new", json={"folder": str(pc / "QMX")}, timeout=10)
        handover = httpx.post(f"{base}/handover", timeout=10)
        running.join(10)
        stopped_by_the_handover = not running.is_alive()
    finally:
        server[0].should_exit = True
        running.join(10)

    assert made.status_code == 200
    assert handover.status_code == 200
    assert handover.json() == {"folder": str((pc / "QMX").resolve()), "port": port}
    assert stopped_by_the_handover, "the card's server stopped after it answered"


def test_the_card_on_a_taken_port_exits_4_before_it_serves(
    pc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    taken = socket.socket()
    taken.bind(("127.0.0.1", 0))
    taken.listen()
    port = taken.getsockname()[1]
    try:
        with pytest.raises(SystemExit) as stopped:
            main(["first-start", "--serve", "--port", str(port)])
    finally:
        taken.close()

    assert stopped.value.code == 4
    assert capsys.readouterr().err.strip() == (
        f"port {port} is in use: stop what holds it, or start the first start on another port"
    )


def test_a_stale_lock_left_by_a_killed_card_is_removed_when_the_card_starts(pc: Path) -> None:
    lock = pc / "profile" / "Roaming" / "QMX" / "first-start.lock"
    lock.parent.mkdir(parents=True)
    lock.write_bytes(b"")

    first_start_app(places(pc), pc / "no-old", "", port=8799)

    assert not lock.exists()
