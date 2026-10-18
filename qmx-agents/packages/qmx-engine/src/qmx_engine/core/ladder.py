"""The failure ladder and his limits (AD-16, SOLUTION-DESIGN 10.2).

`climb` picks the next rung for one failed slot from its `Walk`, in this order: an irreversible
step that failed after its effect parks, since any rerun would repeat it (AD-8); the same signature
twice goes straight to the doctor; then retry, account, model, doctor, park. An ending of unknown
outcome never reaches the ladder unless it may rerun: the runner opens a gate for it (EP7). The
account rung records `skipped: no pool` until the account pool packet (L2). Each call returns one
rung, so every step is in the ledger before the next is chosen.

An attempt the stuck detector ended in a loop parks at once with its summary, since a rerun would
loop again; one that did not converge walks the ladder like any other failure.

There is no runaway guard and no usage ceiling (AD-40). A `limits` block he wrote is checked
before any new attempt starts, which is at each turn end and every tick, since the driver folds
again on both. A breach never asks and never ends the run: no new attempt starts, the running ones
finish, and the run pauses with one `info` line until he resumes it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from pydantic import JsonValue

from qmx_engine.core.commands import Climb, Command, Park, Rung, StartNode
from qmx_engine.core.fold import used
from qmx_engine.core.state import Failure, JsonObject, NodeRun, Slot, State, Walk
from qmx_engine.definition.model import Node
from qmx_engine.definition.registry import REGISTRY

NO_POOL: Final = "skipped: no pool"
NO_DOCTOR: Final = "skipped: no doctor"
NOT_RERUN: Final = {
    "bad_input": "re-running the upstream node is not built yet",
    "logic": "a logic failure is not retried",
    "unavailable": "the doctor gave no verdict",
}


def _ints(value: JsonValue) -> tuple[int, ...]:
    if isinstance(value, int) and not isinstance(value, bool):
        return (value,)
    if isinstance(value, list):
        return tuple(n for n in value if isinstance(n, int) and not isinstance(n, bool))
    return ()


def candidates(state: State, node: Node) -> tuple[str, ...]:
    """The role's candidates in the order they are tried, as the run recorded them."""
    if node.role is None:
        return ()
    found = state.settings.get(f"roles.{node.role}")
    return tuple(c for c in found if isinstance(c, str)) if isinstance(found, list) else ()


def model_bearing(node: Node) -> bool:
    kind = REGISTRY.kind(node.type)
    return kind is not None and kind.model_bearing


def effect(node: Node) -> str:
    if node.effect is not None:
        return node.effect
    kind = REGISTRY.kind(node.type)
    return "none" if kind is None else kind.effect


def retries(state: State, node: Node, failure: Failure) -> tuple[int, tuple[int, ...]]:
    """The node's try cap and backoff, over the run's recorded defaults. A run that recorded no
    retry default tries once unless its node says otherwise. 0 tries left when the failure is
    not one the node retries."""
    retry = node.retry
    allowed = failure.retryable and (
        retry is None or retry.retry_on is None or failure.code in retry.retry_on
    )
    recorded = _ints(state.settings.get("retry.max_tries"))
    tries = (retry.max_tries if retry is not None else None) or (recorded[0] if recorded else 1)
    backoff = (
        tuple(retry.backoff_seconds) if retry is not None and retry.backoff_seconds else ()
    ) or _ints(state.settings.get("retry.backoff"))
    return (tries if allowed else 0), backoff or (0,)


def climb(state: State, node: Node, slot: Slot, run: NodeRun, reason: str) -> list[Command]:
    """The next rung for `slot`, which failed as `run` says; `reason` names the failure."""
    failure = run.failure or Failure("", "", retryable=False, effect_state="before")
    walk = state.walks.get(slot, Walk())

    def park(why: str = reason) -> list[Command]:
        return [Park(why, *slot, run.attempt)]

    def rung(
        step: Rung,
        why: str,
        *,
        seconds: int | None = None,
        candidate: str | None = None,
        skipped: bool = False,
    ) -> Climb:
        return Climb(*slot, run.attempt, step, why, seconds, candidate, skipped)

    declared = effect(node)
    if failure.effect_state == "after" and (
        declared == "irreversible_external"
        or (declared == "irreversible" and not model_bearing(node))
    ):
        return park(f"{reason}; it failed after its effect, so a rerun would repeat it")
    if failure.stalled == "loop":
        return park(f"{reason}; the agent was looping, so a rerun would loop again")
    tries, backoff = retries(state, node, failure)
    taken = walk.steps.count("retry")
    roles = candidates(state, node)
    moved = walk.steps.count("model")
    signatures = walk.signatures
    if len(signatures) >= 2 and signatures[-1] == signatures[-2]:
        if "doctor" in walk.steps:
            return park(doctored(reason, walk))
        step = rung("doctor", "the same failure twice")
    elif len(signatures) < tries:
        seconds = backoff[min(taken, len(backoff) - 1)]
        step = rung("retry", f"try {len(signatures) + 1} of {tries}", seconds=seconds)
    elif "account" not in walk.steps:
        step = rung("account", NO_POOL, skipped=True)
    elif len(roles) > moved + 1:
        step = rung("model", f"role {node.role} candidate {moved + 2}", candidate=roles[moved + 1])
    elif "doctor" not in walk.steps:
        step = rung("doctor", "no rung left before the doctor")
    else:
        return park(doctored(reason, walk))
    return [step]


def doctored(reason: str, walk: Walk) -> str:
    if walk.verdict is None:
        return reason
    why = NOT_RERUN.get(walk.verdict, "its re-run failed too")
    return f"{reason}; the doctor found {walk.verdict}: {why}"


def asks(state: State, node: Node, slot: Slot) -> JsonObject | None:
    """What the ladder asks of the slot's next attempt, or None when it asks nothing."""
    walk = state.walks.get(slot)
    found: JsonObject = {}
    if walk is not None:
        moved = walk.steps.count("model")
        roles = candidates(state, node)
        if 0 < moved < len(roles):
            found["candidate"] = roles[moved]
        if walk.verdict == "bad_output" and walk.hint is not None:
            found["hint"] = walk.hint
    return found or None


def breach(state: State) -> str | None:
    """The first of his limits the run is past since its allowance began, if any."""
    found = used(state.spent, state.turns, state.tools, state.active_seconds)
    for key, limit in state.limits.items():
        count = found.get(key, 0) - state.allowance.get(key, 0)
        if count >= limit:
            return f"{key} {count} of {limit}"
    return None


def admit(state: State, commands: Sequence[Command]) -> tuple[list[Command], str | None]:
    """Hold back every new attempt once a limit he wrote is reached. Returns what may go ahead
    and the breach, if any."""
    detail = breach(state)
    if detail is None:
        return list(commands), None
    return [c for c in commands if not isinstance(c, StartNode)], detail


def step_data(command: Climb | Park, resume_at: str | None = None) -> JsonObject:
    """The `ladder_step` a driver writes for a rung or a park. `resume_at` is the retry's, which
    the driver works out from `seconds` on the run's clock."""
    if isinstance(command, Park):
        data: JsonObject = {"step": "park", "reason": command.reason}
        if command.node_id is not None:
            slot: JsonObject = {
                "node_id": command.node_id,
                "iteration": command.iteration,
                "partition": command.partition,
                "attempt": command.attempt,
            }
            data |= slot
        return data
    data = {
        "node_id": command.node_id,
        "iteration": command.iteration,
        "partition": command.partition,
        "attempt": command.attempt,
        "step": command.step,
        "reason": command.reason,
    }
    if command.step == "retry":
        data["resume_at"] = resume_at
    if command.candidate is not None:
        data["candidate"] = command.candidate
    if command.skipped:
        data["skipped"] = True
    return data


def limits_line(detail: str) -> JsonObject:
    """The run-level `info` digest line a limits pause writes."""
    return {
        "level": "info",
        "digest": True,
        "line": f"limits: {detail}; the run pauses until it is resumed",
        "limits": detail,
    }
