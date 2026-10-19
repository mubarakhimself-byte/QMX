"""EP11 lane 4 (E4 on an agent) and TURN-E lane 4 (B-69): the engine dies after the agent's chat
started but before its task reached the CLI; on restart the call is retried exactly once, on the
same chat, which gets the whole task again, with one `info` digest line and no inbox item.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e04b_agent_unknown.py`
Writes `evidence/ep11/<ENGINE_LOG_PREFIX>ep11-e04.log`. No plan turn and no provider spend: a
throwaway home, the fake model on a key row (`roles.reader` is `fake/fake-model`). A child process
runs the engine; the lane kills the child's whole process tree as soon as the attempt records its
chat, while the CLI still starts, so the chat's transcript holds no prompt. The lane then reopens
the harness on the same home (which kills any CLI tree the child left) and resumes the run with a
fake model that answers. The node declares `Read`, so the fake model scripts the main request.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from agent_lanes import PR, edge, node, read, sessions, workflow
from common import Log, boot, live, opened, throwaway_home

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.store import Ledger, Reader, ledger_path
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.runner import Engine
from qmx_engine.settings import DEFAULTS

RUN_ID = "run-ep11-e04b"
CARD = '{"seen": 2}'
SCHEMA = {"type": "object", "required": ["seen"], "properties": {"seen": {"type": "integer"}}}
SETTINGS = {**DEFAULTS, "roles.reader": ("fake/fake-model",), "retry.backoff": (1, 1, 1)}
HOLD_S = 120.0
BRIEF = "Count the items you are given."


def folder() -> Path:
    return workflow(
        "e04b",
        [
            node("start", "trigger"),
            node(
                "read",
                "agent",
                "reader",
                brief_ref="brief.md",
                output_schema_ref="out.json",
                tools=["Read"],
                max_turns=12,
            ),
        ],
        {"start": {"main": [edge("read")]}},
        {"brief.md": BRIEF, "out.json": json.dumps(SCHEMA)},
    )


async def engine_on(home: Path, engine_home: Path, root: Path, fake: Any, resume: bool) -> str:
    from qma.harness import TestMode  # noqa: PLC0415

    live.put_providers(home, {"fake": live.fake_row(fake.url)})
    found = checked(root)
    assert not isinstance(found, list), found
    async with opened(home, test=TestMode(loopback_http_provider=True)) as h:
        with Ledger.open(engine_home) as ledger:
            engine = Engine(
                engine_home, ledger, settings=SETTINGS, harness=HarnessAdapter(h.harness)
            )
            if resume:
                outcome = await engine.resume(RUN_ID)
            else:
                outcome = await engine.start(
                    root, found[1], mode="live", inputs=["a", "b"], run_id=RUN_ID
                )
            return outcome.status


async def child(home: Path, engine_home: Path, root: Path) -> None:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415

    boot()
    live.use_fake_key()
    fake = FakeModel([Turn([text(CARD)])])
    answer = fake.next_turn

    def held(scripted: bool, request: dict[str, Any] | None = None) -> Any:
        if scripted:
            time.sleep(HOLD_S)
        return answer(scripted, request)

    fake.next_turn = held  # type: ignore[method-assign]
    fake.start()
    await engine_on(home, engine_home, root, fake, resume=False)


def holds_prompt(home: Path, chat: str) -> bool:
    for path in (home / "claude" / "projects").glob(f"*/{chat}.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"type":"user"' in line.replace(" ", ""):
                return True
    return False


def started(engine_home: Path) -> str | None:
    if not ledger_path(engine_home).exists():
        return None
    with Reader.open(engine_home) as reader:
        found = sessions(reader.events(RUN_ID))
    return found[0][2] if found else None


async def main() -> int:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415

    log = Log(PR, "ep11-e04")
    home, engine_home, root = (
        throwaway_home(PR, "e04b"),
        throwaway_home(PR, "e04b-engine"),
        folder(),
    )
    proc = subprocess.Popen(
        [sys.executable, __file__, "child", str(home), str(engine_home), str(root)]
    )
    deadline = time.monotonic() + 120
    chat = None
    while chat is None and time.monotonic() < deadline and proc.poll() is None:
        time.sleep(0.1)
        chat = started(engine_home)
    log(f"the child's agent attempt started chat {chat}; killing the child's process tree")
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, check=False
    )
    proc.wait(30)
    before = chat is not None and holds_prompt(home, chat)
    log(f"the chat's transcript holds a prompt after the kill: {before}")
    boot()
    live.use_fake_key()
    fake = FakeModel([Turn([text(CARD)])]).start()
    try:
        status = await engine_on(home, engine_home, root, fake, resume=True)
    finally:
        fake.stop()
    events, spans = read(engine_home, RUN_ID)
    with InboxTable.open(engine_home) as inbox:
        items = inbox.list_items(open_only=False)
    for event in events:
        if (
            event.data.get("node_id") == "read" and event.kind != "heartbeat"
        ) or "session_id" in event.data:
            shown = {
                k: event.data.get(k)
                for k in ("attempt", "code", "effect_state", "session_id", "note", "line", "step")
                if event.data.get(k) is not None
            }
            log(f"{event.kind} {json.dumps(shown)}")
    started_attempts = [
        e.data["attempt"]
        for e in events
        if e.kind == "node_started" and e.data.get("node_id") == "read"
    ]
    unknown = [
        e.data
        for e in events
        if e.kind == "node_failed" and e.data.get("effect_state") == "unknown"
    ]
    info = [
        e.data
        for e in events
        if e.kind == "log" and e.data.get("level") == "info" and e.data.get("digest")
    ]
    key = f"{RUN_ID}:read:0:1"
    chats = sessions(events)
    log(
        f"run {RUN_ID}: {status}; inbox items: {len(items)}; "
        f"requests the restarted fake model saw: {len(fake.requests)}"
    )
    log.check(
        "the agent call was retried exactly once and the run passed",
        status == "passed" and started_attempts == [1, 2] and len(unknown) == 1,
        {"status": status, "attempts": started_attempts, "unknown": len(unknown)},
    )
    log.check(
        "one info digest line carries the idempotency key",
        len(info) == 1
        and info[0].get("idempotency_key") == key
        and key in str(info[0].get("line")),
        info,
    )
    log.check("no inbox item exists", items == [], [i.kind for i in items])
    notes = [
        str(e.data.get("note"))
        for e in events
        if e.kind == "heartbeat" and e.data.get("attempt") == 2 and "session_id" in e.data
    ]
    task_sent = [s.scripted and BRIEF.encode() in s.body for s in fake.requests]
    log(f"attempt 2 heartbeat: {notes}; scripted requests holding the brief: {task_sent}")
    log.check(
        "the chat never got its task, and the retry resent the whole task (B-69)",
        not before and any(task_sent) and any("resent" in n for n in notes),
        {"held_before": before, "notes": notes, "brief_sent": any(task_sent)},
    )
    log.check(
        "the retry picked up the saved chat (session id) of the attempt that died",
        [(a, s) for _, a, s in chats] == [(1, chat), (2, chat)] and chat is not None,
        chats,
    )
    log(f"spans: {[(s.node_id, s.attempt, s.status) for s in spans if s.kind == 'node']}")
    return log.verdict()


if __name__ == "__main__":
    if sys.argv[1:2] == ["child"]:
        asyncio.run(child(*(Path(a) for a in sys.argv[2:5])))
    else:
        raise SystemExit(asyncio.run(main()))
