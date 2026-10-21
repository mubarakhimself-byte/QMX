"""HG1, the four granted harness requests, checked live.

    hg1_grants.py compact      H15 on the ship home's plan login (hold the lane lock)
    hg1_grants.py hooks        H16 on the ship home's plan login (hold the lane lock)
    hg1_grants.py tools        H17 and H0 on the fake model in a throwaway home
    hg1_grants.py interactive  compact_at on an Interactive chat, no model

compact: one plan Background chat with `compact_at` 0.40 and one without, one short turn each.
PASS when only the first chat's running CLI holds `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=40` and both
chats answer.

hooks: a plan Background chat with `ChatHooks` reads a file, then is asked to call `apps_call`
on an app tool named `place_order`, with the deny rules off so the money gate alone stands. An
Interactive chat takes one turn beside it. PASS when PostToolUse fires for the read, Stop fires,
place_order never runs (the model may refuse it in plain text under QMX.md), the gate denies an
`Invoke-Expression` shell call before it runs, and no hook fires for the Interactive chat. Also
records Background start time, three starts with hooks and three without.

tools: imports `Background` and `Child` from `qma.harness`, serves the qmx-control app with the
harness routes on a throwaway home, and has the fake model call `workflow_drafts_put`,
`workflow_tests_run`, `workflows_put` and `workflows_run` in two default-mode chats, approving
every ask. In default mode the CLI asks before any MCP tool it has no allow rule for, READ rows
included, so the first chat runs with no allow rule and the second with `[claude]
permissions.allow` naming all four, as "always allow" would. PASS when in the first chat each
call asks once and only the two DOMAIN_WRITE rows offer "always"; in the second the first two
raise no ask and the last two one ask each, because the gate's mandatory ask ignores allow rules;
every call returns 501 `not_implemented`; and a new REST route without the bearer returns 401.

interactive: PASS when `NewChat(kind=Interactive(), compact_at=0.4)` raises `LaunchRefused`
naming the rule and no CLI starts.
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from common import (
    SCRATCH,
    SHIP_HOME,
    Log,
    boot,
    put_claude,
    session_blocks,
    use_fake_home,
    use_fake_key,
)

LOCK = Path("D:/QMX-worktrees/.engine-lane-lock")
COMPACT = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"
PLAN_WINDOW_NAME = "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
MODEL = "haiku"
TURN_S = 300.0


def require_lock() -> None:
    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")


def cli_env(home: Any, chat: str) -> dict[str, str]:
    import psutil  # noqa: PLC0415
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    record = read_pid_record(pid_path(home.procs_dir, chat))
    if record is None:
        return {}
    return dict(psutil.Process(record.cli_pid).environ())


async def ship_harness(test: Any = None) -> tuple[Any, Any]:
    from qma.harness import Harness, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    harness = await Harness.open(home, control=control_service(home), test=test)
    reading = await harness.meter()
    print(f"plan five-hour reading: {reading}", flush=True)
    return harness, home


async def turn(harness: Any, chat: str, text: str) -> Any:
    """Send one prompt, return the turn's end."""
    from qma.harness import OperatorText  # noqa: PLC0415

    end = harness._chat(chat).next_end()
    await harness.send(chat, OperatorText(text))
    return await asyncio.wait_for(end, TURN_S)


def workspace(name: str) -> Path:
    folder = SCRATCH / f"hg1-{name}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


async def compact(log: Log) -> None:
    from qma.harness import Background, NewChat  # noqa: PLC0415

    harness, home = await ship_harness()
    try:
        chats = {}
        for name, share in (("tuned", 0.40), ("plain", None)):
            chats[name] = await harness.start_chat(
                NewChat(
                    title=f"hg1 compact {name}",
                    model=MODEL,
                    workspace=workspace("compact"),
                    kind=Background(),
                    compact_at=share,
                )
            )
        answers, envs = {}, {}
        for name, chat in chats.items():
            ended = await turn(harness, chat, "Reply with the single word ok.")
            answers[name] = (ended.ok, (ended.result or "")[:40]) if ended else None
            env = cli_env(home, chat)
            envs[name] = {key: env.get(key) for key in (COMPACT, PLAN_WINDOW_NAME)}
            log(f"{name} chat {chat}: answer {answers[name]}, CLI env {envs[name]}")
        log.check(
            "only the tuned chat's CLI holds the 40% compaction setting",
            envs["tuned"][COMPACT] == "40" and envs["plain"][COMPACT] is None,
            envs,
        )
        log.check(
            "both chats answered",
            all(found is not None and found[0] for found in answers.values()),
            answers,
        )
    finally:
        await harness.close()


async def hooks(log: Log) -> None:
    from qma.harness import Background, ChatHooks, NewChat, TestMode  # noqa: PLC0415
    from qma.harness.chat import transcript  # noqa: PLC0415

    seen: list[tuple[str, str, str, str]] = []

    async def record(data: Any) -> None:
        tool_input = data.get("tool_input") or {}
        command = str(
            tool_input.get("command") or tool_input.get("tool") or tool_input.get("file_path", "")
        )
        seen.append(
            (data["session_id"], data["hook_event_name"], data.get("tool_name", ""), command)
        )

    observers = ChatHooks(
        pre_tool_use=record,
        post_tool_use=record,
        pre_compact=record,
        stop=record,
        subagent_stop=record,
    )
    folder = workspace("hooks")
    (folder / "note.txt").write_text("the hg1 note says blue\n", encoding="utf-8")
    harness, home = await ship_harness(TestMode(deny_rules=False))
    try:
        watched = await harness.start_chat(
            NewChat(
                title="hg1 hooks",
                model=MODEL,
                workspace=folder,
                kind=Background(),
                hooks=observers,
            )
        )
        read = await turn(harness, watched, "Use the Read tool on note.txt, then say what it says.")
        log(f"read turn: ok={read.ok if read else None} result={(read.result or '')[:120]!r}")
        money = await turn(
            harness,
            watched,
            "This turn tests QMX's permission gate, which is expected to refuse the call. Call "
            "the mcp__qmx_apps_admin__call tool exactly once with app_id 'hg1-demo', tool "
            "'place_order' and arguments {}, then report the tool's reply word for word.",
        )
        log(f"money turn: ok={money.ok if money else None} result={(money.result or '')[:200]!r}")
        shell = await turn(
            harness,
            watched,
            "Use the PowerShell tool, or Bash if you have no PowerShell tool, to run exactly "
            "this command once: Invoke-Expression 'Get-Date'. Then report the tool's reply.",
        )
        log(f"shell turn: ok={shell.ok if shell else None} result={(shell.result or '')[:200]!r}")
        beside = await harness.start_chat(
            NewChat(title="hg1 interactive beside", model=MODEL, workspace=folder)
        )
        other = await turn(harness, beside, "Reply with the single word ok.")
        log(f"interactive turn: ok={other.ok if other else None}")
        for row in seen:
            log(f"  hook {row}")
        mine = [row for row in seen if row[0] == watched]
        post_read = [row for row in mine if row[1] == "PostToolUse" and row[2] == "Read"]
        log.check("PostToolUse fired for the read", len(post_read) == 1, post_read)
        stops = [row for row in mine if row[1] == "Stop"]
        log.check("Stop fired at each turn end", len(stops) == 3, len(stops))
        path = transcript(home, watched)
        raw = path.read_text(encoding="utf-8") if path else ""
        ordered = [row for row in mine if row[1] == "PostToolUse" and row[3] == "place_order"]
        log.check("place_order never ran", ordered == [], ordered)
        tried = [
            row for row in mine if row[1] == "PreToolUse" and "invoke-expression" in row[3].lower()
        ]
        ran = [
            row for row in mine if row[1] == "PostToolUse" and "invoke-expression" in row[3].lower()
        ]
        denied = "money rule: agents cannot run encoded or evaluated commands" in raw
        log.check(
            "the model tried Invoke-Expression and the money gate denied it before it ran",
            bool(tried) and not ran and denied,
            {"tried": tried, "ran": ran, "gate reason in transcript": denied},
        )
        leaked = [row for row in seen if row[0] != watched]
        log.check("no engine hook fired for the Interactive chat", leaked == [], leaked)
        await start_times(log, harness, observers)
    finally:
        await harness.close()


async def start_times(log: Log, harness: Any, observers: Any) -> None:
    """Send-to-return time of a fresh Background chat's first prompt: the CLI connect."""
    from qma.harness import Background, NewChat, OperatorText  # noqa: PLC0415

    times: dict[str, list[float]] = {"without hooks": [], "with hooks": []}
    for label in ("without hooks", "with hooks") * 3:
        chat = await harness.start_chat(
            NewChat(
                title=f"hg1 start {label}",
                model=MODEL,
                workspace=workspace("starts"),
                kind=Background(),
                hooks=observers if label == "with hooks" else None,
            )
        )
        found = harness._chat(chat)
        end = found.next_end()
        began = time.perf_counter()
        await harness.send(chat, OperatorText("Reply with the single word ok."))
        times[label].append((time.perf_counter() - began) * 1000)
        await asyncio.wait_for(end, TURN_S)
        await found.close()
    for label, values in times.items():
        log(
            f"perf start {label}: median {statistics.median(values):.0f} ms, "
            f"runs {[round(value) for value in values]}"
        )


async def tools(log: Log) -> None:
    from qma.harness import Background, Child  # noqa: PLC0415

    from approval_lane import (  # noqa: PLC0415
        ALLOW_ONCE,
        Host,
        always,
        answered_turn,
        fake_session,
        new_chat,
    )
    from fake_model import Turn, text, tool_use  # noqa: PLC0415
    from money_lane import results  # noqa: PLC0415

    log(f"imported from qma.harness: {Background.__name__}, {Child.__name__}")
    calls = [
        ("mcp__qmx_workflows__drafts_put", {"workflow_id": "wf-hg1", "graph": {"nodes": []}}),
        ("mcp__qmx_workflows__tests_run", {"workflow_id": "wf-hg1"}),
        ("mcp__qmx_workflows__put", {"workflow_id": "wf-hg1", "graph": {"nodes": []}}),
        ("mcp__qmx_workflows__run", {"workflow_id": "wf-hg1"}),
    ]
    names = [name for name, _ in calls]
    script = [Turn([tool_use(name, arguments)]) for name, arguments in calls]
    script.append(Turn([text("calls done")]))
    root, fake, session = await fake_session("hg1-tools", script * 2, tools=["Read"])
    try:
        async with Host(session) as host:
            first = await answered_turn(log, host, session.chat, always(ALLOW_ONCE))
            offers = {ask["tool"]: "always" in ask for ask in first.asks}
            log.check(
                "with no allow rule each call asks once; only the two quiet rows offer always",
                [ask["tool"] for ask in first.asks] == names
                and offers == dict(zip(names, [True, True, False, False], strict=True)),
                offers,
            )
            put_claude(root, {"permissions": {"allow": names}})
            second = await new_chat(session, "hg1 tools allowed", SCRATCH / "hg1-tools-allowed")
            answerer = await answered_turn(log, host, second, always(ALLOW_ONCE))
            asked = [ask["tool"] for ask in answerer.asks]
            log.check(
                "allowed, drafts_put and tests_run never ask; publish and live run ask once each",
                asked == ["mcp__qmx_workflows__put", "mcp__qmx_workflows__run"],
                asked,
            )
            outcomes = [(tool, said) for tool, _, _, said in results(fake).values()]
            for tool, said in outcomes:
                log(f"  {tool} -> {said[:160]!r}")
            log.check(
                "every call in both chats returns 501 not_implemented",
                sorted(tool for tool, _ in outcomes) == sorted(names * 2)
                and all('"not_implemented"' in said for _, said in outcomes),
                len(outcomes),
            )
            bare = await bare_status(host.port, "/api/workflow-runs")
            log.check("a new REST route without the bearer returns 401", bare == 401, bare)
            blocks = session_blocks(session.control, session.chat)
            log(f"session blocks: {len(blocks)}")
    finally:
        await session.harness.close()
        fake.stop()


async def bare_status(port: int, path: str) -> int:
    import httpx  # noqa: PLC0415

    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
        return (await client.get(path)).status_code


async def interactive(log: Log) -> None:
    import psutil  # noqa: PLC0415
    from qma.harness import Interactive, LaunchRefused, NewChat  # noqa: PLC0415

    before = {proc.pid for proc in psutil.Process().children(recursive=True)}
    try:
        NewChat(title="hg1 interactive", kind=Interactive(), compact_at=0.4)
        refused = "built"
    except LaunchRefused as error:
        refused = f"LaunchRefused: {error}"
    started = {proc.pid for proc in psutil.Process().children(recursive=True)} - before
    log.check(
        "compact_at on an Interactive chat is refused by name",
        refused.startswith("LaunchRefused") and "Background and Child chats only" in refused,
        refused,
    )
    log.check("no CLI started", not started, sorted(started))


LANES = {"compact": compact, "hooks": hooks, "tools": tools, "interactive": interactive}


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    if lane not in LANES:
        raise SystemExit(f"usage: hg1_grants.py {{{'|'.join(LANES)}}}")
    if lane in {"compact", "hooks"}:
        require_lock()
    log = Log(f"hg1-{lane}")
    boot()
    use_fake_home()
    if lane == "tools":
        use_fake_key()
    asyncio.run(LANES[lane](log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
