"""One heartbeat row per subject per interval (AD-65), and the home's local log of them.

A host, a remote run sidecar and every supervised app write the same `Heartbeat` row. The live
facts travel only here: CPU, memory, capacity in use per class, intent claims, the version and
node kinds a host runs, the pause flag it sees, and the newest reading per external connection.
Preflight reads a host's kinds before it places a node there (AD-20), the `ops` toolset reads the
rows, and a workflow that names a `connection` reads the reading word here (AD-67).

The row is also what the Hub hears: `HubLink.push` sends it and the reply carries the authoritative
`autonomy_paused` flag and how many claims the batch renewed (AD-65, review 48 M5). A host that
stops hearing from the Hub for `UNKNOWN_AFTER_S` keeps the last flag it knew and says so: "pause
state unknown", because honouring a flag nobody can confirm would quietly stop autonomy for good.

The home keeps rows as JSONL day files `logs/heartbeat-<YYYY-MM-DD>.jsonl` for
`heartbeat.window_days` days (`WINDOW_DAYS`), plus `logs/heartbeat-latest.json`, the newest row
per subject, so a reader never scans a day file. The host is the one writer: it holds the
home's lock. Spend per subject is a reading over these rows, never a cap.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, date, datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Final, Literal, cast

from pydantic import BaseModel, ConfigDict, Field
from qmx_ledger.journal import fingerprint

from qmx_engine.definition.registry import BASE_KINDS

type Subject = Literal["host", "run", "app"]
type PauseState = Literal["known", "unknown"]

INTERVAL_S: Final = 30.0
"""`heartbeat.interval`, seconds between rows (Claude's default; a `[engine]` setting overrides)."""
WINDOW_DAYS: Final = 7.0
"""`heartbeat.window_days`, the PC's rolling log window (Claude's default; a setting overrides)."""
LOGS: Final = "logs"
LATEST: Final = "heartbeat-latest.json"
UNKNOWN_AFTER_S: Final = 300.0
"""Pause state unknown after five minutes without the Hub (Appendix B)."""
UNKNOWN: Final = "pause state unknown"
HEARTBEAT_ROUTE: Final = "/v1/heartbeat"
"""The Hub's one route for a row, and its reply."""
CALL_TIMEOUT_S: Final = 10.0
CONNECTIONS: Final = "connections-health.json"
"""The health workflow's file under `logs/`; the host attaches its readings to its next row."""
type ConnectionWord = Literal["ok", "slowed", "maintenance", "needs_you", "down"]


class ConnectionReading(BaseModel):
    """One connection's reading word, as the `connections-health` workflow left it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connection: str
    word: ConnectionWord
    setup: str = ""
    """The setup state the health walk reached: `available` to `healthy` (AD-30, AD-67)."""
    code: str = ""
    latency_ms: int | None = None
    clock_offset_ms: int | None = None
    at: str = ""


class ClassUse(BaseModel):
    """One capacity class on a host: slots in use, slots it has, and work waiting for one."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    used: int
    size: int
    waiting: int = 0


class Heartbeat(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: Subject
    id: str
    """The host id (its placement name, `pc` on the PC), the run id, or the app id."""
    at: str
    cpu_seconds: float
    rss_bytes: int
    machine_minutes: float
    """Minutes the subject has held this machine since it started."""
    capacity: dict[str, ClassUse] = Field(default_factory=dict[str, ClassUse])
    claims: tuple[str, ...] = ()
    qmx_version: str
    node_kinds: tuple[str, ...] = ()
    """The node kinds this subject's code can run; empty for an app."""
    kinds_digest: str
    paused: bool
    pause_state: PauseState = "known"
    """Whether the flag is still the Hub's current word, or the last one it knew (AD-65)."""
    blob_cache_bytes: int | None = None
    free_disk_bytes: int | None = None
    disk_floor_bytes: int | None = None
    """The room this machine keeps for itself, from its own free space (D-11)."""
    free_ram_bytes: int | None = None
    """RAM this machine can give right now, which admission reserves against (F39, AD-58)."""
    session_bytes: int | None = None
    """What one session of this host really holds: this host's process tree, measured here, and
    the figure that replaces a reserved constant once it is known (D-11)."""
    connections: tuple[ConnectionReading, ...] = ()
    """The newest reading per external connection on this home (AD-67)."""
    clock_offset_ms: int | None = None
    """The largest absolute provider clock offset this home measured, signed as measured."""


def node_kinds() -> tuple[str, ...]:
    """Every kind this code's registry knows, available yet or not: a node of any other kind
    needs a newer host."""
    return tuple(sorted(BASE_KINDS))


def kinds_digest(kinds: Iterable[str]) -> str:
    return fingerprint(sorted(kinds))


def qmx_version() -> str:
    return metadata.version("qmx-engine")


def logs_dir(home: Path) -> Path:
    return home / LOGS


def day_file(home: Path, day: date) -> Path:
    return logs_dir(home) / f"heartbeat-{day.isoformat()}.jsonl"


class HeartbeatLog:
    """The home's heartbeat log. Not thread-safe: one writer, the host's heartbeat loop."""

    def __init__(self, home: Path, window_days: float) -> None:
        self.home = home
        self.window = timedelta(days=window_days)
        logs_dir(home).mkdir(parents=True, exist_ok=True)

    def write(self, rows: Iterable[Heartbeat]) -> None:
        found = [_attached(self.home, row) for row in rows]
        if not found:
            return
        by_day: dict[date, list[str]] = {}
        for row in found:
            by_day.setdefault(_when(row.at).date(), []).append(row.model_dump_json() + "\n")
        for day, lines in by_day.items():
            with day_file(self.home, day).open("a", encoding="utf-8") as file:
                file.writelines(lines)
        newest = {(r.subject, r.id): r for r in latest(self.home).values()}
        newest.update({(r.subject, r.id): r for r in found})
        document = {f"{s}:{i}": r.model_dump(mode="json") for (s, i), r in newest.items()}
        target = logs_dir(self.home) / LATEST
        scratch = target.with_suffix(".tmp")
        scratch.write_text(json.dumps(document), encoding="utf-8")
        os.replace(scratch, target)

    def prune(self, now: datetime) -> int:
        """Drop every row older than the window; returns how many went. Whole day files before
        the cutoff's day go; the cutoff's own day file keeps its newer rows."""
        cutoff = now - self.window
        gone = 0
        for path in sorted(logs_dir(self.home).glob("heartbeat-????-??-??.jsonl")):
            day = date.fromisoformat(path.stem.removeprefix("heartbeat-"))
            if day > cutoff.date():
                continue
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [line for line in lines if _when(json.loads(line)["at"]) >= cutoff]
            gone += len(lines) - len(kept)
            if kept:
                path.write_text("".join(kept), encoding="utf-8")
            else:
                path.unlink()
        return gone

    def rows(self, since: datetime | None = None) -> list[Heartbeat]:
        """Every kept row at or after `since`, oldest first."""
        found: list[Heartbeat] = []
        for path in sorted(logs_dir(self.home).glob("heartbeat-????-??-??.jsonl")):
            day = date.fromisoformat(path.stem.removeprefix("heartbeat-"))
            if since is not None and day < since.date():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                row = Heartbeat.model_validate_json(line)
                if since is None or _when(row.at) >= since:
                    found.append(row)
        return found


def latest(home: Path) -> dict[str, Heartbeat]:
    """The newest row per subject, keyed `<subject>:<id>`; empty before the first beat."""
    try:
        raw = json.loads((logs_dir(home) / LATEST).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return {key: Heartbeat.model_validate(value) for key, value in raw.items()}


def host_kinds(home: Path) -> Mapping[str, frozenset[str]]:
    """Each host's node kinds from its newest row, by host id (its placement name)."""
    return {
        row.id: frozenset(row.node_kinds) for row in latest(home).values() if row.subject == "host"
    }


def _health(home: Path) -> dict[str, object]:
    try:
        raw: object = json.loads((logs_dir(home) / CONNECTIONS).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return cast("dict[str, object]", raw) if isinstance(raw, dict) else {}


def connection_readings(home: Path) -> tuple[ConnectionReading, ...]:
    """The health workflow's newest reading per connection; empty before its first run."""
    rows = _health(home).get("readings")
    if not isinstance(rows, list):
        return ()
    found: list[ConnectionReading] = []
    for row in cast("list[object]", rows):
        try:
            found.append(ConnectionReading.model_validate(row))
        except ValueError:
            continue
    return tuple(found)


def connection_words(home: Path) -> Mapping[str, str]:
    """Each connection's reading word by connection id, which preflight checks before a fire."""
    return {reading.connection: reading.word for reading in connection_readings(home)}


def measured_clock_offset(home: Path) -> int | None:
    """The largest absolute provider clock offset the connections measured, signed as measured."""
    stored = _health(home).get("clock_offset_ms")
    if isinstance(stored, int) and not isinstance(stored, bool):
        return stored
    offsets = [
        reading.clock_offset_ms
        for reading in connection_readings(home)
        if reading.clock_offset_ms is not None
    ]
    return max(offsets, key=abs) if offsets else None


def _attached(home: Path, row: Heartbeat) -> Heartbeat:
    """A host row carries the newest connection readings, so one row answers both questions."""
    if row.subject != "host" or row.connections:
        return row
    readings = connection_readings(home)
    if not readings:
        return row
    return row.model_copy(
        update={"connections": readings, "clock_offset_ms": measured_clock_offset(home)}
    )


class HubReply(BaseModel):
    """What the Hub answers a pushed row with: the authoritative pause flag and the claim batch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    autonomy_paused: bool
    claims_renewed: int = 0


class Pause(BaseModel):
    """The pause flag this host acts on, and how sure it is.

    `paused` is the last flag the Hub gave (or this host's own switch before the first reply).
    `heard_at` is the last time the Hub answered; past `UNKNOWN_AFTER_S` the flag is still
    honoured, and `state` says the host no longer knows it is current (AD-65).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    paused: bool = False
    heard_at: float | None = None
    source: str = "local"
    """`local` before the Hub ever answered; `hub` once it has."""

    def heard(self, reply: HubReply, *, at: float) -> Pause:
        return Pause(paused=reply.autonomy_paused, heard_at=at, source="hub")

    def state(self, now: float) -> PauseState:
        if self.heard_at is None or now - self.heard_at < UNKNOWN_AFTER_S:
            return "known"
        return "unknown"

    def shows(self, now: float) -> str:
        """The one line a screen shows: the flag, or that the flag is nobody's current word."""
        if self.state(now) == "unknown":
            return UNKNOWN
        return "paused" if self.paused else "running"

    def flag(self, now: float) -> bool:
        """What the host honours: the last flag it knew, whatever the state (AD-65)."""
        return self.paused


class HubLink:
    """This host's side of the Hub's heartbeat route: push one row, adopt the reply."""

    def __init__(
        self,
        url: str,
        key: str,
        *,
        clock: Callable[[], float] = time.time,
        post: Callable[[str, Mapping[str, object], Mapping[str, str]], Mapping[str, object]]
        | None = None,
        pause: Pause | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.key = key
        self._clock = clock
        self._post = post or _post
        self.pause = pause or Pause()

    def push(self, row: Heartbeat) -> HubReply:
        """Send one row and read the reply; an unreachable Hub raises `OSError`."""
        now = self._clock()
        body = self._post(
            f"{self.url}{HEARTBEAT_ROUTE}",
            {"heartbeat": row.model_dump(mode="json")},
            {"Authorization": f"Bearer {self.key}"},
        )
        reply = HubReply.model_validate(body)
        self.pause = self.pause.heard(reply, at=now)
        return reply


def _post(url: str, body: Mapping[str, object], headers: Mapping[str, str]) -> Mapping[str, object]:
    request = urllib.request.Request(  # noqa: S310 (the home's own setting)
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as answer:  # noqa: S310
        return json.loads(answer.read())


def _when(text: str) -> datetime:
    found = datetime.fromisoformat(text)
    return found if found.tzinfo is not None else found.replace(tzinfo=UTC)
