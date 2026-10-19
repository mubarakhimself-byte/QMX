"""EP8's live lanes for the watchdog, plus the regression lane and the perf probe.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x08_watchdog.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression stalled limits perf`; none named runs all. Each writes
`evidence/ep8/<ENGINE_LOG_PREFIX>ep8-<lane>.log`, and the script exits 1 if any lane failed.

- `regression` (lane 1): trunk has no ladder; the harness is byte-identical to its base, and the
  EP7 `script-chain` fixture still finishes through the CLI.
- `stalled` (lane 5): an attempt with no progress past its idle timeout is warned, then after
  its grace cancelled, and fails `stalled`. The worker's heartbeat beats every 0.2 s and is never
  progress (CAPE, AD-16).
- `limits` (lane 6, CAPE): no runaway guard exists; a `limits` block he wrote (`turns: 2`) over
  three planted `agent` nodes pauses the run with one info line, and a resume goes on.
- `perf`: one stuck-detector tick over 1,000 open attempts.

No model, no key, no ship home.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from common import Log, throwaway_home
from ep2_lanes import GIT, REPO
from qma.harness import Pulse
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_engine.watchdog import Watchdog, Watched
from qmx_engine.workers.local import LocalWorker
from qmx_ledger.journal import fingerprint
from x07_nodes import CHAIN, HARNESS, cli, edge, events, node, write_folder

OPEN_ATTEMPTS: Final = 1_000


def regression(log: Log, base: str, trunk: str) -> None:
    ladder = "qmx-agents/packages/qmx-engine/src/qmx_engine/core/ladder.py"
    on_trunk = subprocess.run(
        [GIT, "cat-file", "-e", f"{trunk}:{ladder}"], cwd=REPO, capture_output=True, check=False
    )
    log.check("trunk has no ladder to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    home = throwaway_home("ep8", "regression")
    code, lines = cli(log, "run", str(CHAIN), "--mode", "test", "--home", str(home))
    expected = f"run finished {fingerprint({'total': {'main': {'total': 20}}})}"
    log.check(
        "script-chain ends with run finished and the outputs hash",
        code == 0 and lines[-1:] == [expected],
        lines[-1:],
    )


class Hang:
    async def run(self, job: NodeJob) -> NodeResult:
        await asyncio.sleep(3600)
        return Ok({"main": None})


def stalled_lane(log: Log) -> None:
    home = throwaway_home("ep8", "stalled")
    step = node("step", "script", script="scripts/step.py")
    step |= {"timeout": {"idle_seconds": 2}, "retry": {"max_tries": 1}}
    root = write_folder(
        home / "wf-stalled",
        [node("start", "trigger"), step],
        {"start": {"main": [edge("step")]}},
        {"step": "print(1)\n"},
    )
    definition = Workflow.model_validate(load(root).document)
    began = time.monotonic()

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(
                home,
                ledger,
                settings={**DEFAULTS, "timeout.grace": 1},
                executors={"script": Hang()},
                worker=LocalWorker(heartbeat_seconds=0.2),
                watch_every=0.5,
            )
            return await engine.start(root, definition, mode="test", inputs=None)

    outcome = asyncio.run(go())
    took = time.monotonic() - began
    failed = [e.data for e in events(home, outcome.run_id) if e.kind == "node_failed"]
    log(f"run {outcome.status} after {took:.1f} s: {outcome.reason}")
    log(f"node_failed: {[(f['code'], f['retryable'], f['effect_state']) for f in failed]}")
    log.check(
        "the silent attempt was cancelled and failed stalled, retryable",
        [(f["code"], f["retryable"]) for f in failed] == [("stalled", True)],
        failed,
    )
    log.check(
        "it was caught soon after its 2 s idle timeout and 1 s grace", took < 10, f"{took:.1f} s"
    )


class Agent:
    def __init__(self) -> None:
        self.started: list[str] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.started.append(job.node_id)
        return Ok({"main": job.node_id}, span={"turns": 2})


def limits_lane(log: Log) -> None:
    home = throwaway_home("ep8", "limits")
    nodes: list[dict[str, Any]] = [node("start", "trigger")]
    nodes += [node(n, "agent") | {"role": "builder"} for n in ("a", "b", "c")]
    root = write_folder(
        home / "wf-limits",
        nodes,
        {"start": {"main": [edge("a")]}, "a": {"main": [edge("b")]}, "b": {"main": [edge("c")]}},
        {},
        limits={"turns": 2},
    )
    definition = Workflow.model_validate(load(root).document)
    agent = Agent()

    async def go(run_id: str | None) -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, executors={"agent": agent})
            if run_id is None:
                return await engine.start(root, definition, mode="test", inputs=None)
            return await engine.resume(run_id)

    outcome = asyncio.run(go(None))
    found = events(home, outcome.run_id)
    digest = [e.data["line"] for e in found if e.kind == "log" and e.data.get("digest")]
    after = [asyncio.run(go(outcome.run_id)).status for _ in range(2)]
    items = []
    if inbox_path(home).exists():
        with InboxTable.open(home) as inbox:
            items = inbox.list_items(open_only=False)
    log(f"agents started: {agent.started}; run {outcome.status}: {outcome.reason}; then {after}")
    log(f"digest lines: {digest}")
    log.check(
        "the run is waiting(limits) after the first agent",
        (outcome.status, outcome.reason, agent.started[:1]) == ("waiting", "limits", ["a"]),
        (outcome.status, outcome.reason, agent.started),
    )
    log.check("one info digest line", len(digest) == 1, digest)
    log.check("two resumes finish the run", after == ["waiting", "passed"], after)
    log.check("no inbox item", items == [], items)


def perf(log: Log) -> None:
    now = datetime.now(UTC)
    dog = Watchdog(DEFAULTS, tick_seconds=60)
    attempts = [Watched(f"run:n{i}:0:1", "agent", Pulse(i % 3)) for i in range(OPEN_ATTEMPTS)]
    runs = []
    found = []
    for tick in range(5):
        began = time.perf_counter()
        found = dog.tick(now + timedelta(seconds=60 * tick), attempts)
        runs.append((time.perf_counter() - began) * 1000)
    log(f"ticks over {OPEN_ATTEMPTS} open attempts: {[f'{r:.3f}' for r in runs]} ms")
    log(f"actions on the last tick: {len(found)}")
    log.check(
        "one watchdog tick over 1,000 open attempts (ms, not gated)", True, f"{min(runs):.3f} ms"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep7")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, args.base, args.trunk),
        "stalled": stalled_lane,
        "limits": limits_lane,
        "perf": perf,
    }
    failed = 0
    for name in args.lanes or list(lanes):
        log = Log("ep8", f"ep8-{name}")
        lanes[name](log)
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
