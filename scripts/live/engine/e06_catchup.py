"""EP12 lane 2 (E6): the engine is stopped across four cron occurrences and restarted; one
catch-up fire runs and the other three are recorded `skipped: downtime` (ruling 54).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e06_catchup.py`
Writes `evidence/ep12/<ENGINE_LOG_PREFIX>ep12-e06.log`. No model and no key: the script chain on
a throwaway home. Each engine is its own process on an injected clock (`--now`). The first
enables the chain, creates an hourly `Europe/London` cron trigger at 09:30 and ticks once; the
second starts at 13:30, past 10:00, 11:00, 12:00 and 13:00, and ticks once. Then
`python -m qmx_engine triggers list` shows the trigger.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

from common import Log, throwaway_home
from ep2_lanes import AGENTS, ENGINE
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.ticker import Scheduler

PR: Final = "ep12"
LONDON: Final = ZoneInfo("Europe/London")
STOPPED: Final = datetime(2026, 10, 17, 9, 30, tzinfo=LONDON)
RESTARTED: Final = datetime(2026, 10, 17, 13, 30, tzinfo=LONDON)
CHAIN: Final = ENGINE / "tests" / "fixtures" / "workflows" / "script-chain"


class Fixed:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def engine(home: Path, now: datetime, first: bool) -> int:
    """One engine process at `now`: set up on the first start, then one tick."""
    with EngineService.open(home, clock=Fixed(now)) as svc:
        if first:
            item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
            asyncio.run(svc.tests.run(item, caller=OPERATOR))
            version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
            svc.versions.enable(version, caller=OPERATOR)
            trigger = rows.create(
                svc.ctx.engine.ledger,
                workflow_item=item,
                pinned_object=version,
                spec=Cron("0 * * * *", "Europe/London"),
                caller=OPERATOR,
                now=now,
            )
            print(f"created {trigger.id} on {version}, next_fire_at {trigger.next_fire_at}")
        ticker = Scheduler(svc.ctx)

        async def once() -> int:
            tick = await ticker.tick()
            await ticker.settle()
            return len(tick.claimed)

        print(f"engine at {now.isoformat()} ticked, claimed {asyncio.run(once())}")
    return 0


def child(log: Log, home: Path, now: datetime, *, first: bool) -> None:
    command = [sys.executable, __file__, "--home", str(home), "--now", now.isoformat()]
    done = subprocess.run(
        [*command, *(["--first"] if first else [])], capture_output=True, text=True, check=False
    )
    for line in (done.stdout + done.stderr).splitlines():
        log(f"  {line}")
    if done.returncode != 0:
        raise SystemExit(f"BLOCKED: the engine at {now} exited {done.returncode}")


def main() -> int:
    log = Log(PR, "ep12-e06")
    home = throwaway_home(PR, "e06")
    child(log, home, STOPPED, first=True)
    log("engine stopped; 10:00, 11:00, 12:00 and 13:00 Europe/London pass with no engine")
    child(log, home, RESTARTED, first=False)
    with Reader.open(home) as reader:
        (trigger,) = rows.triggers(reader.connection)
        fires = rows.fires(reader.connection, trigger.id)
        runs = [(fire, reader.events(fire.run_id)[-1]) for fire in fires if fire.run_id is not None]
    for fire in fires:
        log(f"fire {fire.occurrence_at} {fire.status} {fire.detail} run={fire.run_id}")
    listed = subprocess.run(
        [sys.executable, "-m", "qmx_engine", "triggers", "list", "--home", str(home)],
        capture_output=True,
        text=True,
        check=False,
        cwd=AGENTS,
    )
    log(f"$ python -m qmx_engine triggers list --home {home}")
    for line in listed.stdout.splitlines():
        log(f"  {line}")
    log.check(
        "exactly one fire ran, for 13:00, and passed",
        [(f.occurrence_at, e.kind, e.data.get("status")) for f, e in runs]
        == [("2026-10-17T12:00:00.000000+00:00", "run_finished", "passed")],
        [(f.occurrence_at, e.kind) for f, e in runs],
    )
    log.check(
        "three occurrences are recorded skipped: downtime",
        [(f.occurrence_at[11:16], f.status, f.detail) for f in fires if f.run_id is None]
        == [
            ("09:00", "skipped", "downtime"),
            ("10:00", "skipped", "downtime"),
            ("11:00", "skipped", "downtime"),
        ],
        len(fires),
    )
    log.check(
        "triggers list shows next_fire_at 14:00 London and last_status ok",
        "next_fire_at=2026-10-17T13:00:00.000000+00:00 last_status=ok" in listed.stdout,
        listed.returncode,
    )
    return log.verdict()


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--home", type=Path)
    cli.add_argument("--now", type=datetime.fromisoformat)
    cli.add_argument("--first", action="store_true")
    args = cli.parse_args()
    raise SystemExit(engine(args.home, args.now, args.first) if args.home else main())
