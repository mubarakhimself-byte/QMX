"""The operator checks through the temporary console (HP15, `04-baseline.md` section 4).

Every lane types into `python -m qma.console` running in its own console window
(`console_window.ConsoleWindow`), answers each ask the way the check says, reads the screen
back, saves it as `<slug>.log` and the window as `<slug>.png` in `QMA_EVIDENCE_DIR`, and checks
the effect on disk or through the routes. Plan chats run on haiku in the ship home; HOME,
USERPROFILE and the app data folders point at a throwaway folder.

    1         /login in a throwaway home shows the choices (claude.ai only); the ship console
              says it is signed in with Max and /usage shows the five-hour window.
    2-4       check 2 (tool steps, then the answer), 3 (asks before each write and command,
              hello.txt holds "goodbye") and 4 (the rejected delete leaves it), recorded as
              a video; the chat id is kept for the later lanes.
    5         fake model in a throwaway home, served in this process: the order proposal asks
              and is refused, the terminal order is denied by the money gate. Positions are
              SKIPPED (no [brokers] row, no read-only broker token).
    6-11      check 6 (only QMX's skills) and check 11 (a helper starts and finishes).
    7-before  names under ~/.claude/skills and ~/.claude/projects, before the lanes.
    7-after   the same names after, compared. Names only; nothing there is read or written.
    8-9       /provider openrouter after its y/N warning, check 2 again under a $0.03 spend
              guard, /usage names openrouter, back to the plan. Check 9 SKIPPED.
    12-13     a new console (so a new host): /resume, recall hello.txt without tools, /usage.
    commands  /rewind restores a file, /export, /mode plan, /effort high, /doctor, Ctrl+C.
    canary    /export in a throwaway home redacts a fake sk-ant token and the provider key.
    perf      five console turns and five drive.py turns, interleaved, first-delta medians.

    op_checks_console.py <lane> [--video]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from common import EVIDENCE, SCRATCH, SHIP_HOME, Log, boot, throwaway_env
from console_window import FFMPEG, ConsoleWindow

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
REVIEW: Final = SHIP / "review"
PORT: Final = 8876
MODEL: Final = "haiku"
WORKSPACE: Final = SCRATCH / "hp15-ws"
STATE: Final = Path(EVIDENCE or ".") / "console-state.json"
TOOL_LINE: Final = re.compile(r"^\* [A-Za-z][\w:.-]*\(")
READ_ONLY: Final = r"(cat|ls|type|dir|Get-Content|Get-ChildItem)\b"
READ_ONLY_SHELL: Final = re.compile(rf"^\* (Bash|PowerShell)\({READ_ONLY}")
WRITE_STEP: Final = re.compile(rf"^\* (Write|Edit|NotebookEdit|Bash|PowerShell)\((?!{READ_ONLY})")
README: Final = (
    "# Lantern demo\n\nThis folder holds a tiny demo. `greet.py` prints a greeting for the "
    "lighthouse keeper, and `notes.txt` lists three chores.\n"
)
CHECK2: Final = "What is in this folder? Summarise the README."
CHECK3: Final = (
    "Make a file hello.txt with today's date, show it using a terminal command, then change "
    "the text to goodbye."
)
CHECK4: Final = "Delete hello.txt"
CHECK6: Final = "List your skills and slash commands."
CLI_SKILLS: Final = frozenset(
    {
        "code-review", "dataviz", "update-config", "keybindings-help", "simplify", "loop",
        "fewer-permission-prompts", "schedule", "claude-api", "run", "plugin-authoring", "init",
        "security-review",
    }
)  # fmt: skip
"""Skills the bundled CLI 2.1.299 ships itself, which vanilla Claude Code lists too. His own
`~/.claude/skills` has a `code-review` of its own; the name alone cannot tell them apart."""
CHECK11: Final = (
    "Use a helper agent to count the files in this folder while you tell me today's date."
)
CHECK13: Final = "What file did we make first?"
BROKEN: Final = "Use the Edit tool to change hello.txt so it holds only the word broken."
COUNT: Final = "Write the numbers from 1 to 3000 as words, one per line. Do not use any tools."
SPEND_BUDGET_USD: Final = 0.03
DEEPSEEK_FLASH_ROW: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "deepseek/deepseek-v4.1-flash"),
}


def evidence(name: str) -> Path:
    return Path(EVIDENCE or ".") / name


def console_env() -> dict[str, str]:
    return dict(os.environ) | throwaway_env()


def open_console(
    title: str, *, home: Path = SHIP_HOME, port: int = PORT, extra: list[str] | None = None
) -> ConsoleWindow:
    argv = [sys.executable, "-m", "qma.console", "--home", str(home), "--port", str(port)]
    argv += ["--workspace", str(WORKSPACE), "--model", MODEL, *(extra or [])]
    window = ConsoleWindow(title, argv, cwd=WORKSPACE, env=console_env())
    window.wait(seconds=180)
    return window


def turn_lines(window: ConsoleWindow, start: int) -> list[str]:
    return [line for line in window.screen()[0][start:] if line.strip()]


def mark(window: ConsoleWindow) -> int:
    return window.screen()[1]


def run_turn(
    window: ConsoleWindow, log: Log, text: str, answers: list[str], *, seconds: float = 300
) -> list[str]:
    start = mark(window)
    log(f"type: {text}  (answers {answers})")
    window.send(text, answers, seconds=seconds)
    lines = turn_lines(window, start)
    for line in lines:
        log(f"  | {line}")
    return lines


def final_answer(lines: list[str]) -> str:
    """The text from the turn's last answer line to the prompt."""
    starts = [
        n for n, line in enumerate(lines) if line.startswith("* ") and not TOOL_LINE.match(line)
    ]
    return " ".join(lines[starts[-1] :]).removesuffix(">").strip() if starts else ""


def asked_steps(lines: list[str]) -> list[tuple[str, bool]]:
    """Each tool line and whether the console's next line is the ask for it."""
    return [
        (line, n + 1 < len(lines) and lines[n + 1].startswith("? "))
        for n, line in enumerate(lines)
        if TOOL_LINE.match(line)
    ]


def tools_before_answer(lines: list[str]) -> tuple[list[str], int]:
    """The tool lines, and how many of them come before the first answer line."""
    tools = [line for line in lines if TOOL_LINE.match(line)]
    answer = next(
        (n for n, line in enumerate(lines) if line.startswith("* ") and not TOOL_LINE.match(line)),
        len(lines),
    )
    return tools, sum(1 for line in lines[:answer] if TOOL_LINE.match(line))


def save_screen(window: ConsoleWindow, slug: str) -> None:
    evidence(f"{slug}.screen.log").write_text(window.text() + "\n", encoding="utf-8")
    window.shot(evidence(f"{slug}.png"))


def chat_of(window: ConsoleWindow) -> str:
    start = mark(window)
    window.send("/status")
    found = next(
        (
            m.group(1)
            for line in turn_lines(window, start)
            if (m := re.search(r"chat (\S+) in", line))
        ),
        None,
    )
    if found is None:
        raise RuntimeError("the console named no chat")
    return found


def remember(**values: str) -> None:
    current = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    STATE.write_text(json.dumps(current | values, indent=2), encoding="utf-8")


def recall(key: str) -> str:
    return str(json.loads(STATE.read_text(encoding="utf-8"))[key])


def resume(window: ConsoleWindow, log: Log, chat: str) -> None:
    run_turn(window, log, f"/resume {chat}", [])


def fresh_workspace() -> None:
    shutil.rmtree(WORKSPACE, ignore_errors=True)
    WORKSPACE.mkdir(parents=True)
    (WORKSPACE / "README.md").write_text(README, encoding="utf-8")
    (WORKSPACE / "greet.py").write_text('print("Good evening, keeper")\n', encoding="utf-8")
    (WORKSPACE / "notes.txt").write_text("trim wick\npolish lens\nlog weather\n", encoding="utf-8")


def hello() -> str:
    path = WORKSPACE / "hello.txt"
    return path.read_text(encoding="utf-8").strip() if path.exists() else "<missing>"


def lane_2_4(log: Log, video: bool) -> None:
    log("trunk's console is the stdin loop in scripts/live/copilot_build_app.py, which needs the")
    log("LangChain providers; there is no trunk console on these routes to compare, so lane 1")
    log("runs check 2 at head only.")
    fresh_workspace()
    window = open_console("QMA console checks 2-4")
    recorder = window.record(evidence("hp15-checks-2-4-raw.mp4"), 600) if video else None
    try:
        lines = run_turn(window, log, CHECK2, ["y"])
        tools, before = tools_before_answer(lines)
        read_readme = any(line.startswith("* Read(") and "README" in line for line in tools)
        log.check(
            "check 2: tool steps print before the answer and the README is read",
            before >= 2 and read_readme,
            f"{before} of {len(tools)} tool lines before the answer; README read {read_readme}",
        )
        answer = " ".join(lines).lower()
        log.check(
            "check 2: the answer summarises the README",
            "greet" in answer and "lighthouse" in answer,
            "greet/lighthouse named"
            if "greet" in answer and "lighthouse" in answer
            else answer[-300:],
        )
        save_screen(window, "hp15-check2")
        remember(chat=chat_of(window))
        lines = run_turn(window, log, CHECK3, ["y"])
        steps = asked_steps(lines)
        writes = [(step, asked) for step, asked in steps if WRITE_STEP.match(step)]
        unasked = [step for step, asked in writes if not asked]
        log.check(
            "check 3: it asked before every write and every command that is not read-only",
            bool(writes) and unasked == [],
            f"{len(writes)} write or command steps, unasked {unasked}",
        )
        read_only = [step for step, asked in steps if READ_ONLY_SHELL.match(step) and not asked]
        log(
            f"read-only shell steps that ran without an ask, as in vanilla Claude Code: {read_only}"
        )
        log.check('check 3: hello.txt holds "goodbye"', hello().lower() == "goodbye", hello())
        lines = run_turn(window, log, CHECK4, ["n"])
        asks = [line for line in lines if line.startswith("? ")]
        log.check("check 4: it asked before deleting", bool(asks), asks)
        log.check("check 4: the rejected delete left hello.txt", hello() != "<missing>", hello())
        save_screen(window, "hp15-checks-3-4")
    finally:
        if recorder is not None:
            recorder.communicate(b"q", timeout=30)
        window.close()
    if video:
        fit_video(log, evidence("hp15-checks-2-4-raw.mp4"), REVIEW / "HP15-review.mp4")


def fit_video(log: Log, raw: Path, final: Path, longest: float = 58.0) -> None:
    ffprobe = str(Path(FFMPEG).with_name("ffprobe"))
    asked = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0"]
    probe = subprocess.run([*asked, str(raw)], capture_output=True, text=True, check=True)
    duration = float(probe.stdout.strip())
    speed = max(1.0, duration / longest)
    final.parent.mkdir(parents=True, exist_ok=True)
    fitted = [FFMPEG, "-y", "-loglevel", "error", "-i", str(raw), "-vf", f"setpts=PTS/{speed:.3f}"]
    subprocess.run([*fitted, "-an", str(final)], check=True)
    log(f"video {duration:.0f} s recorded, played at {speed:.2f}x into {final}")


def lane_1(log: Log) -> None:
    login_home = SCRATCH / "hp15-login-home"
    shutil.rmtree(login_home, ignore_errors=True)
    window = open_console("QMA console login", home=login_home, port=PORT + 1)
    try:
        start = mark(window)
        window.type("/login")
        deadline = time.monotonic() + 90
        screen = ""
        while time.monotonic() < deadline:
            screen = window.text()
            if "Paste code here" in screen or "Select login method" in screen:
                break
            if "Choose the text style" in screen and "Dark mode" in screen:
                window.type("", enter=True)
                time.sleep(2)
            time.sleep(1)
        save_screen(window, "hp15-check1-login")
        console_lines = turn_lines(window, start)
        log.check(
            "check 1: the throwaway /login offers claude.ai only",
            "Login method pre-selected: Subscription Plan" in screen
            and "Anthropic Console" not in screen,
            next((line for line in console_lines if "pre-selected" in line), "<no line>"),
        )
        window.ctrl_c()
        window.ctrl_c()
        window.wait(seconds=60)
    finally:
        window.close()
    log("the login was abandoned at the code prompt; nothing signed in to the throwaway home")
    window = open_console("QMA console check 1")
    try:
        banner = window.text()
        log.check(
            "check 1: the console says it is signed in with the Max plan",
            "Signed in to Claude Max (claude.ai)" in banner,
            [line for line in banner.splitlines() if "Signed in" in line],
        )
        lines = run_turn(window, log, "/usage refresh", [])
        five = next((line for line in lines if "5-hour window:" in line), "")
        log.check(
            "check 1: /usage shows the five-hour window with a percentage and a reset time",
            "% used" in five and "resets" in five,
            five,
        )
        save_screen(window, "hp15-check1")
    finally:
        window.close()


def his_skill_names() -> list[str]:
    folder = Path.home() / ".claude" / "skills"
    return sorted(path.name for path in folder.iterdir()) if folder.is_dir() else []


def lane_6_11(log: Log) -> None:
    window = open_console("QMA console checks 6 and 11")
    try:
        resume(window, log, recall("chat"))
        lines = run_turn(window, log, CHECK6, ["y"])
        said = "\n".join(lines).casefold()
        shared = [name for name in his_skill_names() if name in CLI_SKILLS]
        his = [
            name
            for name in his_skill_names()
            if "-" in name and name not in CLI_SKILLS and name.casefold() in said
        ]
        log(f"his skill names that are also the bundled CLI's own skills: {shared}")
        log.check(
            "check 6: none of his personal skills appear",
            his == [] and "poteto" not in said and "bmad" not in said,
            his or "none",
        )
        log.check(
            "check 6: QMX's own skills appear",
            "qmx" in said,
            "qmx named" if "qmx" in said else said[-300:],
        )
        save_screen(window, "hp15-check6")
        lines = run_turn(window, log, CHECK11, ["y"])
        started = [line for line in lines if "helper started:" in line]
        finished = [line for line in lines if re.search(r"helper (completed|failed|stopped)", line)]
        log.check(
            "check 11: a helper started and finished",
            bool(started) and bool(finished),
            started + finished,
        )
        answer = final_answer(lines)
        today = (
            time.strftime("%B").casefold() in answer.casefold()
            or time.strftime("%Y-%m-%d") in answer
        )
        count = sum(1 for path in WORKSPACE.iterdir() if path.is_file())
        log.check(
            f"check 11: the last answer holds today's date and the count, {count} files",
            today and bool(re.search(rf"\b{count}\b\s+files", answer)),
            answer[-300:],
        )
        save_screen(window, "hp15-check11")
    finally:
        window.close()


def lane_12_13(log: Log) -> None:
    chat = recall("chat")
    window = open_console("QMA console checks 12 and 13")
    try:
        start = mark(window)
        window.type("/resume")
        listing = window.wait("resume which?", seconds=60)
        rows = turn_lines(window, start)
        number = next(
            (
                m.group(1)
                for line in rows
                if (m := re.match(r"\s+(\d+)\. What is in this folder", line))
            ),
            "1",
        )
        log(f"/resume listed {len(rows) - 1} chats; picking {number} ({listing.strip()})")
        window.type(number)
        window.wait(seconds=60)
        log.check("check 13: /resume picked the check-2 chat", chat in chat_of(window), chat)
        lines = run_turn(window, log, CHECK13, ["n"])
        tools, _ = tools_before_answer(lines)
        answer = " ".join(lines)
        log.check(
            "check 13: it answers hello.txt without searching",
            "hello.txt" in answer and tools == [],
            f"tools {tools}; hello.txt named {'hello.txt' in answer}",
        )
        lines = run_turn(window, log, "/usage", [])
        text = "\n".join(lines)
        cache = re.search(r"tokens, this chat, claude: .*cache read (\d+)", text)
        log.check(
            "check 12: /usage shows chat tokens, cache reads, the 50% cap and the 5-hour %",
            bool(cache and int(cache.group(1)) > 0)
            and "background cap 50%" in text
            and bool(re.search(r"5-hour window: \d+% used", text)),
            [line for line in lines if "this chat" in line or "cap" in line or "5-hour" in line],
        )
        save_screen(window, "hp15-checks-12-13")
    finally:
        window.close()


def lane_commands(log: Log) -> None:
    (WORKSPACE / "hello.txt").write_text("goodbye", encoding="utf-8")
    log("hello.txt reset to goodbye, the state check 3 leaves")
    window = open_console("QMA console commands")
    try:
        resume(window, log, recall("chat"))
        run_turn(window, log, BROKEN, ["y"])
        log.check("the overwrite took effect first", hello().lower() == "broken", hello())
        start = mark(window)
        window.type("/rewind")
        window.wait("restore files to before which message?", seconds=60)
        rows = turn_lines(window, start)
        numbers = [
            m.group(1) for line in rows if (m := re.match(r"\s+(\d+)\. Use the Edit tool", line))
        ]
        log(f"/rewind listed: {rows}")
        window.type(numbers[-1] if numbers else "0")
        window.wait(seconds=120)
        log.check('/rewind restored hello.txt to "goodbye"', hello().lower() == "goodbye", hello())
        lines = run_turn(window, log, "/export", [])
        folder = next(
            (line.split("Exported to ", 1)[1] for line in lines if "Exported to " in line), ""
        )
        files = (
            sorted(p.relative_to(folder).as_posix() for p in Path(folder).rglob("*.*"))
            if folder
            else []
        )
        shaped = [
            name
            for name in files
            if re.search(
                r"sk-ant-[a-z]+\d\d-[A-Za-z0-9_-]{20,}",
                (Path(folder) / name).read_text(encoding="utf-8"),
            )
        ]
        log.check(
            "/export wrote the transcript, asks and usage with no token shape left",
            {"transcript.jsonl", "approvals.jsonl", "chat.json"} <= set(files) and shaped == [],
            f"{files}; token shapes in {shaped}",
        )
        lines = run_turn(window, log, "/mode plan", [])
        log.check(
            "/mode plan applies with no warning",
            any("Now claude / haiku / plan" in line for line in lines)
            and not any("  ! " in line for line in lines),
            lines[1:],
        )
        lines = run_turn(window, log, "/effort high", [])
        log.check(
            "/effort high shows its warning or none, then applies or names why not",
            any("Now " in line or "  ! " in line for line in lines),
            lines[1:],
        )
        run_turn(window, log, "/mode default", [])
        lines = run_turn(window, log, "/doctor", [])
        log.check(
            "/doctor lists its checks", sum("[ok]" in line for line in lines) >= 5, len(lines)
        )
        start = mark(window)
        log(f"type: {COUNT}")
        window.type(COUNT)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and not any(
            line.startswith("* ") for line in turn_lines(window, start)
        ):
            time.sleep(0.1)
        window.ctrl_c()
        window.wait(seconds=120)
        rows = turn_lines(window, start)
        for line in rows[-6:]:
            log(f"  | {line}")
        interrupted = any("Interrupted" in line for line in rows)
        finished = any("three thousand" in line.casefold() for line in rows)
        log.check(
            "Ctrl+C ended the turn early and the console kept running",
            interrupted and not finished and window.host.poll() is None,
            f"interrupted {interrupted}; reached three thousand {finished}; {len(rows)} lines",
        )
        lines = run_turn(window, log, "/status", [])
        log.check(
            "the console answers after Ctrl+C",
            any("turn idle" in line for line in lines),
            lines[1:],
        )
        save_screen(window, "hp15-commands")
    finally:
        window.close()


def lane_8_9(log: Log) -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415
    from spend import DEEPSEEK_FLASH, Ledger, key_usage, openrouter_key  # noqa: PLC0415

    secret = openrouter_key()
    if secret is None:
        log("BLOCKED: keyring qmx/openrouter is empty")
        raise SystemExit(3)
    ledger = Ledger(
        evidence("openrouter-spend.tsv"), SPEND_BUDGET_USD, DEEPSEEK_FLASH, key_usage(secret)
    )
    control = control_service(QmxHome(SHIP_HOME))
    found = dict(control.settings_get("providers"))
    control.settings_put("providers", found | {"openrouter": DEEPSEEK_FLASH_ROW})
    log("ship home [providers] += openrouter -> deepseek/deepseek-v4.1-flash for the check")
    window = open_console("QMA console checks 8-9")
    try:
        resume(window, log, recall("chat"))
        start = mark(window)
        window.type("/provider openrouter")
        prompt = window.wait("[y/N]", seconds=120)
        rows = turn_lines(window, start)
        warning = [line for line in rows if line.startswith("  ! ")]
        log.check(
            "check 8: a cost and cache warning shows before the switch",
            bool(warning),
            [*warning, prompt],
        )
        window.type("y")
        window.wait(seconds=180)
        log(f"  | {turn_lines(window, start)[-1]}")

        async def spend() -> list[str]:
            return await asyncio.to_thread(run_turn, window, log, CHECK2, ["y"])

        lines = asyncio.run(ledger.spend("hp15 check 8", 6, 2000, spend))
        tools, before = tools_before_answer(lines)
        log.check("check 8: on OpenRouter it answers using its tools", before >= 1, tools)
        lines = run_turn(window, log, "/usage", [])
        row = next((line for line in lines if "tokens, this chat, openrouter" in line), "")
        log.check(
            "check 8: /usage shows OpenRouter for that reply",
            "calls" in row and "(0 calls)" not in row,
            row,
        )
        save_screen(window, "hp15-checks-8-9")
        window.type("/provider claude")
        window.wait("[y/N]", seconds=60)
        window.type("y")
        window.wait(seconds=180)
    finally:
        window.close()
        control.settings_put("providers", found)
        log(f"ship home [providers] restored to {sorted(control.settings_get('providers'))}")
    log(f"OpenRouter spend this lane: {ledger.spent():.6f} USD (budget {SPEND_BUDGET_USD})")
    log("SKIPPED check 9: OpenRouter is the only keyed provider row")


def claude_names() -> dict[str, list[str]]:
    root = Path(os.environ.get("QMA_REAL_HOME", str(Path.home()))) / ".claude"
    return {
        folder: sorted(p.name for p in (root / folder).iterdir())
        if (root / folder).is_dir()
        else []
        for folder in ("skills", "projects")
    }


def lane_7(log: Log, phase: str) -> None:
    before_path = evidence("hp15-check7-before.json")
    names = claude_names()
    log(
        f"~/.claude/skills: {len(names['skills'])} names; "
        f"~/.claude/projects: {len(names['projects'])} names"
    )
    if phase == "before":
        before_path.write_text(json.dumps(names, indent=2), encoding="utf-8")
        return
    before = json.loads(before_path.read_text(encoding="utf-8"))
    for folder in ("skills", "projects"):
        added = sorted(set(names[folder]) - set(before[folder]))
        log(f"{folder} before: {before[folder]}")
        log(f"{folder} after:  {names[folder]}")
        qmx = [
            name for name in names[folder] if re.search(r"qma-live|qma-ship|hp15|^qmx", name, re.I)
        ]
        log.check(
            f"check 7: no QMX entry in ~/.claude/{folder}",
            qmx == [],
            f"added {added}; QMX-named {qmx}",
        )


async def fake_host_lane(
    log: Log,
    slug: str,
    script: list[Any],
    drive: Callable[[ConsoleWindow, str], None],
    setup: Callable[[Path], None] | None = None,
) -> Any:
    """A throwaway home whose one chat runs on the fake model, served in this process on a free
    port behind the keyring bearer the console reads, and a console window resumed on it."""
    from approval_lane import Host, fake_session  # noqa: PLC0415
    from common import use_fake_home  # noqa: PLC0415
    from qmx_control.server import local_token  # noqa: PLC0415

    use_fake_home()
    root, fake, session = await fake_session(slug, script, tools=["Bash"], workspace=WORKSPACE)
    if setup is not None:
        setup(root)
    try:
        host = Host(session)
        host.secret = local_token()
        async with host:
            log(f"fake-model host on port {host.port}, home {root}, chat {session.chat}")

            def run() -> None:
                window = open_console(
                    f"QMA console {slug}",
                    home=root,
                    port=host.port,
                    extra=["--resume", session.chat],
                )
                try:
                    drive(window, session.chat)
                finally:
                    window.close()

            await asyncio.to_thread(run)
    finally:
        await session.harness.close()
        fake.stop()
    return root, fake


def lane_5(log: Log) -> None:
    from common import use_fake_key  # noqa: PLC0415
    from fake_model import Turn, text, tool_use  # noqa: PLC0415
    from money_lane import results  # noqa: PLC0415
    from op_checks_3_to_5 import PLACE_DIRECTLY, POSITIONS_SKIPPED  # noqa: PLC0415
    from s06_money import broker_connections  # noqa: PLC0415
    from s29_approvals import ORDER_A, propose, put_brokers, rows  # noqa: PLC0415

    use_fake_key()
    fresh_workspace()
    log(POSITIONS_SKIPPED)
    script = [
        propose(ORDER_A),
        Turn([text("The order proposal was refused.")]),
        Turn([tool_use("Bash", {"command": PLACE_DIRECTLY, "description": "place"})]),
        Turn([text("The terminal order was blocked.")]),
    ]
    screens: dict[str, list[str]] = {}

    def drive(window: ConsoleWindow, _: str) -> None:
        screens["order"] = run_turn(
            window, log, "Place a buy order for 0.01 lots of EURUSD.", ["n"]
        )
        screens["terminal"] = run_turn(
            window, log, "Use the terminal to place that order directly.", ["n"]
        )
        save_screen(window, "hp15-check5")

    root, fake = asyncio.run(fake_host_lane(log, "hp15-check5", script, drive, put_brokers))
    found = list(results(fake).values())
    for tool, tool_input, is_error, said in found:
        log(f"  call {tool} {json.dumps(tool_input)[:120]} error={is_error}: {said[:200]!r}")
    order = screens.get("order", [])
    log.check(
        "check 5: the order proposal asked with the money rule's reason and was refused",
        any(line.startswith("? qmx:propose_order") for line in order)
        and any("order proposal always asks" in line for line in order)
        and bool(found)
        and found[0][2]
        and any(line.strip() == "reject (resolved)" for line in order),
        [line for line in order if "propose_order" in line or "reason" in line or "reject" in line],
    )
    terminal = screens.get("terminal", [])
    log.check(
        "check 5: the terminal order was denied by the gate, naming the money rule",
        any("money rule:" in line for line in terminal)
        and len(found) > 1
        and found[1][2]
        and "money rule:" in found[1][3],
        [line for line in terminal if "money rule" in line],
    )
    log.check("check 5: no order proposal row was added", rows(root) == [], len(rows(root)))
    held = broker_connections()
    log.check("check 5: no connection to a broker port", held == [], held)


def lane_canary(log: Log) -> None:
    from common import CANARY, use_fake_key  # noqa: PLC0415
    from fake_model import FAKE_KEY, FAKE_REF, Turn, text  # noqa: PLC0415

    use_fake_key()
    fresh_workspace()
    script = [Turn([text(f"Canary line: {CANARY} and {FAKE_KEY} end.")])]
    exported: dict[str, str] = {}

    def drive(window: ConsoleWindow, _: str) -> None:
        run_turn(window, log, "Repeat the canary line.", ["n"])
        lines = run_turn(window, log, "/export", [])
        folder = next(
            (line.split("Exported to ", 1)[1] for line in lines if "Exported to " in line), ""
        )
        exported.update(
            {
                p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8")
                for p in Path(folder).rglob("*.*")
            }
            if folder
            else {}
        )

    asyncio.run(fake_host_lane(log, "hp15-canary", script, drive))
    transcript = exported.get("transcript.jsonl", "")
    leaked = [name for name, body in exported.items() if CANARY in body or FAKE_KEY in body]
    log.check(
        "export redacts the sk-ant canary and the provider key value in every file",
        bool(transcript) and leaked == [],
        f"files {sorted(exported)}; leaked in {leaked}",
    )
    marks = {
        mark: mark in transcript for mark in ("[redacted sk-ant token]", f"[redacted {FAKE_REF}]")
    }
    log.check("the transcript shows both redaction marks", all(marks.values()), marks)


def drive_turn(chat: str) -> float | None:
    drive = Path(__file__).parent / "drive.py"
    done = subprocess.run(
        [
            sys.executable,
            str(drive),
            "--port",
            str(PORT),
            "turn",
            chat,
            "Reply with the single word ok.",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    found = re.search(r"first text delta on the live channel after ([\d.]+) s", done.stdout)
    return float(found.group(1)) if found else None


def new_drive_chat() -> str:
    import httpx  # noqa: PLC0415
    import keyring  # noqa: PLC0415

    bearer = keyring.get_password("qmx/control-token", "control-token")
    made = httpx.post(
        f"http://127.0.0.1:{PORT}/api/chats",
        json={"title": "hp15 perf drive", "model": MODEL, "workspace": str(WORKSPACE)},
        headers={"Authorization": f"Bearer {bearer}"},
        timeout=60,
    )
    made.raise_for_status()
    return str(made.json()["session_id"])


def lane_perf(log: Log) -> None:
    fresh_workspace()
    window = open_console("QMA console perf", extra=["--timing"])
    console_s: list[float] = []
    drive_s: list[float] = []
    try:
        run_turn(window, log, "Reply with the single word ready.", ["n"])
        drive_chat = new_drive_chat()
        drive_turn(drive_chat)
        for round_number in range(1, 6):
            seconds = drive_turn(drive_chat)
            log(f"round {round_number} drive.py first delta {seconds}")
            if seconds is not None:
                drive_s.append(seconds)
            lines = run_turn(window, log, "Reply with the single word ok.", ["n"])
            found = next(
                (
                    re.search(r"first delta after ([\d.]+) s", line)
                    for line in lines
                    if "first delta" in line
                ),
                None,
            )
            if found:
                console_s.append(float(found.group(1)))
        save_screen(window, "hp15-perf")
    finally:
        window.close()
    drive_median, console_median = statistics.median(drive_s), statistics.median(console_s)
    log(f"baseline drive.py median {drive_median:.2f} s over {drive_s}")
    log(f"console median {console_median:.2f} s over {console_s}")
    log.check(
        "perf: the console's first-delta median is within 300 ms of drive.py's",
        len(drive_s) == 5 and len(console_s) == 5 and console_median - drive_median <= 0.3,
        f"{console_median - drive_median:+.2f} s",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "lane",
        choices=[
            "1",
            "2-4",
            "5",
            "6-11",
            "7-before",
            "7-after",
            "8-9",
            "12-13",
            "commands",
            "canary",
            "perf",
        ],
    )
    parser.add_argument("--video", action="store_true", help="record lane 2-4 for the review")
    args = parser.parse_args()
    os.environ.setdefault("QMA_REAL_HOME", str(Path.home()))
    boot()
    log = Log(f"owner-hp15-{args.lane}")
    match args.lane:
        case "1":
            lane_1(log)
        case "2-4":
            lane_2_4(log, args.video)
        case "5":
            lane_5(log)
        case "6-11":
            lane_6_11(log)
        case "7-before" | "7-after":
            lane_7(log, args.lane.removeprefix("7-"))
        case "8-9":
            lane_8_9(log)
        case "12-13":
            lane_12_13(log)
        case "commands":
            lane_commands(log)
        case "canary":
            lane_canary(log)
        case _:
            lane_perf(log)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
