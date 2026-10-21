"""The node contract (AD-4, SOLUTION-DESIGN 5.1): an `Executor` runs one `NodeJob` and returns one
`NodeResult`.

The span of 5.1's results is not a field here: the ledger derives it from `node_started` and the
ending event (EP4). `step` turns a set of executors into the worker half of a driver, so
`core.simulate` can run them without the core importing an executor.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import JsonValue
from qma.harness import StuckCall
from qmx_ledger.journal import fingerprint

from qmx_engine.core.commands import StartNode
from qmx_engine.ledger.signature import signature

type JsonObject = dict[str, JsonValue]
type Mode = Literal["live", "test"]
type EffectState = Literal["before", "after", "unknown"]


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
    timeouts: JsonObject | None = None
    pinned_outputs: JsonObject | None = None
    session: str | None = None
    """The chat an `agent` attempt picks up again: its slot's last chat, when the engine died
    mid-attempt."""


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
    """An executor that waits on a process or another run. Only the runner's worker awaits it;
    `step` runs plain `Executor`s."""

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


def step(
    executors: Mapping[str, Executor], *, mode: Mode = "test"
) -> Callable[[StartNode], list[tuple[str, JsonObject]]]:
    """Run each `StartNode` on the executor registered for its node's `type`."""

    def run(command: StartNode) -> list[tuple[str, JsonObject]]:
        attempt: JsonObject = {
            "node_id": command.node_id,
            "iteration": command.iteration,
            "partition": command.partition,
            "attempt": command.attempt,
        }
        job = NodeJob(
            run_id=command.run_id,
            node_id=command.node_id,
            iteration=command.iteration,
            partition=command.partition,
            attempt=command.attempt,
            memo_key=command.memo_key,
            idempotency_key=command.idempotency_key,
            node_definition=command.node_definition,
            inputs=command.inputs,
            now=command.now,
            mode=mode,
        )
        executor = executors.get(str(command.node_definition.get("type")))
        started = ("node_started", attempt | {"idempotency_key": command.idempotency_key})
        if executor is None:
            message = f"no executor for node type {command.node_definition.get('type')!r}"
            result: NodeResult = Failed(
                "no_executor", message, signature("no_executor", message), retryable=False
            )
        else:
            result = executor.run(job)
        return [started, *((kind, attempt | data) for kind, data in ending(result))]

    return run
