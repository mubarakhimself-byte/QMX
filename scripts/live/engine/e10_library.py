"""LIB1 lane 2 (E10 on the real store): a live run through `qmx_host` lands its results in the
Library store, and the run ledger keeps none of the definition.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e10_library.py`
Writes `evidence/lib1/<ENGINE_LOG_PREFIX>lib1-e10.log` under the engine store. `python -m qmx_host`
starts on a throwaway home through `lane_host.py`; over REST the `script-chain` fixture is saved as
a draft, tested, published and run live, as real script subprocesses. After the host stops, the
lane opens the home's Library store `<home>/library/` (the host held its writer lock until then)
and every table of `engine.sqlite`. No model, no key, no ship home.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Final

from common import Log, throwaway_home
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import ledger_path
from qmx_engine.ports.library_fake import library_path
from qmx_library.principal import Principal
from qmx_library.store import Store
from x13_doors import chain, host, reply

ITEM: Final = "chain"
NAME: Final = chain(ITEM)["definition"]["name"]
READER: Final = Principal("operator")


def main() -> int:
    log = Log("lib1", "lib1-e10")
    home = throwaway_home("lib1", "e10")
    with host(log, home) as (client, _, _):
        reply(log, "draft put", client.put(f"/api/workflows/{ITEM}/draft", json=chain(ITEM)))
        reply(log, "test", client.post(f"/api/workflows/{ITEM}/test"))
        published = reply(log, "publish", client.put(f"/api/workflows/{ITEM}", json={}))
        version = published["object_id"]
        run = reply(log, "live run", client.post(f"/api/workflows/{ITEM}/run"))
    run_id = run["run_id"]
    log.check(
        "publish answers version 1.0.0, published and tested",
        (published.get("semver"), published.get("state"), published.get("tested"))
        == ("1.0.0", "published", True),
        published,
    )
    log.check(
        "the live run of the published version passed",
        (run.get("mode"), run.get("status"), run.get("object_id")) == ("live", "passed", version),
        run,
    )
    with Store.open(home / "library", redactor=redact) as store:
        on_run = dict(store.heads_on(f"refs/runs/{run_id}"))
        for item, head in on_run.items():
            view = store.get(READER, head)
            log(f"object {head} {view.kind} item {item} blobs {sorted(view.blobs)}")
        summary_id = on_run.get(run_id, "")
        summary = store.get(READER, summary_id).fields if summary_id else {}
        into = store.edges_of(summary_id, reverse=True)
        produced = [a for a, relation, *_ in into if relation == "produced-by"]
        traces = [o for o in produced if store.get(READER, o).fields.get("type") == "trace"]
        trace = store.get(READER, traces[0]) if traces else None
        out = store.edges_of(summary_id, reverse=False)
        run_of = [c for _, relation, c, *_ in out if relation == "run-of"]
        landed = store.head(run_id, "main")
        stored = store.get(READER, version, blobs="fetch")
        log.check(
            "the run summary is a Library object, live and passed",
            (summary.get("mode"), summary.get("status"), summary.get("object_id"))
            == ("live", "passed", version),
            summary,
        )
        log.check(
            "the trace is an artifact whose content blob is the summary's trace_artifact_hash",
            trace is not None
            and trace.blobs["content"].blob_id == summary.get("trace_artifact_hash"),
            trace and trace.blobs,
        )
        log.check("a run-of edge links the run to the version", run_of == [version], run_of)
        log.check("a produced-by edge links the trace to the run", bool(traces), produced)
        log.check(
            "the passed live run's summary landed on main",
            landed is not None and landed[0] == summary_id,
            landed,
        )
        log.check(
            "the published version is a workflow object on main holding the definition",
            (stored.kind, json.loads(stored.data["definition"])["name"]) == ("workflow", NAME),
            stored.kind,
        )
    log.check(
        "the engine wrote nothing to the fake Library",
        not library_path(home).exists(),
        library_path(home),
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
