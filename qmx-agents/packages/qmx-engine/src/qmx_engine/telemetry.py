"""The external monitoring layer: the same records, in OpenTelemetry's shapes (AD-69, ruling 126).

Every write point keeps writing what it already wrote. This module is the second reader of those
records: spans become OTLP traces with the GenAI conventions pinned to one version, heartbeat rows
become gauges, and ledger events and log lines become OTLP logs. The four records stay the source of
truth; a collector that is down loses telemetry and never a record.

This exporter holds one bounded batch in memory and nothing on disk: a send that fails or a batch
that overflows is dropped and counted, in `stats()`, which the data health read lists. A server's
collector (`deploy/otelcol.yaml`) keeps the durable queue, whose queue and drop metrics are the
other half of that reading.

Nothing here is enabled by default. A process turns it on from `settings.toml [telemetry] send_to`
(`qma.telemetry`), which is `off` until he names a target, so a test, a lane or a scratch
home never sends a record anywhere. An endpoint is enough: the exporter speaks OTLP/HTTP with JSON
bodies and no third-party SDK, which keeps the engine's dependency set as it is.

A write point hands over the JSON text it stored (or would store), never an object, so the record
crosses no second redaction and no second serialisation.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Final, Literal, cast

from pydantic import JsonValue
from qma.telemetry import configured

from qmx_engine.ledger import redact
from qmx_engine.ledger.spans import Span, from_record

LOG = logging.getLogger(__name__)

STATE_FILE: Final = "logs/telemetry.json"
"""The exporter's counters under the home, which the data health read lists."""
GENAI: Final = "1.36.0"
"""The one version of the GenAI conventions this exporter pins. `gen_ai.system`,
`gen_ai.request.model`, `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens` are that
version's names; a later version renames the first to `gen_ai.provider.name`, and a reader that
wants the new names changes this pin in one place."""
SCHEMA_URL: Final = f"https://opentelemetry.io/schemas/{GENAI}"
SCOPE: Final = "qmx.engine"
CAPACITY: Final = 512
"""Records held in memory at most. Past it new records are dropped and counted: the queue is
expendable (F42)."""
FLUSH_S: Final = 2.0
TIMEOUT_S: Final = 5.0
"""The collector client's own timeout, per post."""
SEND_WAIT_S: Final = 3 * TIMEOUT_S
"""How long a flush waits for a send already in flight: its three posts at their timeout."""
LEVELS: Final[Mapping[str, int]] = {"debug": 5, "info": 9, "warning": 13, "error": 17}
SEVERITY: Final[Mapping[int, str]] = {5: "DEBUG", 9: "INFO", 13: "WARN", 17: "ERROR"}
STATUS: Final[Mapping[str, int]] = {"ok": 1, "failed": 2, "cancelled": 2}
"""OTLP's span status: `STATUS_CODE_OK` is 1 and `STATUS_CODE_ERROR` is 2."""

type Signal = Literal["traces", "metrics", "logs"]
type Otlp = dict[str, object]
"""One OTLP payload part. JSON's own shapes, described by `object` so a nested builder composes."""
type Post = Callable[[str, bytes], None]


@dataclass
class Counters:
    sent: int = 0
    dropped: int = 0
    failed: int = 0
    last_error: str = ""
    last_sent_at: str = ""

    def document(self, endpoint: str) -> dict[str, JsonValue]:
        return {
            "endpoint": endpoint,
            "sent": self.sent,
            "dropped": self.dropped,
            "failed": self.failed,
            "last_error": self.last_error,
            "last_sent_at": self.last_sent_at,
            "queue_capacity": CAPACITY,
        }


@dataclass(frozen=True, slots=True)
class Unsent:
    """Why a flush returned before its records reached the collector."""

    code: Literal["send_in_flight", "timeout"]
    message: str


@dataclass
class _Batch:
    spans: list[Otlp]
    metrics: list[Otlp]
    logs: list[Otlp]

    def total(self) -> int:
        return len(self.spans) + len(self.metrics) + len(self.logs)


def _post(url: str, body: bytes) -> None:
    request = urllib.request.Request(  # noqa: S310 (the home's own setting)
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as answer:  # noqa: S310
        answer.read()


def _service_version() -> str:
    try:
        return metadata.version("qmx-engine")
    except metadata.PackageNotFoundError:
        return "0"


def _nanos(instant: str | None) -> str:
    if instant is None:
        return "0"
    found = datetime.fromisoformat(instant)
    if found.tzinfo is None:
        found = found.replace(tzinfo=UTC)
    return str(int(found.timestamp() * 1_000_000_000))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _text(value: str) -> Otlp:
    return {"stringValue": value}


def attributes(values: Mapping[str, JsonValue | None]) -> list[Otlp]:
    """OTLP attributes, one entry per value that is there. `None` is absent, never a null."""
    found: list[Otlp] = []
    for key, value in values.items():
        if value is None:
            continue
        entry: Otlp
        if isinstance(value, bool):
            entry = {"boolValue": value}
        elif isinstance(value, int):
            entry = {"intValue": str(value)}
        elif isinstance(value, float):
            entry = {"doubleValue": value}
        elif isinstance(value, str):
            entry = _text(value)
        else:
            entry = _text(json.dumps(value, sort_keys=True))
        found.append({"key": key, "value": entry})
    return found


def resource(service: str = "qmx-host") -> Otlp:
    version = _service_version()
    return {
        "attributes": attributes(
            {
                "service.name": service,
                "service.version": version,
                "telemetry.sdk.name": SCOPE,
                "telemetry.sdk.version": version,
                "telemetry.schema_url": SCHEMA_URL,
            }
        )
    }


def genai(span: Span) -> dict[str, JsonValue | None]:
    """A QMX span's GenAI attributes at the pinned version: a tool span names its tool, an agent
    attempt names its role and model and carries the usage in the version's names."""
    if span.kind == "tool":
        return {"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": span.name}
    return {
        "gen_ai.operation.name": "invoke_agent" if span.role else "chat",
        "gen_ai.system": span.profile,
        "gen_ai.agent.name": span.node_id,
        "gen_ai.request.model": span.model,
        "gen_ai.usage.input_tokens": span.tokens.get("in"),
        "gen_ai.usage.output_tokens": span.tokens.get("out"),
    }


def qmx_attributes(span: Span) -> dict[str, JsonValue | None]:
    """What the conventions have no name for: the run, the attempt, the placement and the rest."""
    return {
        "qmx.trace_id": span.trace_id,
        "qmx.span_id": span.span_id,
        "qmx.node_id": span.node_id,
        "qmx.iteration": span.iteration,
        "qmx.partition": span.partition,
        "qmx.attempt": span.attempt,
        "qmx.kind": span.kind,
        "qmx.status": span.status,
        "qmx.mode": span.mode,
        "qmx.effort": span.effort,
        "qmx.account": span.account,
        "qmx.placement": span.placement,
        "qmx.effect": span.effect,
        "qmx.verdict": span.verdict,
        "qmx.same_family": span.same_family,
        "qmx.uncached_resend": span.uncached_resend,
        "qmx.surface_digest": span.surface_digest,
        "qmx.error_signature": span.error_signature,
        "qmx.cost_estimate_usd": span.cost_estimate_usd,
        "qmx.redactions": span.redactions,
        "qmx.duration_ms": span.duration_ms,
        "qmx.tool_error": span.error,
    }


def trace_id(run_id: str) -> str:
    """The 16-byte OTel trace id of a run, derived from its id: `trace_id = run_id` (AD-15)."""
    from hashlib import sha256  # noqa: PLC0415

    return sha256(run_id.encode()).hexdigest()[:32]


def span_id(raw: str) -> str:
    from hashlib import sha256  # noqa: PLC0415

    return sha256(raw.encode()).hexdigest()[:16]


def span_record(span: Span) -> Otlp:
    """One OTLP span. Its trace id derives from the run's id, so a reader joins on either name."""
    record: Otlp = {
        "traceId": trace_id(span.trace_id),
        "spanId": span_id(span.span_id),
        "name": span.name or f"{span.kind}.{span.node_id}",
        "kind": 1,
        "startTimeUnixNano": _nanos(span.started_at),
        "endTimeUnixNano": _nanos(span.ended_at or span.started_at),
        "attributes": attributes({**genai(span), **qmx_attributes(span)}),
    }
    if span.parent_span_id:
        record["parentSpanId"] = span_id(span.parent_span_id)
    if span.status is not None:
        record["status"] = {"code": STATUS.get(span.status, 0)}
    return record


def gauge(
    name: str, value: int | float, values: Mapping[str, JsonValue | None], unit: str = ""
) -> Otlp:
    point: Otlp = {"timeUnixNano": _nanos(_now()), "attributes": attributes(values)}
    if isinstance(value, int):
        point["asInt"] = str(value)
    else:
        point["asDouble"] = value
    return {"name": name, "unit": unit, "gauge": {"dataPoints": [point]}}


def log_record(
    body: str,
    values: Mapping[str, JsonValue | None],
    *,
    level: str = "info",
    at: str | None = None,
) -> Otlp:
    number = LEVELS.get(level, 9)
    return {
        "timeUnixNano": _nanos(at or _now()),
        "severityNumber": number,
        "severityText": SEVERITY.get(number, "INFO"),
        "body": {"stringValue": body},
        "attributes": attributes(values),
    }


def heartbeat_metrics(row: Mapping[str, JsonValue]) -> list[Otlp]:
    """One heartbeat row as gauges. The labels are the subject and its id, so a reader groups by
    host or run without reading a second record (AD-65, AD-69)."""
    labels: dict[str, JsonValue | None] = {
        "qmx.subject": row.get("subject"),
        "qmx.id": row.get("id"),
        "qmx.qmx_version": row.get("qmx_version"),
        "qmx.paused": row.get("paused"),
    }
    found: list[Otlp] = []
    for name, key, unit in (
        ("qmx.heartbeat.cpu_seconds", "cpu_seconds", "s"),
        ("qmx.heartbeat.rss_bytes", "rss_bytes", "By"),
        ("qmx.heartbeat.machine_minutes", "machine_minutes", "min"),
        ("qmx.host.free_disk_bytes", "free_disk_bytes", "By"),
        ("qmx.host.free_ram_bytes", "free_ram_bytes", "By"),
        ("qmx.host.session_bytes", "session_bytes", "By"),
        ("qmx.host.blob_cache_bytes", "blob_cache_bytes", "By"),
    ):
        value = row.get(key)
        if isinstance(value, int | float) and not isinstance(value, bool):
            found.append(gauge(name, value, labels, unit))
    capacity = row.get("capacity")
    if isinstance(capacity, dict):
        for class_, use in cast("dict[str, object]", capacity).items():
            if not isinstance(use, dict):
                continue
            slots = cast("dict[str, JsonValue]", use)
            for name, key in (("qmx.capacity.used", "used"), ("qmx.capacity.size", "size")):
                value = slots.get(key)
                if isinstance(value, int):
                    found.append(gauge(name, value, {**labels, "qmx.class": class_}, "1"))
    library = row.get("library")
    if isinstance(library, dict):
        held = cast("dict[str, JsonValue]", library)
        if isinstance(held.get("outbox"), int):
            found.append(gauge("qmx.library.outbox", cast("int", held["outbox"]), labels, "1"))
        lag = held.get("sync_lag_s")
        if isinstance(lag, int | float) and not isinstance(lag, bool):
            found.append(gauge("qmx.library.sync_lag_s", float(lag), labels, "s"))
    return found


def log_of(kind: str, record: Mapping[str, JsonValue]) -> Otlp:
    """A ledger event or a log line as one OTLP log, its data as the redacted JSON text."""
    at = record.get("at")
    level = record.get("level")
    body = record.get("message") or record.get("kind") or kind
    values: dict[str, JsonValue | None] = {
        f"qmx.{name}": value
        for name, value in record.items()
        if name not in ("data", "message", "level", "at")
    }
    values["qmx.record"] = kind
    data = record.get("data")
    if isinstance(data, dict):
        values["qmx.data"] = json.dumps(data, sort_keys=True)
    return log_record(
        body if isinstance(body, str) else json.dumps(body, sort_keys=True),
        values,
        level=level if isinstance(level, str) else "info",
        at=at if isinstance(at, str) else None,
    )


class Telemetry:
    """One process's exporter: a bounded in-memory batch, sent as OTLP/HTTP JSON."""

    def __init__(
        self,
        endpoint: str,
        *,
        headers: Mapping[str, str] | None = None,
        post: Post | None = None,
        service: str = "qmx-host",
        state: Path | None = None,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.headers = dict(headers or {})
        self.counters = Counters()
        self.service = service
        self.state = state
        self._post = post or _post
        self._batch = _Batch([], [], [])
        self._lock = threading.Lock()
        """Guards the batch only, so an emitter holds it for an append and never for a send."""
        self._sending = threading.Lock()
        """Held across a flush's swap and its posts, so one send runs at a time."""
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="qmx-telemetry", daemon=True)
        self._thread.start()

    def close(self) -> None:
        """Flush what is held and stop the sender. A record that cannot go is counted, not kept."""
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=FLUSH_S * 4)
            self._thread = None
        self.flush()

    def stats(self) -> dict[str, JsonValue]:
        with self._lock:
            held = self._batch.total()
        document = self.counters.document(self.endpoint)
        document["held"] = held
        return document

    def hand(self, kind: str, record: str) -> None:
        """One already-redacted record from the write seams (AD-69). Never raises."""
        try:
            self._take(kind, record)
        except Exception:  # telemetry never fails a write
            LOG.debug("telemetry dropped a %s record", kind)

    def flush(self) -> Unsent | None:
        """Send what is held. None means every record handed before this call was posted, or
        dropped and counted: a send the sender thread had in flight finishes first.

        A hung collector cannot hold a caller longer than `SEND_WAIT_S` for a send in flight, or
        `TIMEOUT_S` per post of its own; either comes back as an `Unsent` with its reason."""
        if not self._sending.acquire(timeout=SEND_WAIT_S):
            return Unsent("send_in_flight", f"another send held the collector past {SEND_WAIT_S} s")
        try:
            with self._lock:
                batch, self._batch = self._batch, _Batch([], [], [])
            return self._send(batch)
        finally:
            self._sending.release()

    def _take(self, kind: str, record: str) -> None:
        made = _made(kind, record)
        with self._lock:
            over = self._batch.total() + len(made) > CAPACITY
            if not over:
                for signal, item in made:
                    if signal == "spans":
                        self._batch.spans.append(item)
                    elif signal == "metrics":
                        self._batch.metrics.append(item)
                    else:
                        self._batch.logs.append(item)
        if over:
            self.counters.dropped += max(1, len(made))
        self._wake.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.wait(timeout=FLUSH_S)
            self._wake.clear()
            self.flush()

    def _send(self, batch: _Batch) -> Unsent | None:
        held: list[tuple[Signal, list[Otlp]]] = [
            ("traces", batch.spans),
            ("metrics", batch.metrics),
            ("logs", batch.logs),
        ]
        unsent: Unsent | None = None
        for signal, items in held:
            if items:
                unsent = self._post_batch(signal, items) or unsent
        return unsent

    def _post_batch(self, signal: Signal, items: list[Otlp]) -> Unsent | None:
        body = json.dumps(self._body(signal, items), allow_nan=False).encode()
        try:
            self._post(f"{self.endpoint}/v1/{signal}", body)
        except (OSError, urllib.error.HTTPError, ValueError) as error:
            self.counters.failed += 1
            self.counters.dropped += len(items)
            self.counters.last_error = redact.redact(f"{type(error).__name__}: {error}")[:200]
            LOG.warning("telemetry: %s not sent: %s", signal, self.counters.last_error)
            self._write_state()
            timed_out = isinstance(error, TimeoutError) or isinstance(
                getattr(error, "reason", None), TimeoutError
            )
            if timed_out:
                return Unsent("timeout", f"the {signal} post ran past {TIMEOUT_S} s")
            return None
        self.counters.sent += len(items)
        self.counters.last_sent_at = _now()
        self._write_state()
        return None

    def _body(self, signal: Signal, items: list[Otlp]) -> Otlp:
        scope: Otlp = {"name": SCOPE, "version": _service_version()}
        policy = {"traces": "resourceSpans", "metrics": "resourceMetrics", "logs": "resourceLogs"}
        wrapper = {"traces": "scopeSpans", "metrics": "scopeMetrics", "logs": "scopeLogs"}
        held = {"traces": "spans", "metrics": "metrics", "logs": "logRecords"}
        return {
            policy[signal]: [
                {
                    "resource": resource(self.service),
                    wrapper[signal]: [{"scope": scope, held[signal]: items}],
                }
            ]
        }

    def _write_state(self) -> None:
        """The counters under the home, so the data health read lists them without a socket."""
        if self.state is None:
            return
        try:
            self.state.parent.mkdir(parents=True, exist_ok=True)
            scratch = self.state.with_suffix(".tmp")
            scratch.write_text(json.dumps(self.counters.document(self.endpoint)), encoding="utf-8")
            scratch.replace(self.state)
        except OSError:
            LOG.debug("telemetry: the counters file could not be written")


def _made(kind: str, record: str) -> list[tuple[str, Otlp]]:
    """The OTLP items one handed record becomes: a span, a heartbeat row's gauges, or a log."""
    try:
        found: object = json.loads(record)
    except ValueError:
        return []
    if kind == "span":
        return [("spans", span_record(from_record(record)))]
    if not isinstance(found, dict):
        return []
    row = cast("dict[str, JsonValue]", found)
    if kind == "heartbeat":
        return [("metrics", item) for item in heartbeat_metrics(row)]
    return [("logs", log_of(kind, row))]


class _Resident:
    """This process's exporter, built once behind its lock."""

    def __init__(self) -> None:
        self.found: Telemetry | None = None


_resident = _Resident()
_resident_lock = threading.Lock()


def process() -> Telemetry | None:
    """This process's exporter, or None while it has none."""
    return _resident.found


def configure(
    endpoint: str,
    *,
    headers: Mapping[str, str] | None = None,
    service: str = "qmx-host",
    state: Path | None = None,
    post: Post | None = None,
) -> Telemetry:
    """Turn the external layer on for this process and register it at the one call site."""
    with _resident_lock:
        if _resident.found is not None:
            return _resident.found
        found = Telemetry(endpoint, headers=headers, post=post, service=service, state=state)
        found.start()
        redact.exporter(found.hand)
        _resident.found = found
        return found


def opened(home: Path, *, service: str = "qmx-host") -> Telemetry | None:
    """Configure from a home's `[telemetry] send_to`, once, or stay off while it names none."""
    if _resident.found is not None:
        return _resident.found
    endpoint = configured(home)
    if not endpoint:
        return None
    return configure(endpoint, service=service, state=home / STATE_FILE)


def reset() -> None:
    """Stop this process's exporter and let the next `configure` build another. Tests only."""
    with _resident_lock:
        found, _resident.found = _resident.found, None
    if found is not None:
        found.close()
        redact.unexporter(found.hand)
