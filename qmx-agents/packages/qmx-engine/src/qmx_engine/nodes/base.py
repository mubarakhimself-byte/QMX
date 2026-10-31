"""The node contract (AD-4, SOLUTION-DESIGN 5.1): an `Executor` runs one `NodeJob` and returns one
`NodeResult`.

The span of 5.1's results is not a field here: the ledger derives it from `node_started` and the
ending event (EP4).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import JsonValue
from qma.harness import StuckCall
from qmx_ledger.journal import fingerprint

type JsonObject = dict[str, JsonValue]
type Mode = Literal["live", "test"]
type EffectState = Literal["before", "after", "unknown"]
type PlacedBy = Literal["default", "chosen", "spilled", "stand_in"]
"""Why an attempt ran where it did (AD-72): the node named no place, it named this one first, the
places before this one were not ready, or this place stood in for This PC (the stand-in round)."""


def where_ran(job: NodeJob, place: str, machine: str) -> JsonObject:
    """What every attempt records of where it ran (AD-72): `place`, the place that ran it, by its
    name then; its stable id; the device it ran on; and why it ran there."""
    stable = job.place_id if place == job.placement and job.place_id else place
    return {"place": place, "place_id": stable, "machine": machine, "placed_by": job.placed_by}


@dataclass(frozen=True, slots=True)
class NodeJob:
    run_id: str
    node_id: str
    iteration: int
    partition: int | None
    attempt: int
    memo_key: str
    idempotency_key: str
    node_definition: JsonObject
    inputs: JsonValue
    now: str | None
    mode: Mode = "test"
    resolved_model: JsonObject | None = None
    credentials: Mapping[str, str] = field(default_factory=dict[str, str])
    workspace: str | None = None
    placement: str = "pc"
    place_id: str = ""
    """The stable id of `placement` in the place list, which a rename keeps; its name when empty."""
    placed_by: PlacedBy = "default"
    timeouts: JsonObject | None = None
    pinned_outputs: JsonObject | None = None
    session: str | None = None
    """The chat an `agent` attempt picks up again: its slot's last chat, when the engine died
    mid-attempt."""
    priority: int = 0
    """The run's priority: waiting work is served higher first, then oldest first (AD-58)."""


@dataclass(frozen=True, slots=True)
class Ok:
    outputs: JsonObject
    """Outputs by port. A port left out carries nothing downstream."""
    artifacts: tuple[str, ...] = ()
    verdict: str | None = None
    """A grader's `pass` or `fail`, which the span records."""
    span: JsonObject = field(default_factory=dict[str, JsonValue])
    """More ending data for the span, such as a model call's `tokens`."""

    @property
    def output_hash(self) -> str:
        return fingerprint(self.outputs)


@dataclass(frozen=True, slots=True)
class Failed:
    code: str
    message: str
    signature: str
    retryable: bool
    effect_state: EffectState = "before"
    span: JsonObject = field(default_factory=dict[str, JsonValue])


@dataclass(frozen=True, slots=True)
class Waiting:
    reason: str
    resume_at: str | None = None
    event: str | None = None
    span: JsonObject = field(default_factory=dict[str, JsonValue])


@dataclass(frozen=True, slots=True)
class Look:
    """What an attempt in flight shows the stuck detector at one tick (AD-16): a count that moves
    with its progress, a model request in flight, a recorded wait, an open tool call, the process
    whose CPU and IO count as the tool's progress, and an agent's finished tool calls."""

    progress: int
    in_flight: bool = False
    waiting: bool = False
    tool_open: bool = False
    pid: int | None = None
    children_only: bool = False
    """Only the processes under `pid` do the attempt's work; `pid` itself is a chat's CLI."""
    calls: tuple[StuckCall, ...] | None = None


@dataclass(frozen=True, slots=True)
class Gate:
    ask: str
    options: tuple[str, ...]


type NodeResult = Ok | Failed | Waiting | Gate


class Executor(Protocol):
    def run(self, job: NodeJob) -> NodeResult: ...


class AsyncExecutor(Protocol):
    """An executor that waits on a process or another run; the runner's worker awaits it."""

    async def run(self, job: NodeJob) -> NodeResult: ...


def ending(result: NodeResult) -> list[tuple[str, JsonObject]]:
    """The ledger events that record a result, without the attempt keys."""
    match result:
        case Ok():
            finished: JsonObject = {"outputs": result.outputs, "output_hash": result.output_hash}
            if result.artifacts:
                finished["artifacts"] = list(result.artifacts)
            if result.verdict is not None:
                finished["verdict"] = result.verdict
            return [("node_finished", result.span | finished)]
        case Failed():
            return [
                (
                    "node_failed",
                    result.span
                    | {
                        "code": result.code,
                        "message": result.message,
                        "signature": result.signature,
                        "retryable": result.retryable,
                        "effect_state": result.effect_state,
                    },
                )
            ]
        case Waiting():
            data: JsonObject = {"reason": result.reason, "resume_at": result.resume_at}
            return [("node_waiting", result.span | data | {"event": result.event})]
        case Gate():
            return [
                ("gate_opened", {"ask": result.ask, "options": list(result.options)}),
                ("node_waiting", {"reason": "gate", "resume_at": None}),
            ]
