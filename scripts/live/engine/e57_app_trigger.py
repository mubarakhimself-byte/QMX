"""E57 trigger clause and the RUN1a lanes: an app's schedule is an engine trigger on an `app_op`
workflow, the supervisor schedules nothing, and the control's run index never shows a chat journal.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e57_app_trigger.py [lane]`
Lanes are `e57 runs stopped breaker grep heartbeat`; none named runs all. `baseline` runs only when
named, from the parent commit's venv, because it needs the parent's own scheduler. Each lane writes
`D:/QMX-worktrees/qma-ship/build/evidence/run1a/<ENGINE_LOG_PREFIX>run1a-<lane>.log` and the script
exits 1 when a check failed. No model, no key, no ship home: a fixture app (the exchange-status
example with the supervisor test server and one job) on throwaway homes under the store's `homes/`.

- `e57`: his enable creates one interval trigger (60 s) on `<app>-schedule`; within three minutes
  it fires twice, each fire is an engine run whose `app_op` node ran the job in the app's process,
  and those runs are in the engine's run list. Perf: seconds from each fire's due time to its
  `app_op` start, with `scheduler.tick` at 10 s (his setting; the default is 60 s).
- `runs`: a chat journal under `runs/` and a remote run journal; the control's run index shows only
  the remote run.
- `stopped`: the app stops, then its trigger fires; the run fails with the supervisor's reason.
- `breaker`: a job that raises, run three times; the crash breaker still trips.
- `grep`: no interval scheduling or usage budget is left in the supervisor or its bootstrap.
- `heartbeat`: a running app still reports CPU seconds, RSS and a fresh heartbeat.
- `baseline`: the parent's supervisor with a 5 s `[schedule]`; seconds each job run came after
  its nominal interval.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import os
import shutil
import stat
import sys
import threading
import time
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "run1a"
REPO: Final = Path(__file__).resolve().parents[3]
APP: Final = "exchange-status"
ITEM: Final = f"{APP}-schedule"
COUNTER: Final = (
    "import json, time\n"
    "from pathlib import Path\n"
    "def run():\n"
    "    path = Path('data/job-runs.jsonl')\n"
    "    with path.open('a') as out:\n"
    "        out.write(json.dumps({'at': time.time()}) + '\\n')\n"
)
RAISES: Final = "def run():\n    raise RuntimeError('fixture job failure')\n"
WINDOW_S: Final = 180.0
POLL_S: Final = 1.0


class Log:
    def __init__(self, lane: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}run1a-{lane}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def writable(remove: Callable[..., Any], path: str, _: object) -> None:
    os.chmod(path, stat.S_IWRITE)
    remove(path)


def home(lane: str) -> Path:
    root = STORE / "homes" / f"run1a-{lane}"
    for found in (root, root.with_name(f"{root.name}.zones")):
        if found.exists():
            shutil.rmtree(found, onexc=writable)
    root.mkdir(parents=True)
    return root


def fixture_app(root: Path, job: str, manifest_tail: str) -> Path:
    target = root / "app-source"
    shutil.copytree(
        REPO / "examples/apps" / APP, target, ignore=shutil.ignore_patterns(".venv", "__pycache__")
    )
    shutil.copyfile(
        REPO / "qmx-agents/packages/qmx-apps/tests/fixture_server.py", target / "server.py"
    )
    (target / "job.py").write_text(job, encoding="utf-8")
    manifest = target / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        'mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]'
    )
    manifest.write_text(text + manifest_tail, encoding="utf-8")
    return target


SIXTY: Final = '\n[suggested_trigger]\nkind = "interval"\nseconds = 60\n'


@contextmanager
def engine(control: Any) -> Iterator[Any]:
    """The engine door on its own loop thread, as in the host, acting as the operator."""
    from qmx_engine.control_door import EngineDoor  # noqa: PLC0415
    from qmx_engine.service.context import OPERATOR  # noqa: PLC0415

    opened: list[Any] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        async with EngineDoor.open(control, principal=lambda: OPERATOR) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),))
    thread.start()
    if not ready.wait(60):
        raise SystemExit("BLOCKED: the engine door did not open")
    try:
        yield opened[0]
    finally:
        stop.set()
        thread.join(60)


@contextmanager
def control_on(root: Path, job: str, tail: str) -> Generator[Any]:
    from qmx_control import ControlService  # noqa: PLC0415

    control = ControlService(root / "qmx")
    try:
        control.settings_put("engine", {"scheduler": {"tick": 10}})
        control.apps_create(str(fixture_app(root, job, tail)), trust="first_party")
        yield control
    finally:
        control.close()


def runs_of(control: Any) -> list[dict[str, Any]]:
    return [r for r in control.workflow_runs_list(ITEM) if r.get("mode") == "live"]


def events(control: Any, run_id: str) -> list[Any]:
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415

    with Reader.open(control.home) as reader:
        return reader.events(run_id)


def lane_e57(log: Log) -> None:
    from qmx_engine.ledger.store import Reader  # noqa: PLC0415

    with control_on(home("e57"), COUNTER, SIXTY) as control, engine(control):
        enabled = control.apps_enable(APP)
        log(f"enable answered app={enabled['app']['status']} trigger={enabled['trigger']}")
        started = time.monotonic()
        triggers = control.workflow_triggers_list(ITEM)
        log.check(
            "one trigger row from the suggested trigger",
            [(t["kind"], t["spec"], t["enabled"]) for t in triggers]
            == [("interval", {"seconds": 60}, True)],
            [(t["kind"], t["spec"], t["enabled"]) for t in triggers],
        )
        passed: list[dict[str, Any]] = []
        while time.monotonic() - started < WINDOW_S:
            passed = [r for r in runs_of(control) if r["status"] == "passed"]
            if len(passed) >= 2:
                break
            time.sleep(POLL_S)
        elapsed = time.monotonic() - started
        log.check(
            "the interval fired as engine runs twice within three minutes",
            len(passed) >= 2,
            f"{len(passed)} passed live runs after {elapsed:.0f} s",
        )
        with Reader.open(control.home) as reader:
            fired = reader.connection.execute(
                "SELECT f.occurrence_at, f.run_id, f.status FROM fires f JOIN triggers t"
                " ON t.id = f.trigger_id WHERE t.workflow_item = ? ORDER BY f.occurrence_at",
                (ITEM,),
            ).fetchall()
        log(f"fires {fired}")
        delays: list[float] = []
        for occurrence, run_id, _ in fired:
            if run_id is None:
                continue
            found = [
                e
                for e in events(control, run_id)
                if e.kind == "node_started" and e.data.get("node_id") == "a"
            ]
            outputs = [
                e.data.get("outputs")
                for e in events(control, run_id)
                if e.kind == "node_finished" and e.data.get("node_id") == "a"
            ]
            if found:
                start = found[0].at
                delay = (
                    datetime.fromisoformat(start) - datetime.fromisoformat(occurrence)
                ).total_seconds()
                delays.append(delay)
                log(f"run {run_id} due {occurrence} app_op started {start} delay {delay:.2f} s")
                log(f"run {run_id} app_op outputs {outputs}")
        listed = {r["run_id"] for r in control.workflow_runs_list(None)}
        log.check(
            "the app's runs are in the engine run list",
            all(r["run_id"] in listed for r in passed),
            sorted(r["run_id"] for r in passed),
        )
        ran = (control.home / f"apps/{APP}/data/job-runs.jsonl").read_text().splitlines()
        log.check(
            "the job ran in the app once per run (the test run at enable plus each fire)",
            len(ran) == len(runs_of(control)) + 1,
            f"{len(ran)} job runs, {len(runs_of(control))} live runs",
        )
        if delays:
            log(
                f"PERF due-to-app_op-start seconds: {[round(d, 2) for d in delays]}"
                f" max {max(delays):.2f} (scheduler.tick 10 s)"
            )


def lane_runs(log: Log) -> None:
    from qmx_control import ControlService  # noqa: PLC0415
    from qmx_control.library import encoded  # noqa: PLC0415

    root = home("runs")

    def journal(path: Path, run_id: str, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        record: dict[str, Any] = {
            "run_id": run_id,
            "seq": 1,
            "time": "2026-10-19T00:00:01+00:00",
            "event": "run_start",
            "payload": payload,
        }
        record["fingerprint"] = sha256(encoded(record)).hexdigest()
        path.write_bytes(encoded(record) + b"\n")

    journal(root / "runs/chat-7/journal.jsonl", "chat-7", {"kind": "agent", "session_id": "chat-7"})
    journal(root / "journals/remote-r9.jsonl", "r9", {"kind": "job", "target": "contabo"})
    control = ControlService(root)
    try:
        listed = [run["id"] for run in control.run_index.refresh()]
    finally:
        control.close()
    log(f"run index ids {listed}")
    log.check("the chat journal is not listed", "chat-7" not in listed, listed)
    log.check("the remote run still is", listed == ["r9"], listed)


def lane_stopped(log: Log) -> None:
    with control_on(home("stopped"), COUNTER, SIXTY) as control, engine(control):
        enabled = control.apps_enable(APP)
        trigger_id = enabled["trigger"]["id"]
        stopped = control.apps_stop(APP)
        log(f"app stopped: {stopped['status']}")
        fired = control.workflow_triggers_run_now(trigger_id)
        log(f"run_now {fired}")
        deadline = time.monotonic() + 60
        status = ""
        while time.monotonic() < deadline:
            status = control.workflow_runs_get(fired["run_id"])["status"]
            if status not in {"running", "waiting", "created"}:
                break
            time.sleep(POLL_S)
        failed = [e.data for e in events(control, fired["run_id"]) if e.kind == "node_failed"]
        log(f"run {fired['run_id']} status {status} node_failed {failed}")
        log.check(
            "the app_op fails with the supervisor's reason",
            status == "failed"
            and [(f["code"], f["message"]) for f in failed]
            == [("not_running", "The app is stopped.")],
            failed,
        )


def lane_breaker(log: Log) -> None:
    with control_on(home("breaker"), RAISES, "") as control:
        control.apps_start(APP)
        codes = []
        for _ in range(3):
            try:
                control.app_job(APP, "job.py")
                codes.append("ok")
            except Exception as error:
                codes.append(getattr(error, "code", type(error).__name__))
        deadline = time.monotonic() + 15
        status = control.apps_get(APP)["runtime"]
        while status["status"] != "tripped" and time.monotonic() < deadline:
            time.sleep(0.5)
            status = control.apps_get(APP)["runtime"]
        log(f"three job runs answered {codes}; runtime {status['status']} {status['breaker']}")
        log.check(
            "the crash breaker still trips",
            (status["status"], status["breaker"]["reason"]) == ("tripped", "error_limit"),
            status["breaker"],
        )


def lane_grep(log: Log) -> None:
    source = REPO / "qmx-agents/packages/qmx-apps/src/qmx_apps"
    words = ("interval_seconds", "run_budget", "cpu_budget", "budget_exceeded", "RLIMIT_CPU")
    hits = [
        f"{path.name}:{number}: {line.strip()}"
        for path in (source / "supervisor.py", source / "bootstrap.py", source / "docker.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if any(word in line for word in words)
    ]
    for hit in hits:
        log(hit)
    log.check("no interval scheduling or usage budget in the supervisor", hits == [], len(hits))


def lane_heartbeat(log: Log) -> None:
    with control_on(home("heartbeat"), COUNTER, "") as control:
        control.apps_start(APP)
        control.apps_call(APP, "child_cpu", {})
        time.sleep(1)
        runtime = control.apps_get(APP)["runtime"]
        metrics = runtime["metrics"]
        log(f"metrics {json.dumps(metrics)} heartbeat_age {runtime['heartbeat_age_seconds']}")
        log.check(
            "CPU seconds and RSS still report",
            metrics["cpu_seconds"] > 0 and metrics["memory_bytes"] > 0,
            metrics,
        )
        log.check(
            "the heartbeat is fresh",
            runtime["heartbeat_age_seconds"] is not None and runtime["heartbeat_age_seconds"] < 3,
            runtime["heartbeat_age_seconds"],
        )


def lane_baseline(log: Log) -> None:
    from qmx_apps.supervisor import Supervisor  # noqa: PLC0415

    root = home("baseline")
    tail = "\n[schedule]\ninterval_seconds = 5\n"
    source = fixture_app(root, COUNTER, tail)
    manifest = source / "app.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("runs = 100", "runs = 100000"),
        encoding="utf-8",
    )
    owner = Supervisor(root / "qmx")
    try:
        owner.install(source, trust="first_party")
        owner.start(APP)
        time.sleep(32)
        owner.stop(APP)
    finally:
        owner.close()
    stamps = [
        json.loads(line)["at"]
        for line in (root / f"qmx/apps/{APP}/data/job-runs.jsonl").read_text().splitlines()
    ]
    late = [round(b - a - 5, 3) for a, b in itertools.pairwise(stamps)]
    log(f"PERF parent scheduler: {len(stamps)} job runs, seconds past each 5 s interval {late}")
    log.check("the parent scheduler ran jobs", len(stamps) >= 3, len(stamps))


LANES: Final = {
    "e57": lane_e57,
    "runs": lane_runs,
    "stopped": lane_stopped,
    "breaker": lane_breaker,
    "grep": lane_grep,
    "heartbeat": lane_heartbeat,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane", nargs="?", choices=[*LANES, "baseline"])
    args = parser.parse_args()
    chosen = {"baseline": lane_baseline} if args.lane == "baseline" else LANES
    if args.lane and args.lane != "baseline":
        chosen = {args.lane: LANES[args.lane]}
    failed = 0
    for name, lane in chosen.items():
        log = Log(name)
        try:
            lane(log)
        except Exception as error:
            log.check("lane ran to the end", False, repr(error))
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    sys.exit(main())
