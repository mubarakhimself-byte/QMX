"""One heartbeat row per subject per interval (AD-65), and the home's local log of them.

A host, a remote run sidecar and every supervised app write the same `Heartbeat` row. The live
facts travel only here: CPU, memory, capacity in use per class, intent claims (empty until LIB4),
the version and node kinds a host runs, and the pause flag it sees. Preflight reads a host's
kinds before it places a node there (AD-20), and the `ops` toolset reads the rows.

The home keeps rows as JSONL day files `logs/heartbeat-<YYYY-MM-DD>.jsonl` for
`heartbeat.window_days` days, plus `logs/heartbeat-latest.json`, the newest row per subject, so
a reader never scans a day file. The host is the one writer: it holds the home's lock. Spend per
subject is a reading over these rows, never a cap.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field
from qmx_ledger.journal import fingerprint

from qmx_engine.definition.registry import BASE_KINDS

type Subject = Literal["host", "run", "app"]

LOGS: Final = "logs"
LATEST: Final = "heartbeat-latest.json"


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
    blob_cache_bytes: int | None = None
    free_disk_bytes: int | None = None


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
        found = list(rows)
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


def _when(text: str) -> datetime:
    found = datetime.fromisoformat(text)
    return found if found.tzinfo is not None else found.replace(tzinfo=UTC)
