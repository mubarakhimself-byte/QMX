"""The commands the core returns (AD-1). The driver carries each one out and records the result in
the ledger before it folds again."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from pydantic import JsonValue
from qmx_ledger.journal import encoded

type JsonObject = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class StartNode:
    """Run a fresh attempt. The fields are the core's half of `NodeJob` (SOLUTION-DESIGN 5.1)."""

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
    plan: JsonObject | None = None
    """What the core decided for this slot (its chunk, a join's merge, a loop's stop), recorded on
    `node_scheduled`."""


@dataclass(frozen=True, slots=True)
class Hold:
    """Record that a slot may not start yet: a `wait` node, or a join under a `timeout` watermark.
    The driver turns `seconds` into `resume_at` on the run's recorded clock and writes a
    `node_waiting` with no attempt (SOLUTION-DESIGN 3.2: written by core), so the core itself never
    does clock arithmetic (AD-6)."""

    node_id: str
    iteration: int
    partition: int | None
    seconds: int | None = None
    until: str | None = None
    event: str | None = None


@dataclass(frozen=True, slots=True)
class UseMemo:
    """Settle the node with its saved outputs: no executor call, no spend (AD-7)."""

    node_id: str
    iteration: int
    partition: int | None
    memo_key: str
    outputs: JsonObject


@dataclass(frozen=True, slots=True)
class Wait:
    """Nothing can start until a held or waiting node's time or event comes."""

    node_ids: tuple[str, ...]
    resume_at: str | None


@dataclass(frozen=True, slots=True)
class Pause:
    """Every unfinished node waits on a usage limit or the runaway guard: pause the run."""

    reason: str
    resume_at: str | None


@dataclass(frozen=True, slots=True)
class Finish:
    """Every node settled. `outputs` holds each finished sink node's outputs by node id, as a list
    in partition order for a node that fanned out."""

    outputs: JsonObject


@dataclass(frozen=True, slots=True)
class Park:
    """End the run `failed` until the operator resumes it."""

    reason: str


type Command = StartNode | Hold | UseMemo | Wait | Pause | Finish | Park


def encode(commands: list[Command]) -> bytes:
    """The canonical bytes of a command list, for comparing two folds."""
    return encoded([{"command": type(c).__name__, **asdict(c)} for c in commands])
