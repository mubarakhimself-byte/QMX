"""`runs.explain`: one document per run, read from the ledger alone (AD-15, AD-16). And
`explain_trigger`: why a trigger did or did not fire (AD-10), for the UI, the copilot and the
doctor.

For each node, in the order it first appears: its attempts (from the node events), its spans, its
ladder steps, its waits and its cost so far. For the run: its status and reason from SOLUTION-DESIGN
3.1, the park's or the wait's detail, and the cost so far. `text` renders it for the CLI.

Every string passes the one redaction (AD-37). The ledger already stores redacted text; this
covers a ledger written before the seam, since a failure message is quoted verbatim (L-52).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Final, cast

from pydantic import JsonValue

from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import Incident
from qmx_engine.ledger.redact import redact_json
from qmx_engine.ledger.spans import Span
from qmx_engine.ports.library import JsonObject
from qmx_engine.service.runs import status_of
from qmx_engine.trace_export import totals
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import instant, stamp
from qmx_engine.triggers.preflight import Shut, is_market_check, market_shut

ENDINGS: Final = {"node_finished": "ok", "node_failed": "failed", "node_waiting": "waiting"}
STALE_TICKS: Final = 3
"""Ticks without a heartbeat before `explain_trigger` calls the ticker stalled."""
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


@dataclass(frozen=True, slots=True)
class TriggerFacts:
    """What `explain_trigger` reads beside the ledger: the moment, this engine's home and pause
    flag, the pinned version's state, the open incident, and the settings it judges by."""

    now: datetime
    home: str
    paused: bool
    version_state: str
    incident: Incident | None
    tick_seconds: float
    settings: Mapping[str, object]


def explain_trigger(
    connection: sqlite3.Connection, trigger_id: str, facts: TriggerFacts
) -> JsonObject:
    """Why a trigger did or did not fire (AD-10): the ticker's heartbeat age, whether its version
    is enabled, its next fire, its last ten fires with their reasons and its open incident, and a
    `verdict` in one sentence, the first reason that holds."""
    (trigger,) = rows.triggers(connection, "WHERE id = ?", trigger_id)
    recent = rows.fires(connection, trigger_id)[-10:]
    beat = connection.execute("SELECT value FROM meta WHERE key = 'ticker_heartbeat'").fetchone()
    age = None if beat is None else (facts.now - instant(str(beat[0]))).total_seconds()
    held = next((f for f in recent if f.status == "held"), None)
    shut = None
    if is_market_check(trigger.precheck_ref):
        found = market_shut(facts.now, trigger.precheck_ref, trigger.zone, facts.settings)
        shut = found if isinstance(found, Shut) else None
    incident = facts.incident
    document: JsonObject = {
        "trigger_id": trigger.id,
        "kind": trigger.kind,
        "enabled": trigger.enabled,
        "home_engine": trigger.home_engine,
        "paused": facts.paused,
        "version_state": facts.version_state,
        "next_fire_at": trigger.next_fire_at,
        "hold_until": trigger.quota_hold_until,
        "priority": trigger.priority,
        "ready_by": trigger.ready_by,
        "last_status": trigger.last_status,
        "failure_streak": trigger.failure_streak,
        "ticker_heartbeat_age_s": None if age is None else round(age, 1),
        "incident": None if incident is None else cast(JsonObject, asdict(incident)),
        "fires": [
            {
                "fire_id": f.id,
                "occurrence_at": f.occurrence_at,
                "status": f.status,
                "detail": f.detail,
                "run_id": f.run_id,
                "delivery": f.delivery,
                "rerun": f.rerun,
            }
            for f in reversed(recent)
        ],
    }
    document["verdict"] = verdict(trigger, facts, age, held, shut)
    return cast(JsonObject, redact_json(document)[0])


def verdict(
    trigger: rows.Trigger,
    facts: TriggerFacts,
    age: float | None,
    held: rows.Fire | None,
    shut: Shut | None,
) -> str:
    if facts.paused:
        return "paused: autonomy.paused is set, so no fire is claimed on this host until cleared"
    if not trigger.enabled:
        return "the trigger is disabled"
    if trigger.home_engine != facts.home:
        return f"the trigger runs on {trigger.home_engine}, not on this engine ({facts.home})"
    if facts.version_state != "enabled":
        return f"the pinned version is {facts.version_state}"
    if held is not None:
        return f"held: {held.detail}"
    if age is None or age > STALE_TICKS * facts.tick_seconds:
        return "the ticker has not ticked recently, so nothing is claimed"
    if shut is not None:
        return f"{shut.reason} until {stamp(shut.until)}"
    match trigger.spec:
        case rows.Webhook():
            return "it fires once for each new webhook delivery"
        case rows.Manual() | rows.After():
            return f"it fires when asked ({trigger.kind}), never on a clock"
        case rows.Event():
            return "event triggers do not match yet (TRG2b)"
        case rows.Session():
            return "session triggers wait for copilot loops"
        case _:
            return f"it fires next at {trigger.next_fire_at}"


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
