"""Two states computed at read and never stored: a hypothesis's status (Library AD-23) and the
health a store opened in (Library AD-16).

A result links to a `hypothesis` with `tests` and says what it shows in its own `outcome` field
(`supports`, `refutes` or `inconclusive`), because an edge is about, never true (AD-4). Results
whose evidence is quarantined or corrected (AD-22) are left out; a superseded input still counts,
since the result stays true of the data it ran on (Claude's default). A result with a
`regime:<name>` tag counts in that regime. Prose that says "supported" with no result behind it
counts for nothing.

A store survives a torn append. `inspect_logs` reads every append-only log once and classifies the
damage: a last line with no newline or that does not parse, NUL bytes included, is `TornTail` and
the store may quarantine it and open; a bad line before the last is `BadLine` and the store opens
read-only until a replica restores it.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from qmx_library.port import LibraryRefused, ObjectId

if TYPE_CHECKING:
    from qmx_library.principal import Principal
    from qmx_library.store import Store

type Verdict = Literal["supported", "refuted", "open", "mixed"]

IGNORED: Final = frozenset({"quarantined", "corrected"})
REGIME: Final = "regime:"

type Health = Literal["open", "torn", "read_only"]
"""How a store opened. `torn` means a last line was moved to `quarantine/` and the store opens
anyway; `read_only` means a line before the last does not parse and nothing may be written."""

QUARANTINE: Final = "quarantine"
"""Where a log's torn last line goes, at its own path under the store root (AD-16)."""


@dataclass(frozen=True, slots=True)
class TornTail:
    """A log's last line with no newline or that does not parse, NUL bytes included (AD-16)."""

    log: str
    """The log's path under the store root, `refs/log.jsonl`."""
    start: int
    """The byte offset the line starts at, where the log is cut."""
    tail: bytes
    """The line itself, without its newline, kept under `quarantine/`."""

    @property
    def alarm(self) -> str:
        return f"library:torn:{self.log}"


@dataclass(frozen=True, slots=True)
class BadLine:
    """A line before the last that does not parse: the index cannot be trusted, so no writes."""

    log: str
    line: int


type Damage = TornTail | BadLine


@dataclass(frozen=True, slots=True)
class StoreState:
    """What `Store.open` found in the logs and did about them."""

    health: Health = "open"
    alarms: tuple[str, ...] = ()
    """`library:torn:<log>` for every torn tail that was quarantined."""
    incident: str | None = None
    """The line that stayed, `<log> line <n>`, when the store opened read-only."""


def inspect_logs(root: Path) -> tuple[Damage, ...]:
    """Every append-only log under `root`, read once and classified. Reads only: the caller
    quarantines a torn tail and cuts it, so this can run before the index is built."""
    logs = [
        root / "refs" / "log.jsonl",
        *(root / "edges").glob("*.jsonl"),
        root / "annotations" / "log.jsonl",
    ]
    return tuple(found for path in logs if path.exists() for found in _scan(root, path))


def _scan(root: Path, path: Path) -> Iterator[Damage]:
    log = path.relative_to(root).as_posix()
    with path.open("rb") as handle:
        start = 0
        line = 0
        while raw := handle.readline():
            line += 1
            last = not handle.peek(1)
            if raw.strip():
                if not _record(raw):
                    if last:
                        yield TornTail(log, start, raw.removesuffix(b"\n"))
                    else:
                        yield BadLine(log, line)
                elif last and not raw.endswith(b"\n"):
                    yield TornTail(log, start, raw)
            start += len(raw)


def _record(raw: bytes) -> bool:
    """One log line parses as the JSON object it must be, with no NUL byte in it."""
    if b"\x00" in raw:
        return False
    try:
        return isinstance(json.loads(raw), dict)
    except ValueError:
        return False


@dataclass(frozen=True, slots=True)
class Status:
    status: Verdict
    by_regime: Mapping[str, Verdict] = field(default_factory=dict[str, Verdict])
    """Each regime's own status, for results tagged `regime:<name>`."""
    counted: tuple[ObjectId, ...] = ()
    ignored: tuple[ObjectId, ...] = ()
    """Results that test the hypothesis but carry a quarantined or corrected mark."""


def verdict(outcomes: Iterable[str]) -> Verdict:
    found = set(outcomes)
    if {"supports", "refutes"} <= found:
        return "mixed"
    if "supports" in found:
        return "supported"
    if "refutes" in found:
        return "refuted"
    return "open"


def status(store: Store, who: Principal, hypothesis: str) -> Status:
    """The status of the `hypothesis` item from the results that test any of its objects."""
    objects = [object_id for object_id, _ in store.placed(hypothesis, "hypothesis", None)]
    if not objects:
        raise LibraryRefused("not_found", f"no hypothesis {hypothesis}")
    steps = store.walk(who, objects, ["tests"], "in", depth=1)
    outcomes: list[str] = []
    regimes: defaultdict[str, list[str]] = defaultdict(list)
    counted: list[ObjectId] = []
    ignored: list[ObjectId] = []
    for step in steps:
        view = store.get(who, step.object_id)
        outcome = view.fields.get("outcome")
        if not isinstance(outcome, str):
            continue
        if store.marks(who, view.object_id).worst in IGNORED:
            ignored.append(view.object_id)
            continue
        counted.append(view.object_id)
        outcomes.append(outcome)
        tags = view.annotations.get("tags")
        for tag in tags if isinstance(tags, list) else []:
            if isinstance(tag, str) and tag.startswith(REGIME):
                regimes[tag.removeprefix(REGIME)].append(outcome)
    by_regime: dict[str, Verdict] = {n: verdict(found) for n, found in sorted(regimes.items())}
    return Status(verdict(outcomes), by_regime, tuple(counted), tuple(ignored))
