"""The run state the core folds out of the ledger. It is derived on every call and never stored
(SOLUTION-DESIGN 3.1).

A run is folded in passes. `run_resumed` opens a new pass: every node starts pending again and
settles in that pass by a fresh attempt or a saved result. Saved results (memos) are kept for the
whole run, so a later pass finds what an earlier one finished.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import JsonValue

from qmx_engine.definition.model import Node, Workflow

type JsonObject = dict[str, JsonValue]
type Phase = Literal["scheduled", "started", "finished", "failed", "waiting"]
type Ended = Literal["passed", "parked", "stopped"]


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
    """One node's progress in the current pass."""

    phase: Phase
    attempt: int
    memo_key: str
    outputs: JsonObject | None = None
    error: str | None = None
    reason: str | None = None
    resume_at: str | None = None


@dataclass(frozen=True, slots=True)
class State:
    definition: Workflow
    run_id: str
    inputs: JsonValue
    now: str | None
    nodes: Mapping[str, NodeRun]
    """Current pass, by node id. A node with no entry is pending or skipped."""
    memos: Mapping[str, JsonObject]
    """Memo fingerprint to the outputs a finished attempt saved, over every pass."""
    attempts: Mapping[str, int]
    """Node id to the highest attempt scheduled over every pass."""
    ended: Ended | None = None
    unfoldable: str | None = None
    """Why the fold stopped: an event this core cannot fold."""


@dataclass(frozen=True, slots=True)
class Ready:
    node: Node
    inputs: JsonValue


@dataclass(frozen=True, slots=True)
class Plan:
    """The current pass seen through the graph: what may start now and what will never run."""

    ready: list[Ready] = field(default_factory=list[Ready])
    skipped: frozenset[str] = frozenset()
