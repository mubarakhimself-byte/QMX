"""The runner places a data step next to its partitions, or waits `placement` (AD-70).

Each host's heartbeat row carries a partition summary. A step that names series in its
`data_scope` runs on the first placement in its `runs_on` list whose fresh row holds them, and
waits `placement` while no placement holds them or can reach a door that does.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from flows import ONE_TRY, Script, edge, node, workflow

from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, kinds_digest, partition_summary
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob, NodeResult
from qmx_engine.runner import Engine, Outcome
from qmx_engine.workers.local import Emit, LocalWorker

NOW = datetime(2026, 10, 24, 9, 0, tzinfo=UTC)
SERIES = "dukascopy/EURUSD/tick/-"


class Placements(LocalWorker):
    """The local table, recording the placement each `land` attempt arrived with."""

    def __init__(self) -> None:
        super().__init__()
        self.seen: list[str] = []

    async def run(self, job: NodeJob, emit: Emit) -> NodeResult:
        if job.node_id == "land":
            self.seen.append(job.placement)
        return await super().run(job, emit)


def host(name: str, partitions: dict[str, int]) -> Heartbeat:
    return Heartbeat(
        subject="host",
        id=name,
        at=NOW.isoformat(),
        cpu_seconds=0.0,
        rss_bytes=0,
        machine_minutes=0.0,
        qmx_version="0",
        kinds_digest=kinds_digest(()),
        paused=False,
        partitions=partitions,
    )


def run(tmp_path: Path, rows: list[Heartbeat]) -> tuple[Outcome, list[str], list[Event]]:
    home = tmp_path / "home"
    HeartbeatLog(home, 7.0).write(rows)
    folder = tmp_path / "flow"
    folder.mkdir()
    land: dict[str, Any] = node("land", "script", data_scope=[SERIES]) | {
        "runs_on": ["pc", "contabo"]
    }
    definition = workflow([node("start", "trigger"), land], {"start": {"main": [edge("land")]}})
    document = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    worker = Placements()

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(
                home,
                ledger,
                settings=ONE_TRY,
                worker=worker,
                wall=lambda: NOW,
                executors={"script": Script()},
            )
            return await engine.start(folder, definition, mode="test", inputs=None, run_id="run-1")

    outcome = asyncio.run(go())
    with Reader.open(home) as reader:
        events = reader.events("run-1")
    return outcome, worker.seen, events


def test_placement_prefers_the_machine_whose_summary_holds_the_partitions(
    tmp_path: Path,
) -> None:
    outcome, seen, _ = run(tmp_path, [host("pc", {}), host("contabo", {SERIES: 3})])

    assert outcome.status == "passed"
    assert seen == ["contabo"]


def test_a_node_with_no_reachable_data_waits_placement(tmp_path: Path) -> None:
    outcome, seen, events = run(tmp_path, [host("pc", {}), host("contabo", {})])

    waits = [e.data for e in events if e.kind == "node_waiting" and e.data["node_id"] == "land"]
    assert outcome.status == "waiting"
    assert seen == []
    assert [(w["reason"], w["resume_at"]) for w in waits] == [
        ("placement", "2026-10-24T09:01:00+00:00")
    ]


def test_a_host_row_summarises_the_series_its_store_holds(tmp_path: Path) -> None:
    root = tmp_path / "market" / "series" / "dukascopy" / "EURUSD" / "tick" / "-"
    for month in ("2026-07", "2026-08"):
        (root / month).mkdir(parents=True)
        (root / month / "state.json").write_text("{}", encoding="utf-8")

    assert partition_summary(tmp_path) == {SERIES: 2}
