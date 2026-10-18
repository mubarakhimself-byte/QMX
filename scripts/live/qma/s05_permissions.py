"""S5, permissions, on the fake model. `[claude] permissions` denies `Bash(git push *)`, asks
for `Bash(rm *)` and allows `Bash(echo *)`. Every ask is answered through
`POST /api/approvals/{ask_id}`.

    chat 1, workspace A   git push, rm hello.txt (Reject), echo, touch made.txt (AllowAlways)
    chat 2, workspace A   plan mode: Write planned.txt (Reject)
    chat 3, workspace A   touch made.txt
    chat 4, workspace B   touch made.txt (Reject)

The CLI does not refuse a plan-mode Write by itself: it asks, as in default mode, and an
AllowOnce writes the file (measured, CLI 2.1.299, fake model). The model's plan-mode
instructions are what keep a real model from trying.

PASS when push is denied without an ask, rm asks and hello.txt stays, echo runs without an
ask, the plan-mode write asks and Reject leaves no file, and the remembered rule lands in
`[claude.remembered."<workspace A>"]`, lets chat 3 run without an ask, and does not apply in
workspace B.

    s05_permissions.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from approval_lane import (
    ALLOW_ALWAYS,
    Host,
    answered_turn,
    fake_session,
    in_order,
    new_chat,
    reject,
    tools_asked,
)
from common import SCRATCH, Log, boot, put_claude, use_fake_home, use_fake_key
from fake_model import Turn, text, tool_use
from money_lane import results

TOOLS = ["Bash", "Write"]
RULES = {
    "deny": ["Bash(git push *)"],
    "ask": ["Bash(rm *)"],
    "allow": ["Bash(echo *)"],
}


def bash(command: str) -> Turn:
    return Turn([tool_use("Bash", {"command": command, "description": "scripted"})])


def outcome(fake: Any, needle: str) -> tuple[bool, str]:
    """The last call whose input holds `needle`: is_error and its result text."""
    for _tool, tool_input, is_error, said in reversed(list(results(fake).values())):
        if needle in str(tool_input):
            return is_error, said
    return True, "<no call>"


def workspace(name: str) -> Path:
    folder = SCRATCH / "hp9-s05" / name
    folder.mkdir(parents=True, exist_ok=True)
    for stale in ("made.txt", "planned.txt"):
        (folder / stale).unlink(missing_ok=True)
    return folder


async def run(log: Log) -> None:
    from qma.harness.home import workspace_key  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    here, there = workspace("a"), workspace("b")
    (here / "hello.txt").write_text("hello", encoding="utf-8")
    done = Turn([text("done")])
    script = [
        bash("git push origin main"),
        bash("rm hello.txt"),
        bash("echo s05-echo-ran"),
        bash("touch made.txt"),
        done,
        Turn([tool_use("Write", {"file_path": str(here / "planned.txt"), "content": "x"})]),
        done,
        bash("touch made.txt"),
        done,
        bash("touch made.txt"),
        done,
    ]
    root, fake, session = await fake_session("hp9-s05", script, tools=TOOLS, workspace=here)
    put_claude(root, {"permissions": RULES})
    try:
        async with Host(session) as host:
            first_chat = await new_chat(session, "s05 rules", here)
            first = await answered_turn(
                log, host, first_chat, in_order([reject("keep it")], [ALLOW_ALWAYS])
            )
            for ask in first.asks:
                log(f"  ask {ask['tool']} {ask['input'].get('command')} always={ask.get('always')}")
            push = outcome(fake, "git push")
            log.check(
                "push denied without an ask",
                push[0] and not any("git push" in str(a["input"]) for a in first.asks),
                push[1][:160],
            )
            asked_rm = [a for a in first.asks if "rm hello" in str(a["input"])]
            log.check(
                "rm asked, Reject kept hello.txt",
                len(asked_rm) == 1 and (here / "hello.txt").exists(),
                f"{len(asked_rm)} ask(s); hello.txt exists={(here / 'hello.txt').exists()}",
            )
            echo = outcome(fake, "echo s05")
            log.check(
                "echo ran without an ask",
                not echo[0]
                and "s05-echo-ran" in echo[1]
                and not any("echo" in str(a["input"]) for a in first.asks),
                echo[1][:160],
            )
            statuses = [a.status for a in first.answered]
            log.check(
                "touch asked and AllowAlways resolved",
                statuses == ["resolved", "resolved"] and (here / "made.txt").exists(),
                f"{statuses}; made.txt exists={(here / 'made.txt').exists()}",
            )
            claude = control_service(session.home).settings_get("claude")
            remembered = claude.get("remembered", {})
            log(f"  [claude.remembered] {remembered}")
            log.check(
                "the rule landed under workspace A only",
                list(remembered) == [workspace_key(here)]
                and bool(remembered[workspace_key(here)]["allow"]),
                remembered,
            )

            (here / "made.txt").unlink()
            planned = await new_chat(session, "s05 plan", here, mode="plan")
            plan = await answered_turn(log, host, planned, in_order([reject()]))
            write = outcome(fake, "planned.txt")
            log.check(
                "plan mode asked before the write, and Reject blocked it",
                tools_asked(plan) == ["Write"] and write[0] and not (here / "planned.txt").exists(),
                f"asks={tools_asked(plan)}; {write[1][:160]!r}",
            )

            again = await new_chat(session, "s05 remembered", here)
            third = await answered_turn(log, host, again, in_order([reject()]))
            ran = outcome(fake, "touch made")
            log.check(
                "next chat in workspace A ran it without an ask",
                third.asks == [] and (here / "made.txt").exists(),
                f"asks={tools_asked(third)}; {ran[1][:120]!r}",
            )

            elsewhere = await new_chat(session, "s05 elsewhere", there)
            fourth = await answered_turn(log, host, elsewhere, in_order([reject()]))
            log.check(
                "workspace B still asked",
                tools_asked(fourth) == ["Bash"] and not (there / "made.txt").exists(),
                f"asks={tools_asked(fourth)}; made.txt exists={(there / 'made.txt').exists()}",
            )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp9-s05")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
