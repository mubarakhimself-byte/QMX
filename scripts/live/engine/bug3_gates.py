"""BUG3 lanes: inbox answers fold as `gate_resolved` and move the run (AD-17, B-28, B-32), the run
list reads a fold over the ledger (B-40, B-73), a failed partition walks its own ladder (B-35),
and a restart folds an attempt the dead engine left open.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/bug3_gates.py [lane]`
Lanes are `gates runs partition restart irreversible perf`; none named runs all. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/bug3/<ENGINE_LOG_PREFIX>bug3-<lane>.log` and the script
exits 1 when a check failed. No model, no key, no ship home: planted executors and the engine's fake
provider on throwaway homes under the store's `homes/`. Every answer goes through the service's
`inbox.resolve` as the operator, and only the scheduler's own tick resumes an answered run.

- `gates`: the five answers. `retry` reruns an external step of unknown outcome, `skip_node` ends it
  skipped, `stop` ends the run stopped, `stronger_model` moves a parked `llm` node to its role's next
  candidate, and `resume` lifts a crash-loop park.
- `runs`: the run list during a three-node run, while one run waits, and after both end.
- `partition`: one of four partitions on the fake provider fails twice and walks its own ladder;
  one that keeps failing parks alone and the join counts it failed only then.
- `restart`: an engine dies with an attempt in flight; the run reads `interrupted` until a resume
  folds it, then ends `passed`.
- `irreversible`: an external step of unknown outcome stays waiting over a plain resume and runs
  again only on a `retry` answer.
- `perf`: the run list over 1,000 runs in the ledger, ten calls; fails when the median passes
  500 ms. The baseline is the parent's list: `runs.get` per run with the parent's `status_of`,
  read from the parent commit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import stat
import statistics
import subprocess
import sys
import time
import types
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, Final

from common import Log
from ep2_lanes import GIT, REPO, git
from pydantic import JsonValue
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.nodes.fake_provider import FakeProvider
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.runs import status_of
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers.ticker import Scheduler

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "bug3"
ONE_LLM: Final = (
    Path(__file__).resolve().parents[3]
    / "qmx-agents/packages/qmx-engine/tests/fixtures/workflows/one-llm"
)
PARENT: Final = "319baa47f619c88d4503efd42c8977a938902824"
QUICK: Final = {**DEFAULTS, "retry.max_tries": 3, "retry.backoff": (0,)}
MESSAGES: Final = ("timeout talking upstream", "connection reset", "bad gateway", "rate limited")
POLL_S: Final = 0.05
PERF_RUNS: Final = 1000
PERF_CALLS: Final = 10
PERF_FAIL_MS: Final = 500.0


class BugLog(Log):
    """`Log` writing into the build store's `evidence/bug3/`."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}bug3-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def writable(remove: Callable[..., Any], path: str, _: object) -> None:
    os.chmod(path, stat.S_IWRITE)
    remove(path)


def home(slug: str) -> Path:
    """A fresh home `homes/bug3-<slug>`; a run's read-only code copy sits in its zones beside it."""
    root = STORE / "homes" / f"bug3-{slug}"
    for found in (root, root.with_name(f"{root.name}.zones")):
        if found.exists():
            shutil.rmtree(found, onexc=writable)
    root.mkdir(parents=True)
    return root


def node(name: str, kind: str, **fields: Any) -> dict[str, Any]:
    return {"id": name, "name": name, "type": kind, "typeVersion": 1, "parameters": {}, **fields}


def edge(target: str, map_: str = "one") -> dict[str, Any]:
    return {"node": target, "port": "in", "map": map_}


def folder(root: Path, nodes: list[dict[str, Any]], connections: dict[str, Any]) -> Workflow:
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "nodes": nodes,
        "connections": {
            source: {port: [targets] for port, targets in ports.items()}
            for source, ports in connections.items()
        },
    }
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the lane workflow does not validate: {found}")
    return found[1]


def posting(root: Path) -> Workflow:
    """start -> post (an irreversible external step) -> after."""
    post = node("post", "script", effect="irreversible_external")
    return folder(
        root,
        [node("start", "trigger"), post, node("after", "script")],
        {"start": {"main": [edge("post")]}, "post": {"main": [edge("after")]}},
    )


def events_of(base: Path, run_id: str) -> list[Event]:
    with Reader.open(base) as reader:
        return reader.events(run_id)


def of(events: list[Event], kind: str, node_id: str) -> list[dict[str, JsonValue]]:
    return [e.data for e in events if e.kind == kind and e.data.get("node_id") == node_id]


def wakes(base: Path) -> list[str]:
    with Reader.open(base) as reader:
        return [r for (r,) in reader.connection.execute("SELECT run_id FROM wakes")]


class Unknown:
    """The external step's first attempt ends with its outcome unknown; later ones post. Every
    other node passes its node id on."""

    def __init__(self) -> None:
        self.jobs: list[tuple[str, int]] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append((job.node_id, job.attempt))
        if job.node_id == "post" and job.attempt == 1:
            return Failed("timeout", "no answer", "sig", True, effect_state="unknown")
        return Ok({"main": job.node_id})


async def answered(svc: EngineService, action: str, log: Log, run_id: str) -> None:
    """The operator answers the run's open item, then the scheduler ticks once and every run it
    woke settles."""
    [item] = [i for i in svc.inbox.list() if i.run_id == run_id]
    log(f"item {item.id} ({item.category}): {item.title}; offers {list(item.actions)}")
    svc.inbox.resolve(item.id, action, caller=OPERATOR)  # type: ignore[arg-type]
    log(f"answered {action}; wake rows now {wakes(svc.ctx.home)}")
    ticker = Scheduler(svc.ctx)
    await ticker.tick()
    await ticker.settle()


async def gated(slug: str, action: str, log: Log) -> tuple[list[Event], Unknown, EngineService]:
    """Run `posting` until its external step waits on its gate, answer `action`, tick."""
    base = home(f"gates-{slug}")
    step = Unknown()
    definition = posting(base / "wf")
    with EngineService.open(base, executors={"script": step}) as svc:
        held = await svc.ctx.engine.start(base / "wf", definition, mode="test", inputs={})
        before = svc.runs.get(held.run_id)
        log.check(
            f"{slug}: the run waits on the external step's gate",
            (held.status, before.status, before.reason) == ("waiting", "waiting", "gate"),
            (held.status, before.status, before.reason),
        )
        await answered(svc, action, log, held.run_id)
        events = events_of(base, held.run_id)
        [answer] = of(events, "gate_resolved", "post")
        log.check(
            f"{slug}: the answer is the run's gate_resolved on the gated slot",
            (answer["answer"], answer["principal"], answer["attempt"]) == (action, "operator", 1),
            answer,
        )
        return events, step, svc


async def gates(log: Log) -> None:
    events, step, _ = await gated("retry", "retry", log)
    log.check(
        "retry: the step runs as attempt 2 and the run passes",
        step.jobs == [("post", 1), ("post", 2), ("after", 1)] and events[-1].kind == "run_finished",
        (step.jobs, events[-1].kind),
    )
    events, step, _ = await gated("skip", "skip_node", log)
    log.check(
        "skip_node: the step never runs again, what only it feeds is skipped, the run passes",
        step.jobs == [("post", 1)] and events[-1].kind == "run_finished",
        (step.jobs, events[-1].kind),
    )
    events, step, svc = await gated("stop", "stop", log)
    run_id = events[0].run_id
    with EngineService.open(svc.ctx.home, executors={"script": step}) as again:
        state = again.runs.get(run_id)
    log.check(
        "stop: no wake, nothing runs again and the run reads stopped",
        step.jobs == [("post", 1)] and state.status == "stopped" and wakes(svc.ctx.home) == [],
        (step.jobs, state.status, state.reason),
    )
    await stronger(log)
    await crash_loop(log)


class Auth:
    """An `llm` node whose provider refuses the key until the run reaches its third candidate."""

    def __init__(self) -> None:
        self.models: list[JsonValue] = []

    def run(self, job: NodeJob) -> NodeResult:
        candidate = (job.resolved_model or {}).get("candidate")
        self.models.append(candidate)
        if candidate != "minimax/MiniMax-M2.7-highspeed":
            message = "401 unauthorized"
            return Failed("auth", message, signature("auth", message), False)
        return Ok({"main": {"capital": "Paris"}})


async def stronger(log: Log) -> None:
    base = home("gates-stronger")
    shutil.copytree(ONE_LLM, base / "wf")
    found = checked(base / "wf")
    assert not isinstance(found, list), found
    llm = Auth()
    with EngineService.open(base, executors={"llm": llm}) as svc:
        parked = await svc.ctx.engine.start(base / "wf", found[1], mode="test", inputs={})
        steps = [e["step"] for e in of(events_of(base, parked.run_id), "ladder_step", "capital")]
        log(f"stronger_model: the provider refuses; ladder {steps}; candidates tried {llm.models}")
        log.check("stronger_model: the run parks first", parked.status == "failed", parked)
        await answered(svc, "stronger_model", log, parked.run_id)
        ended = svc.runs.get(parked.run_id)
    log.check(
        "stronger_model: the next attempt runs on the role's next candidate and the run passes",
        llm.models[-1] == "minimax/MiniMax-M2.7-highspeed" and ended.status == "passed",
        (llm.models, ended.status),
    )


class Hangs:
    """The node's first attempt never ends on its own; later ones pass."""

    def __init__(self) -> None:
        self.attempts: list[int] = []

    async def run(self, job: NodeJob) -> NodeResult:
        self.attempts.append(job.attempt)
        if job.attempt == 1:
            await asyncio.Event().wait()
        return Ok({"main": job.node_id})


async def die(engine: Engine, start: Coroutine[Any, Any, Outcome], node_id: str, base: Path) -> str:
    """Start a run and kill its engine mid-attempt: every attempt and the drive are cancelled
    with nothing more written, as a crash leaves the ledger. Returns the run id."""
    going = asyncio.create_task(start)
    while not engine.live or not of(
        events_of(base, next(iter(engine.live))), "node_started", node_id
    ):
        await asyncio.sleep(POLL_S)
    [run_id] = list(engine.live)
    for task in list(engine.worker.running.values()):
        task.cancel()
    going.cancel()
    await asyncio.gather(going, return_exceptions=True)
    engine.live.clear()
    return run_id


async def crash_loop(log: Log) -> None:
    base = home("gates-resume")
    definition = folder(
        base / "wf",
        [node("start", "trigger"), node("work", "script")],
        {"start": {"main": [edge("work")]}},
    )
    hangs = Hangs()
    settings = StaticSettings({**DEFAULTS, "crash_loop.restarts": 1})
    with EngineService.open(base, executors={"script": hangs}, settings=settings) as svc:
        engine = svc.ctx.engine
        start = engine.start(base / "wf", definition, mode="test", inputs={})
        run_id = await die(engine, start, "work", base)
        parked = await engine.resume(run_id)
        loop = [
            e for e in events_of(base, run_id) if e.kind == "ladder_step" and "crash_loop" in e.data
        ]
        log(f"resume: after the restart the run reads {parked.status}; park {loop[-1:]}")
        log.check(
            "resume: one restart under crash_loop.restarts 1 parks with a system-fault item",
            parked.status == "failed" and len(loop) == 1,
            parked,
        )
        await answered(svc, "resume", log, run_id)
        ended = svc.runs.get(run_id)
    log.check(
        "resume: the answer lifts the park, the scheduler resumes the run and it passes",
        ended.status == "passed" and hangs.attempts == [1, 2],
        (ended.status, hangs.attempts),
    )


class Slow:
    """`hold` waits until the lane releases it; every other node passes at once."""

    def __init__(self) -> None:
        self.gate = asyncio.Event()

    async def run(self, job: NodeJob) -> NodeResult:
        if job.node_id == "hold":
            await self.gate.wait()
        return Ok({"main": job.node_id})


def listed(svc: EngineService) -> dict[str, str]:
    """What the run list shows: each run in the ledger through `runs.get`, as the door lists."""
    with Reader.open(svc.ctx.home) as reader:
        ids = [r for (r,) in reader.connection.execute("SELECT run_id FROM events WHERE seq = 1")]
    return {run_id: svc.runs.get(run_id).status for run_id in sorted(ids)}


async def runs(log: Log) -> None:
    base = home("runs")
    three = folder(
        base / "three",
        [node("start", "trigger"), node("hold", "script"), node("after", "script")],
        {"start": {"main": [edge("hold")]}, "hold": {"main": [edge("after")]}},
    )
    held = folder(
        base / "held",
        [node("start", "trigger"), node("pause", "wait", parameters={"seconds": 600})],
        {"start": {"main": [edge("pause")]}},
    )
    slow = Slow()
    with EngineService.open(base, executors={"script": slow}) as svc:
        engine = svc.ctx.engine
        going = asyncio.create_task(
            engine.start(base / "three", three, mode="test", inputs={}, run_id="run-three")
        )
        while not of(events_of(base, "run-three"), "node_started", "hold"):
            await asyncio.sleep(POLL_S)
        waiting = await engine.start(base / "held", held, mode="test", inputs={}, run_id="run-held")
        during = listed(svc)
        ledger_three = events_of(base, "run-three")
        open_attempt = of(ledger_three, "node_started", "hold") and not of(
            ledger_three, "node_finished", "hold"
        )
        log(f"while hold runs: {during}; run-held returned {waiting.status}")
        log.check(
            "the in-flight run reads running while its ledger holds an open attempt",
            during.get("run-three") == "running" and bool(open_attempt),
            during,
        )
        log.check(
            "the run held on a wait reads waiting, as its ledger's node_waiting says",
            during.get("run-held") == "waiting"
            and [w["reason"] for w in of(events_of(base, "run-held"), "node_waiting", "pause")]
            == ["wait"],
            during,
        )
        slow.gate.set()
        await going
        svc.runs.cancel("run-held")
        after = listed(svc)
    log(f"after both end: {after}")
    log.check(
        "the list follows the ledger to passed and stopped",
        after == {"run-held": "stopped", "run-three": "passed"},
        after,
    )


class FlakyFake:
    """The fake provider, except that partition 2 fails `failures` times, each with its own
    message, before the fake answers it."""

    def __init__(self, root: Path, failures: int) -> None:
        self.fake = FakeProvider(root)
        self.failures = failures
        self.jobs: list[tuple[int | None, int]] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append((job.partition, job.attempt))
        if job.partition == 2 and job.attempt <= self.failures:
            message = MESSAGES[min(job.attempt, len(MESSAGES)) - 1]
            return Failed("upstream", message, signature("upstream", message), True)
        return self.fake.run(job)


def fanned(root: Path, **join: Any) -> Workflow:
    """The one-llm fixture's node, fanned out one item per chunk over the run's items and joined."""
    shutil.copytree(ONE_LLM, root)
    document = json.loads((root / "definition.json").read_text(encoding="utf-8"))
    start, capital = document["nodes"]
    gather = {"id": "gather", "name": "Gather", "type": "join", "typeVersion": 1}
    gather["parameters"] = join
    document["nodes"] = [start, capital, gather]
    document["connections"] = {
        "Start": {
            "main": [
                [
                    {
                        "node": "Capital",
                        "port": "in",
                        "map": "chunk",
                        "chunk": {"by": "items", "size": 1},
                    }
                ]
            ]
        },
        "Capital": {"main": [[{"node": "Gather", "port": "in", "map": "one"}]]},
    }
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the lane workflow does not validate: {found}")
    return found[1]


async def walk(
    log: Log, slug: str, failures: int, **join: Any
) -> tuple[Outcome, list[Event], FlakyFake]:
    base = home(f"partition-{slug}")
    definition = fanned(base / "wf", **join)
    flaky = FlakyFake(base / "wf", failures)
    with EngineService.open(base, executors={"llm": flaky}, settings=StaticSettings(QUICK)) as svc:
        ended = await svc.ctx.engine.start(
            base / "wf", definition, mode="test", inputs=["fr", "de", "it", "es"], fake=True
        )
    events = events_of(base, ended.run_id)
    steps = [(e["partition"], e["step"]) for e in of(events, "ladder_step", "capital")]
    log(f"{slug}: ended {ended.status} ({ended.reason}); ladder {steps}; attempts {flaky.jobs}")
    return ended, events, flaky


async def partition(log: Log) -> None:
    ended, events, flaky = await walk(log, "twice", 2)
    steps = [e["step"] for e in of(events, "ladder_step", "capital") if e["partition"] == 2]
    siblings = sorted(j for j in flaky.jobs if j[0] != 2)
    log.check(
        "partition 2 walks its own ladder: retry, retry, then the fake answers it",
        steps == ["retry", "retry"]
        and [j for j in flaky.jobs if j[0] == 2] == [(2, 1), (2, 2), (2, 3)],
        steps,
    )
    log.check(
        "the other three ran once each and their memos stand",
        siblings == [(0, 1), (1, 1), (3, 1)],
        siblings,
    )
    log.check(
        "the join merged all four and the run passed",
        ended.status == "passed" and len(ended.outputs["gather"]["main"]) == 4,  # type: ignore[index,arg-type]
        ended.outputs,
    )
    ended, events, flaky = await walk(log, "always", 99)
    steps = [e for e in of(events, "ladder_step", "capital") if e["partition"] == 2]
    last = steps[-1] if steps else {}
    log.check(
        "a partition that keeps failing parks alone at the end of its ladder",
        (last.get("step"), last.get("scope")) == ("park", "partition"),
        [s["step"] for s in steps],
    )
    log.check(
        "the all-join counts it failed only after it parked",
        ended.status == "failed"
        and ended.reason
        == "join gather join_failed: all join has 3 of 4 needed partitions; 1 of 4 failed",
        ended.reason,
    )
    ended, _, _ = await walk(log, "any", 99, mode="any")
    log.check(
        "an any-join goes on without it",
        ended.status == "passed",
        ended.status,
    )


async def restart(log: Log) -> None:
    base = home("restart")
    definition = folder(
        base / "wf",
        [node("start", "trigger"), node("work", "script")],
        {"start": {"main": [edge("work")]}},
    )
    hangs = Hangs()
    with EngineService.open(base, executors={"script": hangs}) as svc:
        engine = svc.ctx.engine
        run_id = await die(
            engine, engine.start(base / "wf", definition, mode="test", inputs={}), "work", base
        )
    with EngineService.open(base, executors={"script": hangs}) as svc:
        dead = svc.runs.get(run_id)
        log(f"after the restart, before any resume: {dead.status} ({dead.reason})")
        log.check(
            "an attempt the dead engine left open reads interrupted",
            dead.status == "interrupted",
            (dead.status, dead.reason),
        )
        ended = await svc.ctx.engine.resume(run_id)
        folded = svc.runs.get(run_id)
    failed = of(events_of(base, run_id), "node_failed", "work")
    log(f"the resume folded the open attempt as {[(f['code'], f['effect_state']) for f in failed]}")
    log.check(
        "the resume folds it and the run ends passed",
        (ended.status, folded.status) == ("passed", "passed") and hangs.attempts == [1, 2],
        (ended.status, folded.status, hangs.attempts),
    )


async def irreversible(log: Log) -> None:
    base = home("irreversible")
    step = Unknown()
    definition = posting(base / "wf")
    with EngineService.open(base, executors={"script": step}) as svc:
        engine = svc.ctx.engine
        held = await engine.start(base / "wf", definition, mode="test", inputs={})
        again = await engine.resume(held.run_id)
        log.check(
            "a plain resume keeps the external step waiting on its gate: still one attempt",
            again.status == "waiting" and step.jobs == [("post", 1)],
            (again.status, step.jobs),
        )
        await answered(svc, "retry", log, held.run_id)
        ended = svc.runs.get(held.run_id)
    log.check(
        "only the retry answer runs the step again, and the run passes",
        ended.status == "passed"
        and [j for j in step.jobs if j[0] == "post"] == [("post", 1), ("post", 2)],
        (ended.status, step.jobs),
    )


def seeded(base: Path) -> None:
    """1,000 finished runs of a three-node chain, written through one ledger writer."""
    from qmx_engine.ledger.store import Ledger

    at = "2026-10-19T09:00:00+00:00"
    with Ledger.open(base) as ledger:
        for i in range(PERF_RUNS):
            run_id = f"run-perf-{i:04d}"
            ledger.append(run_id, "run_created", {"mode": "test", "workflow_id": "perf"}, at=at)
            ledger.append(run_id, "run_input", {"inputs": {}}, at=at)
            for name in ("start", "a", "b"):
                keys: dict[str, JsonValue] = {
                    "node_id": name,
                    "iteration": 0,
                    "partition": None,
                    "attempt": 1,
                }
                ledger.append(run_id, "node_scheduled", keys | {"memo_key": name}, at=at)
                ledger.append(run_id, "node_started", keys, at=at)
                ledger.append(run_id, "node_finished", keys | {"outputs": {"main": name}}, at=at)
            ledger.append(run_id, "run_finished", {"status": "passed"}, at=at)


def parent_status_of() -> Callable[..., Any]:
    """`status_of` as the parent commit has it, loaded from `git show` into its own module."""
    source = subprocess.run(
        [GIT, "show", f"{PARENT}:qmx-agents/packages/qmx-engine/src/qmx_engine/service/runs.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    module = sys.modules["parent_runs"] = types.ModuleType("parent_runs")
    exec(compile(source, "parent_runs.py", "exec"), module.__dict__)  # noqa: S102
    return module.status_of


def timed(call: Callable[[], object]) -> list[float]:
    times: list[float] = []
    for _ in range(PERF_CALLS):
        started = time.perf_counter()
        call()
        times.append((time.perf_counter() - started) * 1000)
    return times


async def perf(log: Log) -> None:
    base = home("perf")
    seeded(base)
    old = parent_status_of()
    with EngineService.open(base) as svc:
        with Reader.open(base) as reader:
            ids = [
                r for (r,) in reader.connection.execute("SELECT run_id FROM events WHERE seq = 1")
            ]
        log(f"runs in the ledger: {len(ids)}")

        def head() -> object:
            return [view.status for view in svc.runs.views(ids)]

        def parent() -> object:
            """The parent's list: `runs.get` per run, each with its own reader."""
            found: list[str] = []
            for run_id in ids:
                with Reader.open(base) as reader:
                    found.append(old(reader.events(run_id)).status)
                svc.ctx.library.objects(run_id, "workflow-run")
            return found

        statuses = head()
        head_ms = timed(head)
        parent_ms = timed(parent)
    median, base_median = statistics.median(head_ms), statistics.median(parent_ms)
    log(f"head runs list ms over {PERF_CALLS} calls: {' '.join(f'{t:.0f}' for t in head_ms)}")
    log(f"parent list ms over {PERF_CALLS} calls: {' '.join(f'{t:.0f}' for t in parent_ms)}")
    log(f"METRIC runs_list_ms_1000_runs median={median:.0f} parent_median={base_median:.0f}")
    log.check("every seeded run reads passed", set(statuses) == {"passed"}, set(statuses))  # type: ignore[arg-type]
    log.check(
        f"the median is at most {PERF_FAIL_MS:.0f} ms", median <= PERF_FAIL_MS, f"{median:.0f} ms"
    )


LANES: Final[dict[str, Callable[[Log], Coroutine[Any, Any, None]]]] = {
    "gates": gates,
    "runs": runs,
    "partition": partition,
    "restart": restart,
    "irreversible": irreversible,
    "perf": perf,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    unknown = sorted(set(args.lanes) - set(LANES))
    if unknown:
        parser.error(f"unknown lanes {unknown}; lanes are {' '.join(LANES)}")
    failed: list[str] = []
    for name in args.lanes or list(LANES):
        log = BugLog(name)
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}")
        asyncio.run(LANES[name](log))
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
