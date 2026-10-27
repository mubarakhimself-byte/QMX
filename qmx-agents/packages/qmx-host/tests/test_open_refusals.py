"""What did not open is one line and an exit code the desktop app branches on (loose strings P6,
C15, Appendix E): a refused store, engine or Library exits 2, a taken port exits 4, a running host
still exits 1, and `start` passes its child's code through."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import IO

import pytest
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


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """The port of each socket the host handed to `serve`, which opens nothing here."""
    ports: list[int] = []

    async def serve(_home: Path, sock: socket.socket, *_args: object) -> None:
        ports.append(sock.getsockname()[1])

    monkeypatch.setattr(qmx_host.host, "serve", serve)
    return ports


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
    async def refused(*_args: object) -> None:
        raise refusal

    monkeypatch.setattr(qmx_host.host, "serve", refused)

    assert serving(home, 0) == 2
    assert capsys.readouterr().err == f"QMX did not start: {line}\n"


def test_a_taken_port_exits_4_before_anything_opens(
    home: Path, opened: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", 0))
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
