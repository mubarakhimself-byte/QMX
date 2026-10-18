"""`fold(definition, events) -> State`: the ledger read forward into the current run state.

Event data keys the fold reads (SOLUTION-DESIGN 3.2): `run_input.inputs`, `clock_tick.now`,
`node_id` and `attempt` on node events, `memo_key` on `node_scheduled` and on a `node_finished`
that carries `memo: true`, `outputs` on `node_finished`, `code` and `message` on `node_failed`,
`reason` and `resume_at` on `node_waiting`, and `step` on `ladder_step`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Final

from pydantic import JsonValue

from qmx_engine.core.state import EventView, JsonObject, NodeRun, State
from qmx_engine.definition.model import Workflow

IGNORED: Final = frozenset(
    {
        "run_created",
        "heartbeat",
        "log",
        "gate_opened",
        "gate_resolved",
        "event_received",
        "doctor_verdict",
        "run_paused",
        "compacted",
        "memory_written",
    }
)
"""Kinds this core knows and that change nothing it decides yet."""


def _text(data: Mapping[str, JsonValue], name: str) -> str | None:
    value = data.get(name)
    return value if isinstance(value, str) else None


def _object(data: Mapping[str, JsonValue], name: str) -> JsonObject:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def _int(data: Mapping[str, JsonValue], name: str) -> int:
    value = data.get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def fold(definition: Workflow, events: Iterable[EventView]) -> State:
    state = State(definition, "", None, None, {}, {}, {})
    nodes: dict[str, NodeRun] = {}
    memos: dict[str, JsonObject] = {}
    attempts: dict[str, int] = {}
    for event in events:
        data, kind = event.data, event.kind
        if not state.run_id:
            state = replace(state, run_id=event.run_id)
        if state.unfoldable is not None:
            if kind == "ladder_step" and data.get("step") == "park":
                state = replace(state, ended="parked")
            continue
        node_id = _text(data, "node_id") or ""
        current = nodes.get(node_id)
        match kind:
            case "run_input":
                state = replace(state, inputs=data.get("inputs"))
            case "clock_tick":
                state = replace(state, now=_text(data, "now"))
            case "run_resumed":
                nodes = {}
                state = replace(state, ended=None)
            case "node_scheduled":
                attempt = _int(data, "attempt")
                attempts[node_id] = max(attempts.get(node_id, 0), attempt)
                nodes[node_id] = NodeRun("scheduled", attempt, _text(data, "memo_key") or "")
            case "node_started" if current is not None:
                nodes[node_id] = replace(current, phase="started")
            case "node_finished":
                outputs = _object(data, "outputs")
                if data.get("memo") is True:
                    nodes[node_id] = NodeRun(
                        "finished", 0, _text(data, "memo_key") or "", outputs=outputs
                    )
                elif current is not None:
                    nodes[node_id] = replace(current, phase="finished", outputs=outputs)
                    memos[current.memo_key] = outputs
            case "node_failed" if current is not None:
                error = f"{_text(data, 'code')}: {_text(data, 'message')}"
                nodes[node_id] = replace(current, phase="failed", error=error)
            case "node_waiting" if current is not None:
                nodes[node_id] = replace(
                    current,
                    phase="waiting",
                    reason=_text(data, "reason"),
                    resume_at=_text(data, "resume_at"),
                )
            case "ladder_step":
                if data.get("step") == "park":
                    state = replace(state, ended="parked")
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
                    unfoldable=f"this core cannot fold event kind {kind!r} at seq {event.seq}",
                )
    return replace(state, nodes=nodes, memos=memos, attempts=attempts)
