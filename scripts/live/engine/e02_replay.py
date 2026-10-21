"""EP5's live lanes and perf probe: the pure orchestrator and node-level replay, driven through the
real `Engine` and its one ledger writer with planted executors (the `executors=` seam). `EngineRun`
here is the driver the other core lanes (`e01`, `e03`, `x06`) share.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e02_replay.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression e02 edit rule rule-safe pure finished unknown-event chain perf`; none named
runs all. Each lane writes `evidence/ep5/<ENGINE_LOG_PREFIX>ep5-<lane>.log` and the script exits 1
if any lane failed. No lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from common import Log, throwaway_home
from ep2_lanes import ENGINE, GIT, REPO, clean_env, git
from pydantic import JsonValue
from qmx_engine.core.commands import Park
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.definition.expr import RuleRefused, check
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.local import AnyExecutor

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
ONE_TRY: Final[Mapping[str, object]] = {**DEFAULTS, "retry.max_tries": 1, "retry.backoff": (0,)}
"""A failed attempt is not retried: it walks the rest of the ladder at once and parks."""
POLL_S: Final = 0.01


@dataclass(frozen=True, slots=True)
class Entry:
    """An event as the core reads it, for a log the ledger would not store as it stands."""

    seq: int
    run_id: str
    at: str
    kind: str
    data: dict[str, JsonValue] = field(default_factory=dict[str, JsonValue])


class EngineRun:
    """One run of `definition` on the real `Engine`, in a throwaway home, on a wall clock the lane
    moves."""

    def __init__(
        self,
        pr: str,
        definition: Workflow,
        run_id: str,
        executors: Mapping[str, AnyExecutor],
        *,
        settings: Mapping[str, object] = ONE_TRY,
        now: str = NOW,
    ) -> None:
        self.home = throwaway_home(pr, run_id)
        self.root = self.home / "workflow"
        self.run_id = run_id
        self.executors = executors
        self.settings = settings
        self.wall = datetime.fromisoformat(now)
        self.write(definition)

    def write(self, definition: Workflow) -> None:
        """The run's folder now holds `definition`: an edit, once the run started."""
        self.root.mkdir(parents=True, exist_ok=True)
        document = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
        (self.root / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    def drive[T](self, scenario: Callable[[Engine], Awaitable[T]]) -> T:
        async def go() -> T:
            with Ledger.open(self.home) as ledger, InboxTable.open(self.home) as inbox:
                engine = Engine(
                    self.home,
                    ledger,
                    settings=self.settings,
                    wall=lambda: self.wall,
                    executors=self.executors,
                    watch_every=POLL_S,
                    inbox=inbox,
                )
                found = await scenario(engine)
                await engine.settle()
                return found

        return asyncio.run(go())

    async def started(self, engine: Engine, inputs: JsonValue) -> Outcome:
        found = checked(self.root)
        if isinstance(found, list):
            raise SystemExit(f"BLOCKED: the lane's workflow does not validate: {found}")
        return await engine.start(
            self.root, found[1], mode="test", inputs=inputs, run_id=self.run_id
        )

    def start(self, inputs: JsonValue) -> Outcome:
        return self.drive(lambda engine: self.started(engine, inputs))

    def resume(self, now: str | None = None, *, reason: str = "operator") -> Outcome:
        if now is not None:
            self.wall = datetime.fromisoformat(now)
        return self.drive(lambda engine: engine.resume(self.run_id, reason=reason))

    def tick(self, now: str) -> Outcome:
        """The ticker wakes the run at `now`."""
        return self.resume(now, reason="wake")

    @property
    def events(self) -> list[Event]:
        with Reader.open(self.home) as reader:
            return reader.events(self.run_id)

    async def seen(self, kind: str, node_id: str, partition: int | None = None) -> None:
        """Wait until the ledger holds `kind` for the slot."""
        while not [
            e
            for e in self.events
            if e.kind == kind
            and e.data.get("node_id") == node_id
            and e.data.get("partition") == partition
        ]:
            await asyncio.sleep(POLL_S)


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


def chain(
    length: int = 5, prompts: dict[str, str] | None = None, *, held: bool = False
) -> Workflow:
    """N1 to N`length`; with `held` a last node waits on an event, so the run stays open for an
    edit."""
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
    last = length
    if held:
        last = length + 1
        nodes.append(
            {
                "id": f"n{last}",
                "name": f"N{last}",
                "type": "wait",
                "typeVersion": 1,
                "parameters": {"event": "go"},
            }
        )
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "chain",
            "name": "chain",
            "nodes": nodes,
            "connections": {
                f"N{i}": {"main": [[{"node": f"N{i + 1}", "port": "in", "map": "one"}]]}
                for i in range(1, last)
            },
        }
    )


def ids(events: Sequence[Event], kind: str, **match: JsonValue) -> list[str]:
    return [
        str(e.data["node_id"])
        for e in events
        if e.kind == kind and all(e.data.get(k) == v for k, v in match.items())
    ]


def e02_run() -> tuple[EngineRun, Script, int]:
    """The five-node chain with node 3 failing once, started and resumed. Returns the mark where
    the resume began."""
    script = Script(failing={"n3"})
    run = EngineRun("ep5", chain(), "run-e02", {"script": script})
    run.start({"topic": "q-fin"})
    mark = len(run.events)
    run.resume(LATER)
    return run, script, mark


def e02(log: Log) -> None:
    script = Script(failing={"n3"})
    run = EngineRun("ep5", chain(), "run-e02", {"script": script})
    first = run.start({"topic": "q-fin"})
    log(f"first pass started: {' '.join(ids(run.events, 'node_started'))}; ended {first}")
    log.check(
        "the first pass parks on node 3",
        (first.status, first.reason) == ("failed", "node n3 failed: boom: planted failure"),
        first,
    )
    mark = len(run.events)
    ended = run.resume(LATER)
    resumed = run.events[mark:]
    started, memo = ids(resumed, "node_started"), ids(resumed, "node_finished", memo=True)
    log(f"started: {' '.join(started)}")
    log(f"memo: {' '.join(memo)}")
    log.check("nodes 1 and 2 get no new node_started", not {"n1", "n2"} & set(started), started)
    log.check("node 3 reruns, then nodes 4 and 5 run once", started == ["n3", "n4", "n5"], started)
    log.check("nodes 1 and 2 settle from their memos", memo == ["n1", "n2"], memo)
    log.check("the resumed run finishes", ended.status == "passed", ended)
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
    """Each run waits on an event after n5, so it is still open when its folder is edited."""
    script = Script()
    run = EngineRun("ep5", chain(held=True), "run-edit", {"script": script})
    first = run.start({"topic": "q-fin"})
    log.check("the first pass runs n1 to n5 and waits", first.status == "waiting", first)
    mark = len(run.events)
    run.write(chain(prompts={"n4": "prompt 4, sharper"}, held=True))
    run.resume(LATER)
    started = ids(run.events[mark:], "node_started")
    memo = ids(run.events[mark:], "node_finished", memo=True)
    log(f"after editing n4's prompt, started: {' '.join(started)}; memo: {' '.join(memo)}")
    log.check(
        "only n4 and n5 (whose input changed with n4's output) rerun",
        started == ["n4", "n5"] and memo == ["n1", "n2", "n3"],
        (started, memo),
    )
    unchanged = Count()
    run = EngineRun("ep5", chain(held=True), "run-edit-2", {"script": unchanged})
    run.start({"topic": "q-fin"})
    mark = len(run.events)
    run.write(chain(prompts={"n4": "prompt 4, sharper"}, held=True))
    run.resume(LATER)
    started = ids(run.events[mark:], "node_started")
    log(f"with an executor whose output ignores the prompt, started: {' '.join(started)}")
    log.check(
        "n4 reruns and n5 keeps its memo (its input hash is unchanged)", started == ["n4"], started
    )


def routed(
    score: float, expr: str = "items.score >= 0.7", *, unchecked: bool = False
) -> tuple[EngineRun, Outcome]:
    """With `unchecked` the run starts from the parsed definition, past validation, so the rule
    node's own refusal is what stops it."""
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
    run = EngineRun("ep5", workflow, f"run-rule-{score}", {"script": Count()})
    if not unchecked:
        return run, run.start({"score": score})
    return run, run.drive(
        lambda engine: engine.start(
            run.root, workflow, mode="test", inputs={"score": score}, run_id=run.run_id
        )
    )


def rule(log: Log) -> None:
    for score, expected in (
        (0.9, ["start", "gate", "keep", "keep-2"]),
        (0.2, ["start", "gate", "drop"]),
    ):
        run, ended = routed(score)
        started = ids(run.events, "node_started")
        log(f"score {score}: started {' '.join(started)}; ended {ended}")
        log.check(f"score {score} runs only the chosen port's branch", started == expected, started)
        log.check(f"score {score} finishes", ended.status == "passed", ended)


def rule_safe(log: Log) -> None:
    sentinel = throwaway_home("ep5", "rule-safe") / "opened-by-rule"
    expr = f"open({str(sentinel)!r}, 'w')"
    try:
        check(expr)
        refusal = None
    except RuleRefused as error:
        refusal = str(error)
    log.check("check refuses the open call", refusal == "Call is not allowed in a rule", refusal)
    run, ended = routed(0.9, expr, unchecked=True)
    failed = [e.data for e in run.events if e.kind == "node_failed"]
    log(f"run with the open rule: {failed}; ended {ended}")
    log.check(
        "the rule node fails rule_refused and the run parks",
        [f.get("code") for f in failed] == ["rule_refused"] and ended.status == "failed",
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
    run = EngineRun("ep5", chain(), "run-finished", {"script": script})
    run.start({"topic": "q-fin"})
    calls = len(script.calls)
    mark = len(run.events)
    ended = run.resume(LATER)
    log(f"resume of a finished run: {[e.kind for e in run.events[mark:]]}")
    log.check("no executor is called", len(script.calls) == calls, script.calls[calls:])
    log.check("no node_started", ids(run.events[mark:], "node_started") == [], "")
    log.check("the run reads passed still", ended.status == "passed", ended)
    log.check(
        "a run that already ended gets no command",
        next_commands(fold(chain(), run.events)) == [],
        "",
    )


def unknown_event(log: Log) -> None:
    run = EngineRun("ep5", chain(held=True), "run-unknown", {"script": Script()})
    run.start({"topic": "q-fin"})
    events = run.events
    teleported = Entry(len(events) + 1, run.run_id, NOW, "node_teleported", {"node_id": "n2"})
    commands = next_commands(fold(chain(held=True), [*events, teleported]))
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
    run = EngineRun("ep5", chain(200), "run-chain", {"script": counter})
    ended = run.start({"topic": "q-fin"})
    elapsed = time.perf_counter() - started_at
    events = run.events
    starts = ids(events, "node_started")
    once = len(starts) == 200 and len(set(starts)) == 200
    log(f"200-node chain: {len(events)} events, {elapsed:.2f} s, ended {ended.status}")
    log.check(
        "every node finishes once",
        once and counter.calls == starts[1:],
        (len(starts), len(set(starts))),
    )
    log.check(
        "the chain finishes",
        (ended.status, ended.outputs) == ("passed", {"n200": {"main": "n200"}}),
        ended,
    )


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
