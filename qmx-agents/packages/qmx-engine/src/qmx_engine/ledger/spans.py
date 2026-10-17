"""One span row per node attempt, derived from `node_started` and its ending event (SOLUTION-DESIGN
10.1), written inside the same transaction as the event that changes it.

An attempt is named by the data keys `node_id`, `iteration` (default 0), `partition` (default none)
and `attempt`; `node_started` must carry `node_id` and `attempt`. The ending events
`node_finished`, `node_failed` and `node_waiting` close the attempt's span, and `compacted` adds to
its `events`. An ending event for an attempt that never started, such as a `node_waiting` the core
writes when no lease was admitted, has no span to close. The other span fields are read from these
data keys when present: on `node_started` `parent_span_id role profile account model effort
placement effect idempotency_key`; on the ending event `tokens cost_estimate_usd signature verdict
same_family uncached_resend`; on `compacted` `trigger at_fraction`. Tool and chunk spans (AD-34)
are written by the PRs that read tool calls.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from typing import Final, Literal

from pydantic import JsonValue
from qmx_ledger.journal import encoded, fingerprint

from qmx_engine.ledger.events import Event, JsonObject

type SpanStatus = Literal["ok", "failed", "waiting", "gate", "cancelled"]
type SpanKind = Literal["node", "tool", "chunk"]

ENDINGS: Final[dict[str, SpanStatus]] = {
    "node_finished": "ok",
    "node_failed": "failed",
    "node_waiting": "waiting",
}


@dataclass(frozen=True, slots=True)
class Span:
    span_id: str
    trace_id: str
    node_id: str
    iteration: int
    partition: str | None
    attempt: int
    started_at: str
    kind: SpanKind = "node"
    parent_span_id: str | None = None
    role: str | None = None
    profile: str | None = None
    account: str | None = None
    model: str | None = None
    effort: str | None = None
    placement: str | None = None
    mode: str | None = None
    ended_at: str | None = None
    status: SpanStatus | None = None
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    cost_estimate_usd: float | None = None
    effect: str | None = None
    idempotency_key: str | None = None
    error_signature: str | None = None
    verdict: str | None = None
    same_family: bool | None = None
    uncached_resend: bool = False
    events: list[JsonObject] = field(default_factory=list[JsonObject])

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        ended = datetime.fromisoformat(self.ended_at)
        return (ended - datetime.fromisoformat(self.started_at)).total_seconds()


AttemptKey = tuple[str, int, str | None, int]


def attempt_of(data: JsonObject) -> AttemptKey | None:
    node_id, attempt = data.get("node_id"), data.get("attempt")
    iteration, partition = data.get("iteration", 0), data.get("partition")
    if not isinstance(node_id, str) or not isinstance(attempt, int):
        return None
    if not isinstance(iteration, int) or not isinstance(partition, str | int | None):
        return None
    return node_id, iteration, None if partition is None else str(partition), attempt


def span_id(run_id: str, key: AttemptKey) -> str:
    return fingerprint([run_id, *key])[:32]


def _text(data: JsonObject, name: str) -> str | None:
    value = data.get(name)
    return value if isinstance(value, str) else None


def _flag(data: JsonObject, name: str) -> bool | None:
    value = data.get(name)
    return value if isinstance(value, bool) else None


def _tokens(value: JsonValue) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        name: count
        for name, count in value.items()
        if isinstance(count, int) and not isinstance(count, bool)
    }


def started(event: Event, key: AttemptKey, mode: str | None) -> Span:
    data = event.data
    node_id, iteration, partition, attempt = key
    return Span(
        span_id=span_id(event.run_id, key),
        trace_id=event.run_id,
        node_id=node_id,
        iteration=iteration,
        partition=partition,
        attempt=attempt,
        started_at=event.at,
        parent_span_id=_text(data, "parent_span_id"),
        role=_text(data, "role"),
        profile=_text(data, "profile"),
        account=_text(data, "account"),
        model=_text(data, "model"),
        effort=_text(data, "effort"),
        placement=_text(data, "placement"),
        mode=mode,
        effect=_text(data, "effect"),
        idempotency_key=_text(data, "idempotency_key"),
    )


def ended(span: Span, event: Event) -> Span:
    data = event.data
    cost = data.get("cost_estimate_usd")
    return replace(
        span,
        ended_at=event.at,
        status=ENDINGS[event.kind],
        tokens=_tokens(data.get("tokens")),
        cost_estimate_usd=float(cost) if isinstance(cost, int | float) else None,
        error_signature=_text(data, "signature"),
        verdict=_text(data, "verdict"),
        same_family=_flag(data, "same_family"),
        uncached_resend=_flag(data, "uncached_resend") or False,
    )


def compacted(span: Span, event: Event) -> Span:
    entry: JsonObject = {
        "compacted": {
            "trigger": event.data.get("trigger"),
            "at_fraction": event.data.get("at_fraction"),
        }
    }
    return replace(span, events=[*span.events, entry])


def from_record(record: str) -> Span:
    return Span(**json.loads(record))


def _load(connection: sqlite3.Connection, span_id_: str) -> Span | None:
    row = connection.execute("SELECT record FROM spans WHERE span_id = ?", (span_id_,)).fetchone()
    return None if row is None else from_record(row[0])


def _save(connection: sqlite3.Connection, span: Span) -> None:
    connection.execute(
        "INSERT OR REPLACE INTO spans (span_id, trace_id, started_at, record) VALUES (?, ?, ?, ?)",
        (span.span_id, span.trace_id, span.started_at, encoded(asdict(span)).decode()),
    )


def _run_mode(connection: sqlite3.Connection, run_id: str) -> str | None:
    row = connection.execute(
        "SELECT data FROM events WHERE run_id = ? AND kind = 'run_created' LIMIT 1", (run_id,)
    ).fetchone()
    if row is None:
        return None
    mode = json.loads(row[0]).get("mode")
    return mode if isinstance(mode, str) else None


def apply(connection: sqlite3.Connection, event: Event) -> None:
    """Write the span change `event` makes, if any. Runs on the writer thread."""
    key = attempt_of(event.data)
    if key is None:
        return
    if event.kind == "node_started":
        _save(connection, started(event, key, _run_mode(connection, event.run_id)))
        return
    if event.kind not in ENDINGS and event.kind != "compacted":
        return
    span = _load(connection, span_id(event.run_id, key))
    if span is None:
        return
    _save(connection, ended(span, event) if event.kind in ENDINGS else compacted(span, event))
