"""OPS1's live lanes: one heartbeat row per interval from `qmx_host` and its apps (AD-65).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/host/ops1_lanes.py [--parent TREE] [lane ...]`
Lanes are `regression rows skew ops incident logs secrets processes`; none named runs every lane
but `regression` and `ops`. Each writes `evidence/ops1/<ENGINE_LOG_PREFIX>ops1-<lane>.log`, and
the script exits 1 when a check failed.

- `regression` (lane 1): the qmx-engine, qmx-apps and qmx-host suites with `-n 2` at `--parent`
  and here. Pass when head fails nothing the parent passes.
- `rows` (lanes 2, 6, 8 and the perf block): `qmx_host` on a throwaway home with the fixture app
  started and a workflow test run sleeping in a script node, for five minutes. Pass when ten
  host rows and the app's rows are in the log in the one schema, every row is at most 4 KB, and
  a row written after `autonomy.paused` is set shows it. Perf: the CPU seconds of one beat (rows
  built and written, as the host's loop does) over the interval, as a share of one core.
- `skew` (lane 3): a fire of a workflow whose node runs on `contabo`, while contabo's newest
  heartbeat lacks that node's kind. Pass when the fire waits `placement` with `node needs update`.
- `ops` (lane 4): `qmx_host` on the ship home under the lane lock; a haiku chat asked what is
  running here. Pass when it called `mcp__qmx_ops__heartbeats` in this turn and its answer cites
  the newest host row. The ship home's `settings.toml` hashes the same before and after.
- `incident` (lane 5): a consumer refuses a producer's output; the incident is filed on the
  producer with class `dependency`.
- `logs` (lane 7): rows written over nine days on a fake clock; pruning leaves none older than
  the seven-day window.
- `secrets` (lane 9): `tools/secret_scan.py` is clean.
- `processes` (lane 10): no `qmx_host`, app, `claude` or `qma-cli-launcher` process from these
  lanes and no lane lock is left.

No key and no money act. Only `ops` opens the ship home, through `lane_host.py` with a bearer
made for the run, so the operator's control token is never read.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Final

ENGINE_LANES: Final = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE_LANES))

import httpx  # noqa: E402
import psutil  # noqa: E402
from common import SHIP_HOME, boot, lane_lock  # noqa: E402
from common import Log as EngineLog  # noqa: E402
from ep2_lanes import AGENTS, ENGINE, clean_env  # noqa: E402
from lane_host import BEARER_ENV  # noqa: E402
from x13_doors import LANE_HOST, free_port, healthy, host, kill_tree  # noqa: E402

PR: Final = "ops1"
STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
PREFIX: Final = os.environ.get("ENGINE_LOG_PREFIX", "")
"""Read before `boot()`, which scrubs the environment."""
REPO: Final = Path(__file__).resolve().parents[3]
APP: Final = "exchange-status"
ITEM: Final = "ops1-sleeper"
RUN_S: Final = 300.0
SLEEP_S: Final = 330
INTERVAL_S: Final = 30.0
ROW_LIMIT: Final = 4_096
CORE_LIMIT: Final = 0.01
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
SUITES: Final = ("qmx-engine", "qmx-apps", "qmx-host")
OPS_TOOL: Final = "mcp__qmx_ops__heartbeats"
ASK: Final = (
    f"Call {OPS_TOOL} once. Then say in two short sentences what is running on this machine and "
    "how loaded it is, and quote the newest host row's `at` time exactly as the tool returned it."
)


class Log(EngineLog):
    """`Log` writing to this PR's evidence folder in the build store."""

    def __init__(self, slug: str) -> None:
        folder = STORE / "evidence" / PR
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{PREFIX}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def throwaway_home(slug: str) -> Path:
    root = STORE / "homes" / f"{PR}-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def sleeper() -> dict[str, Any]:
    definition = {
        "schema": "qmx.workflow/1",
        "id": ITEM,
        "name": "OPS1 sleeper",
        "nodes": [
            {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1,
             "parameters": {"kinds": ["manual"]}},
            {"id": "sleep", "name": "Sleep", "type": "script", "typeVersion": 1,
             "parameters": {"script": "scripts/sleep.py"}},
        ],
        "connections": {"Start": {"main": [[{"node": "Sleep", "port": "in", "map": "one"}]]}},
    }  # fmt: skip
    script = (
        f"import json, time\ntime.sleep({SLEEP_S})\nprint(json.dumps({{'slept': {SLEEP_S}}}))\n"
    )
    return {"definition": definition, "files": {"scripts/sleep.py": script}}


def fixture_app(root: Path) -> Path:
    target = root / "app-source"
    shutil.copytree(
        REPO / "examples/apps" / APP, target, ignore=shutil.ignore_patterns(".venv", "__pycache__")
    )
    shutil.copyfile(AGENTS / "packages/qmx-apps/tests/fixture_server.py", target / "server.py")
    return target


def rows_of(home: Path) -> list[Any]:
    from qmx_engine.heartbeat import HeartbeatLog  # noqa: PLC0415

    return HeartbeatLog(home, 7).rows()


def until[T](predicate: Callable[[], T | None], seconds: float, every: float = 1.0) -> T | None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if (found := predicate()) is not None:
            return found
        time.sleep(every)
    return None


def beat_share(home: Path) -> float:
    """CPU seconds of one beat, as the host's loop does it (the host row and one app row built,
    written and the newest-row file replaced), over the interval."""
    from qma.harness.harness import SlotTable  # noqa: PLC0415
    from qmx_engine.admission import Capacity  # noqa: PLC0415
    from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, kinds_digest  # noqa: PLC0415
    from qmx_engine.settings import DEFAULTS  # noqa: PLC0415
    from qmx_host.host import beat  # noqa: PLC0415

    engine = SimpleNamespace(worker=SimpleNamespace(capacity=Capacity.of(DEFAULTS)), paused=False)
    table = SlotTable(capacity=4, reserve=1, held=(), unattended=(), waiting=())
    harness = SimpleNamespace(slot_table=lambda: table)
    log = HeartbeatLog(home, 7)
    me = psutil.Process()
    app = {"subject": "app", "id": APP, "cpu_seconds": 1.0, "rss_bytes": 1, "machine_minutes": 1}
    beats = 20
    started = time.process_time()
    for _ in range(beats):
        row = beat(home, "pc", me, engine, harness)  # pyright: ignore[reportArgumentType]
        extra = {"at": row.at, "qmx_version": row.qmx_version, "paused": False}
        app_row = Heartbeat.model_validate({**app, **extra, "kinds_digest": kinds_digest(())})
        log.write([row, app_row])
    return (time.process_time() - started) / beats / INTERVAL_S


def lane_rows(log: Log) -> None:
    from qmx_control import ControlService  # noqa: PLC0415

    home = throwaway_home("rows")
    control = ControlService(home)
    try:
        control.apps_create(str(fixture_app(home)), trust="first_party")
    finally:
        control.close()
    with host(log, home) as (client, process, _):
        started = client.post(f"/api/apps/{APP}/start", timeout=300)
        log(f"app start: http {started.status_code} {started.text[:200]}")
        saved = client.put(f"/api/workflows/{ITEM}/draft", json=sleeper()).json()
        log(f"draft {ITEM}: {saved.get('state')} revision {saved.get('revision')}")

        def test() -> None:
            with contextlib.suppress(httpx.HTTPError):
                client.post(f"/api/workflows/{ITEM}/test", timeout=SLEEP_S + 120)

        threading.Thread(target=test, daemon=True).start()
        began = time.monotonic()
        running = until(
            lambda: next(
                (
                    r
                    for r in client.get("/api/workflow-runs", params={"workflow_id": ITEM}).json()
                    if r.get("status") == "running"
                ),
                None,
            ),
            60,
        )
        log(f"workflow run running: {None if running is None else running.get('run_id')}")
        time.sleep(max(0.0, RUN_S - (time.monotonic() - began)) + 5)
        status = client.get(f"/api/apps/{APP}").json()
        log(f"app status after five minutes: {status.get('status')}")
        found = rows_of(home)
        hosts = [r for r in found if r.subject == "host"]
        apps = [r for r in found if r.subject == "app" and r.id == APP]
        log(f"rows: {len(hosts)} host, {len(apps)} app over {RUN_S:.0f} s; pid {process.pid}")
        log(f"newest host row: {hosts[-1].model_dump_json() if hosts else None}")
        log(f"newest app row: {apps[-1].model_dump_json() if apps else None}")
        log.check("ten host rows in five minutes", len(hosts) >= 10, len(hosts))
        log.check("the app wrote rows in the same schema", len(apps) >= 9, len(apps))
        log.check(
            "the running workflow shows in the host row's capacity",
            running is not None and any(r.capacity["cpu"].used > 0 for r in hosts),
            [r.capacity["cpu"].used for r in hosts],
        )
        sizes = [len(r.model_dump_json().encode()) for r in found]
        log.check("lane 6: every row is at most 4 KB", max(sizes) <= ROW_LIMIT, f"max {max(sizes)}")
        client.put("/api/settings/engine", json={"autonomy": {"paused": True}})
        put_at = datetime.now(UTC)
        paused = until(
            lambda: next((r for r in rows_of(home) if r.subject == "host" and r.paused), None),
            INTERVAL_S * 3,
        )
        log.check(
            "lane 8: a row written while paused shows the flag",
            paused is not None and datetime.fromisoformat(paused.at) >= put_at,
            None if paused is None else paused.at,
        )
        client.put("/api/settings/engine", json={"autonomy": {"paused": False}})
    share = beat_share(throwaway_home("perf"))
    log(f"PERF heartbeat work {share * 100:.4f} % of one core (P-OPS PC 0.0408 %, line 1 %)")
    log.check("perf: heartbeat work under 1 % of one core", share < CORE_LIMIT, f"{share:.6f}")


def lane_skew(log: Log) -> None:
    sys.path.insert(0, str(ENGINE / "tests"))
    import asyncio  # noqa: PLC0415

    from qmx_engine.heartbeat import (  # noqa: PLC0415
        Heartbeat,
        HeartbeatLog,
        kinds_digest,
        node_kinds,
    )
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415
    from qmx_engine.triggers import rows  # noqa: PLC0415
    from qmx_engine.triggers.cron import Cron  # noqa: PLC0415
    from qmx_engine.triggers.ticker import Scheduler  # noqa: PLC0415
    from scheduled import Clock, enabled, fires_of  # noqa: PLC0415

    home = throwaway_home("skew")
    chain = Bundle.read(ENGINE / "tests/fixtures/workflows/script-chain")
    nodes = [
        n | {"runs_on": "contabo"} if n["name"] == "Numbers" else n
        for n in chain.definition["nodes"]
    ]
    bundle = Bundle(chain.definition | {"nodes": nodes}, chain.files)
    clock = Clock(datetime(2026, 10, 17, 9, 0, tzinfo=UTC))
    with enabled(home, clock, bundle) as (svc, version):
        stale = tuple(k for k in node_kinds() if k != "script")
        old = Heartbeat(
            subject="host", id="contabo", at=clock.now().isoformat(), cpu_seconds=0.0,
            rss_bytes=0, machine_minutes=0.0, qmx_version="0.0.9", node_kinds=stale,
            kinds_digest=kinds_digest(stale), paused=False,
        )  # fmt: skip
        HeartbeatLog(home, 7).write([old])
        log(f"contabo's heartbeat: version {old.qmx_version}, kinds {list(stale)}")
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=Cron("0 * * * *", "UTC"),
            caller=OPERATOR,
            now=clock.now(),
        )
        clock.move(hours=1)
        ticker = Scheduler(svc.ctx)

        async def go() -> None:
            await ticker.tick()
            await ticker.settle()

        asyncio.run(go())
        found = fires_of(home, trigger.id)
        explained = ticker.explain(trigger.id)
    seen = [(f.status, f.detail, f.run_id) for f in found]
    log(f"fires: {seen}")
    log(f"explain verdict: {explained.get('verdict')}")
    log.check(
        "the fire waits placement with node needs update",
        len(found) == 1
        and found[0].status == "held"
        and (found[0].detail or "").startswith(
            "placement: node needs update (Numbers: contabo lacks script)"
        )
        and found[0].run_id is None,
        seen,
    )


def settings_sha() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


def tool_calls(client: httpx.Client, chat: str, after: int) -> tuple[list[str], str, int]:
    """Tool names and the text of this turn's blocks: every session event past `after`."""
    events = client.get(f"/api/sessions/{chat}/events", params={"after": after, "limit": 1000})
    names: list[str] = []
    text: list[str] = []
    last = after
    for event in events.json():
        last = max(last, int(event["id"]))
        block = event.get("data", {}).get("block") or {}
        content = block.get("content", {})
        if block.get("type") == "tool" and content.get("name"):
            names.append(str(content["name"]))
        if block.get("type") == "text":
            text.append(str(content.get("text", "")))
    return names, "".join(text), last


def lane_ops(log: Log) -> None:
    if not LANE_LOCK.is_dir():
        raise SystemExit(f"the ops lane runs only while holding {LANE_LOCK}")
    before = settings_sha()
    bearer = secrets.token_urlsafe(32)
    port = free_port()
    headers = {"Authorization": f"Bearer {bearer}"}
    out = (log.path.parent / f"{log.path.stem}-host.out").open("wb")
    command = [sys.executable, str(LANE_HOST), "qmx_host", "serve", "--home", str(SHIP_HOME)]
    process = subprocess.Popen(
        [*command, "--port", str(port)],
        cwd=AGENTS,
        env=clean_env(**{BEARER_ENV: bearer}),
        stdout=out,
        stderr=out,
    )
    try:
        if until(lambda: healthy(port, headers), 120, 0.2) is None:
            raise SystemExit("qmx_host did not start on the ship home")
        log(f"qmx_host pid {process.pid} on the ship home, port {port}")
        client = httpx.Client(base_url=f"http://127.0.0.1:{port}", headers=headers, timeout=120)
        time.sleep(INTERVAL_S + 5)
        workspace = Path("D:/Temp/ops1-ops-ws")
        workspace.mkdir(parents=True, exist_ok=True)
        made = client.post(
            "/api/chats",
            json={"title": "OPS1 ops", "model": "haiku", "profile": "claude",
                  "workspace": str(workspace)},
        ).json()  # fmt: skip
        chat = made["session_id"]
        _, _, after = tool_calls(client, chat, 0)
        log(f"chat {chat} on claude/haiku; events before the turn end at seq {after}")
        client.post(f"/api/sessions/{chat}/turns", json={"text": ASK})
        time.sleep(2)
        idle = until(
            lambda: True if client.get(f"/api/chats/{chat}").json().get("turn") == "idle" else None,
            300,
        )
        names, answer, _ = tool_calls(client, chat, after)
        from qmx_engine.heartbeat import latest  # noqa: PLC0415

        newest = latest(SHIP_HOME).get("host:pc")
        log(f"turn idle: {idle}; tools this turn: {names}")
        log(f"answer: {answer[:600]!r}")
        log(f"newest host row at {None if newest is None else newest.at}")
        log.check("the chat called ops_heartbeats in this turn", OPS_TOOL in names, names)
        stamps = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", answer)
        cited = [s for s in stamps if any(r.at.startswith(s) for r in rows_of(SHIP_HOME))]
        log.check("the answer quotes a host row's time", bool(cited), stamps)
        log.check(
            "the answer speaks to the capacity queue",
            bool(re.search(r"slot|capacity|queue|waiting|cpu|load", answer, re.IGNORECASE)),
            answer[:120],
        )
        client.close()
    finally:
        kill_tree(process.pid)
        out.close()
    after_sha = settings_sha()
    log.check("the ship home's settings.toml is unchanged", before == after_sha, after_sha[:12])


def lane_incident(log: Log) -> None:
    from qmx_engine.ledger.inbox_table import InboxTable  # noqa: PLC0415

    home = throwaway_home("incident")
    with InboxTable.open(home) as inbox:
        inbox.refused_output("digest", APP, "snapshot", "observations[0].status is 'up'", at="t1")
        found = inbox.app_incidents()
    log(f"app incidents: {[(i.app_id, i.kind, i.title, i.count) for i in found]}")
    log.check(
        "the refusal is filed on the producer with class dependency",
        [(i.app_id, i.kind) for i in found] == [(APP, "dependency")],
        [(i.app_id, i.kind) for i in found],
    )


def lane_logs(log: Log) -> None:
    from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, kinds_digest  # noqa: PLC0415

    home = throwaway_home("logs")
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    beats = HeartbeatLog(home, 7)
    rows = [
        Heartbeat(
            subject="host", id="pc", at=(now - timedelta(hours=h)).isoformat(), cpu_seconds=0.0,
            rss_bytes=0, machine_minutes=0.0, qmx_version="0.1.0", kinds_digest=kinds_digest(()),
            paused=False,
        )
        for h in range(0, 9 * 24, 6)
    ]  # fmt: skip
    beats.write(rows)
    gone = beats.prune(now)
    kept = beats.rows()
    oldest = min(datetime.fromisoformat(r.at) for r in kept)
    log(f"{len(rows)} rows over nine days; pruned {gone}; kept {len(kept)}; oldest {oldest}")
    log.check("no row older than seven days is left", oldest >= now - timedelta(days=7), oldest)
    log.check("rows inside the window stay", len(kept) == 29, len(kept))


def lane_secrets(log: Log) -> None:
    done = subprocess.run(
        [sys.executable, "tools/secret_scan.py"], cwd=REPO, capture_output=True, text=True
    )
    log(f"secret_scan exit {done.returncode}: {(done.stdout + done.stderr).strip()[-400:]}")
    log.check("secret scan is clean", done.returncode == 0, done.returncode)


def desktop_app(process: psutil.Process) -> bool:
    """The Claude desktop app or a session it runs, the operator's and never a lane's."""
    for member in [process, *process.parents()]:
        with contextlib.suppress(psutil.Error):
            if "WindowsApps" in member.exe() and member.name().lower() == "claude.exe":
                return True
    return False


def lane_processes(log: Log) -> None:
    names = ("claude", "qma-cli-launcher")
    left = []
    for process in psutil.process_iter(["name", "cmdline"]):
        with contextlib.suppress(psutil.Error):
            if desktop_app(process):
                continue
            line = " ".join(process.info["cmdline"] or [])
            name = (process.info["name"] or "").lower()
            ours = "homes" in line and "ops1-" in line
            if (
                any(n in name for n in names)
                or ("qmx_host" in line and (ours or "qma-ship" in line))
                or ours
            ):
                left.append((process.pid, name, line[:120]))
    log(f"left: {left}")
    log.check("no host, app, claude or launcher process is left", left == [], left)
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK.exists())


def lane_regression(log: Log, parent: Path) -> None:
    def suite(tree: Path, package: str) -> tuple[set[str], str]:
        done = subprocess.run(
            [str(tree / "qmx-agents/.venv/Scripts/python.exe"), "-m", "pytest", "-n", "2", "-q",
             "-p", "no:cacheprovider", "-rf"],
            cwd=tree / "qmx-agents/packages" / package, env=clean_env(PYTHONIOENCODING="utf-8"),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )  # fmt: skip
        out = done.stdout + done.stderr
        failed = set(re.findall(r"^(?:FAILED|ERROR) (\S+)", out, re.MULTILINE))
        summary = next((ln for ln in reversed(out.splitlines()) if " in " in ln), "")
        return failed, summary

    for package in SUITES:
        base, base_line = suite(parent, package)
        head, head_line = suite(REPO, package)
        log(f"{package} parent: {base_line} {sorted(base)}")
        log(f"{package} head:   {head_line} {sorted(head)}")
        log.check(f"{package}: head fails nothing the parent passes", head <= base, head - base)


LANES: Final = ("rows", "skew", "incident", "logs", "secrets", "processes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lanes", nargs="*")
    parser.add_argument("--parent", type=Path, default=Path("D:/Temp/ops1-parent"))
    args = parser.parse_args()
    boot()
    passed = True
    for lane in args.lanes or LANES:
        log = Log(f"ops1-{lane}")
        match lane:
            case "regression":
                lane_regression(log, args.parent)
            case "ops":
                with lane_lock(log):
                    lane_ops(log)
            case _:
                globals()[f"lane_{lane}"](log)
        passed &= log.verdict() == 0
    os.environ.pop(BEARER_ENV, None)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
