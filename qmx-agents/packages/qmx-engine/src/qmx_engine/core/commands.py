"""The commands the core returns (AD-1). The driver carries each one out and records the result in
the ledger before it folds again."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

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
    ladder: JsonObject | None = None
    """What the failure ladder asks of this attempt: the role `candidate` a model step moved to, a
    doctor's repair `hint`, or `degrade` after a runaway breach. EP10 resolves it to a model."""


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
    detail: str | None = None
    """Which runaway limit was breached, for the digest line."""


@dataclass(frozen=True, slots=True)
class Degrade:
    """The runaway guard was breached under `on_runaway: degrade`: the run goes on once with its
    model nodes on their role's cheapest candidate, and pauses on the next breach (AD-16)."""

    detail: str


type Rung = Literal["retry", "account", "model", "doctor"]


@dataclass(frozen=True, slots=True)
class Climb:
    """Take one rung of the failure ladder for a failed slot (AD-16, SOLUTION-DESIGN 10.2). The
    driver records it as `ladder_step`; a `retry` waits `seconds` on the run's clock first, and a
    `doctor` step asks the injected doctor and records its `doctor_verdict`."""

    node_id: str
    iteration: int
    partition: int | None
    attempt: int
    step: Rung
    reason: str
    seconds: int | None = None
    candidate: str | None = None
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class Finish:
    """Every node settled. `outputs` holds each finished sink node's outputs by node id, as a list
    in partition order for a node that fanned out."""

    outputs: JsonObject


@dataclass(frozen=True, slots=True)
class Park:
    """End the run `failed` (reason `parked`) until the operator resumes it. A park that ends a
    slot's ladder names the slot."""

    reason: str
    node_id: str | None = None
    iteration: int = 0
    partition: int | None = None
    attempt: int | None = None


type Command = StartNode | Hold | UseMemo | Wait | Pause | Degrade | Climb | Finish | Park


def encode(commands: list[Command]) -> bytes:
    """The canonical bytes of a command list, for comparing two folds."""
    return encoded([{"command": type(c).__name__, **asdict(c)} for c in commands])
