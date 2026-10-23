"""Connection readings ride the host heartbeat, and preflight refuses a fire on a bad reading."""

from __future__ import annotations

import json
from pathlib import Path

from flows import node, workflow

from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, latest
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.preflight import preflight

NOW = "2026-10-23T09:00:00.000000+00:00"


def host_row() -> Heartbeat:
    return Heartbeat(
        subject="host",
        id="pc",
        at=NOW,
        cpu_seconds=0.0,
        rss_bytes=0,
        machine_minutes=0.0,
        qmx_version="0.1.0",
        kinds_digest="digest",
        paused=False,
    )


def test_a_host_heartbeat_carries_the_connection_readings_and_clock_offset(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "connections-health.json").write_text(
        json.dumps(
            {
                "at": NOW,
                "clock_offset_ms": -120,
                "readings": [
                    {"connection": "dukascopy", "word": "ok", "setup": "healthy", "latency_ms": 42},
                    {"connection": "vision", "word": "down", "code": "http_503"},
                    {"connection": "stale", "word": "unknown"},
                ],
            }
        ),
        encoding="utf-8",
    )
    HeartbeatLog(tmp_path, 7.0).write([host_row()])

    seen = latest(tmp_path)["host:pc"]

    assert [(reading.connection, reading.word) for reading in seen.connections] == [
        ("dukascopy", "ok"),
        ("vision", "down"),
    ]
    assert seen.clock_offset_ms == -120


def check(words: dict[str, str], settings: dict[str, object] | None = None) -> str:
    body = workflow(
        [node("Fetch", "script", connection="dukascopy") | {"runs_on": "pc"}], {}
    )
    blocked = preflight(
        body,
        DEFAULTS if settings is None else settings,
        profiles=None,
        credentials=None,
        skills=None,
        connections=words,
    )
    return "ok" if blocked is None else f"{blocked.cause}:{blocked.code}"


def test_preflight_blocks_a_fire_whose_connection_reads_down() -> None:
    assert check({"dukascopy": "ok"}) == "ok"
    assert check({"dukascopy": "down"}) == "config:connection_unhealthy"
    assert check({"dukascopy": "slowed"}) == "config:connection_unhealthy"
    assert check({}) == "config:connection_unknown"
    assert check({"dukascopy": "ok"}, {**DEFAULTS, "connection.dukascopy.home": "contabo"}) == (
        "config:connection_unreachable"
    )
    assert check({"dukascopy": "ok"}, {**DEFAULTS, "connection.dukascopy.home": "pc"}) == "ok"
