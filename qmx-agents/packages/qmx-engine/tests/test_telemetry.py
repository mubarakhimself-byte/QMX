"""The external layer (AD-69): the records QMX already writes, handed to one exporter.

The tests drive the write seams the app uses, not only the payload builders: a ledger write and a
heartbeat write, with the exporter pointed at a function that records what arrives.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qmx_engine import telemetry
from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, kinds_digest
from qmx_engine.ledger import redact
from qmx_engine.ledger.events import JsonObject
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger

T0 = datetime(2026, 10, 23, 9, 0, tzinfo=UTC)
RUN = "run-1"
ENDPOINT = "http://collector.invalid:4318"


def a_span() -> Span:
    return Span(
        span_id="s-1",
        trace_id=RUN,
        node_id="step",
        iteration=0,
        partition=None,
        attempt=1,
        started_at=T0.isoformat(),
        ended_at=T0.isoformat(),
        status="ok",
        role="builder",
        profile="deepseek",
        model="deepseek-v4-flash",
        tokens={"in": 120, "out": 40},
    )


def a_host_row(free_disk_bytes: int | None = None) -> Heartbeat:
    return Heartbeat(
        subject="host",
        id="pc",
        at=T0.isoformat(),
        cpu_seconds=1.5,
        rss_bytes=1_000,
        machine_minutes=2.0,
        qmx_version="0.1.0",
        node_kinds=("script",),
        kinds_digest=kinds_digest(("script",)),
        paused=False,
        free_disk_bytes=free_disk_bytes,
    )


def attribute_values(record: dict[str, object]) -> dict[str, object]:
    entries = cast("list[dict[str, object]]", record["attributes"])
    return {str(entry["key"]): entry["value"] for entry in entries}


def test_the_pinned_genai_names_and_the_runs_trace_id() -> None:
    record = telemetry.span_record(a_span())
    values = attribute_values(record)

    assert telemetry.GENAI == "1.36.0"
    assert values["gen_ai.system"] == {"stringValue": "deepseek"}
    assert values["gen_ai.request.model"] == {"stringValue": "deepseek-v4-flash"}
    assert values["gen_ai.usage.input_tokens"] == {"intValue": "120"}
    assert values["gen_ai.usage.output_tokens"] == {"intValue": "40"}
    assert values["gen_ai.operation.name"] == {"stringValue": "invoke_agent"}
    assert record["traceId"] == "4e65d3fbe8ad6535681b021b30785b12"
    assert record["status"] == {"code": 1}


def test_an_exported_record_carries_no_value_the_redactor_masks(tmp_path: Path) -> None:
    sent: list[tuple[str, bytes]] = []
    telemetry.reset()
    exporter = telemetry.configure(ENDPOINT, post=lambda url, body: sent.append((url, body)))
    secret = "sk-or-v1-" + "a" * 32
    with Ledger.open(tmp_path) as ledger:
        ledger.append(
            RUN,
            "run_created",
            {"mode": "test", "note": f"the key {secret} was echoed"},
            at=T0.isoformat(),
        )
    exporter.flush()

    bodies = b"".join(body for _, body in sent)
    assert sent and sent[0][0] == f"{ENDPOINT}/v1/logs"
    assert secret.encode() not in bodies
    assert b"[redacted]" in bodies


def test_a_heartbeat_row_goes_out_as_gauges(tmp_path: Path) -> None:
    sent: list[tuple[str, bytes]] = []
    telemetry.reset()
    exporter = telemetry.configure(ENDPOINT, post=lambda url, body: sent.append((url, body)))
    HeartbeatLog(tmp_path, 7).write([a_host_row(free_disk_bytes=73_259_859_968)])
    exporter.flush()

    assert [url for url, _ in sent] == [f"{ENDPOINT}/v1/metrics"]
    body = json.loads(sent[0][1])
    gauges = body["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
    assert [gauge["name"] for gauge in gauges] == [
        "qmx.heartbeat.cpu_seconds",
        "qmx.heartbeat.rss_bytes",
        "qmx.heartbeat.machine_minutes",
        "qmx.host.free_disk_bytes",
        "qmx.library.outbox",
    ]
    disk = gauges[3]["gauge"]["dataPoints"][0]
    assert disk["asInt"] == "73259859968"
    labels = {entry["key"]: entry["value"] for entry in disk["attributes"]}
    assert labels["qmx.id"] == {"stringValue": "pc"}


def test_a_collector_that_is_down_drops_and_counts_and_never_fails_the_write(
    tmp_path: Path,
) -> None:
    def refuse(url: str, body: bytes) -> None:
        raise OSError(f"the collector at {url} is away")

    telemetry.reset()
    exporter = telemetry.configure(ENDPOINT, post=refuse, state=tmp_path / telemetry.STATE_FILE)
    with Ledger.open(tmp_path) as ledger:
        ledger.append(RUN, "run_created", {"mode": "test"}, at=T0.isoformat())
    exporter.flush()

    assert exporter.counters.sent == 0
    assert exporter.counters.dropped == 1
    assert exporter.counters.failed == 1
    state = json.loads((tmp_path / telemetry.STATE_FILE).read_text(encoding="utf-8"))
    assert state["dropped"] == 1
    assert state["endpoint"] == ENDPOINT


def test_a_span_write_reaches_the_exporter_once_it_closes(tmp_path: Path) -> None:
    seen: list[tuple[str, str]] = []

    def sink(kind: str, record: str) -> None:
        seen.append((kind, record))

    telemetry.reset()
    redact.exporter(sink)
    try:
        with Ledger.open(tmp_path) as ledger:
            key: JsonObject = {"node_id": "step", "iteration": 0, "partition": None, "attempt": 1}
            ledger.append(RUN, "node_started", key, at=T0.isoformat())
            ledger.append(RUN, "node_finished", key, at=T0.isoformat())
    finally:
        redact.unexporter(sink)

    assert [kind for kind, _ in seen].count("span") == 1
    span = json.loads(next(record for kind, record in seen if kind == "span"))
    assert span["status"] == "ok"
    assert span["trace_id"] == RUN
    assert span["node_id"] == "step"
    assert span["tokens"] == {}
