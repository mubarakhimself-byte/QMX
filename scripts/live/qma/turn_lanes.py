"""TURN-H lanes: the turn call and chat options that survive a host restart, live.

    turn_lanes.py h1        a 40-tool-call haiku turn ends through `result()` with no poll loop,
                            three times, then the parent's 50 ms poll on the same turn once
    turn_lanes.py h19       kill the host mid-turn on a Background chat with `compact_at` 0.40
                            and a named hook sink, then resume in a new host process
    turn_lanes.py cache     two Background chats in two folders; the second reads the system
                            prefix from cache
    turn_lanes.py h2        a resumed `tools=()` chat asked to use a tool runs none
    turn_lanes.py h18       closing a finished Background chat leaves no CLI process of it
    turn_lanes.py h20       the copilot saves a workflow draft and nothing asks
    turn_lanes.py h41       a workflow chat's PostToolUse command hook runs there and not in a
                            copilot chat

Every lane runs on the ship home's plan login on haiku and needs the engine lane lock held by
whoever runs it (`mkdir D:/QMX-worktrees/.engine-lane-lock`); this script never takes it. Logs go
to `<QMA_EVIDENCE_DIR>/owner-turn-h-<lane>.log`.

h1: PASS when each run's `result()` is `ok` with at least 40 tool calls, and no harness module
called `asyncio.sleep` while the turn ran. Records the milliseconds from the CLI's
`ResultMessage` reaching the chat's reader to `result()` resolving (perf metric; fail above a
50 ms median), and the same gap for the engine adapter's `wait_turn` on the same turn.

h19: a child host process starts the chat and its turn; the parent kills it once the sink has
seen a PostToolUse. A second child host opens the same home, registers the sink again and sends
the next turn. haiku's plan window is 1M tokens, so the lane names a 200,000-token window for
its own chats (`LANE_WINDOW`). PASS when the resumed CLI holds the 40 % compaction setting, the
resumed turn compacts with the CLI's first `pre_tokens` from 72,000 (0.40 of the 180,000-token
effective window) to under 105,000, and PostToolUse events from the second host arrive.

cache: P-SET's rule (B's read minus A's at least 70 % of A's write), adjusted for the folder's
own first message, which B must write: PASS when B's read minus A's is at least 70 % of the part
of A's write that B did not write again, and a control chat in A's folder writes under 5 % of
what B wrote. A fresh nonce in every chat's system text means no earlier run warmed it.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from common import SCRATCH, SHIP_HOME, Log, boot, use_fake_home

LOCK = Path("D:/QMX-worktrees/.engine-lane-lock")
COMPACT = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"
MODEL = "haiku"
TURN_S = 600.0
HARNESS_FILES = ("qma\\harness\\", "qma/harness/")
RECORDED_SLEEPS: list[tuple[str, str, float]] = []


def require_lock() -> None:
    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")


def folder(name: str) -> Path:
    found = SCRATCH / f"turn-h-{name}"
    found.mkdir(parents=True, exist_ok=True)
    return found


def cli_pid(home: Any, chat: str) -> int | None:
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    record = read_pid_record(pid_path(home.procs_dir, chat))
    return None if record is None else record.cli_pid


def cli_env(home: Any, chat: str) -> dict[str, str]:
    import psutil  # noqa: PLC0415

    pid = cli_pid(home, chat)
    return {} if pid is None else dict(psutil.Process(pid).environ())


async def ship_harness() -> tuple[Any, Any]:
    from qma.harness import AllowOnce, Harness, QmxHome, Reject  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    harness = await Harness.open(home, control=control_service(home))

    async def reads_only(call: Any) -> Any:
        return AllowOnce() if call.tool in ("Read", "Glob", "Grep") else Reject("lane policy")

    harness.register_policy("lane", reads_only)
    return harness, home


def watch_sleeps() -> None:
    """Record every `asyncio.sleep` a harness module awaits, with the function that awaited it."""
    real = asyncio.sleep

    async def sleep(delay: float, result: Any = None) -> Any:
        caller = inspect.stack()[1]
        if any(part in caller.filename for part in HARNESS_FILES):
            RECORDED_SLEEPS.append((Path(caller.filename).name, caller.function, delay))
        return await real(delay, result)

    asyncio.sleep = sleep  # type: ignore[assignment]


def tap_results() -> dict[str, float]:
    """The monotonic time each chat's reader received its latest `ResultMessage`."""
    import qma.harness.chat as chat_module  # noqa: PLC0415
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    seen: dict[str, float] = {}
    base = chat_module.ClaudeSDKClient

    class Tap(base):  # type: ignore[misc, valid-type]
        async def receive_messages(self) -> Any:
            async for message in super().receive_messages():
                if isinstance(message, ResultMessage):
                    seen[str(self.options.session_id or self.options.resume)] = time.monotonic()
                yield message

    chat_module.ClaudeSDKClient = Tap
    return seen


def files_to_read(where: Path, count: int, lines: int) -> list[str]:
    """`count` files of `lines` lines. Line `lines // 2 + n` of file n holds the word KEY-n, so
    only a whole read finds it."""
    names = []
    for n in range(1, count + 1):
        name = f"f{n:02d}.txt"
        body = "".join(
            f"file {n:02d} line {i:04d}: "
            + (f"KEY-{n:02d}" if i == lines // 2 + n else "the tide turns, boats fill the harbour")
            + "\n"
            for i in range(lines)
        )
        (where / name).write_text(body, "utf-8")
        names.append(name)
    return names


FORTY = (
    "Use the Read tool on each of the files f01.txt to f40.txt in the working folder, one file "
    "per call, one call at a time. Do not use any other tool. When all 40 are read, reply with "
    "the single word DONE."
)


async def h1(log: Log) -> None:
    from qma.harness import Background, ChatPermissions, InjectedText, NewChat  # noqa: PLC0415

    seen = tap_results()
    watch_sleeps()
    work = folder("h1")
    files_to_read(work, 40, 3)
    harness, home = await ship_harness()
    gaps: list[float] = []
    try:
        for run in range(1, 4):
            chat = await harness.start_chat(
                NewChat(
                    title=f"turn-h h1 run {run}",
                    model=MODEL,
                    workspace=work,
                    kind=Background(),
                    permissions=ChatPermissions("lane"),
                )
            )
            warm = await harness.run_turn(chat, InjectedText("Reply with the single word ok."))
            await asyncio.wait_for(warm.result(), TURN_S)
            RECORDED_SLEEPS.clear()
            handle = await harness.run_turn(chat, InjectedText(FORTY))
            done = await asyncio.wait_for(handle.result(), TURN_S)
            resolved = time.monotonic()
            gap = (resolved - seen[chat]) * 1000
            gaps.append(gap)
            polls = [s for s in RECORDED_SLEEPS if s[1] != "_reap"]
            log(
                f"run {run}: status={done.status} text={(done.text or '')[:40]!r} "
                f"tools={len(done.tools)} usage={done.usage} gap_ms={gap:.2f} sleeps={polls}"
            )
            log.check(f"run {run} ended ok through result()", done.status == "ok", done.status)
            log.check(
                f"run {run} made at least 40 tool calls", len(done.tools) >= 40, len(done.tools)
            )
            log.check(f"run {run} ran no poll loop", polls == [], polls)
            await harness.close_chat(chat)
        median = statistics.median(gaps)
        log(
            f"perf: CLI turn end to result() in ms: {[round(g, 2) for g in gaps]}, "
            f"median {median:.2f}"
        )
        log.check("median turn end to result() is at most 50 ms", median <= 50, round(median, 2))
        await baseline(log, harness, home, seen, work)
    finally:
        await harness.close()


async def baseline(log: Log, harness: Any, home: Any, seen: dict[str, float], work: Path) -> None:
    """The parent's way: the engine adapter's `wait_turn`, polling the record every 50 ms."""
    from qmx_engine.ports.harness_adapter import HarnessAdapter  # noqa: PLC0415

    adapter = HarnessAdapter(harness)
    chat = await adapter.start_chat(
        title="turn-h h1 baseline", profile="claude", model=MODEL, effort=None, workspace=work
    )
    await adapter.send(chat, "Reply with the single word ok.")
    await adapter.wait_turn(chat)
    await adapter.send(chat, FORTY)
    turn = await adapter.wait_turn(chat)
    gap = (time.monotonic() - seen[chat]) * 1000
    log(
        f"baseline: the 50 ms poll returned {gap:.2f} ms after the CLI's turn end; "
        f"tools={len(turn.tools)}"
    )
    await harness.close_chat(chat)


async def sink_to(path: Path) -> Any:
    async def sink(chat: str, data: Any) -> None:
        row = {
            "pid": os.getpid(),
            "chat": chat,
            "event": data.get("hook_event_name"),
            "tool": data.get("tool_name", ""),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")

    return sink


H19_FIRST = (
    "Use the Read tool on each of f01.txt to f07.txt in the working folder, one file per call, "
    "one call at a time, each file whole with no offset and no limit. One line of each file "
    "holds a word starting with KEY-. Reply with the seven KEY- words."
)
H19_NEXT = (
    "Your last turn was cut off. Use the Read tool on each of f01.txt to f07.txt again, one "
    "file per call, one call at a time, each file whole with no offset and no limit. Reply with "
    "the seven KEY- words."
)


LANE_WINDOW = "200000"
"""Lane only. haiku's window on the plan is 1M (the CLI reports an effective 980,000 tokens), so
0.40 of it is about 392,000 tokens. The lane names a 200,000-token window so 0.40 is reached by
seven file reads."""


def lane_window() -> None:
    from qma.harness import launch  # noqa: PLC0415

    launch.CONSTANT_ENV = {**launch.CONSTANT_ENV, "CLAUDE_CODE_AUTO_COMPACT_WINDOW": LANE_WINDOW}


def tap_boundaries(path: Path) -> None:
    import claude_agent_sdk._internal.message_parser as parser  # noqa: PLC0415

    original = parser.parse_message

    def logged(data: dict[str, Any]) -> Any:
        if data.get("subtype") == "compact_boundary":
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(data.get("compact_metadata", {})) + "\n")
        return original(data)

    parser.parse_message = logged


async def h19_child(stage: str, state: Path) -> None:
    """One host process: `start` makes the chat and starts its turn, `resume` sends the next."""
    from qma.harness import Background, ChatPermissions, InjectedText, NewChat  # noqa: PLC0415

    lane_window()
    tap_boundaries(state / "boundaries.jsonl")
    harness, home = await ship_harness()
    events = state / "events.jsonl"
    harness.register_sink("lane-spans", await sink_to(events))
    try:
        if stage == "start":
            chat = await harness.start_chat(
                NewChat(
                    title="turn-h h19",
                    model=MODEL,
                    workspace=folder("h19"),
                    kind=Background(),
                    compact_at=0.4,
                    tools=("Read",),
                    hook_sink="lane-spans",
                    permissions=ChatPermissions("lane"),
                )
            )
            (state / "chat.txt").write_text(chat, encoding="utf-8")
            handle = await harness.run_turn(chat, InjectedText(H19_FIRST))
            await asyncio.wait_for(handle.result(), TURN_S)
            return
        chat = (state / "chat.txt").read_text(encoding="utf-8")
        handle = await harness.run_turn(chat, InjectedText(H19_NEXT))
        env = cli_env(home, chat)
        done = await asyncio.wait_for(handle.result(), TURN_S)
        (state / "resumed.json").write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "compact_env": env.get(COMPACT),
                    "compact_window": env.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW"),
                    "status": done.status,
                    "text": done.text,
                    "compactions": list(done.compactions),
                    "tools": len(done.tools),
                    "context": done.context,
                }
            ),
            encoding="utf-8",
        )
    finally:
        await harness.close()


def child(stage: str, state: Path) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [sys.executable, __file__, "h19-child", stage, str(state)],
        stdout=(state / f"{stage}.out").open("ab"),
        stderr=subprocess.STDOUT,
    )


def rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


async def h19(log: Log) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.home import read_record  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    state = SCRATCH / f"turn-h-h19-state-{uuid.uuid4().hex[:8]}"
    state.mkdir(parents=True)
    files_to_read(folder("h19"), 7, 700)
    first = child("start", state)
    deadline = time.monotonic() + TURN_S
    while not any(r["event"] == "PostToolUse" for r in rows(state / "events.jsonl")):
        if time.monotonic() > deadline or first.poll() is not None:
            break
        await asyncio.sleep(0.2)
    first.kill()
    first.wait(60)
    chat = (state / "chat.txt").read_text(encoding="utf-8")
    log(f"chat {chat}; host {first.pid} killed after events {rows(state / 'events.jsonl')}")
    record = read_record(QmxHome(SHIP_HOME), chat)
    log(
        f"record at the kill: turn={record.turn if record else None} "
        f"compact_at={record.config.compact_at if record else None} "
        f"hook_sink={record.config.hook_sink if record else None}"
    )
    second = child("resume", state)
    second.wait(TURN_S)
    resumed = json.loads((state / "resumed.json").read_text(encoding="utf-8"))
    log(f"resumed turn: {resumed}")
    late = [r for r in rows(state / "events.jsonl") if r["pid"] == resumed["pid"]]
    log(f"events from the resumed host: {late}")
    home = QmxHome(SHIP_HOME)
    blocks = control_service(home).events("sessions", 0, chat, 1000)
    needs = [
        e["data"]["block"]["content"]
        for e in blocks
        if e["data"].get("type") == "block" and e["data"]["block"]["type"] == "needs_you"
    ]
    log(f"needs_you blocks: {needs}")
    log.check(
        "the record kept compact_at 0.4 and the sink name",
        bool(
            record and record.config.compact_at == 0.4 and record.config.hook_sink == "lane-spans"
        ),
        record.config if record else None,
    )
    log.check(
        "the resumed CLI holds the 40 % compaction setting",
        resumed["compact_env"] == "40",
        resumed["compact_env"],
    )
    boundaries = rows(state / "boundaries.jsonl")
    log(f"compact boundaries the resumed CLI sent: {boundaries}")
    first = boundaries[0].get("pre_tokens", 0) if boundaries else 0
    log.check(
        "the resumed turn compacted at 0.40 of the 200,000-token lane window",
        bool(resumed["compactions"]) and 0.4 * 180_000 <= first < 0.4 * 200_000 + 25_000,
        {"turn compactions": resumed["compactions"], "first pre_tokens": first},
    )
    posts = [r for r in late if r["event"] == "PostToolUse" and r["chat"] == chat]
    log.check("PostToolUse events from the resumed host arrived", len(posts) >= 1, len(posts))


async def cache(log: Log) -> None:
    """Chat a in one folder, chat b in another, then chat a2 in a's folder as the control. With
    `exclude_dynamic_sections` the folder's own sections move into the first user message,
    which sits after the cached system prefix, so b writes that message and nothing else; a2,
    whose first message matches a's, writes almost nothing."""
    from qma.harness import Background, InjectedText, NewChat  # noqa: PLC0415

    nonce = uuid.uuid4().hex
    brief = f"Run brief {nonce}. " + "Keep every answer short and plain. " * 400
    harness, _ = await ship_harness()
    usages = {}
    folders = {"a": "a", "b": "b", "a2": "a"}
    try:
        for name, where in folders.items():
            chat = await harness.start_chat(
                NewChat(
                    title=f"turn-h cache {name}",
                    model=MODEL,
                    workspace=folder(f"cache-{where}-{nonce[:6]}"),
                    kind=Background(),
                    append_system_prompt=brief,
                )
            )
            handle = await harness.run_turn(chat, InjectedText("Reply with the single word ok."))
            done = await asyncio.wait_for(handle.result(), TURN_S)
            usages[name] = done.usage
            log(f"chat {name} {chat}: status={done.status} usage={done.usage}")
            await harness.close_chat(chat)
    finally:
        await harness.close()
    a, b, a2 = usages["a"], usages["b"], usages["a2"]
    shared = a.cache_write_tokens - b.cache_write_tokens
    seen = {
        "a_write": a.cache_write_tokens,
        "a_read": a.cache_read_tokens,
        "b_read": b.cache_read_tokens,
        "b_write": b.cache_write_tokens,
        "a2_write": a2.cache_write_tokens,
        "shared_prefix_a_wrote": shared,
    }
    log.check(
        "the second folder's chat read the whole prefix a wrote except its own first message",
        shared > 0 and b.cache_read_tokens - a.cache_read_tokens >= 0.7 * shared,
        seen,
    )
    log.check(
        "the control chat in a's folder wrote under 5 % of what b wrote",
        a2.cache_write_tokens < 0.05 * b.cache_write_tokens,
        seen,
    )


async def h2(log: Log) -> None:
    from qma.harness import Background, InjectedText, NewChat  # noqa: PLC0415

    work = folder("h2")
    (work / "secret-word.txt").write_text("the word is HERON\n", encoding="utf-8")
    harness, _ = await ship_harness()
    try:
        chat = await harness.start_chat(
            NewChat(title="turn-h h2", model=MODEL, workspace=work, kind=Background(), tools=())
        )
        first = await harness.run_turn(chat, InjectedText("Reply with the single word ok."))
        await asyncio.wait_for(first.result(), TURN_S)
        await harness.close_chat(chat)
        handle = await harness.run_turn(
            chat, InjectedText("Use the Read tool on secret-word.txt and tell me the word.")
        )
        done = await asyncio.wait_for(handle.result(), TURN_S)
        log(f"resumed turn: status={done.status} text={(done.text or '')[:200]!r}")
        log.check("the resumed tools=() chat ran no tool", done.tools == (), done.tools)
        log.check("the word stayed unread", "HERON" not in (done.text or ""), done.text)
    finally:
        await harness.close()


async def h18(log: Log) -> None:
    import psutil  # noqa: PLC0415
    from qma.harness import Background, InjectedText, NewChat  # noqa: PLC0415

    harness, home = await ship_harness()
    try:
        chat = await harness.start_chat(
            NewChat(title="turn-h h18", model=MODEL, workspace=folder("h18"), kind=Background())
        )
        handle = await harness.run_turn(chat, InjectedText("Reply with the single word ok."))
        await asyncio.wait_for(handle.result(), TURN_S)
        pid = cli_pid(home, chat)
        alive_before = pid is not None and psutil.pid_exists(pid)
        await harness.close_chat(chat)
        await asyncio.sleep(1)
        alive_after = pid is not None and psutil.pid_exists(pid)
        log(f"CLI pid {pid}: alive before {alive_before}, after close {alive_after}")
        log.check("the finished chat's CLI ran before the close", alive_before, pid)
        log.check("no CLI process of it is left", not alive_after, pid)
    finally:
        await harness.close()


async def h20(log: Log) -> None:
    from qma.harness import NewChat, OperatorText  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    harness, home = await ship_harness()
    try:
        chat = await harness.start_chat(
            NewChat(title="turn-h h20 copilot", model=MODEL, workspace=folder("h20"))
        )
        handle = await harness.run_turn(
            chat,
            OperatorText(
                "Call the mcp__qmx_workflows__drafts_put tool exactly once to save a draft "
                "workflow named turn-h-draft with a minimal document of your choice. Report the "
                "tool's reply in one line, even if it is an error."
            ),
        )
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(handle.result(), 240)
        events = control_service(home).events("sessions", 0, chat, 1000)
        blocks = [e["data"]["block"] for e in events if e["data"].get("type") == "block"]
        asks = [b for b in blocks if b["type"] == "permission"]
        calls = [b for b in blocks if b["type"] == "tool" and "drafts_put" in str(b["content"])]
        log(f"tool blocks: {calls}")
        log(f"permission blocks: {asks}")
        log.check("the draft save ran", bool(calls), len(calls))
        log.check("no ask appeared", asks == [], asks)
    finally:
        await harness.close()


HOOK = """import json, sys, pathlib
data = json.load(sys.stdin)
with pathlib.Path(sys.argv[1]).open("a", encoding="utf-8") as out:
    out.write(json.dumps({"chat": data.get("session_id"), "tool": data.get("tool_name")}) + "\\n")
"""


async def h41(log: Log) -> None:
    from qma.harness import Background, InjectedText, NewChat, OperatorText  # noqa: PLC0415

    work = folder("h41")
    (work / "note.txt").write_text("the note says blue\n", encoding="utf-8")
    script, seen = work / "hook.py", work / f"hooked-{uuid.uuid4().hex[:6]}.jsonl"
    script.write_text(HOOK, encoding="utf-8")
    command = f"'{Path(sys.executable).as_posix()}' '{script.as_posix()}' '{seen.as_posix()}'"
    hooks = {"PostToolUse": [{"hooks": [{"type": "command", "command": command}]}]}
    harness, _ = await ship_harness()
    try:
        workflow = await harness.start_chat(
            NewChat(
                title="turn-h h41 workflow",
                model=MODEL,
                workspace=work,
                kind=Background(),
                claude_hooks=hooks,
            )
        )
        copilot = await harness.start_chat(
            NewChat(title="turn-h h41 copilot", model=MODEL, workspace=work)
        )
        ask = "Use the Read tool on note.txt, then say what it says."
        for chat, prompt in ((workflow, InjectedText(ask)), (copilot, OperatorText(ask))):
            handle = await harness.run_turn(chat, prompt)
            done = await asyncio.wait_for(handle.result(), TURN_S)
            log(f"{chat}: status={done.status} tools={[t.name for t in done.tools]}")
        lines = rows(seen)
        log(f"hook lines: {lines}")
        log.check(
            "the hook ran in the workflow chat",
            any(r["chat"] == workflow and r["tool"] == "Read" for r in lines),
            lines,
        )
        log.check(
            "the hook did not run in the copilot chat",
            not any(r["chat"] == copilot for r in lines),
            lines,
        )
    finally:
        await harness.close()


LANES = {"h1": h1, "h19": h19, "cache": cache, "h2": h2, "h18": h18, "h20": h20, "h41": h41}


def main() -> int:
    if sys.argv[1:2] == ["h19-child"]:
        boot()
        use_fake_home()
        asyncio.run(h19_child(sys.argv[2], Path(sys.argv[3])))
        return 0
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    if lane not in LANES:
        raise SystemExit(f"usage: turn_lanes.py {{{','.join(LANES)}}}")
    require_lock()
    log = Log(f"owner-turn-h-{lane}")
    boot()
    use_fake_home()
    asyncio.run(LANES[lane](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
