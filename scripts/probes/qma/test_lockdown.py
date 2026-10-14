# ruff: noqa: S101
from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from common import Lockdown, guard, plan_options

if TYPE_CHECKING:
    from claude_agent_sdk import HookContext, HookInput

B1 = Lockdown(commands=frozenset({"echo hp1-b1-marker"}), tools=frozenset({"ToolSearch"}))


def decide(lockdown: Lockdown, tool: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    call = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    hook_input, context = cast("HookInput", call), cast("HookContext", {"signal": None})
    return dict(asyncio.run(guard(lockdown)(hook_input, "toolu_1", context)))


def error_of(make: Callable[[], object]) -> str:
    try:
        make()
    except (ValueError, TypeError) as error:
        return f"{type(error).__name__}: {error}"
    return "no error"


def denied(lockdown: Lockdown, tool: str, tool_input: dict[str, Any]) -> bool:
    output = decide(lockdown, tool, tool_input).get("hookSpecificOutput", {})
    return output.get("permissionDecision") == "deny"


def test_the_guard_lets_only_the_exact_expected_bash_command_run() -> None:
    assert not denied(B1, "Bash", {"command": "echo hp1-b1-marker"})
    assert not denied(B1, "Bash", {"command": "  echo hp1-b1-marker\n"})
    assert denied(B1, "Bash", {"command": "cmdkey /list"})
    assert denied(B1, "Bash", {"command": "echo hp1-b1-marker; cmdkey /list"})
    assert denied(B1, "Bash", {"command": "echo hp1-b1-marker && cat ~/.claude/.credentials.json"})
    assert denied(B1, "Bash", {"command": 'echo "hp1-b1-marker"'})
    assert denied(B1, "Bash", {})


def test_the_guard_denies_every_tool_outside_the_probe_and_says_why() -> None:
    assert not denied(B1, "ToolSearch", {"query": "ping"})
    assert decide(
        B1, "Read", {"file_path": "D:/QMX-worktrees/qma-ship/home/claude/.credentials.json"}
    ) == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "This probe chat may not use Read.",
        }
    }
    assert denied(B1, "WebFetch", {"url": "https://example.com"})
    assert denied(B1, "mcp__probe__ping", {})


def test_a_chat_with_no_commands_may_not_run_bash_at_all() -> None:
    assert denied(Lockdown(), "Bash", {"command": ""})
    assert denied(Lockdown(), "Bash", {"command": "echo hp1-b1-marker"})


def test_the_cli_gets_only_the_built_in_tools_the_probe_needs() -> None:
    assert B1.builtins == ["Bash", "ToolSearch"]
    assert Lockdown(tools=frozenset({"WebSearch", "mcp__probe__ping"})).builtins == ["WebSearch"]
    assert Lockdown().builtins == []


def test_bash_with_any_input_cannot_be_allowed() -> None:
    assert error_of(lambda: Lockdown(tools=frozenset({"Bash"}))) == (
        "ValueError: Bash is allowed only through exact commands"
    )


def test_a_probe_cannot_override_what_the_lockdown_sets() -> None:
    for name in ("tools", "allowed_tools", "cwd", "permission_mode", "can_use_tool", "add_dirs"):
        assert error_of(partial(plan_options, Lockdown(), **{name: None})) == (
            f"TypeError: the lockdown sets ['{name}']; a probe cannot override them"
        )
