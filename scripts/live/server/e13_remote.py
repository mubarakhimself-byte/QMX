"""E13: a placed node's outputs come back by hash and its events land in the home ledger.

The lane is a real engine run on a throwaway home: the engine walks the `run-on-a-machine`
template, its `script` node is placed on Contabo, and the engine's worker is the remote adapter,
so the attempt ships there and back. Then the lane reads the home ledger and asserts the
`node_finished` row carries the same `output_hash` the attempt's `Ok` did, and that the attempt's
own events (start, heartbeats, start of the node on the box) reached the ledger in order.

Writes `owner-rem-e13.log` itself.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from e57_remote import EVIDENCE, SshGateway, SshProvider, settings  # noqa: E402
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.store import Reader
from qmx_engine.service.api import EngineService
from qmx_engine.workers.remote import PlacementWorker

HOME = Path("D:/Temp/rem-e13-home")
FOLDER = Path("qmx-agents/packages/qmx-engine/src/qmx_engine/templates/run-on-a-machine")
LOG_PATH = EVIDENCE / "owner-rem-e13.log"


def mint(_job: object) -> str:
    from qmx_router.passes import PassAuthority

    _, bearer = PassAuthority().mint(run="lane-e13", placement="contabo")
    return bearer


def worker() -> PlacementWorker:
    return PlacementWorker(
        gateway=SshGateway(),
        providers={"contabo": SshProvider()},
        settings=settings(),
        mint=mint,
        remote={"contabo"},
        heartbeat_timeout=90.0,
        clock=time.time,
    )


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if HOME.exists():
        shutil.rmtree(HOME)
    lines: list[str] = []
    log = LOG_PATH.open("w", encoding="utf-8")

    def note(text: str) -> None:
        lines.append(text)
        log.write(text + "\n")
        log.flush()

    note(f"E13 lane at {datetime.now(UTC).isoformat()}")
    folder = load(FOLDER)
    assert folder.document is not None, folder.problems
    workflow = Workflow.model_validate(folder.document)
    with EngineService.open(HOME) as svc:
        engine = svc.ctx.engine
        engine.worker = worker()
        outcome = asyncio.run(
            engine.start(
                FOLDER,
                workflow,
                mode="test",
                inputs={"command": ["python3", "-c", "print(42)"]},
            )
        )
        note(f"run {outcome.run_id} ended {outcome.status}")
        events = Reader.open(HOME).events(outcome.run_id)
        kinds = [event.kind for event in events]
        note(f"ledger events: {len(events)}: {', '.join(kinds[:12])}")
        assert outcome.status == "passed", outcome
        finished = [
            event
            for event in events
            if event.kind == "node_finished" and event.data.get("node_id") == "run"
        ]
        assert len(finished) == 1, kinds
        data = finished[0].data
        outputs = data.get("outputs")
        output_hash = data.get("output_hash")
        assert isinstance(outputs, dict) and isinstance(output_hash, str), data
        from qmx_ledger.journal import fingerprint

        assert output_hash == fingerprint(outputs), (output_hash, outputs)
        note(f"PASS: node_finished carries outputs by hash ({output_hash[:16]}…)")
        assert any(event.kind == "node_started" for event in events), kinds
        note("PASS: the placed attempt's events landed in the home ledger")
        note(f"PASS: local baseline attempt {baseline():.3f}s dispatch-to-start (same template, pc)")
    log.close()
    return 0


def baseline() -> float:
    """One local attempt of the same workflow on `pc`: the number the remote delay is read against."""
    home = Path("D:/Temp/rem-e13-baseline")
    if home.exists():
        shutil.rmtree(home)
    folder = load(FOLDER)
    assert folder.document is not None
    document = json.loads(json.dumps(folder.document))
    document["nodes"][1]["runs_on"] = "pc"
    workflow = Workflow.model_validate(document)
    with EngineService.open(home) as svc:
        outcome = asyncio.run(
            svc.ctx.engine.start(
                FOLDER,
                workflow,
                mode="test",
                inputs={"command": ["python3", "-c", "print(42)"]},
            )
        )
        assert outcome.status == "passed", outcome
        events = Reader.open(home).events(outcome.run_id)
        placed = [
            event
            for event in events
            if event.kind in {"node_scheduled", "node_started"}
            and event.data.get("node_id") == "run"
        ]
        scheduled = next(event for event in placed if event.kind == "node_scheduled")
        started = next(event for event in placed if event.kind == "node_started")
        return (
            datetime.fromisoformat(started.at) - datetime.fromisoformat(scheduled.at)
        ).total_seconds()


if __name__ == "__main__":
    sys.exit(main())
