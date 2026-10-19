"""BUG1 lanes for E40 (AD-10 wakes): a held run writes a wake row, reads `waiting`, and the
scheduler resumes it on its own.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e40_wakes.py <lane>`
Lanes are `e40 wait backoff kill perf`; `e40` runs `wait` then `backoff`. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/bug1/<ENGINE_LOG_PREFIX>bug1-<lane>.log` and exits 1
when a check failed. No model, no key, no ship home: script and wait nodes on throwaway homes.

- `wait`: a run held on `wait seconds: 90` returns `waiting`, leaves one wake row at its
  `resume_at`, reads `waiting` in the runs list, and a scheduler serving on its own (nobody calls
  resume) resumes it 90 s on and it ends `passed`.
- `backoff`: a script that fails once under `retry.backoff_seconds: [20]` returns `waiting` with a
  wake row at the retry's `resume_at`; the serving scheduler resumes it and it ends `passed`.
- `kill`: a run of one slow script is killed with its engine process twice; each restart resumes
  it once from the ledger, and no attempt is started twice for one engine life.
- `perf`: ten ticks over 200 enabled interval triggers, the median tick in ms. Runs at any commit
  that has `Scheduler.tick`, so the parent gives the baseline.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any, Final

from common import Log
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Interval
from qmx_engine.triggers.ticker import Scheduler

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "bug1"
CHAIN: Final = (
    Path(__file__).resolve().parents[3]
    / "qmx-agents/packages/qmx-engine/tests/fixtures/workflows/script-chain"
)
SERVE_SETTINGS: Final = StaticSettings({**DEFAULTS, "scheduler.tick": 2})
FLAKY: Final = """
    import json, sys
    from pathlib import Path
    counter = Path(json.load(sys.stdin)["in"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    sys.exit(1 if tries == 1 else 0)
"""
SLOW: Final = """
    import json, sys, time
    from pathlib import Path
    marks = Path(json.load(sys.stdin)["in"])
    with marks.open("a") as handle:
        handle.write("started\\n")
    time.sleep(6)
    print(json.dumps("done"))
"""


class BugLog(Log):
    """`Log` writing into the build store's `evidence/bug1/`."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}bug1-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def home(slug: str) -> Path:
    root = STORE / "homes" / f"bug1-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def node(name: str, kind: str, **parameters: Any) -> dict[str, Any]:
    return {"id": name, "name": name, "type": kind, "typeVersion": 1, "parameters": parameters}


def folder(root: Path, nodes: list[dict[str, Any]], scripts: dict[str, str]) -> Path:
    """A two-node workflow: a manual trigger feeding `nodes[0]`."""
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": "qmx.workflow/1",
        "id": "e40",
        "name": "e40",
        "nodes": [node("start", "trigger", kinds=["manual"]), *nodes],
        "connections": {
            "start": {"main": [[{"node": nodes[0]["name"], "port": "in", "map": "one"}]]}
        },
    }
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    (root / "scripts").mkdir(exist_ok=True)
    for name, text in scripts.items():
        (root / "scripts" / f"{name}.py").write_text(dedent(text), encoding="utf-8")
    return root


def parsed(root: Path) -> Workflow:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"the lane workflow does not validate: {found}")
    return found[1]


def events_of(base: Path, run_id: str) -> list[Event]:
    with Reader.open(base) as reader:
        return reader.events(run_id)


def wakes(base: Path) -> list[tuple[str, str]]:
    with Reader.open(base) as reader:
        return reader.connection.execute("SELECT run_id, resume_at FROM wakes").fetchall()


async def held_then_served(log: Log, base: Path, root: Path, inputs: Any, budget: float) -> None:
    """Start the run, check its hold, then serve the scheduler until the run ends or `budget`
    seconds pass. Nobody resumes the run but the scheduler."""
    found = parsed(root)
    with EngineService.open(base, settings=SERVE_SETTINGS) as svc:
        outcome = await svc.ctx.engine.start(root, found, mode="test", inputs=inputs)
        held_at = datetime.now(UTC)
        rows_now = wakes(base)
        listed = svc.runs.get(outcome.run_id)
        log.check("the start returns waiting", outcome.status == "waiting", outcome)
        log.check(
            "one wake row for the run",
            [r for r, _ in rows_now] == [outcome.run_id],
            rows_now,
        )
        log.check(
            "the runs list reads waiting",
            listed.status == "waiting",
            (listed.status, listed.reason),
        )
        stop = asyncio.Event()
        serving = asyncio.create_task(Scheduler(svc.ctx).serve(stop))
        deadline = time.monotonic() + budget
        while time.monotonic() < deadline:
            await asyncio.sleep(1)
            if events_of(base, outcome.run_id)[-1].kind == "run_finished":
                break
        stop.set()
        await serving
        events = events_of(base, outcome.run_id)
        resumed = [e for e in events if e.kind == "run_resumed"]
        waited = (
            (datetime.fromisoformat(resumed[0].at) - held_at).total_seconds() if resumed else None
        )
        log(f"resumed {waited} s after the hold; wake row was {rows_now[0][1]}")
        log.check(
            "the scheduler resumed the run once, on its own",
            [e.data.get("reason") for e in resumed] == ["wake"],
            [e.data for e in resumed],
        )
        due = datetime.fromisoformat(rows_now[0][1])
        log.check(
            "it resumed at or after its resume_at",
            bool(resumed) and datetime.fromisoformat(resumed[0].at) >= due - timedelta(seconds=1),
            (resumed[0].at if resumed else None, rows_now[0][1]),
        )
        log.check(
            "the run ended passed",
            events[-1].kind == "run_finished" and events[-1].data.get("status") == "passed",
            events[-1].data,
        )
        log.check("no wake row is left", wakes(base) == [], wakes(base))


async def wait(log: Log) -> None:
    base = home("wait")
    root = folder(base / "wf", [node("pause", "wait", seconds=90)], {})
    await held_then_served(log, base, root, None, budget=150)


async def backoff(log: Log) -> None:
    base = home("backoff")
    flaky = node("flaky", "script", script="scripts/flaky.py")
    flaky["retry"] = {"backoff_seconds": [20]}
    root = folder(base / "wf", [flaky], {"flaky": FLAKY})
    await held_then_served(log, base, root, str(base / "tries.txt"), budget=80)
    tries = (base / "tries.txt").read_text(encoding="utf-8")
    log.check("the script ran twice, once per attempt", tries == "2", tries)


async def e40(log: Log) -> None:
    await wait(log)
    await backoff(log)


def kill(log: Log) -> None:
    """Start one engine process per life; the first two are killed mid-attempt."""
    base = home("kill")
    marks = base / "marks.txt"
    slow = node("slow", "script", script="scripts/slow.py")
    slow["retry"] = {"max_tries": 5, "backoff_seconds": [0]}
    root = folder(base / "wf", [slow], {"slow": SLOW})
    child = Path(__file__).resolve()
    run_id = "run-bug1-kill"
    for life in (1, 2, 3):
        verb = "start" if life == 1 else "resume"
        proc = subprocess.Popen(
            [sys.executable, str(child), "_life", verb, str(base), str(root), run_id, str(marks)]
        )
        if life < 3:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                seen = marks.read_text(encoding="utf-8").count("started") if marks.exists() else 0
                if seen >= life:
                    break
                time.sleep(0.2)
            time.sleep(1)
            proc.kill()
            proc.wait()
            log(f"life {life}: killed the engine with its attempt in flight")
        else:
            proc.wait(timeout=120)
    events = events_of(base, run_id)
    resumed = [e.data.get("reason") for e in events if e.kind == "run_resumed"]
    starts = [e.seq for e in events if e.kind == "node_started" and e.data["node_id"] == "slow"]
    lives = resumed.count("interrupted")
    twice = resumed == ["interrupted", "interrupted"]
    log.check("each restart resumed the run once", twice, resumed)
    log.check("one attempt per engine life, no duplicate fire", len(starts) == 3, starts)
    log.check(
        "the run ended passed",
        events[-1].kind == "run_finished" and events[-1].data.get("status") == "passed",
        (lives, events[-1].kind, events[-1].data),
    )


def life(verb: str, base: str, root: str, run_id: str, marks: str) -> None:
    found = parsed(Path(root))

    async def go() -> None:
        with EngineService.open(Path(base)) as svc:
            engine = svc.ctx.engine
            if verb == "start":
                await engine.start(Path(root), found, mode="test", inputs=marks, run_id=run_id)
            else:
                await engine.resume(run_id)

    asyncio.run(go())


async def perf(log: Log) -> None:
    base = home("perf")
    now = datetime.now(UTC)
    with EngineService.open(base) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        await svc.tests.run(item, caller=OPERATOR)
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        svc.versions.enable(version, caller=OPERATOR)
        for _ in range(200):
            rows.create(
                svc.ctx.engine.ledger,
                workflow_item=item,
                pinned_object=version,
                spec=Interval(3600, now),
                caller=OPERATOR,
                now=now,
            )
        ticker = Scheduler(svc.ctx)
        times: list[float] = []
        for _ in range(10):
            began = time.perf_counter()
            await ticker.tick()
            times.append((time.perf_counter() - began) * 1000)
        await ticker.settle()
    log(f"PERF ticker tick over 200 trigger rows: median {statistics.median(times):.2f} ms")
    log(f"ticks ms: {[round(t, 2) for t in times]}")
    log.check("ten ticks ran", len(times) == 10, len(times))


LANES: Final = {"e40": e40, "wait": wait, "backoff": backoff, "perf": perf}


def main() -> int:
    if sys.argv[1:2] == ["_life"]:
        life(*sys.argv[2:7])
        return 0
    lane = sys.argv[1] if len(sys.argv) > 1 else "e40"
    log = BugLog(lane)
    if lane == "kill":
        kill(log)
    else:
        asyncio.run(LANES[lane](log))
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
