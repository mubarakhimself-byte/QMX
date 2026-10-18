"""EP5's live lanes and perf probe: the pure orchestrator and node-level replay, driven through
`qmx_engine.core.simulate` with planted executors.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e02_replay.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression e02 edit rule rule-safe pure finished unknown-event chain perf`; none named
runs all. Each lane writes `evidence/ep5/<ENGINE_LOG_PREFIX>ep5-<lane>.log` and the script exits 1
if any lane failed. No lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from common import Log, throwaway_home
from ep2_lanes import ENGINE, GIT, REPO, clean_env, git
from pydantic import JsonValue
from qmx_engine.core.commands import Finish, Park
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.core.simulate import Entry, Simulation
from qmx_engine.definition.expr import RuleRefused, check
from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok, step
from qmx_engine.nodes.rule import Rule
from qmx_engine.nodes.trigger import Trigger

HARNESS: Final = "qmx-agents/packages/qma-harness"
CORE: Final = ENGINE / "src" / "qmx_engine" / "core"
NOW: Final = "2026-10-17T09:00:00+00:00"
LATER: Final = "2026-10-17T10:00:00+00:00"
PERF_EVENTS: Final = 10_000
PERF_ROUNDS: Final = 5
CORE_MAY_IMPORT: Final = (
    "__future__",
    "collections",
    "collections.abc",
    "dataclasses",
    "typing",
    "pydantic",
    "qmx_ledger.journal",
    "qmx_engine.core",
    "qmx_engine.definition",
)
"""Everything `core` may import. A clock, entropy or environment read needs a module outside this
list (`time`, `datetime`, `os`, `random`, `secrets`, `uuid`, `importlib`), whatever its alias."""


class Script:
    """Outputs its node id, its `prompt` parameter and what reached it; fails the nodes in
    `failing` once each and counts every call."""

    def __init__(self, failing: set[str] | None = None) -> None:
        self.failing = set(failing or ())
        self.calls: list[str] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.calls.append(job.node_id)
        if job.node_id in self.failing:
            self.failing.discard(job.node_id)
            return Failed("boom", "planted failure", "planted", retryable=True)
        parameters = job.node_definition.get("parameters")
        prompt = parameters.get("prompt") if isinstance(parameters, dict) else None
        return Ok({"main": {"node": job.node_id, "prompt": prompt, "upstream": job.inputs}})


class Count:
    """Outputs only its node id, so a long chain carries no growing payload."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.calls.append(job.node_id)
        return Ok({"main": job.node_id})


def chain(length: int = 5, prompts: dict[str, str] | None = None) -> Workflow:
    nodes: list[dict[str, Any]] = [{"id": "n1", "name": "N1", "type": "trigger", "typeVersion": 1}]
    nodes += [
        {
            "id": f"n{i}",
            "name": f"N{i}",
            "type": "script",
            "typeVersion": 1,
            "parameters": {"prompt": (prompts or {}).get(f"n{i}", f"prompt {i}")},
        }
        for i in range(2, length + 1)
    ]
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "chain",
            "name": "chain",
            "nodes": nodes,
            "connections": {
                f"N{i}": {"main": [[{"node": f"N{i + 1}", "port": "in", "map": "one"}]]}
                for i in range(1, length)
            },
        }
    )


def simulation(definition: Workflow, run_id: str, script: Any) -> Simulation:
    return Simulation(
        definition, run_id, step({"trigger": Trigger(), "rule": Rule(), "script": script})
    )


def ids(events: list[Entry], kind: str, **match: JsonValue) -> list[str]:
    return [
        str(e.data["node_id"])
        for e in events
        if e.kind == kind and all(e.data.get(k) == v for k, v in match.items())
    ]


def e02_run() -> tuple[Simulation, Script, int]:
    """The five-node chain with node 3 failing once, started and resumed. Returns the mark where
    the resume began."""
    script = Script(failing={"n3"})
    sim = simulation(chain(), "run-e02", script)
    sim.start({"topic": "q-fin"}, NOW)
    mark = len(sim.events)
    sim.resume(LATER)
    return sim, script, mark


def e02(log: Log) -> None:
    script = Script(failing={"n3"})
    sim = simulation(chain(), "run-e02", script)
    first = sim.start({"topic": "q-fin"}, NOW)
    log(f"first pass started: {' '.join(ids(sim.events, 'node_started'))}; ended {first}")
    log.check(
        "the first pass parks on node 3",
        first == Park("node n3 failed: boom: planted failure", "n3", 0, None, 1),
        first,
    )
    mark = len(sim.events)
    ended = sim.resume(LATER)
    resumed = sim.events[mark:]
    started, memo = ids(resumed, "node_started"), ids(resumed, "node_finished", memo=True)
    log(f"started: {' '.join(started)}")
    log(f"memo: {' '.join(memo)}")
    log.check("nodes 1 and 2 get no new node_started", not {"n1", "n2"} & set(started), started)
    log.check("node 3 reruns, then nodes 4 and 5 run once", started == ["n3", "n4", "n5"], started)
    log.check("nodes 1 and 2 settle from their memos", memo == ["n1", "n2"], memo)
    log.check("the resumed run finishes", isinstance(ended, Finish), ended)
    log.check(
        "executor calls over both passes",
        script.calls == ["n2", "n3", "n3", "n4", "n5"],
        script.calls,
    )


def regression(log: Log, base: str, trunk: str) -> None:
    on_trunk = subprocess.run(
        [
            GIT,
            "cat-file",
            "-e",
            f"{trunk}:qmx-agents/packages/qmx-engine/src/qmx_engine/core/fold.py",
        ],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    log.check("trunk has no core to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    e02(log)


def edit(log: Log) -> None:
    script = Script()
    sim = simulation(chain(), "run-edit", script)
    log.check("the first run finishes", isinstance(sim.start({"topic": "q-fin"}, NOW), Finish), "")
    mark = len(sim.events)
    sim.resume(LATER, chain(prompts={"n4": "prompt 4, sharper"}))
    started = ids(sim.events[mark:], "node_started")
    memo = ids(sim.events[mark:], "node_finished", memo=True)
    log(f"after editing n4's prompt, started: {' '.join(started)}; memo: {' '.join(memo)}")
    log.check(
        "only n4 and n5 (whose input changed with n4's output) rerun",
        started == ["n4", "n5"] and memo == ["n1", "n2", "n3"],
        (started, memo),
    )
    unchanged = Count()
    sim = simulation(chain(), "run-edit-2", unchanged)
    sim.start({"topic": "q-fin"}, NOW)
    mark = len(sim.events)
    sim.resume(LATER, chain(prompts={"n4": "prompt 4, sharper"}))
    started = ids(sim.events[mark:], "node_started")
    log(f"with an executor whose output ignores the prompt, started: {' '.join(started)}")
    log.check(
        "n4 reruns and n5 keeps its memo (its input hash is unchanged)", started == ["n4"], started
    )


def routed(score: float, expr: str = "items.score >= 0.7") -> tuple[Simulation, Any]:
    workflow = Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "routed",
            "name": "routed",
            "nodes": [
                {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1},
                {
                    "id": "gate",
                    "name": "Good enough?",
                    "type": "rule",
                    "typeVersion": 1,
                    "parameters": {"expr": expr},
                },
                {"id": "keep", "name": "Keep", "type": "script", "typeVersion": 1},
                {"id": "keep-2", "name": "Keep more", "type": "script", "typeVersion": 1},
                {"id": "drop", "name": "Drop", "type": "script", "typeVersion": 1},
            ],
            "connections": {
                "Start": {"main": [[{"node": "Good enough?", "port": "in", "map": "one"}]]},
                "Good enough?": {
                    "true": [[{"node": "Keep", "port": "in", "map": "one"}]],
                    "false": [[{"node": "Drop", "port": "in", "map": "one"}]],
                },
                "Keep": {"main": [[{"node": "Keep more", "port": "in", "map": "one"}]]},
            },
        }
    )
    sim = simulation(workflow, f"run-rule-{score}", Count())
    return sim, sim.start({"score": score}, NOW)


def rule(log: Log) -> None:
    for score, expected in (
        (0.9, ["start", "gate", "keep", "keep-2"]),
        (0.2, ["start", "gate", "drop"]),
    ):
        sim, ended = routed(score)
        started = ids(sim.events, "node_started")
        log(f"score {score}: started {' '.join(started)}; ended {ended}")
        log.check(f"score {score} runs only the chosen port's branch", started == expected, started)
        log.check(f"score {score} finishes", isinstance(ended, Finish), ended)


def rule_safe(log: Log) -> None:
    sentinel = throwaway_home("ep5", "rule-safe") / "opened-by-rule"
    expr = f"open({str(sentinel)!r}, 'w')"
    try:
        check(expr)
        refusal = None
    except RuleRefused as error:
        refusal = str(error)
    log.check("check refuses the open call", refusal == "Call is not allowed in a rule", refusal)
    sim, ended = routed(0.9, expr)
    failed = [e.data for e in sim.events if e.kind == "node_failed"]
    log(f"run with the open rule: {failed}; ended {ended}")
    log.check(
        "the rule node fails rule_refused and the run parks",
        [f.get("code") for f in failed] == ["rule_refused"] and isinstance(ended, Park),
        ended,
    )
    log.check("nothing was opened (refused before evaluation)", not sentinel.exists(), sentinel)


def imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append("." * node.level + (node.module or ""))
    return found


def pure(log: Log) -> None:
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_import_rules.py", "-q", "-n", "0"],
        cwd=ENGINE,
        env=clean_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    log(f"  | {(done.stdout + done.stderr).strip().splitlines()[-1:]}")
    log.check("EP2's AD-1/AD-6 import rules pass over core", done.returncode == 0, done.returncode)
    outside = sorted(
        f"{path.name}: {name}"
        for path in CORE.glob("*.py")
        for name in imports(path)
        if not any(name == ok or name.startswith(f"{ok}.") for ok in CORE_MAY_IMPORT)
    )
    log(f"core modules scanned: {' '.join(sorted(p.name for p in CORE.glob('*.py')))}")
    log.check(
        "core imports nothing outside its allow-list (no alias can reach a clock)",
        outside == [],
        outside,
    )


def finished(log: Log) -> None:
    script = Script()
    sim = simulation(chain(), "run-finished", script)
    sim.start({"topic": "q-fin"}, NOW)
    calls = len(script.calls)
    mark = len(sim.events)
    ended = sim.resume(LATER)
    log(f"resume of a finished run: {[e.kind for e in sim.events[mark:]]}")
    log.check("no executor is called", len(script.calls) == calls, script.calls[calls:])
    log.check("no node_started", ids(sim.events[mark:], "node_started") == [], "")
    log.check("the run finishes again from memos", isinstance(ended, Finish), ended)
    log.check("a run that already ended gets no command", next_commands(sim.state()) == [], "")


def unknown_event(log: Log) -> None:
    sim = simulation(chain(), "run-unknown", Script())
    sim.start({"topic": "q-fin"}, NOW)
    sim.append("node_teleported", {"node_id": "n2"})
    commands = next_commands(sim.state())
    log(f"commands after an unknown kind: {commands}")
    log.check(
        "the fold returns Park naming the kind",
        len(commands) == 1
        and isinstance(commands[0], Park)
        and "'node_teleported'" in commands[0].reason,
        commands,
    )


def chain_lane(log: Log) -> None:
    counter = Count()
    started_at = time.perf_counter()
    sim = simulation(chain(200), "run-chain", counter)
    ended = sim.start({"topic": "q-fin"}, NOW)
    elapsed = time.perf_counter() - started_at
    starts = ids(sim.events, "node_started")
    once = len(starts) == 200 and len(set(starts)) == 200
    log(f"200-node chain: {len(sim.events)} events, {elapsed:.2f} s, ended {type(ended).__name__}")
    log.check(
        "every node finishes once",
        once and counter.calls == starts[1:],
        (len(starts), len(set(starts))),
    )
    log.check("the chain finishes", ended == Finish({"n200": {"main": "n200"}}), ended)


def perf(log: Log) -> None:
    """Fold over a synthesized 10,000-event log: a 3,332-node chain, three events per node."""
    nodes = (PERF_EVENTS - 4) // 3
    definition = chain(nodes)
    events: list[Entry] = []

    def add(kind: str, data: dict[str, JsonValue]) -> None:
        events.append(Entry(len(events) + 1, "run-perf", NOW, kind, data))

    add("run_created", {})
    add("run_input", {"inputs": {}})
    add("clock_tick", {"now": NOW})
    for i in range(1, nodes + 1):
        keys: dict[str, JsonValue] = {
            "node_id": f"n{i}",
            "iteration": 0,
            "partition": None,
            "attempt": 1,
        }
        add("node_scheduled", keys | {"memo_key": f"key-{i}"})
        add("node_started", keys)
        add("node_finished", keys | {"outputs": {"main": f"n{i}"}})
    add("heartbeat", {})
    log(f"events: {len(events)}, nodes: {nodes}")
    times: list[float] = []
    for _ in range(PERF_ROUNDS):
        started_at = time.perf_counter()
        state = fold(definition, events)
        times.append((time.perf_counter() - started_at) * 1000)
    log(f"fold ms over {PERF_ROUNDS} rounds: {' '.join(f'{t:.1f}' for t in times)}")
    log(f"METRIC fold_ms_10k_events={min(times):.1f} (best of {PERF_ROUNDS}; not gated)")
    log.check("the fold saw every node finished", len(state.nodes) == nodes, len(state.nodes))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep4")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base, trunk = git("rev-parse", args.base), git("rev-parse", args.trunk)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, trunk),
        "e02": e02,
        "edit": edit,
        "rule": rule,
        "rule-safe": rule_safe,
        "pure": pure,
        "finished": finished,
        "unknown-event": unknown_event,
        "chain": chain_lane,
        "perf": perf,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep5", f"ep5-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
