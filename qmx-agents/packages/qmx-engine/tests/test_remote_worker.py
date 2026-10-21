"""The remote worker's contract: one job in, one ending out, and no key on the wire."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from qmx_ledger.journal import fingerprint

from qmx_engine.ledger.events import EventKind
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.remote import (
    SCHEMA,
    PlacementWorker,
    attempt_bundle,
    result_from_document,
    sessions_of,
)

PASS = "pass_" + "a" * 48
"""A stand-in run pass, long enough that the sidecar registers it for redaction."""


def job(placement: str = "contabo") -> NodeJob:
    return NodeJob(
        run_id="run-1",
        node_id="count",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="memo-1",
        idempotency_key="run-1.count.0.1",
        node_definition={
            "type": "script",
            "parameters": {"script": "count.py"},
            "outputs": {"count": "int"},
        },
        inputs={"rows": [1, 2, 3]},
        now="2026-10-21T20:00:00+00:00",
        mode="test",
        credentials={"OPENROUTER_KEY": "qmx/openrouter"},
        workspace="D:/Temp/rem-zones/run-1",
        placement=placement,
    )


class FakeGateway:
    def __init__(self, rows: list[dict[str, Any]], result: dict[str, Any] | None) -> None:
        self.rows = rows
        self.ending = result

    def events(self, run_id: str) -> list[dict[str, Any]]:
        return list(self.rows)

    def result(self, run_id: str) -> dict[str, Any] | None:
        return self.ending


class FakeProvider:
    def __init__(self) -> None:
        self.bundle: dict[str, Any] | None = None
        self.secrets: dict[str, str] = {}
        self.stops = 0
        self.state = "running"

    def provision(self, run_id: str, bundle: Any) -> dict[str, Any]:
        self.bundle = json.loads(json.dumps(bundle.model_dump(mode="json")))
        return {"run_id": run_id}

    def start(self, handle: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
        self.secrets = dict(secrets)
        return handle

    def status(self, handle: dict[str, Any]) -> str:
        return self.state

    def logs(self, handle: dict[str, Any]) -> str:
        return ""

    def stop(self, handle: dict[str, Any]) -> None:
        self.stops += 1
        self.state = "stopped"

    def teardown(self, handle: dict[str, Any]) -> None:
        self.stop(handle)


class Clock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        self.now += 0.01
        return self.now


def worker(
    gateway: FakeGateway, provider: FakeProvider, *, clock: Clock | None = None
) -> PlacementWorker:
    return PlacementWorker(
        gateway=gateway,
        providers={"contabo": provider},
        settings=DEFAULTS,
        mint=lambda _job: PASS,
        remote={"contabo"},
        heartbeat_timeout=0.05,
        poll_seconds=0.0,
        clock=clock or Clock(),
    )


def run(worker: PlacementWorker, job: NodeJob) -> tuple[Any, list[tuple[str, dict[str, Any]]]]:
    emitted: list[tuple[str, dict[str, Any]]] = []

    def emit(kind: EventKind, data: dict[str, Any]) -> None:
        emitted.append((str(kind), data))

    return asyncio.run(worker.run(job, emit)), emitted


def test_a_placed_job_ships_its_shape_and_returns_the_result() -> None:
    gateway = FakeGateway(
        rows=[
            {"kind": "heartbeat", "at": "2026-10-21T20:00:05+00:00", "note": "running"},
            {"kind": "log", "at": "2026-10-21T20:00:06+00:00", "line": "counting"},
        ],
        result={
            "status": "ok",
            "outputs": {"count": 3},
            "output_hash": fingerprint({"count": 3}),
            "artifacts": ["outputs/count.json"],
        },
    )
    provider = FakeProvider()
    result, emitted = run(worker(gateway, provider), job())

    assert isinstance(result, Ok)
    assert result.outputs == {"count": 3}
    assert result.artifacts == ("outputs/count.json",)
    bundle = provider.bundle
    assert bundle is not None
    shipped = bundle["definition"]
    assert shipped["schema"] == SCHEMA
    assert shipped["job"]["node_definition"]["type"] == "script"
    assert shipped["job"]["inputs_hash"] == fingerprint({"rows": [1, 2, 3]})
    assert shipped["job"]["placement"] == "contabo"
    assert shipped["resources"] == {
        "cpus": 2,
        "memory_mb": 2_048,
        "timeout": 3_600,
        "gpu": 0,
    }
    assert [kind for kind, _ in emitted] == ["node_started", "heartbeat", "log"]
    assert emitted[1][1] == {"at": "2026-10-21T20:00:05+00:00", "note": "running"}


def test_a_lost_heartbeat_folds_unknown_instead_of_a_failure_or_a_retry() -> None:
    provider = FakeProvider()
    result, _ = run(worker(FakeGateway(rows=[], result=None), provider), job())

    assert isinstance(result, Failed)
    assert result.code == "heartbeat_lost"
    assert result.effect_state == "unknown"
    assert result.retryable is True
    assert provider.stops == 0


def test_the_job_carries_the_pass_and_no_key() -> None:
    provider = FakeProvider()
    run(
        worker(FakeGateway(rows=[], result={"status": "ok", "outputs": {"count": 1}}), provider),
        job(),
    )

    assert provider.secrets == {"QMX_RUN_PASS": PASS}
    assert provider.bundle is not None
    shipped = json.dumps(provider.bundle["definition"])
    assert PASS not in shipped
    assert provider.bundle["definition"]["secrets"] == ["OPENROUTER_KEY"]
    assert "sk-" not in shipped
    assert "qmx/openrouter" not in shipped


def test_the_contabo_row_derives_four_sessions() -> None:
    assert DEFAULTS["placement.contabo.ram_budget_mb"] == 12_288
    assert DEFAULTS["placement.contabo.overhead_mb"] == 6_144
    assert sessions_of(DEFAULTS, "contabo") == 4


def test_a_wire_result_round_trips_every_ending() -> None:
    ok = result_from_document({"status": "ok", "outputs": {"n": 1}, "verdict": "pass"})
    assert isinstance(ok, Ok) and ok.verdict == "pass"
    failed = result_from_document(
        {
            "status": "failed",
            "code": "script_failed",
            "message": "no",
            "retryable": False,
            "effect_state": "after",
        }
    )
    assert isinstance(failed, Failed)
    assert (failed.code, failed.retryable, failed.effect_state) == ("script_failed", False, "after")
    assert failed.signature == signature("script_failed", "no")


def test_a_bundle_carries_files_by_hash() -> None:
    files = {"count.py": "print('{\"count\": 3}')\n"}
    bundle = attempt_bundle(job(), files=files)
    assert bundle["file_hashes"] == {"count.py": fingerprint(files["count.py"])}
    assert bundle["files"] == files
