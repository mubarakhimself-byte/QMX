"""EP12's regression lane, its claims and preflight lanes, and its perf probe.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x12_scheduler.py [--base REV] [lane]`
Lanes are `regression claims preflight perf`; none named runs all. Each writes
`evidence/ep12/<ENGINE_LOG_PREFIX>ep12-<lane>.log`, and the script exits 1 if any lane failed.

- `regression` (lane 1): the harness is byte-identical to its base, and EP11's `e05_pause` passes
  with the run woken by the ticker.
- `claims` (lane 3): two engine processes tick one ledger. The second waits on the writer lock,
  the first is killed mid-run, the second takes the writer, takes over the killed fire once its
  lease runs out, and ticks on. Every occurrence has at most one fire and every live run belongs
  to exactly one fire.
- `preflight` (lane 4): a trigger whose workflow names a role Settings no longer has ends
  `blocked_config` with one digest line, no inbox item and no run.
- `perf`: ten ticks over 500 enabled triggers, every one due on each tick, then ten idle ticks.

No model, no key, no ship home: the script chain, and for `preflight` the engine tests' fake
harness port answering the one test run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from ep2_lanes import ENGINE, GIT, HARNESS, REPO, run
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Reader, WriterRefused
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS, Setting
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Interval, stamp
from qmx_engine.triggers.ticker import Scheduler

PR: Final = "ep12"
CHAIN: Final = ENGINE / "tests" / "fixtures" / "workflows" / "script-chain"
TRIGGERS: Final = 500
PERF_BUDGET_S: Final = 1.0
CLAIM_SETTINGS: Final[dict[str, Setting]] = {
    **DEFAULTS,
    "scheduler.tick": 1,
    "scheduler.lease_seconds": 4,
}


class Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def enable(svc: EngineService, bundle: Bundle) -> tuple[str, str]:
    """Draft, test, publish and enable `bundle`; its item and version."""
    item = svc.drafts.put(None, bundle, 0, caller=OPERATOR).item
    report = asyncio.run(svc.tests.run(item, caller=OPERATOR))
    if report.status != "passed":
        raise SystemExit(f"BLOCKED: the setup test run ended {report.status}")
    version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
    svc.versions.enable(version, caller=OPERATOR)
    return item, version


def live_runs(home: Path) -> list[str]:
    with Reader.open(home) as reader:
        found = reader.connection.execute(
            "SELECT run_id, data FROM events WHERE kind = 'run_created'"
        ).fetchall()
    return sorted(r for r, data in found if json.loads(data).get("mode") == "live")


def regression(log: Log, base: str) -> None:
    diff = run(log, [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], REPO)
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    sys.path.insert(0, str(Path(__file__).parent))
    import e05_pause  # noqa: PLC0415

    log("EP11 e05_pause at head, its run woken by the ticker:")
    code = asyncio.run(e05_pause.main(log, PR))
    log.check("e05_pause passes with the ticker waking the run", code == 0, code)


def ticker_child(home: Path, claimant: str, seconds: float) -> int:
    """One engine process: wait for the writer, then tick until `seconds` have passed."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            service = EngineService.open(home, settings=StaticSettings(CLAIM_SETTINGS))
            svc = service.__enter__()
            break
        except WriterRefused as refused:
            print(f"{claimant} standby: {refused}", flush=True)
            if time.monotonic() > deadline:
                return 2
            time.sleep(0.5)
    print(f"{claimant} holds the writer", flush=True)
    ticker = Scheduler(svc.ctx, claimant=claimant)

    async def serve() -> None:
        stop = asyncio.Event()
        asyncio.get_running_loop().call_later(max(deadline - time.monotonic(), 0), stop.set)
        while not stop.is_set():
            tick = await ticker.tick()
            for found in tick.claimed:
                print(
                    f"{claimant} claimed {found.fire.id} {found.fire.occurrence_at}"
                    f" status={found.fire.status} run={found.fire.run_id}",
                    flush=True,
                )
            await asyncio.sleep(1)
        await ticker.settle()

    asyncio.run(serve())
    service.__exit__(None, None, None)
    print(f"{claimant} stopped", flush=True)
    return 0


def spawn(command: list[str]) -> tuple[subprocess.Popen[str], list[str]]:
    """Start a child and collect its output lines as they come."""
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines: list[str] = []

    def pump() -> None:
        lines.extend(line.rstrip() for line in child.stdout or ())

    threading.Thread(target=pump, daemon=True).start()
    return child, lines


def wait_for(ready: Callable[[], bool], seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while not ready():
        if time.monotonic() > deadline:
            raise SystemExit("BLOCKED: the claims lane timed out waiting on a child")
        time.sleep(0.1)


def claims(log: Log) -> None:
    home = throwaway_home(PR, "claims")
    with EngineService.open(home, settings=StaticSettings(CLAIM_SETTINGS)) as svc:
        item, version = enable(svc, Bundle.read(CHAIN))
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=item,
            pinned_object=version,
            spec=Interval(2, datetime.now(UTC)),
            caller=OPERATOR,
            now=datetime.now(UTC),
        )
    log(f"interval trigger {trigger.id} every 2 s on {version}; lease 4 s, tick 1 s")
    command = [sys.executable, __file__, "ticker", "--home", str(home)]
    first, out_a = spawn([*command, "--claimant", "A", "--seconds", "120"])
    wait_for(lambda: "A holds the writer" in out_a, 60)
    second, out_b = spawn([*command, "--claimant", "B", "--seconds", "40"])
    wait_for(lambda: sum("standby" in line for line in out_b) >= 3, 60)

    def running() -> list[str]:
        with Reader.open(home) as reader:
            listed = rows.fires(reader.connection, trigger.id)
        return [f.id for f in listed if f.status == "running" and f.claimed_by == "A"]

    wait_for(lambda: bool(running()), 30)
    killed = running()
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(first.pid)],  # noqa: S607
        capture_output=True,
        check=False,
    )
    log(f"killed A (pid {first.pid}) while it ran fires {killed}")
    first.wait()
    second.wait(timeout=120)
    standby = sum("standby" in line for line in out_b)
    for line in out_a + out_b:
        if "standby" not in line:
            log(f"  {line}")
    first_wait = next((line for line in out_b if "standby" in line), None)
    log(f"  {first_wait}  (B logged standby {standby} times while A held the writer)")
    with Reader.open(home) as reader:
        found = rows.fires(reader.connection, trigger.id)
    by_occurrence: dict[str, int] = {}
    for fire in found:
        by_occurrence[fire.occurrence_at] = by_occurrence.get(fire.occurrence_at, 0) + 1
    fired = [f for f in found if f.run_id is not None]
    runs = live_runs(home)
    log(
        "fires: "
        + ", ".join(f"{f.occurrence_at[17:23]} {f.status} {f.claimed_by or '-'}" for f in found)
    )
    log.check(
        "B waited on the writer lock while A held it",
        standby > 0 and "B holds the writer" in out_b,
        standby,
    )
    log.check(
        "every occurrence has at most one fire",
        max(by_occurrence.values()) == 1,
        len(by_occurrence),
    )
    log.check(
        "every live run belongs to exactly one fire, and every fire that ran has one run",
        sorted(str(f.run_id) for f in fired) == runs and len(set(runs)) == len(runs),
        {"runs": len(runs), "fires_with_runs": len(fired)},
    )
    taken = [f for f in found if f.id in killed]
    log.check(
        "the fire A was running when killed was taken over by B and settled, not fired again",
        bool(taken) and all(f.claimed_by == "B" and f.status == "ok" for f in taken),
        [(f.id, f.claimed_by, f.status) for f in taken],
    )
    log.check(
        "no fire is left claimed or running",
        not [f for f in found if f.status in ("claimed", "running")],
        sorted({f.status for f in found}),
    )


LLM_SCHEMA: Final = {
    "type": "object",
    "required": ["seen"],
    "properties": {"seen": {"type": "integer"}},
}


def triage_bundle() -> Bundle:
    definition = {
        "schema": "qmx.workflow/1",
        "id": "triage",
        "name": "triage",
        "nodes": [
            {"id": "start", "name": "start", "type": "trigger", "typeVersion": 1},
            {
                "id": "ask",
                "name": "ask",
                "type": "llm",
                "typeVersion": 1,
                "role": "triage",
                "parameters": {"prompt_ref": "p.md", "schema_ref": "s.json"},
            },
        ],
        "connections": {"start": {"main": [[{"node": "ask", "port": "in", "map": "one"}]]}},
    }
    files = {"p.md": b"Count what you are given.", "s.json": json.dumps(LLM_SCHEMA).encode()}
    return Bundle(definition, files)  # pyright: ignore[reportArgumentType]


def preflight(log: Log) -> None:
    sys.path.insert(0, str(ENGINE / "tests"))
    from fake_port import CARD, FakePort  # noqa: PLC0415

    home = throwaway_home(PR, "preflight")
    port = FakePort(CARD)
    without_triage = {k: v for k, v in DEFAULTS.items() if k != "roles.triage"}
    with EngineService.open(home, settings=StaticSettings(DEFAULTS), harness=port) as svc:
        item, version = enable(svc, triage_bundle())
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=datetime.now(UTC),
        )
    runs_before = live_runs(home)
    log(f"published and enabled {version}, an llm node on role triage; manual trigger {trigger.id}")
    log("reopened the engine with Settings that no longer name role triage")
    with EngineService.open(home, settings=StaticSettings(without_triage), harness=port) as svc:
        rows.fire_now(svc.ctx.engine.ledger, trigger.id, datetime.now(UTC), {})
        ticker = Scheduler(svc.ctx)

        async def go() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(go())
    with Reader.open(home) as reader:
        (fire,) = rows.fires(reader.connection, trigger.id)
        (after,) = rows.triggers(reader.connection)
        digests = reader.connection.execute(
            "SELECT digest FROM fires WHERE digest IS NOT NULL"
        ).fetchall()
    with InboxTable.open(home) as inbox:
        items = inbox.list_items(open_only=False)
    log(f"fire {fire.id}: {fire.status} {fire.detail}; digest {digests}")
    log.check(
        "the fire ended blocked_config on role_missing",
        (fire.status, fire.detail, after.last_status)
        == ("blocked_config", "role_missing", "blocked_config"),
        (fire.status, fire.detail, after.last_status),
    )
    log.check("one digest line", len(digests) == 1, digests)
    log.check("no inbox item", items == [], [i.title for i in items])
    log.check("no run started", live_runs(home) == runs_before, live_runs(home))


def perf(log: Log) -> None:
    home = throwaway_home(PR, "perf")
    t0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
    clock = Clock(t0)
    with EngineService.open(home, clock=clock) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        ledger = svc.ctx.engine.ledger
        for n in range(TRIGGERS):
            trigger = rows.Trigger(
                id=f"trigger-perf-{n:03d}",
                workflow_item=item,
                pinned_object=version,
                spec=Interval(60, t0),
                created_by="operator",
                created_at=stamp(t0),
                next_fire_at=stamp(t0 + timedelta(seconds=60)),
            )
            ledger.write(rows.insert(trigger))
        log(
            f"seeded {TRIGGERS} interval triggers of 60 s on {version}, published but not "
            "enabled, so each fire settles `skipped` without starting a run"
        )
        ticker = Scheduler(svc.ctx)

        async def timed(move: float) -> tuple[float, float, int]:
            clock.current += timedelta(seconds=move)
            started = time.perf_counter()
            tick = await ticker.tick()
            ticked = time.perf_counter() - started
            await ticker.settle()
            return ticked, time.perf_counter() - started, len(tick.claimed)

        def ten(move: float) -> list[tuple[float, float, int]]:
            return [asyncio.run(timed(move)) for _ in range(10)]

        due = ten(60)
        idle = ten(1)
    for name, found in (("due", due), ("idle", idle)):
        ticks = [t for t, _, _ in found]
        settled = [s for _, s, _ in found]
        log(
            f"{name}: claimed {[c for _, _, c in found]}; tick s median "
            f"{statistics.median(ticks):.3f} max {max(ticks):.3f}; tick plus every fire "
            f"settled s median {statistics.median(settled):.3f} max {max(settled):.3f}"
        )
    log.check(
        f"every due tick claimed all {TRIGGERS} triggers",
        all(c == TRIGGERS for _, _, c in due),
        [c for _, _, c in due],
    )
    worst = max(t for t, _, _ in due + idle)
    log.check(
        f"PERF a tick over {TRIGGERS} triggers takes at most {PERF_BUDGET_S:.0f} s",
        worst <= PERF_BUDGET_S,
        f"worst {worst:.3f} s",
    )


LANES: Final[dict[str, Callable[[Log, argparse.Namespace], None]]] = {
    "regression": lambda log, args: regression(log, args.base),
    "claims": lambda log, _: claims(log),
    "preflight": lambda log, _: preflight(log),
    "perf": lambda log, _: perf(log),
}


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--base", default="origin/engine/hg2")
    cli.add_argument("--home", type=Path)
    cli.add_argument("--claimant", default="A")
    cli.add_argument("--seconds", type=float, default=30)
    cli.add_argument("lanes", nargs="*", choices=[*LANES, "ticker"])
    args = cli.parse_args()
    if args.lanes == ["ticker"]:
        return ticker_child(args.home, args.claimant, args.seconds)
    prefix = os.environ.get("ENGINE_LOG_PREFIX", "")
    failed = False
    for lane in args.lanes or list(LANES):
        os.environ["ENGINE_LOG_PREFIX"] = prefix  # e05_pause's boot scrub drops it
        log = Log(PR, f"ep12-{lane}")
        log(f"pid {os.getpid()}")
        LANES[lane](log, args)
        failed |= log.verdict() != 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
