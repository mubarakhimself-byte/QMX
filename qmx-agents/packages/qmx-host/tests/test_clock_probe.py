"""The clock probe against a fake SNTP server on localhost, and the doctor's three clock rows.
No test here reaches a real time server or reads or changes this machine's time service."""

from __future__ import annotations

import asyncio
import socket
import threading
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from qma.harness.home import DoctorLine
from qmx_engine.heartbeat import ClockBand, ClockFacts, Heartbeat, HeartbeatLog, TimeService

from qmx_host.clock_probe import (
    NTP_EPOCH_S,
    PACKET,
    clock_line,
    mismatch_line,
    mismatch_week,
    probe,
    query,
    tzdata_line,
)
from qmx_host.host import clock_doctor, heartbeats_read, host_row

SENT = 1_800_000_000.0
BACK = SENT + 0.010
SERVER_AT = SENT + 0.125


def ntp(unix_s: float) -> int:
    return int((unix_s + NTP_EPOCH_S) * 2**32)


def serve_once(answer: Callable[[bytes], bytes | None]) -> tuple[int, threading.Thread]:
    """A UDP server on 127.0.0.1 that reads one request and sends what `answer` makes of it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(5)

    def run() -> None:
        with sock:
            try:
                request, peer = sock.recvfrom(1024)
            except OSError:
                return
            reply = answer(request)
            if reply is not None:
                sock.sendto(reply, peer)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return sock.getsockname()[1], thread


def server_reply(request: bytes, *, origin: int | None = None) -> bytes:
    """A stratum 2 server whose clock reads `SERVER_AT` on receipt and on transmit."""
    stamp = PACKET.unpack(request)[-1] if origin is None else origin
    return PACKET.pack(0x24, 2, 6, -20, 0, 0, 0, 0, stamp, ntp(SERVER_AT), ntp(SERVER_AT))


def stepped() -> Callable[[], float]:
    """This machine's clock: `SENT` when the request leaves, `BACK` when the answer lands, and
    `BACK` for any later read."""
    readings: Iterator[float] = iter([SENT, BACK])
    return lambda: next(readings, BACK)


def windows_time(running: bool) -> Callable[[], tuple[TimeService, bool]]:
    return lambda: ("w32time", running)


def test_a_probe_against_a_local_stub_returns_its_offset_and_band() -> None:
    port, thread = serve_once(server_reply)

    facts = probe(
        ["127.0.0.1"], port=port, timeout=2, now=stepped(), service=windows_time(running=True)
    )
    thread.join(5)

    assert (facts.offset_ms, facts.delay_ms, facts.band) == (120, 10, "no_new_entry")
    assert (facts.source, facts.source_kind, facts.synced) == ("127.0.0.1", "w32time", True)
    assert facts.probed_at == "2027-01-15T08:00:00.010000+00:00"
    assert clock_line(facts).detail.startswith(
        "Clock 120 ms off 127.0.0.1 (round trip 10 ms), band no_new_entry"
    )
    assert clock_line(facts).ok is False


def test_a_silent_source_leaves_the_offset_unproven() -> None:
    port, thread = serve_once(lambda _request: None)

    facts = probe(
        ["127.0.0.1"], port=port, timeout=0.2, now=stepped(), service=windows_time(running=True)
    )
    thread.join(5)

    assert (facts.offset_ms, facts.delay_ms, facts.band) == (None, None, None)
    line = clock_line(facts)
    assert line.ok is False
    assert line.detail == (
        "no time source answered (127.0.0.1), so the offset is unproven; Windows Time is running"
    )


def test_an_answer_to_another_request_is_refused() -> None:
    port, thread = serve_once(lambda request: server_reply(request, origin=12345))

    with pytest.raises(ValueError, match="did not send"):
        query("127.0.0.1", port=port, timeout=2, now=stepped())
    thread.join(5)


def test_stopped_windows_time_names_the_step_he_takes() -> None:
    facts = ClockFacts(
        zone="E. Africa Standard Time",
        offset_ms=3,
        delay_ms=21,
        source="0.pool.ntp.org",
        source_kind="w32time",
        synced=False,
        tzdata="2025b",
        band="ok",
        probed_at="2026-11-01T09:00:00+00:00",
    )

    line = clock_line(facts)

    assert line.ok is False
    assert line.detail.startswith(
        "Windows Time is stopped, turn it on: open PowerShell as administrator and run "
        "`Set-Service W32Time -StartupType Automatic; Start-Service W32Time; w32tm /resync`. "
        "Clock 3 ms off 0.pool.ntp.org"
    )
    assert clock_line(facts.model_copy(update={"synced": True})).ok is True
    assert clock_line(None).ok is False


def test_the_tzdata_row_shows_the_version_and_its_least_age() -> None:
    stale = tzdata_line("2025b", date(2026, 11, 1))
    fresh = tzdata_line("2026a", date(2026, 11, 1))

    assert (stale.ok, stale.detail) == (
        False,
        "tzdata 2025b, released in 2025, at least 305 days old; flagged past 180 days",
    )
    assert (fresh.ok, fresh.detail) == (
        True,
        "tzdata 2026a, released in 2026, at least 0 days old; flagged past 180 days",
    )
    assert tzdata_line("unknown", date(2026, 11, 1)).ok is False


def test_the_next_london_and_new_york_mismatch_week() -> None:
    assert mismatch_week(date(2026, 10, 28)) == (date(2026, 10, 25), date(2026, 10, 31))
    assert mismatch_week(date(2026, 11, 1)) == (date(2027, 3, 14), date(2027, 3, 27))

    far = mismatch_line(date(2026, 11, 1))
    near = mismatch_line(date(2027, 3, 10))
    now = mismatch_line(date(2027, 3, 20))

    assert (far.ok, far.detail) == (
        True,
        "next London and New York mismatch week 2027-03-14 to 2027-03-27, in 133 days",
    )
    assert (near.ok, near.detail) == (
        False,
        "next London and New York mismatch week 2027-03-14 to 2027-03-27, in 4 days",
    )
    assert now.ok is False
    assert now.detail.startswith("London and New York are in a mismatch week now, 2027-03-14")


def machine_row(host_id: str, offset_ms: int, band: ClockBand) -> Heartbeat:
    return Heartbeat(
        subject="host",
        id=host_id,
        at="2026-11-01T09:00:00+00:00",
        cpu_seconds=0.0,
        rss_bytes=0,
        machine_minutes=0.0,
        qmx_version="0.0.0",
        kinds_digest="none",
        paused=False,
        clock=ClockFacts(
            zone="UTC",
            offset_ms=offset_ms,
            delay_ms=20,
            source=f"{host_id}-src",
            source_kind="w32time",
            synced=True,
            tzdata="2026a",
            band=band,
            probed_at="2026-11-01T09:00:00+00:00",
        ),
    )


def test_a_server_home_holding_the_pcs_row_shows_its_own_clock(tmp_path: Path) -> None:
    HeartbeatLog(tmp_path, 7).write([machine_row("pc", 3, "ok")])
    HeartbeatLog(tmp_path, 7).write([machine_row("server", 400, "no_new_entry")])
    rows: list[Callable[[], DoctorLine]] = []

    clock_doctor(cast("Any", SimpleNamespace(doctor_from=rows.append)), tmp_path, "server", {})
    read = asyncio.run(heartbeats_read(tmp_path, "server")({}))

    assert (rows[0]().ok, rows[0]().detail) == (
        False,
        "Clock 400 ms off server-src (round trip 20 ms), band no_new_entry; zone UTC; "
        "probed 2026-11-01T09:00:00+00:00; Windows Time is running",
    )
    clock = cast("dict[str, object]", read["clock"])
    assert (clock["offset_ms"], clock["source"]) == (400, "server-src")
    pc = host_row(tmp_path, "pc")
    assert pc is not None and pc.clock is not None
    assert (pc.id, pc.clock.offset_ms, pc.clock.source) == ("pc", 3, "pc-src")
