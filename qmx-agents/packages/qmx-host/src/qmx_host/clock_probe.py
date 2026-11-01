"""Every machine proves its clock (AD-10, AD-43; Part C `DEVOPS-CLOCKS.md` section 2).

One SNTP query per source over UDP 123, standard library only, gives the offset and round trip
the host writes into its heartbeat's `clock` field every `clock.probe_s`. The machine's own time
service (Windows Time on This PC, chrony on a server) is read beside it, read-only: nothing here
starts, stops or configures a service, and the doctor line only names the step for him.

The doctor gets three lines from here: the clock, the age of the pinned `tzdata`, and the next
week London and New York disagree on daylight saving time.
"""

from __future__ import annotations

import re
import shutil
import socket
import struct
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Final, cast
from zoneinfo import ZoneInfo

from qma.harness.home import DoctorLine
from qmx_engine.admission import setting
from qmx_engine.heartbeat import ClockBand, ClockFacts, TimeService

SOURCES: Final = ("0.pool.ntp.org", "1.pool.ntp.org", "2.pool.ntp.org", "3.pool.ntp.org")
"""`clock.sources`. One kind of source only: smeared servers are never mixed in (CK-06)."""
PROBE_S: Final = 60.0
"""`clock.probe_s`, seconds between probes."""
TIMEOUT_S: Final = 2.0
"""`clock.timeout_s`, how long one source gets to answer."""
WARN_MS: Final = 25.0
"""`clock.warn_ms`; with the two below, QMN's bands (TN-14)."""
NO_NEW_ENTRY_MS: Final = 100.0
"""`clock.no_new_entry_ms`."""
HALT_MS: Final = 250.0
"""`clock.halt_ms`."""
TZDATA_MAX_AGE_DAYS: Final = 180.0
"""`clock.tzdata_max_age_days`."""
DST_NOTICE_DAYS: Final = 7.0
"""`clock.dst_mismatch_notice_days`, how far ahead the doctor announces a mismatch week."""
NTP_PORT: Final = 123
NTP_EPOCH_S: Final = 2_208_988_800
"""Seconds from 1900-01-01, the NTP era start, to the Unix epoch."""
PACKET: Final = struct.Struct("!BBbbIII4Q")
CLIENT_V4: Final = 0x23
"""Leap indicator 0, version 4, mode 3 (client)."""
SERVER_MODE: Final = 4
SERVICE_TIMEOUT_S: Final = 5.0
MISMATCH_PAIR: Final = ("Europe/London", "America/New_York")
WINDOWS_TIME_FIX: Final = (
    "turn it on: open PowerShell as administrator and run "
    "`Set-Service W32Time -StartupType Automatic; Start-Service W32Time; w32tm /resync`"
)
CHRONY_FIX: Final = "run `sudo systemctl enable --now chrony`, then check `chronyc tracking`"


@dataclass(frozen=True)
class Answer:
    """One source's answer: the offset of this machine's clock and the round trip, in ms."""

    source: str
    offset_ms: float
    delay_ms: float
    stratum: int


@dataclass(frozen=True)
class Bands:
    warn_ms: float = WARN_MS
    no_new_entry_ms: float = NO_NEW_ENTRY_MS
    halt_ms: float = HALT_MS

    @classmethod
    def of(cls, settings: Mapping[str, object]) -> Bands:
        return cls(
            setting(settings, "clock.warn_ms", WARN_MS),
            setting(settings, "clock.no_new_entry_ms", NO_NEW_ENTRY_MS),
            setting(settings, "clock.halt_ms", HALT_MS),
        )

    def band(self, offset_ms: int) -> ClockBand:
        drift = abs(offset_ms)
        if drift >= self.halt_ms:
            return "halt"
        if drift >= self.no_new_entry_ms:
            return "no_new_entry"
        if drift >= self.warn_ms:
            return "warn"
        return "ok"


def query(
    source: str,
    *,
    port: int = NTP_PORT,
    timeout: float = TIMEOUT_S,
    now: Callable[[], float] = time.time,
) -> Answer:
    """One SNTP exchange with `source` (RFC 4330). Raises `OSError` when it does not answer in
    `timeout`, and `ValueError` when its answer is not a usable server reply to this request."""
    sent = now()
    stamp = _to_ntp(sent)
    request = PACKET.pack(CLIENT_V4, 0, 0, 0, 0, 0, 0, 0, 0, 0, stamp)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(request, (source, port))
        data, _ = sock.recvfrom(1024)
    back = now()
    if len(data) < PACKET.size:
        raise ValueError(f"{source} answered {len(data)} bytes, not an NTP packet")
    first, stratum, *_, origin, received, transmitted = PACKET.unpack(data[: PACKET.size])
    if first & 0x7 != SERVER_MODE or not 1 <= stratum <= 15 or transmitted == 0:
        raise ValueError(f"{source} gave no usable time (mode {first & 0x7}, stratum {stratum})")
    if origin != stamp:
        raise ValueError(f"{source} answered a request this probe did not send")
    t2, t3 = _from_ntp(received), _from_ntp(transmitted)
    offset = ((t2 - sent) + (t3 - back)) / 2
    delay = (back - sent) - (t3 - t2)
    return Answer(source, offset * 1000, delay * 1000, stratum)


def probe(
    sources: Sequence[str] = SOURCES,
    *,
    port: int = NTP_PORT,
    timeout: float = TIMEOUT_S,
    bands: Bands | None = None,
    now: Callable[[], float] = time.time,
    service: Callable[[], tuple[TimeService, bool]] | None = None,
) -> ClockFacts:
    """Ask every source and keep the answer with the shortest round trip, the one whose offset
    is best bounded. With no answer the facts say so: no offset, no band."""
    answers: list[Answer] = []
    for source in sources:
        try:
            answers.append(query(source, port=port, timeout=timeout, now=now))
        except OSError, ValueError:
            continue
    kind, synced = (service or time_service)()
    best = min(answers, key=lambda answer: answer.delay_ms, default=None)
    offset = None if best is None else round(best.offset_ms)
    return ClockFacts(
        zone=machine_zone(),
        offset_ms=offset,
        delay_ms=None if best is None else round(best.delay_ms),
        source=", ".join(sources) if best is None else best.source,
        source_kind=kind,
        synced=synced,
        tzdata=tzdata_version(),
        band=None if offset is None else (bands or Bands()).band(offset),
        probed_at=datetime.fromtimestamp(now(), UTC).isoformat(),
    )


def probe_from(settings: Mapping[str, object]) -> ClockFacts:
    """A probe with the `[engine]` clock settings, or their defaults."""
    named = settings.get("clock.sources")
    listed = cast("list[object]", named) if isinstance(named, list) else []
    sources = tuple(str(item) for item in listed) or SOURCES
    return probe(
        sources, timeout=setting(settings, "clock.timeout_s", TIMEOUT_S), bands=Bands.of(settings)
    )


def time_service() -> tuple[TimeService, bool]:
    """This machine's time service and whether it says it keeps time, read-only."""
    if sys.platform == "win32":
        return "w32time", "RUNNING" in _run(["sc", "query", "W32Time"])
    if shutil.which("chronyc"):
        tracking = _run(["chronyc", "tracking"])
        return "chrony", re.search(r"Leap status\s*:\s*Normal", tracking) is not None
    synced = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"]).strip() == "yes"
    return "ntp", synced


def machine_zone() -> str:
    """The machine's zone: the IANA name a Linux `/etc/localtime` links to, else the name the OS
    gives (on Windows its own zone name). Shown only; a machine zone never enters a rule."""
    try:
        target = Path("/etc/localtime").resolve(strict=True).as_posix()
    except OSError:
        target = ""
    if "/zoneinfo/" in target:
        return target.split("/zoneinfo/", 1)[1]
    return datetime.now().astimezone().tzname() or "unknown"


def tzdata_version() -> str:
    """The IANA version of the time zone data this process reads: the pinned `tzdata` package,
    else the system's `tzdata.zi`."""
    try:
        import tzdata  # noqa: PLC0415 - optional where the system ships zone data

        return str(tzdata.IANA_VERSION)
    except ImportError:
        pass
    try:
        head = Path("/usr/share/zoneinfo/tzdata.zi").read_text(encoding="utf-8").split("\n", 1)[0]
    except OSError:
        return "unknown"
    return head.removeprefix("# version ").strip() or "unknown"


def mismatch_week(
    today: date, pair: tuple[str, str] = MISMATCH_PAIR, *, horizon_days: int = 400
) -> tuple[date, date] | None:
    """The first run of days, ending today or later, when the pair's clocks sit a different
    distance apart than they do most of the year; None when none falls inside the horizon."""
    first, second = (ZoneInfo(name) for name in pair)
    days = [today + timedelta(days=step) for step in range(-31, horizon_days)]
    gaps = [_gap(day, first, second) for day in days]
    usual = max(set(gaps), key=gaps.count)
    start: date | None = None
    for day, gap in zip(days, gaps, strict=True):
        if gap != usual and start is None:
            start = day
        if gap == usual and start is not None:
            if day - timedelta(days=1) >= today:
                return start, day - timedelta(days=1)
            start = None
    return None


def clock_line(facts: ClockFacts | None) -> DoctorLine:
    """The doctor's clock row from the newest host row's facts."""
    if facts is None:
        return DoctorLine("clock", False, "not probed yet; the host probes it with its heartbeat")
    service = _service_words(facts)
    if facts.offset_ms is None:
        return DoctorLine(
            "clock",
            False,
            f"no time source answered ({facts.source}), so the offset is unproven; {service}",
        )
    measured = (
        f"Clock {facts.offset_ms} ms off {facts.source} (round trip {facts.delay_ms} ms), "
        f"band {facts.band}; zone {facts.zone}; probed {facts.probed_at}"
    )
    if not facts.synced:
        return DoctorLine("clock", False, f"{service}. {measured}")
    return DoctorLine("clock", facts.band == "ok", f"{measured}; {service}")


def tzdata_line(version: str, today: date, max_age_days: float = TZDATA_MAX_AGE_DAYS) -> DoctorLine:
    """The doctor's `tzdata` row. A version names only its year (2025b), so the age shown is the
    least it can be: the days since that year ended."""
    found = re.match(r"(\d{4})[a-z]*$", version)
    if found is None:
        return DoctorLine("tzdata", False, f"tzdata version {version} could not be read")
    year = int(found.group(1))
    least = max((today - date(year, 12, 31)).days, 0)
    return DoctorLine(
        "tzdata",
        least <= max_age_days,
        f"tzdata {version}, released in {year}, at least {least} days old; "
        f"flagged past {max_age_days:g} days",
    )


def mismatch_line(
    today: date, notice_days: float = DST_NOTICE_DAYS, pair: tuple[str, str] = MISMATCH_PAIR
) -> DoctorLine:
    """The doctor's next mismatch week row; it turns to a warning `notice_days` ahead and stays
    one while the week runs."""
    found = mismatch_week(today, pair)
    names = " and ".join(name.split("/")[-1].replace("_", " ") for name in pair)
    if found is None:
        return DoctorLine("dst mismatch", True, f"no {names} mismatch week within 400 days")
    start, end = found
    span = f"{start.isoformat()} to {end.isoformat()}"
    if start <= today:
        return DoctorLine(
            "dst mismatch", False, f"{names} are in a mismatch week now, {span}; sessions shift"
        )
    ahead = (start - today).days
    return DoctorLine(
        "dst mismatch",
        ahead > notice_days,
        f"next {names} mismatch week {span}, in {ahead} days",
    )


def _service_words(facts: ClockFacts) -> str:
    if facts.source_kind == "w32time":
        return (
            "Windows Time is running"
            if facts.synced
            else f"Windows Time is stopped, {WINDOWS_TIME_FIX}"
        )
    if facts.source_kind == "chrony":
        return "chrony is synced" if facts.synced else f"chrony is not synced, {CHRONY_FIX}"
    return "the system clock is synced" if facts.synced else "the system clock is not synced"


def _gap(day: date, first: ZoneInfo, second: ZoneInfo) -> timedelta:
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=UTC)
    first_offset = noon.astimezone(first).utcoffset() or timedelta()
    second_offset = noon.astimezone(second).utcoffset() or timedelta()
    return first_offset - second_offset


def _run(command: list[str]) -> str:
    try:
        found = subprocess.run(
            command, capture_output=True, text=True, timeout=SERVICE_TIMEOUT_S, check=False
        )
    except OSError, subprocess.SubprocessError:
        return ""
    return found.stdout


def _to_ntp(unix_s: float) -> int:
    return int((unix_s + NTP_EPOCH_S) * 2**32)


def _from_ntp(stamp: int) -> float:
    return stamp / 2**32 - NTP_EPOCH_S
