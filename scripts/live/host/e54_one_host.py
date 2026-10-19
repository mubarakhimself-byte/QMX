"""HOST lane 2 (E54): one `qmx_host` on the ship home runs a copilot turn and a workflow agent node
at once, dies mid-turn, and comes back.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/host/e54_one_host.py`
Writes `<QMA_EVIDENCE_DIR>/<ENGINE_LOG_PREFIX>host-e54.log` and the hosts' output beside it.

Under the lane lock, `python -m qmx_host serve` starts on the ship home through `lane_host.py`,
with a bearer made for this run and passed in `QMX_LANE_BEARER`, so nothing is written to the
home's files but the chat and the run themselves. Over REST the lane makes a haiku chat and sends
it a long turn, and test-runs a workflow whose agent node does a long count; a test run's cheap
role resolves to `claude/haiku` on the plan login (`roles.test_order`). Once the chat's turn and
the agent node are both running, the host's whole process tree is killed and a new host starts on
the same home. Pass when both ran at once, the chat's turn reads unknown after the restart, the
run resumes from its ledger to `passed` without a second `run_created`, a second host on the home
is refused in one line, and the ship home's `settings.toml` hashes the same before and after.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Final

ENGINE_LANES: Final = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE_LANES))

import httpx  # noqa: E402
from common import SHIP_HOME, Log, boot, lane_lock, live  # noqa: E402
from ep2_lanes import AGENTS  # noqa: E402
from lane_host import BEARER_ENV  # noqa: E402
from qmx_engine.ledger.store import Reader  # noqa: E402
from x13_doors import LANE_HOST, free_port, healthy, kill_tree  # noqa: E402

EVIDENCE: Final = Path(
    os.environ.get("QMA_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/host")
)
PREFIX: Final = os.environ.get("ENGINE_LOG_PREFIX", "")
SETTINGS: Final = SHIP_HOME / "settings.toml"
ITEM: Final = "host-e54-count"
START_S: Final = 120.0
BOTH_S: Final = 180.0
OVERLAP_S: Final = 5.0
RUN_S: Final = 420.0
CHAT_TURN: Final = (
    "Write every whole number from one to three hundred in English words, one per line. "
    "No other text."
)
BRIEF: Final = (
    "The input item has a number `upto`. Before your final answer, write every whole number from "
    "one to `upto` in English words, one per line. Then answer with `count` set to `upto`."
)
SCHEMA: Final = {
    "type": "object",
    "required": ["count"],
    "properties": {"count": {"type": "integer"}},
}
ITEM_SCRIPT: Final = 'import json\nprint(json.dumps([{"id": 1, "upto": 200}]))\n'


class HostLog(Log):
    """`Log` writing to this PR's evidence folder instead of the engine store."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def workflow() -> dict[str, Any]:
    nodes = [
        {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1,
         "parameters": {"kinds": ["manual"]}},
        {"id": "item", "name": "Item", "type": "script", "typeVersion": 1, "effect": "none",
         "parameters": {"script": "scripts/item.py"}},
        {"id": "count", "name": "Count", "type": "agent", "typeVersion": 1, "role": "triage",
         "effect": "none",
         "parameters": {"brief_ref": "prompts/brief.md", "output_schema_ref": "schemas/count.json",
                        "tools": [], "max_turns": 4}},
    ]  # fmt: skip
    definition = {
        "schema": "qmx.workflow/1",
        "id": ITEM,
        "name": "HOST E54 count",
        "nodes": nodes,
        "connections": {
            "Start": {"main": [[{"node": "Item", "port": "in", "map": "one"}]]},
            "Item": {"main": [[{"node": "Count", "port": "in", "map": "one"}]]},
        },
    }
    files = {
        "scripts/item.py": ITEM_SCRIPT,
        "prompts/brief.md": BRIEF,
        "schemas/count.json": json.dumps(SCHEMA),
    }
    return {"definition": definition, "files": files}


def settings_sha() -> str:
    return hashlib.sha256(SETTINGS.read_bytes()).hexdigest()


def host_command(port: int) -> list[str]:
    return [sys.executable, str(LANE_HOST), "qmx_host", "serve", "--home", str(SHIP_HOME),
            "--port", str(port)]  # fmt: skip


@contextlib.contextmanager
def served(
    log: Log, bearer: str, slug: str
) -> Iterator[tuple[httpx.Client, subprocess.Popen[bytes]]]:
    """`qmx_host` on the ship home and a client with the lane bearer. The block may kill it."""
    port = free_port()
    headers = {"Authorization": f"Bearer {bearer}"}
    output = (EVIDENCE / f"{PREFIX}host-e54-{slug}.out").open("wb")
    env = {**os.environ, BEARER_ENV: bearer}
    began = time.perf_counter()
    process = subprocess.Popen(
        host_command(port), cwd=AGENTS, env=env, stdout=output, stderr=output
    )
    while healthy(port, headers) is None:
        if process.poll() is not None or time.perf_counter() - began > START_S:
            output.close()
            kill_tree(process.pid)
            raise SystemExit(f"qmx_host did not start; see {output.name}")
        time.sleep(0.1)
    seconds = time.perf_counter() - began
    log(f"qmx_host pid {process.pid} healthy on port {port} after {seconds:.2f} s")
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", headers=headers, timeout=120)
    try:
        yield client, process
    finally:
        client.close()
        kill_tree(process.pid)
        output.close()


def until[T](predicate: Callable[[], T | None], seconds: float, every: float = 0.5) -> T | None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = predicate()
        if found:
            return found
        time.sleep(every)
    return None


def events(run_id: str) -> list[Any]:
    with Reader.open(SHIP_HOME) as reader:
        return list(reader.events(run_id))


def agent_running(run_id: str) -> bool:
    """The agent node has started an attempt that has not ended."""
    found = [e for e in events(run_id) if e.data.get("node_id") == "count"]
    started = [e for e in found if e.kind == "node_started"]
    ended = [e for e in found if e.kind in ("node_finished", "node_failed")]
    return bool(started) and len(ended) < len(started)


def unknown_blocks(chat: str) -> list[dict[str, Any]]:
    from qma.harness import QmxHome, control_service  # noqa: PLC0415

    control = control_service(QmxHome(SHIP_HOME))
    return [
        block
        for block in live.session_blocks(control, chat)
        if block.get("type") == "needs_you" and "unknown" in str(block["content"].get("reason"))
    ]


def lane(log: Log) -> None:
    bearer = secrets.token_urlsafe(32)
    with served(log, bearer, "host1") as (client, first):
        saved = client.put(f"/api/workflows/{ITEM}/draft", json=workflow()).json()
        log(f"draft {ITEM}: {saved.get('state')} revision {saved.get('revision')}")
        workspace = live.SCRATCH / "host-e54-ws"
        workspace.mkdir(parents=True, exist_ok=True)
        made = client.post(
            "/api/chats",
            json={"title": "HOST e54", "model": "haiku", "profile": "claude",
                  "workspace": str(workspace)},
        ).json()  # fmt: skip
        chat = made["session_id"]
        log(f"copilot chat {chat} on claude/haiku")
        tested: dict[str, Any] = {}

        def test() -> None:
            with contextlib.suppress(httpx.HTTPError):
                tested["reply"] = client.post(f"/api/workflows/{ITEM}/test").json()

        tester = threading.Thread(target=test, daemon=True)
        tester.start()
        sent = client.post(f"/api/sessions/{chat}/turns", json={"text": CHAT_TURN})
        log(f"copilot turn sent: http {sent.status_code}")

        def run_id() -> str | None:
            listed = client.get("/api/workflow-runs", params={"workflow_id": ITEM}).json()
            going = [r for r in listed if r.get("in_flight") and r.get("workflow_item") == ITEM]
            return going[0]["run_id"] if going else None

        run = until(run_id, 60)
        log(f"in-flight run listed with its workflow (L-68): {run}")
        if run is None:
            log.check("the workflow run started", False, tested)
            return

        def both() -> bool:
            turn = client.get(f"/api/chats/{chat}").json().get("turn")
            return turn == "running" and agent_running(run)

        overlap = until(both, BOTH_S) and (time.sleep(OVERLAP_S) or both())
        turn = client.get(f"/api/chats/{chat}").json().get("turn")
        log.check(
            "the copilot turn and the agent node ran at once on one host",
            bool(overlap),
            {"chat_turn": turn, "agent_running": agent_running(run)},
        )
        log(f"killing qmx_host pid {first.pid} and its process tree mid-turn")
        kill_tree(first.pid)
        first.wait(30)
        log(f"tester saw: {json.dumps(tested.get('reply'))[:200]}")

    with served(log, bearer, "host2") as (client, second):
        record = client.get(f"/api/chats/{chat}").json()
        blocks = unknown_blocks(chat)
        log(f"chat after restart: turn {record.get('turn')}; unknown blocks {blocks}")
        log.check(
            "the chat shows its killed turn as unknown",
            record.get("turn") == "idle" and len(blocks) == 1,
            {"turn": record.get("turn"), "unknown_blocks": len(blocks)},
        )
        refused = subprocess.run(
            [*host_command(1)],
            cwd=AGENTS,
            env={**os.environ, BEARER_ENV: bearer},
            capture_output=True,
            text=True,
            timeout=120,
        )
        said = refused.stderr.strip().splitlines()
        log(f"second host: exit {refused.returncode} {said}")
        log.check(
            "a second host on the ship home is refused in one line",
            refused.returncode == 1 and len(said) == 1 and f"PID {second.pid}" in said[0],
            said,
        )
        resumed = client.post(f"/api/workflow-runs/{run}/resume").json()
        log(f"resume: {json.dumps(resumed)[:300]}")

        def ended() -> dict[str, Any] | None:
            found = client.get(f"/api/workflow-runs/{run}").json()
            return found if found.get("status") in ("passed", "stopped") else None

        final = until(ended, RUN_S, every=2) or client.get(f"/api/workflow-runs/{run}").json()
    found = events(run)
    for event in found:
        if event.data.get("node_id") or event.kind.startswith("run_"):
            shown = {
                k: event.data.get(k)
                for k in ("node_id", "attempt", "effect_state", "code", "status")
                if event.data.get(k) is not None
            }
            log(f"{event.seq} {event.kind} {json.dumps(shown)}")
    created = [e for e in found if e.kind == "run_created"]
    attempts = [
        e.data.get("attempt")
        for e in found
        if e.kind == "node_started" and e.data.get("node_id") == "count"
    ]
    items = [e for e in found if e.kind == "node_started" and e.data.get("node_id") == "item"]
    log.check(
        "the run resumed from its ledger and passed: one run_created, the finished script node "
        "not run again, the agent node's attempt retried",
        final.get("status") == "passed" and len(created) == 1 and len(items) == 1
        and len(attempts) >= 2,
        {"status": final.get("status"), "created": len(created), "item_starts": len(items),
         "agent_attempts": attempts},
    )  # fmt: skip


def main() -> int:
    log = HostLog("host-e54")
    boot()
    live.require_login(log)
    before = settings_sha()
    log(f"ship home settings.toml sha256 before: {before}")
    with lane_lock(log):
        lane(log)
    after = settings_sha()
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
