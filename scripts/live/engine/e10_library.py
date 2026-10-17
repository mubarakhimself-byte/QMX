"""EP9 lane 3 (E10): a live run's results land in the Library, and the run ledger keeps none of
the definition.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e10_library.py`
Writes `evidence/ep9/<ENGINE_LOG_PREFIX>ep9-e10.log`. The `script-chain` fixture is saved as a
draft, tested, published and started live through the engine service, as real script subprocesses;
the lane then reads the fake Library's SQLite file and every table of `engine.sqlite`. No model, no
key, no ship home.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Final

from common import Log, throwaway_home
from qmx_engine.ledger.store import ledger_path
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library_fake import library_path
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from x07_nodes import CHAIN

NAME: Final = json.loads((CHAIN / "definition.json").read_text(encoding="utf-8"))["name"]


def main() -> int:
    log = Log("ep9", "ep9-e10")
    home = throwaway_home("ep9", "e10")
    with EngineService.open(home) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        run = asyncio.run(svc.runs.start(version, caller=OPERATOR))
    log(f"live run {run.run_id} of version {version}: {run.mode} {run.status}")
    with sqlite3.connect(library_path(home)) as db:
        rows = db.execute(
            "SELECT object_id, kind, ref, blob, fields FROM objects WHERE ref = ?",
            (f"refs/runs/{run.run_id}",),
        ).fetchall()
        for object_id, kind, ref, blob, _ in rows:
            log(f"object {object_id} {kind} on {ref} blob {blob}")
        edges = db.execute("SELECT from_id, edge, to_id FROM edges").fetchall()
        for edge in edges:
            log(f"edge {edge}")
    summaries = [(o, json.loads(f)) for o, k, _, _, f in rows if k == "workflow-run"]
    traces = [(o, b) for o, k, _, b, _ in rows if k == "artifact"]
    kinds = {o: json.loads(f).get("type") for o, k, _, _, f in rows if k == "artifact"}
    summary_id, summary = summaries[-1] if summaries else ("", {})
    trace_id, trace_blob = traces[-1] if traces else ("", None)
    log.check(
        "the run summary exists, live and passed",
        (summary.get("mode"), summary.get("status"), summary.get("object_id"))
        == ("live", "passed", version),
        summary,
    )
    log.check("the trace artifact exists", kinds.get(trace_id) == "trace", kinds)
    log.check(
        "the trace artifact's blob is the summary's trace_artifact_hash",
        trace_blob is not None and summary.get("trace_artifact_hash") == trace_blob,
        (trace_blob, summary.get("trace_artifact_hash")),
    )
    log.check(
        "a run-of edge links the run to the version",
        (summary_id, "run-of", version) in edges,
        summary_id,
    )
    log.check(
        "a produced-by edge links the trace to the run",
        (trace_id, "produced-by", summary_id) in edges,
        trace_id,
    )
    with sqlite3.connect(f"{ledger_path(home).resolve().as_uri()}?mode=ro", uri=True) as db:
        tables = [t for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        holding = [
            table
            for table in tables
            if NAME in str(db.execute(f"SELECT * FROM {table}").fetchall())  # noqa: S608
        ]
    log(f"engine.sqlite tables: {tables}")
    log.check("no engine.sqlite table holds the definition", holding == [], holding)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
