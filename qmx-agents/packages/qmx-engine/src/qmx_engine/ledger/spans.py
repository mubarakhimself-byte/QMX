"""One span row per node attempt, derived from `node_started` and its ending event (SOLUTION-DESIGN
10.1), written inside the same transaction as the event that changes it.

An attempt is named by the data keys `node_id`, `iteration`, `partition` and `attempt`, which every
node event carries (AD-15; the store refuses one without them). The ending events `node_finished`,
`node_failed` and `node_waiting` close the attempt's span, and `compacted` adds to its `events`.
Span status is derived only: `ok`, `failed` and `waiting` from those endings, `gate` from
`gate_opened` until its `gate_resolved` (a `node_waiting` on the gate keeps it `gate`), and
`cancelled` from a `node_failed` with code `cancelled` or from `run_cancelled`, which closes every
span of the run still open (B-18). An ending event for an attempt that never started, such as a hold
the core asked for (attempt 0), has no span to close. The other span fields are read from these data
keys when present: on `node_started` `parent_span_id role profile account model effort placement
effect idempotency_key`; on the ending event `tokens cost_estimate_usd signature verdict same_family
uncached_resend surface_digest` (AD-62: what an agent's chat was offered); on `compacted` `trigger
at_fraction`. A `tool_called` event writes one `tool` span (AD-34), a child of its attempt's span,
from its `tool` object: `id name duration_ms error`. An attempt's span counts the secrets the ledger
redacted from any of its events (`redactions`, AD-37); it never records a value.
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
NODE_EVENTS: Final = frozenset(
    {
        "node_scheduled",
        "node_started",
        "node_finished",
        "node_failed",
        "node_waiting",
        "gate_opened",
        "gate_resolved",
        "compacted",
        "tool_called",
        "doctor_verdict",
    }
)
"""The kinds that are always about one attempt. `heartbeat`, `log` and `ladder_step` may also be
run-level; when one names a `node_id` it carries the whole key too."""
KEYS: Final = ("node_id", "iteration", "partition", "attempt")


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
    surface_digest: str | None = None
    events: list[JsonObject] = field(default_factory=list[JsonObject])
    name: str | None = None
    """A tool span's tool."""
    duration_ms: int | None = None
    error: str | None = None
    redactions: int = 0

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


def keyed(data: JsonObject) -> bool:
    """True when the event names its attempt in full (AD-15)."""
    return all(name in data for name in KEYS) and attempt_of(data) is not None


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
    status = ENDINGS[event.kind]
    if event.kind == "node_failed" and data.get("code") == "cancelled":
        status = "cancelled"
    elif event.kind == "node_waiting" and span.status == "gate":
        status = "gate"
    return replace(
        span,
        ended_at=event.at,
        status=status,
        tokens=_tokens(data.get("tokens")),
        cost_estimate_usd=float(cost) if isinstance(cost, int | float) else None,
        error_signature=_text(data, "signature"),
        verdict=_text(data, "verdict"),
        same_family=_flag(data, "same_family"),
        uncached_resend=_flag(data, "uncached_resend") or False,
        surface_digest=_text(data, "surface_digest"),
    )


def compacted(span: Span, event: Event) -> Span:
    entry: JsonObject = {
        "compacted": {
            "trigger": event.data.get("trigger"),
            "at_fraction": event.data.get("at_fraction"),
        }
    }
    return replace(span, events=[*span.events, entry])


def tool(event: Event, key: AttemptKey) -> Span | None:
    found = event.data.get("tool")
    if not isinstance(found, dict) or not isinstance(tool_id := found.get("id"), str):
        return None
    node_id, iteration, partition, attempt = key
    duration, error = found.get("duration_ms"), _text(found, "error")
    return Span(
        span_id=fingerprint([event.run_id, *key, tool_id])[:32],
        trace_id=event.run_id,
        node_id=node_id,
        iteration=iteration,
        partition=partition,
        attempt=attempt,
        started_at=event.at,
        kind="tool",
        parent_span_id=span_id(event.run_id, key),
        placement=_text(found, "placement"),
        ended_at=event.at,
        status="failed" if error is not None else "ok",
        name=_text(found, "name"),
        duration_ms=duration if isinstance(duration, int) else None,
        error=error,
    )


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


def apply(connection: sqlite3.Connection, event: Event, redactions: int = 0) -> None:
    """Write the span change `event` makes, if any, and add the event's `redactions` to its
    attempt's span. Runs on the writer thread."""
    if event.kind == "run_cancelled":
        cancel_open(connection, event)
        return
    key = attempt_of(event.data)
    if key is None:
        return
    if event.kind == "node_started":
        made = started(event, key, _run_mode(connection, event.run_id))
        _save(connection, replace(made, redactions=redactions))
        return
    if event.kind == "tool_called" and (child := tool(event, key)) is not None:
        _save(connection, replace(child, redactions=redactions))
    changes = event.kind in ENDINGS or event.kind in ("compacted", "gate_opened", "gate_resolved")
    if not changes and redactions == 0:
        return
    span = _load(connection, span_id(event.run_id, key))
    if span is None:
        return
    if event.kind in ENDINGS:
        span = ended(span, event)
    elif event.kind == "compacted":
        span = compacted(span, event)
    elif event.kind == "gate_opened":
        span = replace(span, status="gate")
    elif event.kind == "gate_resolved" and span.status == "gate":
        span = replace(span, status="waiting" if span.ended_at is not None else None)
    _save(connection, replace(span, redactions=span.redactions + redactions))


def cancel_open(connection: sqlite3.Connection, event: Event) -> None:
    """`run_cancelled` closes every span of the run that has not ended, as `cancelled`."""
    rows = connection.execute(
        "SELECT record FROM spans WHERE trace_id = ?", (event.run_id,)
    ).fetchall()
    for (record,) in rows:
        span = from_record(record)
        if span.ended_at is None:
            _save(connection, replace(span, ended_at=event.at, status="cancelled"))
