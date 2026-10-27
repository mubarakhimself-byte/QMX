"""What did not open is one line and an exit code the desktop app branches on (loose strings P6,
C15, Appendix E): a refused store, engine, Library or app startup exits 2, a taken port exits 4, a
running host still exits 1, and `start` passes its child's code through."""

from __future__ import annotations

import socket
import threading
import webbrowser
from collections.abc import Iterator
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import IO, override

import keyring
import pytest
from fastapi import FastAPI
from keyring.backend import KeyringBackend
from qmx_engine.ports.library import LibraryRefused as EngineRefused
from qmx_home import resolve
from qmx_home.versions import StoreRefused
from qmx_library.port import LibraryRefused

import qmx_host.host
from qmx_host.host import serve_forever, single_instance, start

NOT_A_LEDGER = (
    "D:/QMX/data/engine.db is not a QMX engine ledger: file is not a database. QMX leaves it as "
    "it is; move it aside and start QMX again to make a new one."
)
APP_FAILED = (
    "QMX did not start: the host's app failed while it started up. Its error is in the lines "
    "above; fix that and start QMX again."
)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """The port of each socket the host handed to `serve`, which opens nothing here."""
    ports: list[int] = []

    async def serve(_home: Path, sock: socket.socket, *_args: object, **_kw: object) -> None:
        ports.append(sock.getsockname()[1])

    monkeypatch.setattr(qmx_host.host, "serve", serve)
    return ports


class Memory(KeyringBackend):
    """A keyring in memory, so a real `serve` mints its bearer without Credential Manager."""

    priority = 1  # pyright: ignore[reportAssignmentType]

    def __init__(self) -> None:
        super().__init__()
        self.held: dict[tuple[str, str], str] = {}

    @override
    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    @override
    def set_password(self, service: str, username: str, password: str) -> None:
        self.held[service, username] = password

    @override
    def delete_password(self, service: str, username: str) -> None:
        self.held.pop((service, username), None)


@pytest.fixture
def scratch_machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A real `serve` on a scratch profile with an in-memory keyring, no browser and no
    Hindsight, so nothing reaches his profile, his Credential Manager or pg0."""
    profile = tmp_path / "profile"
    for name, path in {
        "USERPROFILE": profile,
        "HOME": profile,
        "APPDATA": profile / "AppData" / "Roaming",
        "LOCALAPPDATA": profile / "AppData" / "Local",
    }.items():
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(name, str(path))
    monkeypatch.delenv("QMX_HOME", raising=False)

    def real_browser(_url: str) -> bool:
        raise AssertionError("his real browser opened")

    monkeypatch.setattr(webbrowser, "open", real_browser)

    def no_hindsight(_control: object, _role: object) -> bool:
        return False

    monkeypatch.setattr(qmx_host.host, "hindsight_runs", no_hindsight)
    before = keyring.get_keyring()
    keyring.set_keyring(Memory())
    try:
        yield
    finally:
        keyring.set_keyring(before)


def serving(home: Path, port: int) -> int:
    return serve_forever(home, port=port, role="pc", ui_origin="", scrubbed=(), keep=())


@pytest.mark.parametrize(
    ("refusal", "line"),
    [
        (StoreRefused("engine", NOT_A_LEDGER), NOT_A_LEDGER),
        (
            LibraryRefused("too-new", "this Library store needs a newer QMX\nInstall it."),
            "too-new: this Library store needs a newer QMX Install it.",
        ),
        (
            EngineRefused("not-found", "workflow chain has no published version"),
            "not-found: workflow chain has no published version",
        ),
    ],
    ids=["store", "library", "engine-library"],
)
def test_a_refusal_raised_while_the_host_opens_prints_one_line_and_exits_2(
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    refusal: Exception,
    line: str,
) -> None:
    async def refused(*_args: object, **_kw: object) -> None:
        raise refusal

    monkeypatch.setattr(qmx_host.host, "serve", refused)

    assert serving(home, 0) == 2
    assert capsys.readouterr().err == f"QMX did not start: {line}\n"


@pytest.mark.usefixtures("scratch_machine")
def test_a_ledger_that_is_not_one_stops_the_real_open_with_one_line_and_2(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = home / "engine" / "engine.sqlite"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(b"this is not a ledger\n" * 64)

    code = serving(home, 0)

    said = capsys.readouterr().err
    assert code == 2
    assert "Traceback" not in said
    assert [line for line in said.splitlines() if line.startswith("QMX did not start")] == [
        f"QMX did not start: {ledger} is not a QMX run ledger: it is not a SQLite database. QMX "
        "leaves it as it is; move it aside and start QMX again to make a new one."
    ]


@pytest.mark.usefixtures("scratch_machine")
def test_an_app_whose_startup_fails_exits_2_with_one_line_not_3(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Failing(AbstractAsyncContextManager[None]):
        async def __aenter__(self) -> None:
            raise RuntimeError("the control store did not open")

        async def __aexit__(self, *_exc: object) -> None:
            return None

    def failing_app(*_args: object) -> FastAPI:
        return FastAPI(lifespan=lambda _app: Failing())

    monkeypatch.setattr(qmx_host.host, "compose", failing_app)

    code = serving(home, 0)

    said = capsys.readouterr().err.splitlines()
    assert (code, said[-1]) == (2, APP_FAILED)
    assert [line for line in said if line.startswith("QMX did not start")] == [APP_FAILED]


def test_a_refusal_after_the_host_served_is_not_named_did_not_start(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def served_then_refused(*_args: object, served: threading.Event, **_kw: object) -> None:
        served.set()
        raise StoreRefused("engine", NOT_A_LEDGER)

    monkeypatch.setattr(qmx_host.host, "serve", served_then_refused)

    with pytest.raises(StoreRefused, match="is not a QMX engine ledger"):
        serving(home, 0)
    assert "QMX did not start" not in capsys.readouterr().err


@pytest.mark.parametrize("held_on", ["127.0.0.1", "0.0.0.0"])  # noqa: S104 - a listener on every interface
def test_a_taken_port_exits_4_before_anything_opens(
    home: Path, opened: list[int], capsys: pytest.CaptureFixture[str], held_on: str
) -> None:
    with socket.socket() as holder:
        holder.bind((held_on, 0))
        holder.listen()
        port = holder.getsockname()[1]

        assert serving(home, port) == 4

    assert opened == []
    assert capsys.readouterr().err == (
        f"QMX did not start: port {port} is in use. Stop what holds it, or start QMX on another "
        "port.\n"
    )


def test_the_host_serves_on_the_port_it_bound(home: Path, opened: list[int]) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free = probe.getsockname()[1]

    assert serving(home, free) == 0
    assert opened == [free]


def test_a_running_host_still_exits_1(
    home: Path, opened: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    with single_instance(home):
        assert serving(home, 0) == 1

    assert opened == []
    assert capsys.readouterr().err.startswith(f"refused: {home} already has a host")


def test_start_passes_its_childs_code_and_line_through(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Refused:
        pid = 0

        def __init__(self, _command: list[str], *, stdout: IO[bytes], **_: object) -> None:
            stdout.write(b"starting\nQMX did not start: the engine ledger is refused.\n")

        def poll(self) -> int:
            return 2

    monkeypatch.setattr(qmx_host.host.subprocess, "Popen", Refused)
    host_log = home.parent / "logs" / "host.log"

    assert start(home, 0, "pc", "") == 2
    assert capsys.readouterr().err == (
        "QMX did not start: the engine ledger is refused.\n"
        f"The host failed to start; see {host_log}.\n"
    )


def test_start_on_a_taken_port_exits_4(home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", 0))
        holder.listen()
        port = holder.getsockname()[1]

        assert start(home, port, "pc", "") == 4

    assert capsys.readouterr().err == (
        f"QMX did not start: port {port} is in use. Stop what holds it, or start QMX on another "
        "port.\n"
    )
