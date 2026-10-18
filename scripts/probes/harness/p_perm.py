"""P-PERM (H39, AD-60, review 48 H3). The order of the guard, the CLI's own rules, `can_use_tool`
and the named policy in a Background chat in `default` mode.

The attempt overlay is the chat's working folder. The guard is a PreToolUse callback, first on
every call: it refuses a write into the fake store folder and, for probe safety, any Bash
command that is not one of this probe's exact commands. The CLI allow rule is
`Edit(//d/<overlay>/**)`, the form the pinned CLI matches for Write and Edit on Windows (a
`Write(...)` path rule and the `//D:/` form do not match). `can_use_tool` hands every ask to the
`engine` policy: declared tools are allowed, writes only under the overlay, anything else is
denied at once with a reason, and the declared irreversible tool waits on a deferral that an
inbox stand-in resolves allow after 3 s.

Chat A declares Write, Edit and the irreversible `notify`; Bash and `peek` are offered but not
declared. Chat B also declares Bash. One haiku turn per step:

- A1 Write under the overlay: passes by the allow rule, `can_use_tool` never sees it.
- A2 Write outside the overlay, A3 an undeclared read-only Bash (`echo`), A3W an undeclared
  Bash writing into the overlay, A4 `peek` (an MCP tool in no allow rule):
  each reaches the policy and is denied with its reason, which the tool result carries.
- A5 `notify`: waits on the deferral and runs when it resolves allow.
- B1 declared Bash writing outside the overlay: runs, is not committed and is not an output.
- B2 declared Bash writing into the store: refused by the guard before any other layer.

PASS when the guard saw every call first and each step behaves as above. The fake model then
records, at no plan cost, which Bash calls the CLI runs without asking `can_use_tool`. Fail: AGW is not
built, agent steps stay read-only as built, and the coordinator tells the operator.

    <venv>/Scripts/python.exe p_perm.py
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from common import (
    LIVE_QMA,
    PLAN_MODEL,
    Case,
    Log,
    QmxServer,
    Verdict,
    answers,
    fresh,
    home_env,
    lane_lock,
    plan_env,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

sys.path.append(str(LIVE_QMA))

FALLBACK: Final = (
    "AGW is not built, agent steps stay read-only as built, and the coordinator tells the operator"
)
DEFER_S: Final = 3.0
OUTPUTS: Final = ("result.txt",)
GUARD_STORE: Final = "guard: no write into a QMX store"
GUARD_SAFETY: Final = "guard: this probe allows only its exact Bash commands"
POLICY_UNDECLARED: Final = "engine policy: {tool} is not declared by this node"
POLICY_OUTSIDE: Final = "engine policy: writes only under the attempt overlay"


@dataclass
class Call:
    tool: str
    guard_at: float | None = None
    guard: str = "pass"
    asked_at: float | None = None
    policy: str | None = None
    reason: str | None = None
    waited: float | None = None
    ran: bool = False


@dataclass
class Chat:
    """One attempt: its overlay, its declaration, and every call each layer saw."""

    name: str
    root: Path
    declared: frozenset[str]
    irreversible: frozenset[str]
    commands: frozenset[str]
    calls: dict[str, Call] = field(default_factory=dict[str, Call])

    @property
    def overlay(self) -> Path:
        return self.root / "attempt-1"

    @property
    def store(self) -> Path:
        return self.root / "store"

    def call(self, tool_use_id: str, tool: str) -> Call:
        return self.calls.setdefault(tool_use_id, Call(tool))


def under(path: str, folder: Path) -> bool:
    return Path(path).resolve().is_relative_to(folder.resolve())


def drive_rule(folder: Path) -> str:
    posix = folder.resolve().as_posix()
    return f"Edit(//{posix[0].lower()}{posix[2:]}/**)"


def guard(chat: Chat) -> Any:
    async def hook(data: Any, tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        try:
            call = chat.call(str(tool_use_id), str(data["tool_name"]))
            call.guard_at = time.perf_counter()
            tool_input = data.get("tool_input", {})
            store = chat.store.as_posix()
            written = str(tool_input.get("file_path", ""))
            command = " ".join(str(tool_input.get("command", "")).split())
            if (written and under(written, chat.store)) or store in command.replace("\\", "/"):
                call.guard = GUARD_STORE
            elif call.tool == "Bash" and command not in chat.commands:
                call.guard = GUARD_SAFETY
            else:
                return {}
        except Exception as error:  # noqa: BLE001
            reason = f"guard failed closed: {error}"
        else:
            reason = call.guard
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }

    return hook


def ran(chat: Chat) -> Any:
    async def hook(data: Any, tool_use_id: str | None, _ctx: Any) -> dict[str, Any]:
        chat.call(str(tool_use_id), str(data["tool_name"])).ran = True
        return {}

    return hook


def engine_policy(chat: Chat, inbox: asyncio.Queue[asyncio.Future[bool]]) -> Any:
    from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny  # noqa: PLC0415

    async def can_use_tool(tool: str, tool_input: dict[str, Any], ctx: Any) -> Any:
        call = chat.call(str(ctx.tool_use_id), tool)
        call.asked_at = time.perf_counter()
        written = str(tool_input.get("file_path", ""))
        if tool not in chat.declared:
            call.policy, call.reason = "deny", POLICY_UNDECLARED.format(tool=tool)
        elif written and not under(written, chat.overlay):
            call.policy, call.reason = "deny", POLICY_OUTSIDE
        elif tool in chat.irreversible:
            call.policy = "defer"
            decided: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
            await inbox.put(decided)
            allowed = await decided
            call.waited = round(time.perf_counter() - call.asked_at, 2)
            call.policy = "defer->allow" if allowed else "defer->deny"
            if not allowed:
                call.reason = "inbox answered deny"
        else:
            call.policy = "allow"
        if call.reason:
            return PermissionResultDeny(message=call.reason)
        return PermissionResultAllow()

    return can_use_tool


async def inbox_stand_in(inbox: asyncio.Queue[asyncio.Future[bool]]) -> None:
    while True:
        decided = await inbox.get()
        await asyncio.sleep(DEFER_S)
        decided.set_result(True)


def commit(chat: Chat) -> list[str]:
    """What the engine keeps when the attempt ends ok: only the declared outputs."""
    work = chat.root / "work"
    work.mkdir(exist_ok=True)
    kept = []
    for name in OUTPUTS:
        if (chat.overlay / name).is_file():
            shutil.copy2(chat.overlay / name, work / name)
            kept.append(name)
    return kept


async def drive(say: Log, chat: Chat, steps: dict[str, str]) -> dict[str, Any]:
    from claude_agent_sdk import (  # noqa: PLC0415
        ClaudeAgentOptions,
        ClaudeSDKClient,
        HookMatcher,
    )

    chat.overlay.mkdir(parents=True)
    chat.store.mkdir()
    server = QmxServer({"peek": answers("PEEK-RAN"), "notify": answers("NOTIFY-RAN")})
    inbox: asyncio.Queue[asyncio.Future[bool]] = asyncio.Queue()
    rule = drive_rule(chat.overlay)
    options = ClaudeAgentOptions(
        env=plan_env(f"perm-{chat.name}"),
        cwd=str(chat.overlay),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        permission_mode="default",
        tools=["Write", "Edit", "Bash"],
        allowed_tools=[rule],
        mcp_servers={"qmx": server.config},  # type: ignore[dict-item]
        can_use_tool=engine_policy(chat, inbox),
        hooks={
            "PreToolUse": [HookMatcher(matcher=None, hooks=[guard(chat)])],
            "PostToolUse": [HookMatcher(matcher=None, hooks=[ran(chat)])],
        },
    )
    say(f"[{chat.name}] overlay {chat.overlay}, allow rule {rule}, declared {sorted(chat.declared)}")
    results: dict[str, Any] = {}
    worker = asyncio.create_task(inbox_stand_in(inbox))
    try:
        async with ClaudeSDKClient(options) as client:
            for step, prompt in steps.items():
                before = set(chat.calls)
                say(f"[{chat.name}] {step}: {prompt}")
                seen = await turn(client, prompt, say)
                first = next((tid for tid in chat.calls if tid not in before), None)
                text_by_id = {r["id"]: r for r in seen.tool_results}
                results[step] = {
                    "call": first,
                    "tool_uses": [u["name"] for u in seen.tool_uses],
                    "result": text_by_id.get(first or ""),
                    "model_turns": seen.num_turns,
                }
    finally:
        worker.cancel()
    for tid, call in chat.calls.items():
        cli = "passed with no ask (allow rule or read-only)" if call.asked_at is None and call.ran else "-"
        say(
            f"[{chat.name}] call {tid} {call.tool}: guard={call.guard} cli_rules={cli} "
            f"can_use_tool={'saw it' if call.asked_at is not None else 'not reached'} "
            f"policy={call.policy} reason={call.reason!r} waited={call.waited} ran={call.ran}"
        )
    return {
        "steps": results,
        "calls": {tid: vars(call) for tid, call in chat.calls.items()},
        "server_calls": server.calls,
        "committed": commit(chat),
        "files": sorted(p.relative_to(chat.root).as_posix() for p in chat.root.rglob("*") if p.is_file()),
        "allow_rule": rule,
    }


def verdict(observation: dict[str, Any]) -> Verdict:
    a, b = observation["a"], observation["b"]

    def call(chat: dict[str, Any], step: str) -> dict[str, Any]:
        found = chat["steps"].get(step, {}).get("call")
        return chat["calls"].get(found, {}) if found else {}

    def result_text(chat: dict[str, Any], step: str) -> str:
        return str((chat["steps"].get(step, {}).get("result") or {}).get("text", ""))

    every = [c for chat in (a, b) for c in chat["calls"].values()]
    first = all(
        c["guard_at"] is not None and (c["asked_at"] is None or c["guard_at"] < c["asked_at"])
        for c in every
    )
    a1, a2, a3, a3w, a4, a5 = (call(a, s) for s in ("A1", "A2", "A3", "A3W", "A4", "A5"))
    b1, b2 = call(b, "B1"), call(b, "B2")

    def denied(c: dict[str, Any], reason: str, step: str) -> bool:
        return (
            c.get("asked_at") is not None
            and c.get("policy") == "deny"
            and c.get("reason") == reason
            and not c.get("ran")
            and reason in result_text(a, step)
        )

    cases = (
        Case("the guard saw every call first", bool(every) and first, {"calls": len(every)}),
        Case(
            "A1 a write under the overlay passes by the allow rule without reaching can_use_tool",
            bool(a1) and a1["asked_at"] is None and a1["ran"] and "attempt-1/result.txt" in a["files"],
            a1,
        ),
        Case(
            "A2 a write outside the overlay reaches the policy and is denied with its reason",
            denied(a2, POLICY_OUTSIDE, "A2") and "outside-write.txt" not in a["files"],
            a2,
        ),
        Case(
            "A3 an undeclared Bash, read-only (A3) and writing (A3W), reaches the policy and is "
            "denied with its reason",
            denied(a3, POLICY_UNDECLARED.format(tool="Bash"), "A3")
            and denied(a3w, POLICY_UNDECLARED.format(tool="Bash"), "A3W")
            and "attempt-1/a3.txt" not in a["files"],
            {"A3": a3, "A3W": a3w},
        ),
        Case(
            "A4 an MCP tool in no allow rule reaches the policy and is denied with its reason",
            denied(a4, POLICY_UNDECLARED.format(tool="mcp__qmx__peek"), "A4")
            and "peek" not in a["server_calls"],
            a4,
        ),
        Case(
            "A5 the declared irreversible tool waits on the deferral and runs when it resolves allow",
            a5.get("policy") == "defer->allow"
            and (a5.get("waited") or 0) >= DEFER_S
            and a5.get("ran") is True
            and "notify" in a["server_calls"],
            a5,
        ),
        Case(
            "B1 a declared Bash writing outside the overlay runs, is not committed and is no output",
            bool(b1)
            and b1["guard"] == "pass"
            and b1["ran"]
            and "outside-bash.txt" in b["files"]
            and "outside-bash.txt" not in b["committed"]
            and "work/outside-bash.txt" not in b["files"],
            {**b1, "committed": b["committed"]},
        ),
        Case(
            "B2 a declared Bash writing into a store is refused by the guard",
            b2.get("guard") == GUARD_STORE
            and b2.get("asked_at") is None
            and not b2.get("ran")
            and "store/control.db" not in b["files"],
            b2,
        ),
    )
    return Verdict("P-PERM", cases, FALLBACK)


def commands(root: Path) -> dict[str, str]:
    run = root.as_posix()
    return {
        "A3": "echo a3-undeclared",
        "A3W": f'echo a3 > "{run}/attempt-1/a3.txt"',
        "B1": f'echo outside > "{run}/outside-bash.txt"',
        "B2": f'echo bad > "{run}/store/control.db"',
    }


async def run(say: Log) -> dict[str, Any]:
    root_a, root_b = fresh("perm-a-run"), fresh("perm-b-run")
    cmd_a, cmd_b = commands(root_a), commands(root_b)
    exact = "Use the Bash tool to run exactly this command, character for character: "
    chat_a = Chat(
        "a",
        root_a,
        declared=frozenset({"Write", "Edit", "mcp__qmx__notify"}),
        irreversible=frozenset({"mcp__qmx__notify"}),
        commands=frozenset({cmd_a["A3"], cmd_a["A3W"]}),
    )
    chat_b = Chat(
        "b",
        root_b,
        declared=frozenset({"Write", "Edit", "Bash"}),
        irreversible=frozenset(),
        commands=frozenset({cmd_b["B1"], cmd_b["B2"]}),
    )
    tail = " Make exactly one tool call. If it is refused, do not retry; reply with the refusal."
    a = await drive(
        say,
        chat_a,
        {
            "A1": f"Use the Write tool to create {chat_a.overlay.as_posix()}/result.txt with the content ok.{tail}",
            "A2": f"Use the Write tool to create {root_a.as_posix()}/outside-write.txt with the content x.{tail}",
            "A3": f"{exact}{cmd_a['A3']}{tail}",
            "A3W": f"{exact}{cmd_a['A3W']}{tail}",
            "A4": f"Call the tool mcp__qmx__peek once with no arguments.{tail}",
            "A5": f"Call the tool mcp__qmx__notify once with no arguments.{tail}",
        },
    )
    b = await drive(
        say, chat_b, {"B1": f"{exact}{cmd_b['B1']}{tail}", "B2": f"{exact}{cmd_b['B2']}{tail}"}
    )
    plan_turns = sum(s["model_turns"] for chat in (a, b) for s in chat["steps"].values())
    return {"a": a, "b": b, "plan_turns": plan_turns, "bash_mechanism": await bash_mechanism(say)}


BASH_VARIANTS: Final = (
    ("read-only", "echo hi", False),
    ("write in the folder", 'echo a > "{overlay}/a.txt"', False),
    ("write in the folder", 'echo a > "{overlay}/a.txt"', True),
    ("write outside", 'echo a > "{root}/o.txt"', True),
)


async def bash_mechanism(say: Log) -> list[dict[str, Any]]:
    """Which Bash calls the CLI runs without asking `can_use_tool`, with and without the overlay's
    Edit allow rule. The fake model makes each call, so no plan turn is spent and the call is
    exactly the one named."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient  # noqa: PLC0415
    from claude_agent_sdk import PermissionResultDeny  # noqa: PLC0415
    from fake_model import FAKE_KEY, MODEL, FakeModel, Turn, text, tool_use  # noqa: PLC0415

    found: list[dict[str, Any]] = []
    for index, (label, template, with_rule) in enumerate(BASH_VARIANTS):
        root = fresh(f"perm-mechanism-{index}")
        overlay = root / "attempt-1"
        overlay.mkdir()
        command = template.format(overlay=overlay.as_posix(), root=root.as_posix())
        fake = FakeModel([Turn([tool_use("Bash", {"command": command})]), Turn([text("done")])])
        fake.start()
        asked: list[str] = []

        async def refuse(tool: str, _input: dict[str, Any], _ctx: Any, seen: list[str] = asked) -> Any:
            seen.append(tool)
            return PermissionResultDeny(message="policy deny")

        options = ClaudeAgentOptions(
            env=home_env(root / "home", root / "claude")
            | {"ANTHROPIC_BASE_URL": fake.url, "ANTHROPIC_API_KEY": FAKE_KEY},
            cwd=str(overlay),
            model=MODEL,
            setting_sources=[],
            strict_mcp_config=True,
            permission_mode="default",
            tools=["Write", "Edit", "Bash"],
            allowed_tools=[drive_rule(overlay)] if with_rule else [],
            can_use_tool=refuse,
        )
        try:
            async with ClaudeSDKClient(options) as client:
                await turn(client, "go", say)
        finally:
            fake.stop()
        row = {
            "bash": label,
            "edit_allow_rule": with_rule,
            "reached_can_use_tool": bool(asked),
            "wrote": sorted(p.name for p in root.rglob("*.txt")),
        }
        say(f"[mechanism] {row}")
        found.append(row)
    return found


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-perm")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    say(f"haiku plan model turns: {observation['plan_turns']}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
