"""EP6's live lanes for fan-out by chunk (E3, E29 by chunk), driven through
`qmx_engine.core.simulate` with planted executors, then read back through the real ledger.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e03_chunks.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression e03 chunk-setting token-cap perf`; none named runs all. Each lane writes
`evidence/ep6/<ENGINE_LOG_PREFIX>ep6-<lane>.log` and the script exits 1 if any lane failed. Every
workflow is written as a folder and passes the EP3 validator before it runs. No lane needs a model,
a key or the ship home.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections.abc import Callable
from typing import Any, Final, cast

from common import Log, throwaway_home
from e02_replay import e02
from ep2_lanes import GIT, REPO, git
from pydantic import JsonValue
from qmx_engine.core.commands import Finish, Park
from qmx_engine.core.fold import fold
from qmx_engine.core.partitions import chunks, estimate
from qmx_engine.core.ready import next_commands
from qmx_engine.core.simulate import Entry, Simulation
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Chunk, Workflow
from qmx_engine.definition.validate import validate
from qmx_engine.ledger.events import EventKind
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Executor, Failed, NodeJob, NodeResult, Ok, step
from qmx_engine.nodes.join import Join
from qmx_engine.nodes.loop import Loop
from qmx_engine.nodes.trigger import Trigger
from qmx_engine.nodes.wait import Wait, resume_at
from qmx_engine.settings import DEFAULTS

HARNESS: Final = "qmx-agents/packages/qma-harness"
NOW: Final = "2026-10-17T09:00:00+00:00"
LATER: Final = "2026-10-17T10:00:00+00:00"
PERF_ITEMS: Final = 100_000
PERF_ROUNDS: Final = 5

type Planted = tuple[str, int | None]


class Script:
    """Applies `fn` to the `in` value of node `only` (others pass it through). A `(node,
    partition)` in `failing` fails once; one in `slow` starts and stays in flight."""

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

    def run(self, job: NodeJob) -> NodeResult:
        self.calls.append((job.node_id, job.iteration, job.partition))
        if (job.node_id, job.partition) in self.failing:
            self.failing.discard((job.node_id, job.partition))
            return Failed("boom", "planted failure", "planted", retryable=True)
        value = job.inputs.get("in") if isinstance(job.inputs, dict) else None
        return Ok({"main": self.fn(job, value) if self.only in (None, job.node_id) else value})


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


def simulation(
    definition: Workflow,
    script: Script,
    run_id: str,
    settings: dict[str, object] | None = None,
) -> Simulation:
    executors: dict[str, Executor] = {
        "trigger": Trigger(),
        "script": script,
        "join": Join(),
        "loop": Loop(),
        "wait": Wait(),
    }
    run = step(executors)

    def stepped(command: Any) -> list[tuple[str, dict[str, JsonValue]]]:
        drafts = run(command)
        return drafts[:1] if (command.node_id, command.partition) in script.slow else drafts

    return Simulation(
        definition, run_id, stepped, settings=settings or dict(DEFAULTS), clock=resume_at
    )


def of(events: list[Entry], kind: str, node_id: str) -> list[dict[str, JsonValue]]:
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
    sim = simulation(definition, script, "run-e03")
    first = sim.start(list(range(60)), NOW)
    scheduled = of(sim.events, "node_scheduled", "read")
    log(f"partitions={len(scheduled)} by=items size=10")
    log(f"first pass ended: {first}")
    first_calls = [c for c in script.calls if c[0] == "read"]
    log.check("6 attempts ran, not 60", len(first_calls) == 6, len(first_calls))
    log.check("the run parks on the join", isinstance(first, Park), first)
    mark, calls = len(sim.events), len(script.calls)
    ended = sim.resume(LATER)
    resumed = of(sim.events[mark:], "node_started", "read")
    log(f"new attempts={len(resumed)}")
    pairs = [(e["partition"], e["attempt"]) for e in resumed]
    log(f"resumed attempts (partition, attempt): {pairs}")
    log.check(
        "exactly 2 new attempts, for partitions 1 and 4",
        pairs == [(1, 2), (4, 2)],
        resumed,
    )
    memo = of(sim.events[mark:], "node_finished", "read")
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
    output = ended.outputs if isinstance(ended, Finish) else None
    log(f"join output: {output}")
    expected = {"gather": {"main": [{"first": p * 10, "count": 10} for p in range(6)]}}
    log.check("the join output is ordered by partition id", output == expected, output)
    ledger_lane(log, definition, sim)


def ledger_lane(log: Log, definition: Workflow, sim: Simulation) -> None:
    """The same events written through the real ledger fold to the same state, and every chunk
    attempt has its own partition span."""
    home = throwaway_home("ep6", "e03-ledger")
    with Ledger.open(home) as ledger:
        for entry in sim.events:
            ledger.append(sim.run_id, cast(EventKind, entry.kind), entry.data, at=entry.at)
    with Reader.open(home) as reader:
        stored = reader.events(sim.run_id)
        spans = [s for s in reader.spans(sim.run_id) if s.node_id == "read"]
    same = fold(definition, stored).nodes == fold(definition, sim.events).nodes
    log.check("the ledger read back folds to the same slots", same, len(stored))
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
    sim = simulation(
        definition, Script(summary, only="read"), "run-setting", dict(DEFAULTS) | overrides
    )
    ended = sim.start(list(range(60)), NOW)
    scheduled = of(sim.events, "node_scheduled", "read")
    log(f"partitions={len(scheduled)} by=items chunk.size=15; ended {type(ended).__name__}")
    log.check("4 partitions run", len(of(sim.events, "node_started", "read")) == 4, len(scheduled))
    recorded = sim.events[0].data.get("settings")
    log.check(
        "run_created recorded chunk.size 15",
        isinstance(recorded, dict) and recorded.get("chunk.size") == 15,
        recorded,
    )


def token_cap(log: Log) -> None:
    definition = validated(log, "token-cap", chunked({"by": "tokens", "fill": 0.3}))
    items: list[JsonValue] = [{"id": i, "text": "w" * (40 + (i * 37) % 2400)} for i in range(1000)]
    sim = simulation(definition, Script(), "run-tokens")
    ended = sim.start(items, NOW)
    plans = [cast(dict[str, Any], e["plan"]) for e in of(sim.events, "node_scheduled", "read")]
    tokens = [p["chunk"]["tokens"] for p in plans]
    log(f"window {DEFAULTS['context_window']} fill 0.3 cap 60000; partitions={len(plans)}")
    log(f"chunk tokens: {tokens}")
    log.check("no chunk exceeds 60k estimated tokens", max(tokens) <= 60_000, max(tokens))
    ranges = [p["chunk"]["items"] for p in plans]
    covered = [i for start, end in ranges for i in range(start, end)]
    log.check("every item lands in exactly one chunk", covered == list(range(1000)), len(covered))
    inputs = [
        e for e in sim.events if e.kind == "node_finished" and e.data.get("node_id") == "read"
    ]
    passed = [item for e in inputs for item in cast(dict[str, Any], e.data["outputs"])["main"]]
    log.check("the chunks' inputs, joined, are the item list", passed == items, len(passed))
    log.check("the run finishes", isinstance(ended, Finish), type(ended).__name__)
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
