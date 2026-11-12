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
    S.RED: frozenset({S.RED, S.CHECKED, S.HELD, S.DEAD, S.PARKED}),
    S.CHECKED: frozenset({S.CHECKED, S.READY, S.RED, S.LANDED, S.HELD, S.DEAD, S.PARKED}),
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
    ask: str = ""  # the SCOPE.md ask it serves, from SLICES.md's `ask` column
    checkpoint: str = ""  # the stop point it lands in, from SLICES.md's `stop` column; "" when there is none
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
    merged: list[str] = dataclasses.field(default_factory=list)  # checkpoints merged into the target, in order
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
        return self.block_dependents(slice_id, f"needs {slice_id}")

    def block_dependents(self, slice_id: str, reason: str) -> list[str]:
        """Mark every pending slice that needs `slice_id`, directly or not, blocked-by it."""
        blocked = []
        for dep_id in self.dependents(slice_id):
            dep = self.slices[dep_id]
            if dep.status == S.PENDING:
                self.move(dep_id, S.BLOCKED_BY, reason)
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

    def checkpoints(self) -> list[str]:
        """Checkpoint ids in the order SLICES.md first names them."""
        return list(dict.fromkeys(sl.checkpoint for sl in self.slices.values()))

    def open_checkpoint(self) -> str | None:
        """The first checkpoint not merged yet: its slices build and land now."""
        return next((c for c in self.checkpoints() if c not in self.merged), None)

    def ahead(self, slice_id: str) -> int:
        """How far the slice's checkpoint sits after the open one. 1 may be pre-built but not landed."""
        order, current = self.checkpoints(), self.open_checkpoint()
        if current is None:
            return 0
        return order.index(self.slices[slice_id].checkpoint) - order.index(current)

    def checkpoint_files(self, checkpoint: str) -> list[str]:
        return [f for sl in self.slices.values() if sl.checkpoint == checkpoint for f in sl.files]

    def mark_merged(self, checkpoint: str) -> str:
        """Record a checkpoint merged into the target. Run twice, the second run changes nothing."""
        if checkpoint in self.merged:
            return f"checkpoint {checkpoint} was already recorded merged"
        current = self.open_checkpoint()
        if checkpoint != current:
            raise StateError(f"checkpoint {checkpoint} is not the open one ({current})")
        busy = sorted(s.id for s in self.slices.values() if s.checkpoint == checkpoint and s.status in IN_FLIGHT)
        if busy:
            raise StateError(f"checkpoint {checkpoint} still has slices in flight: {busy}")
        self.merged.append(checkpoint)
        self.log("merged", None, checkpoint=checkpoint)
        return f"checkpoint {checkpoint} merged; {self.open_checkpoint() or 'no checkpoint'} is open"

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
                raise StateError("state.lock taken twice by one process") from None
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
