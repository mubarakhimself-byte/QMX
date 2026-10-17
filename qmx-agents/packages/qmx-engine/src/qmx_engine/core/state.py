"""The run state the core folds out of the ledger. It is derived on every call and never stored
(SOLUTION-DESIGN 3.1).

A run is folded in passes. `run_resumed` opens a new pass: every slot starts pending again and
settles in that pass by a fresh attempt or a saved result. Memos, attempt counts, holds and spend
are kept for the whole run, so a later pass finds what an earlier one did.

The unit the core schedules is a slot: one node at one loop iteration and one fan-out partition.
A node outside a loop runs at iteration 0, and a node that does not fan out has partition None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, NamedTuple, Protocol

from pydantic import JsonValue

from qmx_engine.core.commands import Hold
from qmx_engine.definition.model import Node, Workflow

type JsonObject = dict[str, JsonValue]
type Phase = Literal["scheduled", "started", "finished", "failed", "waiting"]
type Ended = Literal["passed", "parked", "stopped"]


class Slot(NamedTuple):
    node_id: str
    iteration: int = 0
    partition: int | None = None


class EventView(Protocol):
    """What the core reads of a ledger event. `qmx_engine.ledger.events.Event` satisfies it; the
    core cannot import the ledger (AD-1)."""

    @property
    def seq(self) -> int: ...
    @property
    def run_id(self) -> str: ...
    @property
    def kind(self) -> str: ...
    @property
    def data(self) -> Mapping[str, JsonValue]: ...


@dataclass(frozen=True, slots=True)
class NodeRun:
    """One slot's progress in the current pass. `seq` is the event that last changed it, so
    finished partitions sort by arrival."""

    phase: Phase
    attempt: int
    memo_key: str
    seq: int = 0
    outputs: JsonObject | None = None
    error: str | None = None
    reason: str | None = None
    resume_at: str | None = None
    failure: Failure | None = None


@dataclass(frozen=True, slots=True)
class Failure:
    """What a `node_failed` said, for the ladder."""

    code: str
    signature: str
    retryable: bool
    effect_state: str


@dataclass(frozen=True, slots=True)
class Walk:
    """One slot's walk down the failure ladder (AD-16), from its first failure to its park. It
    lasts over every pass, so a resume goes on from the rung it reached; a park ends it, so an
    operator resume of a parked run walks again from the top."""

    steps: tuple[str, ...] = ()
    signatures: tuple[str, ...] = ()
    """Each failure's signature, in order."""
    retry_at: str | None = None
    """The latest retry's `resume_at`: the slot may not start again before it."""
    verdict: str | None = None
    hint: str | None = None


@dataclass(frozen=True, slots=True)
class Held:
    """A recorded `Hold`. It lasts over every pass, so a resume never restarts its clock."""

    resume_at: str | None
    event: str | None
    seq: int


@dataclass(frozen=True, slots=True)
class State:
    definition: Workflow
    run_id: str
    inputs: JsonValue
    now: str | None
    nodes: Mapping[Slot, NodeRun]
    """Current pass, by slot. A slot with no entry is pending or skipped."""
    memos: Mapping[str, JsonObject]
    """Memo fingerprint to the outputs a finished attempt saved, over every pass."""
    attempts: Mapping[Slot, int]
    """Slot to the highest attempt scheduled over every pass."""
    ended: Ended | None = None
    unfoldable: str | None = None
    """Why the fold stopped: an event this core cannot fold."""
    settings: Mapping[str, JsonValue] = field(default_factory=dict[str, JsonValue])
    """The settings `run_created` recorded, so every pass sizes chunks the same way."""
    holds: Mapping[Slot, Held] = field(default_factory=dict[Slot, Held])
    received: tuple[tuple[str, int], ...] = ()
    """Each `event_received` name with its seq."""
    spent: Mapping[Slot, int] = field(default_factory=dict[Slot, int])
    """Tokens the slot's attempts reported on their ending events, over every pass."""
    joins: Mapping[Slot, tuple[int, ...]] = field(default_factory=dict[Slot, tuple[int, ...]])
    """The partitions each join merged the first time it fired, over every pass, so a resume
    merges the same ones (AD-7) and a late arrival never gets in."""
    walks: Mapping[Slot, Walk] = field(default_factory=dict[Slot, Walk])
    runaway: Mapping[str, JsonValue] = field(default_factory=dict[str, JsonValue])
    """The runaway guard `run_created` recorded: limits, `deadline` and `on_runaway`."""
    tool_calls: int = 0
    degraded: bool = False


@dataclass(frozen=True, slots=True)
class Ready:
    node: Node
    inputs: JsonValue
    iteration: int = 0
    partition: int | None = None
    plan: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class Plan:
    """The current pass seen through the graph: what may start now, what to hold, what waits on a
    hold, and the reason the run cannot go on, if any."""

    ready: list[Ready] = field(default_factory=list[Ready])
    holds: list[Hold] = field(default_factory=list[Hold])
    held: list[tuple[Slot, str | None]] = field(default_factory=list[tuple[Slot, str | None]])
    """Slots waiting on a recorded hold, with its `resume_at`."""
    unsettled: list[str] = field(default_factory=list[str])
    """Node ids with a slot in their current iteration that has not settled."""
    sinks: JsonObject = field(default_factory=dict[str, JsonValue])
    park: str | None = None
