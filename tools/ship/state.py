"""state.json: the one record of a run. Schema in README.md.

Status changes go through `State.move`, which refuses any move the TRANSITIONS table does not list and
logs an event. Every write holds `state.lock`, so two scripts never lose each other's update.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import enum
import json
import os
import time
from pathlib import Path
from typing import Iterator

from ship.layout import Program
from ship.proc import pid_alive

SCHEMA = 1


class Status(enum.StrEnum):
    PENDING = "pending"  # not dispatched yet
    HELD = "held"  # a builder holds the seat
    DEAD = "dead"  # the holder died (restart, crash, usage limit); the next dispatch is a restart
    READY = "ready"  # verify_ready passed and the PR is open
    RED = "red"  # verify_ready or slice_checks failed, or landing hit a conflict; awaits a fix round
    CHECKED = "checked"  # slice checks passed at `head`
    LANDED = "landed"  # on the build branch
    PARKED = "parked"  # stopped for this run; see `reason`
    BLOCKED_BY = "blocked-by"  # a dependency parked; see `blocked_by`


S = Status
TRANSITIONS: dict[Status, frozenset[Status]] = {
    S.PENDING: frozenset({S.HELD, S.PARKED, S.BLOCKED_BY}),
    S.HELD: frozenset({S.READY, S.RED, S.DEAD, S.PARKED}),
    S.DEAD: frozenset({S.HELD, S.PARKED}),
    S.READY: frozenset({S.CHECKED, S.RED, S.HELD, S.DEAD, S.PARKED}),
    S.RED: frozenset({S.HELD, S.DEAD, S.PARKED}),
    S.CHECKED: frozenset({S.CHECKED, S.RED, S.LANDED, S.HELD, S.DEAD, S.PARKED}),
    S.LANDED: frozenset(),
    S.PARKED: frozenset(),
    S.BLOCKED_BY: frozenset(),
}
# Slices that own a branch and files that are not on the build branch yet.
IN_FLIGHT = frozenset({S.HELD, S.DEAD, S.READY, S.RED, S.CHECKED})


class ParkCause(enum.StrEnum):
    ROUNDS = "rounds"  # max_attempts quality rounds used; counts toward the breaker
    DISPUTE = "dispute"  # an open DISPUTE after round 2; counts toward the breaker
    BRIEF_MISMATCH = "brief-mismatch"  # a brief fact failed at dispatch; a planning fault
    MANUAL = "manual"  # the coordinator or the operator parked it


QUALITY_CAUSES = frozenset({ParkCause.ROUNDS, ParkCause.DISPUTE})


class StateError(Exception):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


@dataclasses.dataclass
class Holder:
    dispatch_id: str
    attempt: int
    restart: int
    started: str


@dataclasses.dataclass
class Slice:
    id: str
    name: str
    depends_on: list[str]
    files: list[str]
    size: str = ""
    status: Status = S.PENDING
    reason: str = ""
    blocked_by: str | None = None
    attempts: int = 0  # quality rounds started; parks and the breaker read only this
    restarts: int = 0  # infra restarts (crash, usage limit, power); never parks a slice
    holder: Holder | None = None
    parent: str | None = None  # build-branch tip the slice branch was cut from
    head: str | None = None  # sha verify_ready accepted
    pr: str | None = None
    patch_id: str | None = None
    landed_sha: str | None = None
    seen_sha: str | None = None  # last remote sha `status` saw, for liveness
    seen_at: str | None = None

    @property
    def branch(self) -> str:
        return f"slice/{self.id}"


@dataclasses.dataclass
class State:
    repo: str
    build_branch: str
    remote: str
    worktree_root: str
    slices: dict[str, Slice]
    events: list[dict] = dataclasses.field(default_factory=list)
    usage_reset_at: str | None = None
    last_green: str | None = None  # build tip of the last green nightly
    nightly: dict = dataclasses.field(default_factory=dict)
    schema: int = SCHEMA

    def worktree(self, slice_id: str) -> Path:
        return Path(self.worktree_root) / f"slice-{slice_id}"

    def log(self, kind: str, slice_id: str | None = None, **detail: object) -> None:
        self.events.append({"at": now_iso(), "kind": kind, "slice": slice_id, **detail})

    def move(self, slice_id: str, to: Status, reason: str = "") -> None:
        sl = self.slices[slice_id]
        if to not in TRANSITIONS[sl.status]:
            raise StateError(f"{slice_id}: {sl.status} -> {to} is not allowed")
        self.log("status", slice_id, **{"from": str(sl.status), "to": str(to), "reason": reason})
        sl.status = to
        sl.reason = reason

    def park(self, slice_id: str, cause: ParkCause, detail: str) -> list[str]:
        """Park a slice and mark every pending slice that needs it, directly or not, blocked-by it."""
        self.move(slice_id, S.PARKED, f"{cause}: {detail}")
        self.events[-1]["cause"] = str(cause)
        blocked = []
        for dep_id in self.dependents(slice_id):
            dep = self.slices[dep_id]
            if dep.status == S.PENDING:
                self.move(dep_id, S.BLOCKED_BY, f"needs {slice_id}")
                dep.blocked_by = slice_id
                blocked.append(dep_id)
        return blocked

    def dependents(self, slice_id: str) -> list[str]:
        found: list[str] = []
        frontier = [slice_id]
        while frontier:
            current = frontier.pop()
            for sl in self.slices.values():
                if current in sl.depends_on and sl.id not in found:
                    found.append(sl.id)
                    frontier.append(sl.id)
        return sorted(found)

    def breaker_tripped(self, limit: int) -> bool:
        """`limit` quality parks with no landing between them."""
        run = 0
        for event in self.events:
            if event["kind"] != "status":
                continue
            if event["to"] == S.LANDED:
                run = 0
            elif event["to"] == S.PARKED and event.get("cause") in QUALITY_CAUSES:
                run += 1
        return run >= limit

    def held_count(self) -> int:
        return sum(1 for sl in self.slices.values() if sl.status == S.HELD)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=False) + "\n"

    @classmethod
    def from_json(cls, text: str) -> State:
        raw = json.loads(text)
        if raw.get("schema") != SCHEMA:
            raise StateError(f"state.json schema {raw.get('schema')} is not {SCHEMA}")
        slices = {}
        for key, item in raw.pop("slices").items():
            holder = Holder(**item.pop("holder")) if item.get("holder") else None
            item.pop("holder", None)
            item["status"] = Status(item["status"])
            slices[key] = Slice(holder=holder, **item)
        return cls(slices=slices, **raw)


def load(program: Program) -> State:
    return State.from_json(program.state.read_text("utf-8"))


def save(program: Program, state: State) -> None:
    tmp = program.state.with_suffix(".json.tmp")
    tmp.write_text(state.to_json(), "utf-8")
    for _ in range(50):  # Windows refuses the replace while a reader has the file open
        try:
            os.replace(tmp, program.state)
            return
        except PermissionError:
            time.sleep(0.1)
    os.replace(tmp, program.state)


def _age_s(path: Path) -> float:
    try:
        return time.time() - path.stat().st_mtime
    except OSError:
        return 1e9


@contextlib.contextmanager
def locked(program: Program) -> Iterator[State]:
    """Load, yield and save state.json under an exclusive lock. A dead holder's lock is taken over."""
    while True:
        try:
            fd = os.open(program.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                owner = int(program.lock.read_text("utf-8").strip() or 0)
            except (OSError, ValueError):
                owner = 0
            if owner == os.getpid():
                raise StateError("state.lock taken twice by one process")
            young = _age_s(program.lock) < 10  # the creator may not have written its pid yet
            if (owner and pid_alive(owner)) or (not owner and young):
                time.sleep(0.2)
                continue
            program.lock.unlink(missing_ok=True)
    try:
        state = load(program)
        yield state
        save(program, state)
    finally:
        program.lock.unlink(missing_ok=True)
