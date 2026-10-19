"""`runs.explain`: one document per run, read from the ledger alone (AD-15, AD-16).

For each node, in the order it first appears: its attempts (from the node events), its spans, its
ladder steps, its waits and its cost so far. For the run: its status and reason from SOLUTION-DESIGN
3.1, the park's or the wait's detail, and the cost so far. `text` renders it for the CLI.

Every string passes the one redaction (AD-37). The ledger already stores redacted text; this
covers a ledger written before the seam, since a failure message is quoted verbatim (L-52).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Final, cast

from pydantic import JsonValue

from qmx_engine.ledger.events import Event
from qmx_engine.ledger.redact import redact_json
from qmx_engine.ledger.spans import Span
from qmx_engine.ports.library import JsonObject
from qmx_engine.service.runs import status_of
from qmx_engine.trace_export import totals

ENDINGS: Final = {"node_finished": "ok", "node_failed": "failed", "node_waiting": "waiting"}
FAILURE_KEYS: Final = ("code", "message", "signature", "retryable", "effect_state")
LADDER_KEYS: Final = ("attempt", "step", "reason", "candidate", "resume_at", "skipped")
WAIT_KEYS: Final = ("attempt", "reason", "resume_at", "event", "idempotency_key")
SPAN_KEYS: Final = (
    "span_id",
    "attempt",
    "iteration",
    "partition",
    "status",
    "started_at",
    "ended_at",
    "role",
    "model",
    "tokens",
    "cost_estimate_usd",
    "error_signature",
)


def pick(data: JsonObject, keys: tuple[str, ...]) -> JsonObject:
    return {key: data[key] for key in keys if key in data}


@dataclass(slots=True)
class NodeDoc:
    node_id: str
    state: str = "pending"
    attempts: list[JsonObject] = field(default_factory=list[JsonObject])
    spans: list[JsonObject] = field(default_factory=list[JsonObject])
    ladder: list[JsonObject] = field(default_factory=list[JsonObject])
    waits: list[JsonObject] = field(default_factory=list[JsonObject])
    cost: JsonObject = field(default_factory=dict[str, JsonValue])


def explain(events: list[Event], spans: list[Span]) -> JsonObject:
    created = events[0].data if events else {}
    nodes: dict[str, NodeDoc] = {}
    attempts: dict[tuple[str, JsonValue, JsonValue, JsonValue], JsonObject] = {}
    for event in events:
        data = event.data
        node_id = data.get("node_id")
        if not isinstance(node_id, str):
            continue
        node = nodes.setdefault(node_id, NodeDoc(node_id))
        key = (node_id, data.get("iteration", 0), data.get("partition"), data.get("attempt"))
        match event.kind:
            case "node_scheduled":
                attempts[key] = {
                    "attempt": data.get("attempt"),
                    "iteration": data.get("iteration", 0),
                    "partition": data.get("partition"),
                    "scheduled_at": event.at,
                    "status": "scheduled",
                }
                node.attempts.append(attempts[key])
                node.state = "scheduled"
            case "node_started":
                if key in attempts:
                    attempts[key] |= {"started_at": event.at, "status": "started"}
                node.state = "started"
            case "node_finished" | "node_failed" | "node_waiting" as kind:
                ended: JsonObject = {"ended_at": event.at, "status": ENDINGS[kind]}
                if kind == "node_failed":
                    ended |= pick(data, FAILURE_KEYS)
                if data.get("memo") is True:
                    ended["memo"] = True
                if key in attempts:
                    attempts[key] |= ended
                elif kind == "node_finished":
                    node.attempts.append({"attempt": data.get("attempt"), **ended})
                if kind == "node_waiting":
                    node.waits.append(pick(data, WAIT_KEYS) | {"at": event.at})
                node.state = ENDINGS[kind]
            case "ladder_step":
                node.ladder.append(pick(data, LADDER_KEYS) | {"at": event.at})
                if data.get("step") == "park":
                    node.state = "parked"
            case "gate_opened":
                node.waits.append({"reason": "gate", "ask": data.get("ask"), "at": event.at})
            case _:
                pass
    for span in spans:
        node = nodes.setdefault(span.node_id, NodeDoc(span.node_id))
        node.spans.append(pick(cast(JsonObject, asdict(span)), SPAN_KEYS))
    for node in nodes.values():
        node.cost = cost(totals([], [s for s in spans if s.node_id == node.node_id]))
    state = status_of(events)
    document: JsonObject = {
        "run_id": events[0].run_id if events else None,
        "workflow_id": created.get("workflow_id"),
        "mode": created.get("mode"),
        "content_hash": created.get("content_hash"),
        "status": state.status,
        "reason": state.reason,
        "detail": state.detail,
        "cost": cost(totals(events, spans)),
        "nodes": [cast(JsonValue, asdict(node)) for node in nodes.values()],
    }
    return cast(JsonObject, redact_json(document)[0])


def cost(summed: JsonObject) -> JsonObject:
    return {"tokens": summed["tokens"], "cost_estimate_usd": summed["cost_estimate_usd"]}


def text(document: JsonObject) -> list[str]:
    """The document as lines for `python -m qmx_engine explain`."""
    head = f"run {document['run_id']} {document['status']}"
    if document["reason"]:
        head += f" ({document['reason']})"
    lines = [head]
    if document["detail"]:
        lines.append(f"  cause: {document['detail']}")
    lines.append(
        f"  mode {document['mode']}, workflow {document['workflow_id']}, cost {document['cost']}"
    )
    for node in cast(list[dict[str, list[JsonObject]]], document["nodes"]):
        tried = node["attempts"]
        lines.append(f"node {node['node_id']}: {node['state']}, {len(tried)} attempt(s)")
        for attempt in tried:
            why = f" {attempt.get('code')}: {attempt.get('message')}" if "code" in attempt else ""
            lines.append(f"  attempt {attempt.get('attempt')} {attempt.get('status')}{why}")
        for span in node["spans"]:
            where = "" if span.get("partition") is None else f" partition {span.get('partition')}"
            lines.append(
                f"  span {span.get('attempt')}{where} {span.get('status')}"
                f" model {span.get('model')} tokens {span.get('tokens')}"
            )
        for step in node["ladder"]:
            extra = " (skipped)" if step.get("skipped") else ""
            lines.append(f"  ladder {step.get('step')}{extra}: {step.get('reason')}")
        for wait in node["waits"]:
            lines.append(f"  wait {wait.get('reason')} until {wait.get('resume_at')}")
    return lines
