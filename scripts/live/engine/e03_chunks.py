"""EP6's live lanes for fan-out by chunk (E3, E29 by chunk), driven through the real `Engine` with
planted executors (`e02_replay.EngineRun`), then read back from its ledger.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e03_chunks.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression e03 chunk-setting token-cap perf`; none named runs all. Each lane writes
`evidence/ep6/<ENGINE_LOG_PREFIX>ep6-<lane>.log` and the script exits 1 if any lane failed. Every
workflow is written as a folder and passes the EP3 validator before it runs. No lane needs a model,
a key or the ship home.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Final, cast

from common import Log, throwaway_home
from e02_replay import ONE_TRY, EngineRun, e02
from ep2_lanes import GIT, REPO, git
from pydantic import JsonValue
from qmx_engine.core.fold import fold
from qmx_engine.core.partitions import chunks, estimate
from qmx_engine.core.ready import next_commands
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Chunk, Workflow
from qmx_engine.definition.validate import validate
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.settings import DEFAULTS

HARNESS: Final = "qmx-agents/packages/qma-harness"
NOW: Final = "2026-10-17T09:00:00+00:00"
LATER: Final = "2026-10-17T10:00:00+00:00"
PERF_ITEMS: Final = 100_000
PERF_ROUNDS: Final = 5

type Planted = tuple[str, int | None]


class Script:
    """Applies `fn` to the `in` value of node `only` (others pass it through). A `(node,
    partition)` in `failing` fails once; one in `slow` stays in flight until the lane releases
    it."""

    def __init__(
        self,
        fn: Callable[[NodeJob, JsonValue], JsonValue] = lambda _, value: value,
        *,
        only: str | None = None,
        failing: set[Planted] | None = None,
        slow: set[Planted] | None = None,
    ) -> None:
        self.fn, self.only = fn, only
        self.failing: set[Planted] = set(failing or ())
        self.slow: set[Planted] = set(slow or ())
        self.calls: list[tuple[str, int, int | None]] = []
        self.gates: dict[Planted, asyncio.Event] = {}
        self.released: dict[Planted, JsonValue] = {}

    async def run(self, job: NodeJob) -> NodeResult:
        self.calls.append((job.node_id, job.iteration, job.partition))
        key = (job.node_id, job.partition)
        if key in self.failing:
            self.failing.discard(key)
            return Failed("boom", "planted failure", "planted", retryable=True)
        if key in self.slow:
            await self.gates.setdefault(key, asyncio.Event()).wait()
            return Ok({"main": self.released[key]})
        value = job.inputs.get("in") if isinstance(job.inputs, dict) else None
        return Ok({"main": self.fn(job, value) if self.only in (None, job.node_id) else value})

    def release(self, node_id: str, partition: int | None, value: JsonValue) -> None:
        """A slow slot's worker reports in with `value`."""
        self.released[(node_id, partition)] = value
        self.gates.setdefault((node_id, partition), asyncio.Event()).set()


def node(name: str, type_: str, **parameters: Any) -> dict[str, Any]:
    return {"id": name, "name": name, "type": type_, "typeVersion": 1, "parameters": parameters}


def edge(target: str, map_: str = "one", port: str = "in", **extra: Any) -> dict[str, Any]:
    return {"node": target, "port": port, "map": map_, **extra}


def document(nodes: list[dict[str, Any]], connections: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "qmx.workflow/1",
        "id": "lane-flow",
        "name": "lane flow",
        "nodes": nodes,
        "connections": {
            source: {port: [targets] for port, targets in ports.items()}
            for source, ports in connections.items()
        },
    }


def validated(log: Log, slug: str, doc: dict[str, Any]) -> Workflow:
    """Write the workflow as a folder and run the EP3 validator over it."""
    folder = throwaway_home("ep6", slug)
    (folder / "definition.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    problems = validate(load(folder))
    log.check(f"the {slug} workflow passes validation", problems == [], problems)
    return Workflow.model_validate(doc)


def engine_run(
    definition: Workflow,
    script: Script,
    run_id: str,
    settings: Mapping[str, object] | None = None,
) -> EngineRun:
    return EngineRun("ep6", definition, run_id, {"script": script}, settings=settings or ONE_TRY)


def of(events: Sequence[Event], kind: str, node_id: str) -> list[dict[str, JsonValue]]:
    return [e.data for e in events if e.kind == kind and e.data.get("node_id") == node_id]


def chunked(spec: dict[str, Any]) -> dict[str, Any]:
    return document(
        [node("start", "trigger"), node("read", "script"), node("gather", "join")],
        {
            "start": {"main": [edge("read", "chunk", chunk=spec)]},
            "read": {"main": [edge("gather")]},
        },
    )


def summary(_: NodeJob, chunk: JsonValue) -> JsonValue:
    items = chunk if isinstance(chunk, list) else []
    return {"first": items[0] if items else None, "count": len(items)}


def regression(log: Log, base: str, trunk: str) -> None:
    on_trunk = subprocess.run(
        [
            GIT,
            "cat-file",
            "-e",
            f"{trunk}:qmx-agents/packages/qmx-engine/src/qmx_engine/core/partitions.py",
        ],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    log.check("trunk has no fan-out to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    log("EP5's E2 lane from e02_replay.py, at head:")
    e02(log)


def e03(log: Log) -> None:
    doc = chunked({"by": "items", "size": 10})
    definition = validated(log, "e03", doc)
    script = Script(summary, only="read", failing={("read", 1), ("read", 4)})
    run = engine_run(definition, script, "run-e03")
    first = run.start(list(range(60)))
    scheduled = of(run.events, "node_scheduled", "read")
    log(f"partitions={len(scheduled)} by=items size=10")
    log(f"first pass ended: {first}")
    first_calls = [c for c in script.calls if c[0] == "read"]
    log.check("6 attempts ran, not 60", len(first_calls) == 6, len(first_calls))
    log.check(
        "each failed chunk parks alone, then the run parks on the join",
        first.status == "failed" and "join_failed" in (first.reason or ""),
        first,
    )
    mark, calls = len(run.events), len(script.calls)
    ended = run.resume(LATER)
    resumed = of(run.events[mark:], "node_started", "read")
    log(f"new attempts={len(resumed)}")
    pairs = [(e["partition"], e["attempt"]) for e in resumed]
    log(f"resumed attempts (partition, attempt): {pairs}")
    log.check(
        "exactly 2 new attempts, for partitions 1 and 4",
        pairs == [(1, 2), (4, 2)],
        resumed,
    )
    memo = of(run.events[mark:], "node_finished", "read")
    log.check(
        "the other 4 chunks settle from their memos",
        sorted(cast(int, e["partition"]) for e in memo if e.get("memo")) == [0, 2, 3, 5],
        memo,
    )
    again = [c for c in script.calls[calls:] if c[0] == "read"]
    log.check(
        "the executor ran only the two failed chunks again",
        again == [("read", 0, 1), ("read", 0, 4)],
        again,
    )
    output = ended.outputs if ended.status == "passed" else None
    log(f"join output: {output}")
    expected = {"gather": {"main": [{"first": p * 10, "count": 10} for p in range(6)]}}
    log.check("the join output is ordered by partition id", output == expected, output)
    ledger_lane(log, definition, run)


def ledger_lane(log: Log, definition: Workflow, run: EngineRun) -> None:
    """The run's ledger, read back, folds to an ended run, and every chunk attempt has its own
    partition span."""
    with Reader.open(run.home) as reader:
        stored = reader.events(run.run_id)
        spans = [s for s in reader.spans(run.run_id) if s.node_id == "read"]
    log.check(
        "the ledger read back folds to a passed run",
        fold(definition, stored).ended == "passed",
        len(stored),
    )
    log.check(
        "a ledger fold of the finished run gives no command",
        next_commands(fold(definition, stored)) == [],
        "",
    )
    shown = sorted((s.partition, s.attempt, s.status) for s in spans)
    log(f"read spans (partition, attempt, status): {shown}")
    log.check(
        "8 chunk spans: 6 first attempts, 2 failed then rerun",
        len(spans) == 8
        and [s for s in shown if s[2] == "failed"] == [("1", 1, "failed"), ("4", 1, "failed")],
        shown,
    )


def chunk_setting(log: Log) -> None:
    home = throwaway_home("ep6", "chunk-setting-doc")
    settings_doc = home / "settings.json"
    settings_doc.write_text(json.dumps({"chunk.size": 15}), encoding="utf-8")
    overrides = json.loads(settings_doc.read_text(encoding="utf-8"))
    log(f"settings document {settings_doc}: {overrides}")
    definition = validated(log, "chunk-setting", chunked({"by": "items"}))
    run = engine_run(
        definition, Script(summary, only="read"), "run-setting", dict(ONE_TRY) | overrides
    )
    ended = run.start(list(range(60)))
    scheduled = of(run.events, "node_scheduled", "read")
    log(f"partitions={len(scheduled)} by=items chunk.size=15; ended {ended.status}")
    log.check("4 partitions run", len(of(run.events, "node_started", "read")) == 4, len(scheduled))
    recorded = run.events[0].data.get("settings")
    log.check(
        "run_created recorded chunk.size 15",
        isinstance(recorded, dict) and recorded.get("chunk.size") == 15,
        recorded,
    )


def token_cap(log: Log) -> None:
    definition = validated(log, "token-cap", chunked({"by": "tokens", "fill": 0.3}))
    items: list[JsonValue] = [{"id": i, "text": "w" * (40 + (i * 37) % 2400)} for i in range(1000)]
    run = engine_run(definition, Script(), "run-tokens")
    ended = run.start(items)
    events = run.events
    plans = [cast(dict[str, Any], e["plan"]) for e in of(events, "node_scheduled", "read")]
    tokens = [p["chunk"]["tokens"] for p in plans]
    log(f"window {DEFAULTS['context_window']} fill 0.3 cap 60000; partitions={len(plans)}")
    log(f"chunk tokens: {tokens}")
    log.check("no chunk exceeds 60k estimated tokens", max(tokens) <= 60_000, max(tokens))
    ranges = [p["chunk"]["items"] for p in plans]
    covered = [i for start, end in ranges for i in range(start, end)]
    log.check("every item lands in exactly one chunk", covered == list(range(1000)), len(covered))
    inputs = [e for e in events if e.kind == "node_finished" and e.data.get("node_id") == "read"]
    passed = [item for e in inputs for item in cast(dict[str, Any], e.data["outputs"])["main"]]
    log.check("the chunks' inputs, joined, are the item list", passed == items, len(passed))
    log.check("the run finishes", ended.status == "passed", ended.status)
    log(f"total estimated tokens {sum(estimate(i) for i in items)}")


def perf(log: Log) -> None:
    items: list[JsonValue] = [{"id": i, "text": f"abstract {i}"} for i in range(PERF_ITEMS)]
    settings: dict[str, JsonValue] = {
        "chunk.size": 10,
        "chunk.fill": 0.3,
        "context_window": 200_000,
    }
    for by in ("items", "tokens"):
        times: list[float] = []
        for _ in range(PERF_ROUNDS):
            started = time.perf_counter()
            spans = chunks(items, Chunk(by=by), settings)
            times.append((time.perf_counter() - started) * 1000)
        shown = " ".join(f"{t:.1f}" for t in times)
        log(f"by={by}: {len(spans)} chunks; ms over {PERF_ROUNDS} rounds: {shown}")
        best = f"{min(times):.1f} (best of {PERF_ROUNDS}; not gated)"
        log(f"METRIC partition_ms_100k_items_by_{by}={best}")
    log.check("the partition probe ran", True, PERF_ITEMS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep5")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base, trunk = git("rev-parse", args.base), git("rev-parse", args.trunk)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, trunk),
        "e03": e03,
        "chunk-setting": chunk_setting,
        "token-cap": token_cap,
        "perf": perf,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep6", f"ep6-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
