"""TRG2a's live lanes: trigger kinds, priorities, market time, the pause switch and failure
contracts. None needs a model.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/trg2a_lanes.py <lane> [--parent-tree DIR]`
Lanes are `regression webhook pause priority market rerun catchup migrate secrets processes
perf`. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/trg2a/<ENGINE_LOG_PREFIX>trg2a-<lane>.log` and exits 1
when a check failed. `--parent-tree` is a checkout of the parent commit with its own synced venv
(`regression`, `migrate`, `perf`).

- `regression` (lane 1): the `qmx-engine` suite with `-n 2` at the parent and at head. PASS when
  head fails nothing the parent passes.
- `webhook` (lane 2): `qmx_host` on a throwaway home; the script chain is published with a webhook
  trigger, and one delivery id is posted twice to `/api/hooks/<trigger>`. PASS when one live run
  starts and the second answer says duplicate.
- `pause` (lane 3, E64's local half): `qmx_host` on a throwaway home whose `settings.toml` sets
  `[engine.autonomy] paused = true` and a 5 s tick; three every-minute cron triggers stay due
  past two occurrences, then the flag is cleared in `settings.toml`. PASS when nothing fires while
  paused, `explain_trigger` says paused, and each trigger fires once after.
- `priority` (lane 4): one CPU slot held by a 2 s fire; a priority 1 fire, then a priority 5
  fire, queue behind it. PASS when the priority 5 fire's script starts first.
- `market` (lane 5): an hourly cron with `market_open` due on a Saturday on a fake clock. PASS
  when the fire is held, `explain_trigger` says why, and the held fire runs on Monday.
- `rerun` (lane 6): a fire whose script prints `[QMX_FAILURE]`, on a fake clock. PASS when it
  re-runs at 5 and 15 minutes and every failure counts on one incident.
- `catchup` (lane 7): `e06_catchup.py` at head.
- `migrate` (lane 8): the ledger `e06_catchup.py` leaves at the parent, migrated by head. PASS
  when every old row survives.
- `secrets` (lane 9): `tools/secret_scan.py`.
- `processes` (lane 10): no `qmx_host`, `claude` or `qma-cli-launcher` process and no lane lock.
- `perf`: ten ticks over 500 cron rows, at the parent and at head; the median is recorded.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any, Final

import httpx
from common import LANE_LOCK, Log
from ep2_lanes import AGENTS, ENGINE, REPO, UV, clean_env, run

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "trg2a"
CHAIN: Final = ENGINE / "tests" / "fixtures" / "workflows" / "script-chain"
SATURDAY: Final = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
MONDAY: Final = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
TIMED: Final = """
    import json, sys, time

    def seconds(value):
        if isinstance(value, dict):
            if "seconds" in value:
                return float(value["seconds"])
            return next((s for v in value.values() if (s := seconds(v)) is not None), None)
        if isinstance(value, list):
            return next((s for v in value if (s := seconds(v)) is not None), None)
        return None

    began = time.time()
    time.sleep(seconds(json.load(sys.stdin)) or 0.1)
    print(json.dumps([began, time.time()]))
"""
FAILING: Final = """
    import json, os
    if os.environ["QMX_MODE"] == "live":
        print("[QMX_FAILURE] the feed is down")
    else:
        print(json.dumps([1, 2, 3, 4]))
"""


class TrgLog(Log):
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}trg2a-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def home(slug: str) -> Path:
    root = STORE / "homes" / f"trg2a-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


class Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def publish(svc: Any, bundle: Any) -> str:
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415

    item = svc.drafts.put(None, bundle, 0, caller=OPERATOR).item
    asyncio.run(svc.tests.run(item, caller=OPERATOR))
    version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
    svc.versions.enable(version, caller=OPERATOR)
    return version


def failed_ids(output: str) -> set[str]:
    return set(re.findall(r"^FAILED (\S+)", output, re.MULTILINE))


def regression(log: Log, parent: Path) -> None:
    suite = [UV, "run", "--no-sync", "python", "-m", "pytest", "-q", "-n", "2", "-rf"]
    suite += ["-p", "no:cacheprovider"]
    engine = Path("qmx-agents") / "packages" / "qmx-engine"
    at_parent = run(log, suite, parent / engine)
    at_head = run(log, suite, REPO / engine)
    lost = failed_ids(at_head.stdout) - failed_ids(at_parent.stdout)
    tail = [line for line in at_head.stdout.splitlines() if " passed" in line][-1:]
    log(f"parent: {[ln for ln in at_parent.stdout.splitlines() if ' passed' in ln][-1:]}")
    log(f"head: {tail}")
    log.check("the parent suite ran", at_parent.returncode in (0, 1), at_parent.returncode)
    log.check("head fails nothing the parent passes", not lost and at_head.returncode == 0, lost)


def started_host(log: Log, root: Path) -> Any:
    from x13_doors import host  # noqa: PLC0415

    return host(log, root)


def reply(log: Log, name: str, found: httpx.Response) -> Any:
    body = found.json()
    log(f"{name}: http {found.status_code} {json.dumps(body)[:400]}")
    return body


def chain_body(item: str) -> dict[str, Any]:
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415

    bundle = Bundle.read(CHAIN)
    files = {ref: data.decode() for ref, data in bundle.files.items()}
    return {"definition": bundle.definition | {"id": item}, "files": files}


def published_chain(log: Log, client: httpx.Client, item: str) -> None:
    reply(log, "draft put", client.put(f"/api/workflows/{item}/draft", json=chain_body(item)))
    tested = reply(log, "test", client.post(f"/api/workflows/{item}/test"))
    log(f"test run {tested['run']['run_id']} {tested['run'].get('status')}")
    reply(log, "publish", client.put(f"/api/workflows/{item}", json={}))


def live_runs(client: httpx.Client) -> list[dict[str, Any]]:
    return [r for r in client.get("/api/workflow-runs").json() if r.get("mode") == "live"]


def wait_for(predicate: Any, seconds: float) -> Any:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if found := predicate():
            return found
        time.sleep(0.5)
    return None


def webhook(log: Log) -> None:
    root = home("webhook")
    with started_host(log, root) as (client, _, _):
        published_chain(log, client, "hooked")
        trigger = reply(
            log,
            "add webhook trigger",
            client.post(
                "/api/triggers", params={"workflow_id": "hooked"}, json={"kind": "webhook"}
            ),
        )
        reply(log, "enable", client.post(f"/api/triggers/{trigger['id']}/enable"))
        path = f"/api/hooks/{trigger['id']}"
        bare = client.post(path, json={"order": 7})
        log(f"no delivery id: http {bare.status_code} {bare.text[:200]}")
        headers = {"X-QMX-Delivery": "lane-delivery-1"}
        first = reply(log, "delivery 1", client.post(path, json={"order": 7}, headers=headers))
        second = reply(
            log, "delivery 1 again", client.post(path, json={"order": 7}, headers=headers)
        )
        ran = wait_for(lambda: [r for r in live_runs(client) if r.get("status") == "passed"], 60)
        time.sleep(3)
        runs = live_runs(client)
        explained = reply(log, "explain", client.get(f"/api/triggers/{trigger['id']}/explain"))
    log.check("trigger home is pc (no server yet)", trigger.get("home_engine") == "pc", trigger)
    log.check("a delivery without an id is refused", bare.status_code == 400, bare.status_code)
    log.check(
        "the second post is a duplicate of the first fire",
        (first.get("duplicate"), second.get("duplicate"), first["fire_id"] == second["fire_id"])
        == (False, True, True),
        (first.get("duplicate"), second.get("duplicate")),
    )
    log.check(
        "exactly one live run started, and it passed",
        ran is not None and [(r["status"]) for r in runs] == ["passed"],
        [(r["run_id"], r["status"]) for r in runs],
    )
    fires = explained.get("fires") or []
    log.check(
        "the trigger has one fire, delivered",
        [(f["status"], f["delivery"]) for f in fires] == [("ok", "delivered")],
        fires,
    )


def settings_toml(root: Path, paused: bool) -> None:
    (root / "settings.toml").write_text(
        dedent(
            f"""
            [engine.scheduler]
            tick = 5

            [engine.autonomy]
            paused = {"true" if paused else "false"}
            """
        ),
        encoding="utf-8",
    )


def pause(log: Log) -> None:
    root = home("pause")
    settings_toml(root, paused=True)
    with started_host(log, root) as (client, _, _):
        published_chain(log, client, "paused")
        made = []
        for n in range(3):
            body = {"kind": "cron", "expr": "* * * * *", "zone": "UTC"}
            trigger = reply(
                log,
                f"cron {n}",
                client.post("/api/triggers", params={"workflow_id": "paused"}, json=body),
            )
            reply(log, f"enable {n}", client.post(f"/api/triggers/{trigger['id']}/enable"))
            made.append(trigger["id"])
        now = datetime.now(UTC)
        wake = now.replace(second=0, microsecond=0) + timedelta(minutes=2, seconds=3) - now
        log(f"paused; waiting {wake.total_seconds():.0f} s across two minute occurrences")
        time.sleep(wake.total_seconds())
        while_paused = [
            reply(log, f"explain {t} paused", client.get(f"/api/triggers/{t}/explain"))
            for t in made
        ]
        paused_runs = live_runs(client)
        settings_toml(root, paused=False)
        log("cleared autonomy.paused in settings.toml")
        wait_for(
            lambda: all(
                any(
                    f["status"] == "ok"
                    for f in client.get(f"/api/triggers/{t}/explain").json()["fires"]
                )
                for t in made
            ),
            40,
        )
        after = [
            reply(log, f"explain {t} cleared", client.get(f"/api/triggers/{t}/explain"))
            for t in made
        ]
        cleared_runs = live_runs(client)
    log.check(
        "nothing fired while paused: no fire rows and no live run",
        all(not d["fires"] for d in while_paused) and not paused_runs,
        [len(d["fires"]) for d in while_paused],
    )
    log.check(
        "explain_trigger said paused on every trigger",
        all(str(d["verdict"]).startswith("paused: autonomy.paused is set") for d in while_paused),
        while_paused[0]["verdict"],
    )
    ran = [[f for f in d["fires"] if f["run_id"]] for d in after]
    log.check(
        "after clearing, each trigger fired exactly once and passed",
        [[f["status"] for f in fires] for fires in ran] == [["ok"]] * 3 and len(cleared_runs) == 3,
        [[(f["occurrence_at"][11:19], f["status"]) for f in d["fires"]] for d in after],
    )


def timed_bundle(root: Path) -> Any:
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415

    document = {
        "schema": "qmx.workflow/1",
        "id": "timed",
        "name": "timed",
        "nodes": [
            {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1,
             "parameters": {"kinds": ["manual"]}},
            {"id": "work", "name": "Work", "type": "script", "typeVersion": 1,
             "parameters": {"script": "scripts/timed.py"}},
        ],
        "connections": {"Start": {"main": [[{"node": "Work", "port": "in", "map": "one"}]]}},
    }  # fmt: skip
    (root / "scripts").mkdir(parents=True)
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    (root / "scripts" / "timed.py").write_text(dedent(TIMED), encoding="utf-8")
    return Bundle.read(root)


def priority(log: Log) -> None:
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415
    from qmx_engine.ports.settings import StaticSettings  # noqa: PLC0415
    from qmx_engine.service.api import EngineService  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.settings import DEFAULTS  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415
    from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415

    root = home("priority")
    bundle = timed_bundle(root / "folder")
    settings = StaticSettings({**DEFAULTS, "placement.pc.cpu_slots": 1})
    with EngineService.open(root / "home", settings=settings) as svc:
        version = publish(svc, bundle)
        ledger = svc.ctx.engine.ledger

        def manual(rank: int) -> Any:
            return rows.create(
                ledger, workflow_item="timed", pinned_object=version, spec=rows.Manual(),
                caller=OPERATOR, now=svc.ctx.clock.now(), priority=rank,
            )  # fmt: skip

        blocker, low, high = manual(0), manual(1), manual(5)
        ticker = Scheduler(svc.ctx)

        async def go() -> list[int]:
            rows.fire_now(ledger, blocker.id, svc.ctx.clock.now(), {"seconds": 2})
            await ticker.tick()
            await asyncio.sleep(0.6)
            rows.fire_now(ledger, low.id, svc.ctx.clock.now(), {"seconds": 0.2})
            await asyncio.sleep(0.05)
            rows.fire_now(ledger, high.id, svc.ctx.clock.now(), {"seconds": 0.2})
            tick = await ticker.tick()
            await ticker.settle()
            return [c.trigger.priority for c in tick.claimed]

        order = asyncio.run(go())
        with Reader.open(root / "home") as reader:
            stored = {t.id: t for t in rows.triggers(reader.connection)}
    began = {
        name: next(iter(stored[t.id].last_outputs.values()))["main"][0]
        for name, t in (("blocker", blocker), ("priority 1", low), ("priority 5", high))
    }
    log(f"claim order by priority {order}; script start times {began}")
    log.check("the tick claimed priority 5 before priority 1", order == [5, 1], order)
    log.check(
        "the priority 5 fire's script started first, though it was fired last",
        began["blocker"] < began["priority 5"] < began["priority 1"],
        f"{began['priority 1'] - began['priority 5']:.2f} s ahead",
    )


def market(log: Log) -> None:
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415
    from qmx_engine.service.api import EngineService  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415
    from qmx_engine.triggers.cron import Cron  # noqa: PLC0415
    from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415

    root = home("market")
    clock = Clock(SATURDAY)
    with EngineService.open(root, clock=clock) as svc:
        version = publish(svc, Bundle.read(CHAIN))
        trigger = rows.create(
            svc.ctx.engine.ledger, workflow_item="script-chain", pinned_object=version,
            spec=Cron("0 * * * *", "Europe/London"), caller=OPERATOR, now=clock.now(),
            precheck_ref="market_open",
        )  # fmt: skip
        ticker = Scheduler(svc.ctx)

        async def tick() -> None:
            await ticker.tick()
            await ticker.settle()

        clock.current = SATURDAY + timedelta(hours=1)
        asyncio.run(tick())
        saturday = ticker.explain(trigger.id)
        clock.current = datetime(2026, 10, 18, 23, 0, 30, tzinfo=UTC)
        asyncio.run(tick())
        monday = ticker.explain(trigger.id)
        with Reader.open(root) as reader:
            every = rows.fires(reader.connection, trigger.id)
    for line in json.dumps(saturday, indent=1).splitlines():
        log(f"  {line}")
    held = saturday["fires"][0]
    log.check(
        "the Saturday 11:00 London fire is held until Monday 00:00 London",
        (held["status"], held["run_id"]) == ("held", None)
        and held["detail"]
        == "the market is shut in Europe/London until 2026-10-18T23:00:00.000000+00:00",
        held,
    )
    log.check(
        "explain_trigger says why",
        saturday["verdict"]
        == "held: the market is shut in Europe/London until 2026-10-18T23:00:00.000000+00:00",
        saturday["verdict"],
    )
    ran = [f for f in every if f.status == "ok"]
    merged = [f for f in every if f.status == "merged"]
    log(f"monday verdict: {monday['verdict']}")
    log.check(
        "the held fire runs once the market opens, carrying the merged occurrences",
        [(f.id, f.merged) for f in ran] == [(held["fire_id"], len(merged))] and len(merged) > 30,
        [(f.occurrence_at[:16], f.status, f.merged, f.delivery) for f in ran],
    )


def rerun(log: Log) -> None:
    from qmx_engine.ledger.inbox_table import InboxTable  # noqa: PLC0415
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415
    from qmx_engine.service.api import EngineService  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415
    from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415

    root = home("rerun")
    chain = Bundle.read(CHAIN)
    bundle = Bundle(
        chain.definition, {**chain.files, "scripts/numbers.py": dedent(FAILING).encode()}
    )
    clock = Clock(MONDAY)
    with EngineService.open(root, clock=clock) as svc:
        version = publish(svc, bundle)
        trigger = rows.create(
            svc.ctx.engine.ledger, workflow_item="script-chain", pinned_object=version,
            spec=rows.Manual(), caller=OPERATOR, now=clock.now(),
        )  # fmt: skip
        ticker = Scheduler(svc.ctx)

        async def go() -> list[str]:
            seen = []
            await ticker.run_now(trigger.id)
            await ticker.settle()
            for minutes in (4, 5, 6, 14, 15, 16):
                clock.current = MONDAY + timedelta(minutes=minutes, seconds=1)
                tick = await ticker.tick()
                await ticker.settle()
                seen.append(f"{minutes} min: claimed {len(tick.claimed)}")
            return seen

        for line in asyncio.run(go()):
            log(line)
        explained = ticker.explain(trigger.id)
        with InboxTable.open(root) as table:
            incident = table.open_incident(trigger.id)
    fires = list(reversed(explained["fires"]))
    for fire in fires:
        at = fire["occurrence_at"][11:19]
        log(f"fire {at} {fire['status']} rerun={fire['rerun']} {fire['detail']}")
    log(f"incident {incident}")
    log.check(
        "the failed fire re-ran at 5 and 15 minutes, and the 30 minute re-run is held",
        [(f["occurrence_at"][11:16], f["status"]) for f in fires]
        == [("09:00", "failed"), ("09:05", "failed"), ("09:15", "failed"), ("09:30", "held")],
        [(f["occurrence_at"][11:16], f["status"]) for f in fires],
    )
    log.check(
        "each failure delivered its [QMX_FAILURE] line",
        all(f["delivery"] == "delivered" for f in fires if f["status"] == "failed"),
        [f["delivery"] for f in fires],
    )
    log.check(
        "the three failures are one incident of one signature",
        incident is not None
        and incident.count == 3
        and explained["incident"] is not None
        and explained["incident"]["id"] == incident.id,
        None if incident is None else (incident.id, incident.count),
    )


def catchup(log: Log) -> None:
    done = run(
        log,
        [sys.executable, str(Path(__file__).with_name("e06_catchup.py"))],
        AGENTS,
        ENGINE_LOG_PREFIX="trg2a-owner-",
    )
    log.check("e06_catchup passes at head", done.returncode == 0, done.returncode)


def migrate(log: Log, parent: Path) -> None:
    from qmx_engine.ledger.store import Ledger, Reader  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415

    python = parent / "qmx-agents" / ".venv" / "Scripts" / "python.exe"
    script = parent / "scripts" / "live" / "engine" / "e06_catchup.py"
    made = run(
        log, [str(python), str(script)], parent / "qmx-agents", ENGINE_LOG_PREFIX="trg2a-parent-"
    )
    log.check("the parent's e06 made its ledger", made.returncode == 0, made.returncode)
    source = Path("D:/QMX-worktrees/qma-ship/engine/homes/ep12-e06")
    root = home("migrate")
    shutil.copytree(source, root, dirs_exist_ok=True)
    db = root / "engine" / "engine.sqlite"

    def snapshot() -> dict[str, list[tuple[Any, ...]]]:
        with sqlite3.connect(db) as connection:
            return {
                "events": connection.execute(
                    "SELECT run_id, seq, kind, data FROM events"
                ).fetchall(),
                "triggers": connection.execute(
                    "SELECT id, kind, spec, next_fire_at, last_status FROM triggers"
                ).fetchall(),
                "fires": connection.execute(
                    "SELECT id, occurrence_at, status, detail, run_id FROM fires"
                ).fetchall(),
                "wakes": connection.execute("SELECT * FROM wakes").fetchall(),
                "version": connection.execute(
                    "SELECT value FROM meta WHERE key = 'schema_version'"
                ).fetchall(),
            }

    before = snapshot()
    with Ledger.open(root) as ledger:
        applied = ledger.applied
        rows.create(
            ledger, workflow_item="wf", pinned_object="obj", spec=rows.Webhook(),
            caller=OPERATOR, now=MONDAY,
        )  # fmt: skip
    after = snapshot()
    with Reader.open(root) as reader:
        kinds = sorted(t.kind for t in rows.triggers(reader.connection))
    log(f"before: { {k: len(v) for k, v in before.items()} } version {before['version']}")
    log(f"after: { {k: len(v) for k, v in after.items()} } version {after['version']}")
    log.check("the parent's ledger was at schema 2 and step 3 applied", applied == [3], applied)
    log.check(
        "every old event, fire and wake row survives unchanged",
        all(before[k] == after[k] for k in ("events", "fires", "wakes")),
        {k: (len(before[k]), len(after[k])) for k in ("events", "fires", "wakes")},
    )
    log.check(
        "the old trigger survives and a webhook trigger now stores beside it",
        after["triggers"][: len(before["triggers"])] == before["triggers"]
        and kinds == ["cron", "webhook"],
        kinds,
    )


def secrets(log: Log) -> None:
    done = run(log, [UV, "run", "--no-sync", "python", "../tools/secret_scan.py"], AGENTS)
    log.check(
        "secret scan is clean", done.returncode == 0 and "clean" in done.stdout, done.returncode
    )


def processes(log: Log) -> None:
    import psutil  # noqa: PLC0415

    found = []
    for process in psutil.process_iter(["name", "cmdline"]):
        name = (process.info["name"] or "").lower()
        line = " ".join(process.info["cmdline"] or [])
        if name.startswith(("claude", "qma-cli-launcher")) or "qmx_host" in line:
            found.append((process.pid, name, line[:120]))
    for row in found:
        log(f"  {row}")
    log.check("no qmx_host, claude or qma-cli-launcher process is left", not found, len(found))
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK.exists())


def perf_child(root: Path) -> None:
    """Ten ticks over 500 cron rows on this checkout's engine; prints the tick times in ms."""
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415
    from qmx_engine.service.api import EngineService  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415
    from qmx_engine.triggers.cron import Cron  # noqa: PLC0415
    from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415

    clock = Clock(MONDAY)
    with EngineService.open(root, clock=clock) as svc:
        version = publish(svc, Bundle.read(CHAIN))
        for n in range(500):
            rows.create(
                svc.ctx.engine.ledger, workflow_item="script-chain", pinned_object=version,
                spec=Cron(f"{n % 60} 3 * * *", "Europe/London"), caller=OPERATOR, now=clock.now(),
            )  # fmt: skip
        ticker = Scheduler(svc.ctx)

        async def ten() -> list[float]:
            times = []
            for n in range(10):
                clock.current = MONDAY + timedelta(minutes=n)
                began = time.perf_counter()
                await ticker.tick()
                times.append((time.perf_counter() - began) * 1000)
            return times

        print(json.dumps(asyncio.run(ten())))


def perf(log: Log, parent: Path) -> None:
    medians = {}
    for name, python in (
        ("parent", parent / "qmx-agents" / ".venv" / "Scripts" / "python.exe"),
        ("head", Path(sys.executable)),
    ):
        root = home(f"perf-{name}")
        done = subprocess.run(
            [str(python), __file__, "perf-child", "--root", str(root)],
            cwd=Path(__file__).parent, env=clean_env(), capture_output=True, text=True, check=False,
        )  # fmt: skip
        if done.returncode != 0:
            log(done.stderr[-2000:])
        times = json.loads(done.stdout.strip().splitlines()[-1])
        medians[name] = statistics.median(times)
        log(f"{name}: tick ms {[round(t, 1) for t in times]}, median {medians[name]:.1f}")
    log(
        f"PERF tick with 500 trigger rows: parent {medians['parent']:.1f} ms,"
        f" head {medians['head']:.1f} ms (recorded, not gated)"
    )


LANES: Final = ("regression", "webhook", "pause", "priority", "market", "rerun", "catchup",
                "migrate", "secrets", "processes", "perf")  # fmt: skip


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("lane", choices=(*LANES, "perf-child"))
    cli.add_argument("--parent-tree", type=Path, default=Path("D:/Temp/trg2a-parent"))
    cli.add_argument("--root", type=Path)
    args = cli.parse_args()
    if args.lane == "perf-child":
        perf_child(args.root)
        return 0
    log = TrgLog(args.lane)
    match args.lane:
        case "regression" | "migrate" | "perf":
            {"regression": regression, "migrate": migrate, "perf": perf}[args.lane](
                log, args.parent_tree
            )
        case _:
            globals()[args.lane](log)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
