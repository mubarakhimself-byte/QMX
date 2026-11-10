"""The heartbeat task never waits on the supervisor's lock on the host's loop, and the clock probe
it takes reaches the node's volume.

An install holds that lock through `uv sync` and, at its end, hops onto the loop for the UI's
totals. A beat that took the lock on the loop froze every route and deadlocked the install. For
the same reason the facts rewrite after a probe runs off the loop, and it must land with no
Settings write: the node reads that file to stop entries on a drifted clock.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import socket
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from qma.harness import QmxHome, control_service
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_engine.heartbeat import ClockFacts, TimeService

from qmx_host import host
from qmx_host.clock_probe import NTP_EPOCH_S, PACKET, probe
from qmx_host.host import host_facts, market_door, placement_name

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "exchange-status"
SETTLE_S = 60.0


class Log:
    def __init__(self, *_args: object) -> None:
        pass

    def write(self, _rows: object) -> None:
        pass

    def prune(self, _now: object) -> None:
        pass


def no_bytes(*_args: object) -> int:
    return 0


def nothing(*_args: object) -> None:
    return None


def one_row(*_args: object, **_kwargs: object) -> str:
    return "row"


def test_the_loop_runs_on_while_a_beat_waits_for_the_supervisors_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(host, "HeartbeatLog", Log)
    monkeypatch.setattr(host, "floor_bytes", no_bytes)
    monkeypatch.setattr(host, "free_bytes", no_bytes)
    monkeypatch.setattr(host, "make_room", nothing)
    monkeypatch.setattr(host, "probe_from", nothing)
    monkeypatch.setattr(host, "beat", one_row)
    waiting, lock_free = threading.Event(), threading.Event()
    freed_in_time: list[bool] = []

    def rows() -> list[dict[str, object]]:
        waiting.set()
        freed_in_time.append(lock_free.wait(3.0))
        return []

    runtime = SimpleNamespace(heartbeats=rows)
    control = SimpleNamespace(app_runtime=lambda: runtime)
    core = SimpleNamespace(settings={}, paused=False)
    engine = SimpleNamespace(svc=SimpleNamespace(ctx=SimpleNamespace(engine=core)))

    async def run() -> None:
        beats = asyncio.create_task(
            host.heartbeats(tmp_path, "pc", cast(Any, control), cast(Any, None), cast(Any, engine))
        )
        while not waiting.is_set():
            await asyncio.sleep(0.01)
        lock_free.set()
        while not freed_in_time:
            await asyncio.sleep(0.01)
        beats.cancel()
        await asyncio.gather(beats, return_exceptions=True)

    asyncio.run(run())

    assert freed_in_time == [True]


SENT = 1_800_000_000.0
BACK = SENT + 0.010
SERVER_AT = SENT + 0.125
PROBED_AT = "2027-01-15T08:00:00.010000+00:00"


def ntp(unix_s: float) -> int:
    return int((unix_s + NTP_EPOCH_S) * 2**32)


def serve_once(answer: Callable[[bytes], bytes | None]) -> int:
    """A UDP time server on 127.0.0.1 that reads one request and answers what `answer` makes."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(30)

    def run() -> None:
        with sock:
            try:
                request, peer = sock.recvfrom(1024)
            except OSError:
                return
            reply = answer(request)
            if reply is not None:
                sock.sendto(reply, peer)

    threading.Thread(target=run, daemon=True).start()
    return cast(int, sock.getsockname()[1])


def server_reply(request: bytes) -> bytes:
    """A stratum 2 server whose clock reads `SERVER_AT` on receipt and on transmit."""
    stamp = PACKET.unpack(request)[-1]
    return PACKET.pack(0x24, 2, 6, -20, 0, 0, 0, 0, stamp, ntp(SERVER_AT), ntp(SERVER_AT))


def stepped() -> Callable[[], float]:
    readings = iter([SENT, BACK])
    return lambda: next(readings, BACK)


def windows_time(running: bool) -> Callable[[], tuple[TimeService, bool]]:
    return lambda: ("w32time", running)


def drifted() -> ClockFacts:
    facts = probe(
        ["127.0.0.1"],
        port=serve_once(server_reply),
        timeout=5,
        now=stepped(),
        service=windows_time(running=True),
    )
    assert facts.offset_ms == 120
    return facts


@pytest.fixture
def served(tmp_path: Path) -> Generator[tuple[Any, Supervisor, host.ClockRead]]:
    """A real control service, its supervisor, and one real app running in its volume."""
    home = tmp_path / "home"
    control = control_service(QmxHome(home))
    try:
        runtime = control.app_runtime()
        clock_read = host.ClockRead()
        door = market_door(home, control, "pc")
        name = placement_name(control, "pc")
        runtime.attach_facts(lambda: host_facts(control, "pc", name, door, clock=clock_read.facts))
        source = tmp_path / "exchange-status"
        shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
        runtime.install(source, trust="first_party")
        runtime.start(APP)
        yield control, runtime, clock_read
    finally:
        control.close()


def test_a_drift_reaches_the_nodes_volume_with_no_settings_write(
    served: tuple[Any, Supervisor, host.ClockRead], monkeypatch: pytest.MonkeyPatch
) -> None:
    control, runtime, clock_read = served
    facts = Volume(runtime.home, APP).root / host_facts_path()
    before = read(facts)
    settings_before = len(control.events("settings"))

    monkeypatch.setattr(host, "HeartbeatLog", Log)
    monkeypatch.setattr(host, "floor_bytes", no_bytes)
    monkeypatch.setattr(host, "free_bytes", no_bytes)
    monkeypatch.setattr(host, "make_room", nothing)
    monkeypatch.setattr(host, "beat", one_row)

    def probe_from(_settings: object) -> ClockFacts:
        return drifted()

    monkeypatch.setattr(host, "probe_from", probe_from)
    core = SimpleNamespace(settings={}, paused=False)
    engine = SimpleNamespace(svc=SimpleNamespace(ctx=SimpleNamespace(engine=core)))

    async def run() -> None:
        beats = asyncio.create_task(
            host.heartbeats(
                runtime.home,
                "pc",
                control,
                cast(Any, None),
                cast(Any, engine),
                clock_read=clock_read,
            )
        )
        deadline = time.monotonic() + SETTLE_S
        try:
            while "clock" not in read(facts):
                assert time.monotonic() < deadline, "the probe never reached the volume"
                await asyncio.sleep(0.05)
        finally:
            beats.cancel()
            await asyncio.gather(beats, return_exceptions=True)

    asyncio.run(run())

    assert "clock" not in before
    assert read(facts)["clock"] == {"offset_ms": 120, "probed_at": PROBED_AT}
    assert len(control.events("settings")) == settings_before


def host_facts_path() -> Path:
    return Path("road") / "host" / "facts.json"


def read(path: Path) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except OSError, ValueError:
        return {}
