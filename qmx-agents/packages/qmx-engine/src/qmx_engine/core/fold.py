"""`fold(definition, events) -> State`: the ledger read forward into the current run state.

Event data keys the fold reads (SOLUTION-DESIGN 3.2): `run_created.settings`, `run_input.inputs`,
`clock_tick.now`, `event_received.event`, the slot keys `node_id`, `iteration` and `partition`
with `attempt` on node events, `memo_key` on `node_scheduled` and on a `node_finished` that carries
`memo: true`, `outputs` on `node_finished`, `tokens` on an ending event, `code` and `message` on
`node_failed`, `reason`, `resume_at` and `event` on `node_waiting`, `plan.join.merged` on a join's
`node_scheduled`, `run_created.limits`, `turns` on an ending event, one `tool_called` per tool
call, `active_seconds` on a run-level `heartbeat`, `signature`, `retryable`, `effect_state` and
`stalled` on `node_failed`, `step`, `resume_at` and the slot keys on `ladder_step`,
`classification` and `hint` on `doctor_verdict`, and `reason` on `run_paused` and `run_resumed`.
A `node_waiting` at attempt 0 (or, in an older ledger, with no `attempt`) is a hold the core
asked for. Only the first `run_created`
counts (B-25), and an ending whose `attempt` is not the slot's current one settles nothing (L-32).
`run_resumed` opens a new pass but keeps every slot waiting on a gate; after a `limits` pause it
also moves the limits' allowance on.

A `retry` or `model` step, and a doctor verdict the node may be re-run on, put the slot back to
pending: it starts again as a new attempt once its retry is due.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Final

from pydantic import JsonValue

from qmx_engine.core.state import (
    EventView,
    Failure,
    Held,
    JsonObject,
    NodeRun,
    Slot,
    State,
    Walk,
)
from qmx_engine.definition.model import Workflow

IGNORED: Final = frozenset(
    {
        "heartbeat",
        "log",
        "gate_opened",
        "gate_resolved",
        "compacted",
        "zone_committed",
        "memory_written",
    }
)
"""Kinds this core knows and that change nothing it decides yet."""
ENDINGS: Final = frozenset({"node_finished", "node_failed", "node_waiting"})
RERUN_VERDICTS: Final = frozenset({"transient", "bad_output"})
"""Doctor classifications after which the node runs once more (SOLUTION-DESIGN 10.2)."""


def _text(data: Mapping[str, JsonValue], name: str) -> str | None:
    value = data.get(name)
    return value if isinstance(value, str) else None


def _object(data: Mapping[str, JsonValue], name: str) -> JsonObject:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def _int(value: JsonValue) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def slot_of(data: Mapping[str, JsonValue]) -> Slot:
    return Slot(
        _text(data, "node_id") or "", _int(data.get("iteration")) or 0, _int(data.get("partition"))
    )


def tokens(data: Mapping[str, JsonValue]) -> int:
    return sum(count for value in _object(data, "tokens").values() if (count := _int(value)))


def gated(run: NodeRun) -> bool:
    """A slot waiting on an answer: a resume never reruns it, only the answer does, so a step
    that may already have reached the outside world is never repeated by a resume (AD-8)."""
    return run.phase == "waiting" and run.reason == "gate"


def fold(definition: Workflow, events: Iterable[EventView]) -> State:
    state: State = State(definition, "", None, None, {}, {}, {})
    nodes: dict[Slot, NodeRun] = {}
    memos: dict[str, JsonObject] = {}
    attempts: dict[Slot, int] = {}
    holds: dict[Slot, Held] = {}
    spent: dict[Slot, int] = {}
    received: list[tuple[str, int]] = []
    joins: dict[Slot, tuple[int, ...]] = {}
    walks: dict[Slot, Walk] = {}
    turns: dict[Slot, int] = {}
    tools: dict[Slot, int] = {}
    active = 0
    paused: str | None = None
    allowance: dict[str, int] = {}
    restarts = 0
    created = False
    for event in events:
        data, kind, seq = event.data, event.kind, event.seq
        if not state.run_id:
            state = replace(state, run_id=event.run_id)
        if state.unfoldable is not None:
            if kind == "ladder_step" and data.get("step") == "park":
                state = replace(state, ended="parked")
            continue
        slot = slot_of(data)
        current = nodes.get(slot)
        if (
            kind in ENDINGS
            and current is not None
            and data.get("memo") is not True
            and _int(data.get("attempt")) not in (None, current.attempt)
        ):
            continue  # a late ending of an earlier attempt settles nothing now
        if kind in ENDINGS and "attempt" in data:
            spent[slot] = spent.get(slot, 0) + tokens(data)
            turns[slot] = turns.get(slot, 0) + (_int(data.get("turns")) or 0)
        match kind:
            case "run_created" if not created:
                created = True
                limits = {k: n for k, v in _object(data, "limits").items() if (n := _int(v))}
                state = replace(state, settings=_object(data, "settings"), limits=limits)
            case "run_input":
                state = replace(state, inputs=data.get("inputs"))
            case "clock_tick":
                state = replace(state, now=_text(data, "now"))
            case "event_received":
                received.append((_text(data, "event") or "", seq))
            case "run_paused":
                paused = _text(data, "reason")
            case "run_resumed":
                nodes = {s: run for s, run in nodes.items() if gated(run)}
                state = replace(state, ended=None)
                if paused == "limits":
                    allowance = used(spent, turns, tools, active)
                if data.get("reason") == "interrupted":
                    restarts += 1
                paused = None
            case "tool_called":
                tools[slot] = tools.get(slot, 0) + 1
            case "heartbeat" if "node_id" not in data:
                active = _int(data.get("active_seconds")) or active
            case "node_scheduled":
                attempt = _int(data.get("attempt")) or 0
                attempts[slot] = max(attempts.get(slot, 0), attempt)
                nodes[slot] = NodeRun("scheduled", attempt, _text(data, "memo_key") or "", seq)
                merged = _object(_object(data, "plan"), "join").get("merged")
                if isinstance(merged, list) and slot not in joins:
                    joins[slot] = tuple(n for p in merged if (n := _int(p)) is not None)
            case "node_started" if current is not None:
                nodes[slot] = replace(current, phase="started", seq=seq)
            case "node_finished":
                outputs = _object(data, "outputs")
                if data.get("memo") is True:
                    key = _text(data, "memo_key") or ""
                    nodes[slot] = NodeRun("finished", 0, key, seq, outputs=outputs)
                elif current is not None:
                    nodes[slot] = replace(current, phase="finished", seq=seq, outputs=outputs)
                    memos[current.memo_key] = outputs
            case "node_failed" if current is not None:
                error = f"{_text(data, 'code')}: {_text(data, 'message')}"
                failure = Failure(
                    _text(data, "code") or "",
                    _text(data, "signature") or "",
                    data.get("retryable") is True,
                    _text(data, "effect_state") or "before",
                    _text(data, "stalled"),
                )
                nodes[slot] = replace(
                    current, phase="failed", seq=seq, error=error, failure=failure
                )
                walk = walks.get(slot, Walk())
                walks[slot] = replace(walk, signatures=(*walk.signatures, failure.signature))
            case "node_waiting" if not _int(data.get("attempt")):
                holds.setdefault(slot, Held(_text(data, "resume_at"), _text(data, "event"), seq))
            case "node_waiting" if current is not None:
                nodes[slot] = replace(
                    current,
                    phase="waiting",
                    seq=seq,
                    reason=_text(data, "reason"),
                    resume_at=_text(data, "resume_at"),
                )
            case "ladder_step" if data.get("step") == "park":
                state = replace(state, ended="parked")
                walks.pop(slot, None)
            case "ladder_step":
                step = _text(data, "step") or ""
                walk = walks.get(slot, Walk())
                walks[slot] = replace(
                    walk,
                    steps=(*walk.steps, step),
                    retry_at=_text(data, "resume_at") if step == "retry" else walk.retry_at,
                )
                if step in ("retry", "model"):
                    nodes.pop(slot, None)
            case "doctor_verdict":
                verdict = _text(data, "classification")
                walk = walks.get(slot, Walk())
                walks[slot] = replace(walk, verdict=verdict, hint=_text(data, "hint"))
                if verdict in RERUN_VERDICTS:
                    nodes.pop(slot, None)
            case "run_finished":
                state = replace(state, ended="passed")
            case "run_cancelled":
                state = replace(state, ended="stopped")
            case "node_started" | "node_failed" | "node_waiting" | "run_created":
                pass  # an attempt this pass never scheduled, or a second run_created
            case _ if kind in IGNORED:
                pass
            case _:
                state = replace(
                    state,
                    unfoldable=f"this core cannot fold event kind {kind!r} at seq {seq}",
                )
    return replace(
        state,
        nodes=nodes,
        memos=memos,
        attempts=attempts,
        holds=holds,
        spent=spent,
        received=tuple(received),
        joins=joins,
        walks=walks,
        turns=turns,
        tools=tools,
        active_seconds=active,
        allowance=allowance,
        restarts=restarts,
    )


def used(
    spent: Mapping[Slot, int], turns: Mapping[Slot, int], tools: Mapping[Slot, int], active: int
) -> dict[str, int]:
    """What the run has used, keyed as `State.limits` is: the run's totals by name, and each
    node's as `<node id>.<name>`."""
    found: dict[str, int] = {"wall_seconds": active}
    for name, counts in (("tokens", spent), ("turns", turns), ("tool_calls", tools)):
        for slot, count in counts.items():
            found[name] = found.get(name, 0) + count
            key = f"{slot.node_id}.{name}"
            found[key] = found.get(key, 0) + count
    return found
