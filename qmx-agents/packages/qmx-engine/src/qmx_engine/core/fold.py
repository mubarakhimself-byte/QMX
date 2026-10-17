"""`fold(definition, events) -> State`: the ledger read forward into the current run state.

Event data keys the fold reads (SOLUTION-DESIGN 3.2): `run_created.settings`, `run_input.inputs`,
`clock_tick.now`, `event_received.event`, the slot keys `node_id`, `iteration` and `partition`
with `attempt` on node events, `memo_key` on `node_scheduled` and on a `node_finished` that carries
`memo: true`, `outputs` on `node_finished`, `tokens` on an ending event, `code` and `message` on
`node_failed`, `reason`, `resume_at` and `event` on `node_waiting`, `plan.join.merged` on a join's
`node_scheduled`, `run_created.runaway`, `tool_calls` on an ending event, `signature`,
`retryable` and `effect_state` on `node_failed`, `step`, `resume_at` and the slot keys on
`ladder_step`, `classification` and `hint` on `doctor_verdict`, and `on_runaway` on a run-level
`log`. A `node_waiting` with no `attempt` is a hold the core asked for. `run_resumed` opens a new
pass but keeps every slot waiting on a gate.

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
        "run_paused",
        "compacted",
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
    state = State(definition, "", None, None, {}, {}, {})
    nodes: dict[Slot, NodeRun] = {}
    memos: dict[str, JsonObject] = {}
    attempts: dict[Slot, int] = {}
    holds: dict[Slot, Held] = {}
    spent: dict[Slot, int] = {}
    received: list[tuple[str, int]] = []
    joins: dict[Slot, tuple[int, ...]] = {}
    walks: dict[Slot, Walk] = {}
    tool_calls = 0
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
        if kind in ENDINGS and "attempt" in data:
            spent[slot] = spent.get(slot, 0) + tokens(data)
            tool_calls += _int(data.get("tool_calls")) or 0
        match kind:
            case "run_created":
                state = replace(
                    state, settings=_object(data, "settings"), runaway=_object(data, "runaway")
                )
            case "run_input":
                state = replace(state, inputs=data.get("inputs"))
            case "clock_tick":
                state = replace(state, now=_text(data, "now"))
            case "event_received":
                received.append((_text(data, "event") or "", seq))
            case "run_resumed":
                nodes = {s: run for s, run in nodes.items() if gated(run)}
                state = replace(state, ended=None)
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
                )
                nodes[slot] = replace(
                    current, phase="failed", seq=seq, error=error, failure=failure
                )
                walk = walks.get(slot, Walk())
                walks[slot] = replace(walk, signatures=(*walk.signatures, failure.signature))
            case "node_waiting" if "attempt" not in data:
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
            case "log" if data.get("on_runaway") == "degrade":
                state = replace(state, degraded=True)
            case "run_finished":
                state = replace(state, ended="passed")
            case "run_cancelled":
                state = replace(state, ended="stopped")
            case "node_started" | "node_failed" | "node_waiting":
                pass  # an attempt this pass never scheduled
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
        tool_calls=tool_calls,
    )
