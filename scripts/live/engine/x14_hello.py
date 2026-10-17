"""EP14's example lanes: `examples/hello-chunks` on the engine host.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x14_hello.py [--window] [test|resume ...]`
None named runs both, in order, on one throwaway home. Each lane writes
`evidence/ep14/<ENGINE_LOG_PREFIX>ep14-<lane>.log`; the script exits 1 if any lane failed.

- `test` (lane 3): the example is saved as a draft. Publishing it is refused before a passing test
  run, so nothing can be enabled. A test run on the host finishes with three chunk spans; then the
  version publishes carrying the test report, a disabled cron trigger is added, and enabling it
  succeeds. The run card from
  `explain` is saved as `ep14-hello-card.txt`, and with `--window` it is shown in a console window
  and grabbed as `ep14-hello.png`.
- `resume` (lane 4): the trigger fires once through `run-now`, live. The host is killed once a
  chunk has finished while the others are mid-turn, then restarted, and the run is resumed over
  REST. It must finish without running a finished chunk again.

The home's only provider row is OpenRouter's. Its `[roles]` puts the example's `scanner` role on
the Kimi row and `[engine] roles.test_only` is empty, so live runs may use that key row too (the
plan login is never touched). Spend: three Kimi chunk turns per run, at most $0.05 a run by the
relay journals, counting cache reads as full input.
`--window` sets this console's title, so the review video can record it.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from common import ENGINE_STORE, Log, boot
from llm_lanes import KIMI_ROW, OPENROUTER_ROW, relay_usd
from qmx_engine.ledger.store import Reader
from x13_doors import ENGINE, host, kill_tree, reply, until

PR: Final = "ep14"
EXAMPLE: Final = ENGINE / "examples" / "hello-chunks"
HOME: Final = ENGINE_STORE / "homes" / "ep14-hello"
ITEM: Final = "hello-chunks"
TITLE: Final = "EP14 hello-chunks"
RUN_S: Final = 300.0
SENT_S: Final = 4.0
"""How long an unfinished chunk's chat has had its task before the kill. Killed sooner, the CLI
may not have written the task to the chat yet, and the resumed chat has nothing to finish
(BACKLOG: EP11's resume sends only `RESUMED`)."""


def demo_home() -> Path:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    shutil.rmtree(HOME, ignore_errors=True)
    HOME.mkdir(parents=True)
    control = control_service(QmxHome(HOME))
    control.settings_put("providers", {"openrouter": OPENROUTER_ROW})
    control.settings_put("roles", {"scanner": [KIMI_ROW]})
    control.settings_put("engine", {"roles": {"test_only": []}})
    return HOME


def bundle() -> dict[str, Any]:
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415

    found = Bundle.read(EXAMPLE)
    return {
        "definition": found.definition,
        "files": {k: v.decode() for k, v in found.files.items()},
    }


def finished(client: Any, run_id: str) -> dict[str, Any] | None:
    found = client.get(f"/api/workflow-runs/{run_id}").json()
    return found if found.get("status") not in ("running", "pending") else None


def card(document: dict[str, Any]) -> list[str]:
    """The run card: the run, then each node with its spans, chunk by chunk."""
    lines = [
        f"run {document['run_id']}  {document['status']}  mode {document['mode']}  "
        f"workflow {document['workflow_id']}",
        f"cost {json.dumps(document['cost'])}",
    ]
    for node in document["nodes"]:
        lines.append(
            f"  {node['node_id']:<6} {node['state']:<8} {len(node['attempts'])} attempt(s)"
        )
        for span in node["spans"]:
            chunk = f"chunk {span['partition']}" if span.get("partition") is not None else ""
            model = span.get("model") or ""
            lines.append(
                f"      span {chunk:<8} attempt {span.get('attempt')} {span.get('status'):<7} "
                f"{model:<24} tokens {json.dumps(span.get('tokens') or {})}"
            )
    return lines


def chunk_spans(document: dict[str, Any]) -> list[Any]:
    sort = next(n for n in document["nodes"] if n["node_id"] == "sort")
    return sorted(
        s["partition"] for s in sort["spans"] if s.get("status") == "ok" and s.get("model")
    )


def show(log: Log, lines: list[str], slug: str, png: str) -> None:
    """Show `lines` in a console window of their own and grab it with ffmpeg."""
    text = log.path.parent / f"{log.path.stem}-{slug}.txt"
    text.write_text("\n".join(lines) + "\n", encoding="utf-8")
    title = f"{TITLE} {slug}"
    viewer = (
        "import ctypes,os,sys,time;"
        f"ctypes.windll.kernel32.SetConsoleTitleW({title!r});"
        "os.system('mode con: cols=130 lines=24');"
        f"print(open({str(text)!r},encoding='utf-8').read(),flush=True);time.sleep(12)"
    )
    subprocess.Popen(["conhost.exe", sys.executable, "-c", viewer])  # noqa: S607
    time.sleep(5)
    shot = log.path.parent / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}{png}.png"
    grab = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "gdigrab"]
    done = subprocess.run([*grab, "-i", f"title={title}", "-frames:v", "1", str(shot)], check=False)
    log(f"screen {shot}: ffmpeg exit {done.returncode}")


def test(log: Log, window: bool) -> None:
    with host(log, demo_home()) as (client, _, _):
        saved = reply(log, "draft put", client.put(f"/api/workflows/{ITEM}/draft", json=bundle()))
        log.check(
            "the example saves as a validated draft",
            saved.get("state") == "validated",
            saved.get("problems"),
        )
        early = client.put(f"/api/workflows/{ITEM}", json={})
        log(f"publish before any test: http {early.status_code} {early.text[:200]}")
        log.check(
            "nothing can be published, so nothing enabled, before a passing test",
            early.status_code == 409 and "publish_refused" in early.text,
            early.status_code,
        )
        run = reply(log, "test run", client.post(f"/api/workflows/{ITEM}/test"))["run"]
        ended = until(lambda: finished(client, run["run_id"]), RUN_S) or {}
        log(f"test run {run['run_id']} ended {ended.get('status')} {ended.get('reason') or ''}")
        report = client.get(f"/api/workflows/{ITEM}/draft").json().get("state")
        log.check(
            "the test run passes and the draft reads tested",
            (ended.get("status"), report) == ("passed", "tested"),
            (ended.get("status"), report),
        )
        published = reply(log, "publish", client.put(f"/api/workflows/{ITEM}", json={}))
        trigger = reply(
            log,
            "add cron trigger",
            client.post(
                "/api/triggers",
                params={"workflow_id": ITEM},
                json={"kind": "cron", "expr": "0 3 * * *", "zone": "Europe/London"},
            ),
        )
        log.check(
            "version 1.0.0 carries the test report and its cron trigger starts disabled",
            (published.get("semver"), published.get("tested"), trigger.get("enabled"))
            == ("1.0.0", True, False),
            (published.get("semver"), published.get("tested"), trigger.get("enabled")),
        )
        enabled = reply(log, "enable", client.post(f"/api/triggers/{trigger.get('id')}/enable"))
        log.check(
            "enabling succeeds after the test report",
            enabled.get("enabled") is True,
            enabled.get("enabled"),
        )
        document = client.get(f"/api/workflow-runs/{run['run_id']}/explain").json()
    lines = card(document)
    for line in lines:
        log(line)
    log.check(
        "explain shows three chunk spans, all ok",
        chunk_spans(document) == ["0", "1", "2"],
        chunk_spans(document),
    )
    if window:
        show(log, lines, "card", "ep14-hello")


def sort_events(run_id: str) -> list[Any]:
    with Reader.open(HOME) as reader:
        return [e for e in reader.events(run_id) if e.data.get("node_id") == "sort"]


def partitions(events: list[Any], kind: str) -> list[Any]:
    return sorted(e.data.get("partition") for e in events if e.kind == kind)


def age(at: str) -> float:
    return (datetime.now(UTC) - datetime.fromisoformat(at)).total_seconds()


def run_ids(reader: Reader) -> list[str]:
    found = reader.connection.execute("SELECT DISTINCT run_id FROM events").fetchall()
    return [row[0] for row in found]


def resume(log: Log, window: bool) -> None:
    with host(log, HOME, "host-1") as (client, process, _):
        triggers = client.get("/api/triggers", params={"workflow_id": ITEM}).json()
        if not triggers or not triggers[0].get("enabled"):
            raise SystemExit("BLOCKED: no enabled hello-chunks trigger; run the test lane first")
        with Reader.open(HOME) as reader:
            known = set(run_ids(reader))
        fire = threading.Thread(
            target=lambda: reply(
                log, "run now", client.post(f"/api/triggers/{triggers[0]['id']}/run-now")
            ),
            daemon=True,
        )
        fire.start()

        def live_run() -> str | None:
            with Reader.open(HOME) as reader:
                return next((r for r in run_ids(reader) if r not in known), None)

        run_id = until(live_run, 60)
        if run_id is None:
            raise SystemExit("BLOCKED: run-now started no run")
        log(f"live run {run_id} started")

        def mid_turn() -> bool | None:
            """True once a chunk has finished and every other chunk's chat has had its task for
            `SENT_S`; None once every chunk has finished."""
            events = sort_events(run_id)
            done = partitions(events, "node_finished")
            if done and len(done) == len(partitions(events, "node_scheduled")):
                return None
            chats = {e.data.get("partition"): e.at for e in events if e.data.get("session_id")}
            going = set(partitions(events, "node_scheduled")) - set(done)
            return bool(done) and all(p in chats and age(chats[p]) > SENT_S for p in going)

        caught, deadline = False, time.monotonic() + RUN_S
        while time.monotonic() < deadline and (found := mid_turn()) is not None:
            if found:
                caught = True
                break
            time.sleep(0.1)
        before = sort_events(run_id)
        done_before = partitions(before, "node_finished")
        log(f"chunks finished before the kill: {done_before}; killing host pid {process.pid}")
        kill_tree(process.pid)
    log.check(
        "the kill landed mid-run, with a chunk finished and one not", bool(caught), done_before
    )
    with Reader.open(HOME) as reader:
        mark = max(e.seq for e in reader.events(run_id))
    with host(log, HOME, "host-2") as (client, _, _):
        status = client.get(f"/api/workflow-runs/{run_id}").json().get("status")
        log(f"after the restart the run reads {status}")
        reply(log, "resume", client.post(f"/api/workflow-runs/{run_id}/resume"))
        ended = until(lambda: finished(client, run_id), RUN_S) or {}
        log(f"run {run_id} ended {ended.get('status')} {ended.get('reason') or ''}")
        document = client.get(f"/api/workflow-runs/{run_id}/explain").json()
    after = [e for e in sort_events(run_id) if e.seq > mark]
    rerun = partitions(after, "node_started")
    log(f"chunks started after the restart: {rerun}")
    log.check(
        "the resumed run finishes passed", ended.get("status") == "passed", ended.get("status")
    )
    log.check(
        "no chunk finished before the kill ran again",
        not set(done_before) & set(rerun) and bool(rerun),
        {"finished_before": done_before, "started_after": rerun},
    )
    lines = card(document)
    for line in lines:
        log(line)
    log.check(
        "explain shows three ok chunk spans",
        chunk_spans(document) == ["0", "1", "2"],
        chunk_spans(document),
    )
    if window:
        show(log, lines, "resume-card", "ep14-resume-card")


LANES: Final = {"test": test, "resume": resume}


def main() -> int:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser()
    parser.add_argument("--window", action="store_true", help="title this console; screen cards")
    parser.add_argument("lanes", nargs="*", choices=list(LANES))
    args = parser.parse_args()
    if args.window:
        ctypes.windll.kernel32.SetConsoleTitleW(TITLE)
    prefix = os.environ.get("ENGINE_LOG_PREFIX", "")
    boot()
    os.environ["ENGINE_LOG_PREFIX"] = prefix  # the boot scrub drops it
    failed = 0
    for name in args.lanes or list(LANES):
        log = Log(PR, f"ep14-{name}")
        LANES[name](log, args.window)
        log(f"OpenRouter spend so far on this home, upper bound: ${relay_usd(HOME):.4f}")
        failed += log.verdict()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
