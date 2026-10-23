"""Capacity and plan admission (rulings 26, 27, 90, 106; SOLUTION-DESIGN 7.4, 27.7; AD-9, AD-40,
AD-58).

Capacity is per resource class, one table per host, and every number in it is machine capacity,
never usage. An attempt takes exactly what its kind uses (`CLASSES`): `script`, `monitor` and a
local `rlm` kernel take a CPU slot; a container attempt also takes a container slot and a GPU
attempt a GPU slot. Every other kind takes nothing here: pure kinds use no machine, and a
chat-backed node (`agent`, a plan-row `llm`) takes its slot from the harness slot table when it
sends, which is the only chat-slot counter and keeps the Interactive reserve. Waiting work is
served by the run's priority, higher first, then by when it began to wait, so a low-priority
fan-out yields to a higher run between chunks.

QMX sets no usage limit of its own: there is no background share and no budget, so a plan attempt
waits only when a plan window is used up, as `waiting(limit, resume_at)` with the window's reset
time plus `limits.slack`, and a refused send waits the same way. Nothing here asks the operator
(ruling 27). A refusal that no reset lifts (the overage stop, a refused key row) is not a limit
wait: the attempt fails `unavailable` and the failure ladder takes it.

A key or GPT attempt also takes the router's pool lease for its row, under the attempt's affinity
(AD-9, AD-12, AD-34): the provider's own window is the only limit there, and an account the pool
has none of is a failure the ladder sees, not an exception. The lease is given back when the call
ends; the router's own affinity keeps a run's chunks on one account while it serves them.
"""

from __future__ import annotations

import asyncio
import contextlib
import heapq
import itertools
import os
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Final, Literal, cast

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, Waiting
from qmx_engine.ports.harness_adapter import HarnessPort, PlanUse
from qmx_engine.ports.router import Refused, adopted
from qmx_engine.roles import PLAN, Candidate

type Held = Waiting | Failed
type SlotClass = Literal["cpu", "container", "gpu"]
type Waiter = tuple[int, int, asyncio.Future[None]]

CLASSES: Final[Mapping[str, SlotClass]] = {"script": "cpu", "monitor": "cpu", "rlm": "cpu"}
"""The kinds that take a slot of their own; every kind not named here takes none."""
PLACEMENT_CLASSES: Final[Mapping[str, SlotClass]] = {"container": "container", "gpu": "gpu"}
"""The placements whose attempts also take a slot of that class."""
SETTINGS: Final[Mapping[SlotClass, str]] = {
    "cpu": "placement.pc.cpu_slots",
    "container": "placement.pc.container_slots",
    "gpu": "placement.pc.gpu_slots",
}
MIB: Final = 1024 * 1024
MEMORY_PARAM: Final = "memory_mb"
"""Where a node declares the RAM its attempt needs: `parameters.memory_mb`. A node that declares
none reserves nothing, so a kind the host has no measurement for still runs."""


def setting(settings: Mapping[str, object], key: str, default: float) -> float:
    found = settings.get(key)
    return (
        float(found) if isinstance(found, int | float) and not isinstance(found, bool) else default
    )


@dataclass
class Slots:
    """A counting semaphore that serves its waiters by priority, higher first, then age."""

    size: int
    used: int = 0
    queue: list[Waiter] = field(default_factory=list[Waiter])
    order: itertools.count[int] = field(default_factory=itertools.count)

    async def take(self, priority: int) -> None:
        waiter = asyncio.get_running_loop().create_future()
        heapq.heappush(self.queue, (-priority, next(self.order), waiter))
        self.wake()
        try:
            await waiter
        except asyncio.CancelledError:
            if waiter.done() and not waiter.cancelled():
                self.give()
            raise

    def give(self) -> None:
        self.used -= 1
        self.wake()

    def wake(self) -> None:
        while self.queue and self.used < self.size:
            _, _, waiter = heapq.heappop(self.queue)
            if not waiter.done():
                self.used += 1
                waiter.set_result(None)


@dataclass
class Memory:
    """The RAM a host can give and the memory its attempts have declared (AD-58, F39, D-11).

    `free_bytes` is the host's live reading from its own heartbeat; `None` until the first beat,
    when nothing is refused. An admitted attempt holds the memory its node declared, and the size
    one of this host's sessions really reaches replaces every declaration below it when the
    heartbeat measures it. No budget and no cap: this is the machine's own room, so the next
    attempt waits for room or goes to another placement.
    """

    free_bytes: int | None = None
    held: dict[str, int] = field(default_factory=dict[str, int])

    def observe(self, free_bytes: int) -> None:
        """Take the host's newest free-RAM reading."""
        self.free_bytes = free_bytes

    def observe_session(self, session_bytes: int) -> None:
        """Replace every reservation that declared less than a session of this host really holds."""
        for key, reserved in self.held.items():
            self.held[key] = max(reserved, session_bytes)

    def room(self) -> int | None:
        """Bytes an attempt may still reserve, or None while no reading has arrived."""
        if self.free_bytes is None:
            return None
        return self.free_bytes - sum(self.held.values())

    def take(self, key: str, declared: int) -> bool:
        """Hold an attempt's declared memory; False when the host has no room for it."""
        room = self.room()
        if room is not None and declared > room:
            return False
        self.held[key] = declared
        return True

    def give(self, key: str) -> None:
        """Give a reservation back."""
        self.held.pop(key, None)


def declared_bytes(node_definition: Mapping[str, object]) -> int | None:
    """The memory a node declares for its attempt, or None when it declares none."""
    parameters = node_definition.get("parameters")
    if not isinstance(parameters, Mapping):
        return None
    declared = cast("Mapping[str, object]", parameters).get(MEMORY_PARAM)
    if isinstance(declared, int) and not isinstance(declared, bool) and declared > 0:
        return declared * MIB
    return None


def sessions_of(free_ram_bytes: int, session_bytes: int) -> int:
    """How many sessions a host's live free RAM holds: what AD-30's derived row reads now that
    the machine's figures are measured rather than written down (D-11)."""
    return max(0, free_ram_bytes // session_bytes) if session_bytes > 0 else 0


@dataclass
class Capacity:
    """One host's capacity table. A class whose setting is unset (`gpu_slots` on the PC) is not
    in the table, since no placement here has that hardware."""

    slots: dict[SlotClass, Slots]
    memory: Memory = field(default_factory=Memory)

    @classmethod
    def of(cls, settings: Mapping[str, object]) -> Capacity:
        """`cpu_slots` unset is the logical core count minus one."""
        found: dict[SlotClass, Slots] = {}
        for name, key in SETTINGS.items():
            value = settings.get(key)
            if name == "cpu" and value is None:
                value = (os.cpu_count() or 2) - 1
            if isinstance(value, int) and not isinstance(value, bool):
                found[name] = Slots(max(value, 1))
        return cls(found)

    def observe_free_ram(self, free_bytes: int) -> None:
        """Hand admission the host's newest free-RAM reading, from its heartbeat."""
        self.memory.observe(free_bytes)

    def observe_session(self, session_bytes: int) -> None:
        """Hand admission the measured size of one of this host's sessions."""
        self.memory.observe_session(session_bytes)

    def admit(self, key: str, node_definition: Mapping[str, object]) -> str | None:
        """Hold the memory this node declares, or say why it cannot run on this host."""
        declared = declared_bytes(node_definition)
        if declared is None:
            return None
        if self.memory.take(key, declared):
            return None
        room = self.memory.room()
        free = "no free-RAM reading yet" if room is None else f"{room // MIB} MB free"
        return f"{declared // MIB} MB declared, {free} after what other attempts hold"

    @contextlib.asynccontextmanager
    async def held(self, kind: str, placement: str, priority: int) -> AsyncGenerator[None]:
        """Hold every slot an attempt of `kind` on `placement` takes, taken in one fixed order
        so two attempts never wait on each other."""
        wanted = {CLASSES.get(kind), PLACEMENT_CLASSES.get(placement)}
        taken: list[Slots] = []
        try:
            for name in SETTINGS:
                if name in wanted and (slots := self.slots.get(name)) is not None:
                    await slots.take(priority)
                    taken.append(slots)
            yield
        finally:
            for slots in reversed(taken):
                slots.give()


def later(instant: str, seconds: float) -> str:
    return (datetime.fromisoformat(instant) + timedelta(seconds=seconds)).isoformat()


def held(resume_at: str, why: str) -> Waiting:
    return Waiting("limit", resume_at, span={"detail": why})


def unavailable(why: str, *, retryable: bool) -> Failed:
    return Failed("unavailable", why, signature("unavailable", why), retryable)


def limit_wait(use: PlanUse, slack: float) -> Held | None:
    """What a plan attempt does now: wait for a reset, fail, or None to run."""
    if use.stopped is not None:
        return unavailable(f"plan use is stopped: {use.stopped}", retryable=False)
    if use.blocked_until is not None:
        return held(later(use.blocked_until, slack), "a plan window is used up")
    return None


class Admission:
    """Whether a model attempt may start on its plan window. It counts no chat slot: the harness
    slot table does that when the attempt sends."""

    def __init__(self, harness: HarnessPort, settings: Mapping[str, object]) -> None:
        self.harness = harness
        self.settings = settings

    def slack(self) -> float:
        return setting(self.settings, "limits.slack", 60)

    async def check(self, candidate: Candidate) -> Held | None:
        """A plan candidate's wait or failure, or None. Key rows are never held here."""
        if candidate.profile != PLAN:
            return None
        return limit_wait(await self.harness.plan_use(), self.slack())

    async def refused(self, candidate: Candidate, reason: str) -> Held:
        """A refused send waits for the plan window that holds it, or fails when no reset lifts
        the refusal."""
        if candidate.profile == PLAN:
            wait = limit_wait(await self.harness.plan_use(), self.slack())
            if isinstance(wait, Waiting):
                return replace(wait, span={"detail": reason})
            if wait is not None:
                return wait
        return unavailable(reason, retryable=True)

    def hold(self, candidate: Candidate, affinity: str) -> Held | None:
        """Take the pool lease for a key or GPT attempt on its row, under `affinity`, or fail
        `unavailable` when the pool has no account that serves it. A plan row leases nothing."""
        port = adopted()
        if candidate.profile == PLAN or port is None:
            return None
        try:
            port.hold(provider=candidate.profile, model=candidate.model, affinity=affinity)
        except Refused as refused:
            return unavailable(str(refused), retryable=True)
        return None

    def let_go(self, affinity: str) -> None:
        """Give the attempt's pool lease back to the router."""
        port = adopted()
        if port is not None:
            port.let_go(affinity)
