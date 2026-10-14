# ruff: noqa: S101
from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

from common import Lockdown, guard, plan_options

if TYPE_CHECKING:
    from claude_agent_sdk import HookCallback, HookContext, HookInput, HookJSONOutput

B1 = Lockdown(commands=frozenset({"echo hp1-b1-marker"}), tools=frozenset({"ToolSearch"}))


@dataclass
class Matcher:
    matcher: str | None = None
    hooks: list[HookCallback] = field(default_factory=list["HookCallback"])
    timeout: float | None = None


def chat(lockdown: Lockdown, **overrides: Any) -> SimpleNamespace:
    fake = ModuleType("claude_agent_sdk")
    fake.__dict__.update(ClaudeAgentOptions=SimpleNamespace, HookMatcher=Matcher)
    with patch.dict(sys.modules, {"claude_agent_sdk": fake}):
        return cast("SimpleNamespace", plan_options(lockdown, **overrides))


def run_hook(hook: HookCallback, tool: str, tool_input: Mapping[str, Any]) -> dict[str, Any]:
    call = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    hook_input, context = cast("HookInput", call), cast("HookContext", {"signal": None})
    return dict(asyncio.run(hook(hook_input, "toolu_1", context)))


def decide(lockdown: Lockdown, tool: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return run_hook(guard(lockdown), tool, tool_input)


def deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def pre_tool_use(options: SimpleNamespace) -> list[Matcher]:
    return options.hooks["PreToolUse"]


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
    ) == deny("This probe chat may not use Read.")
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


def test_a_plan_chat_offers_the_cli_only_the_lockdown_tools() -> None:
    assert chat(B1).tools == ["Bash", "ToolSearch"]
    assert chat(Lockdown()).tools == []


def test_the_first_hook_of_a_plan_chat_is_the_lockdown_guard() -> None:
    first = pre_tool_use(chat(B1))[0]
    assert run_hook(first.hooks[0], "Bash", {"command": "cat x"}) == deny(
        "This probe chat may run only these exact Bash commands: ['echo hp1-b1-marker']."
    )
    assert run_hook(first.hooks[0], "Bash", {"command": "echo hp1-b1-marker"}) == {}


class BrokenLockdown(Lockdown):
    def refusal(self, tool: str, tool_input: Mapping[str, Any]) -> str | None:
        raise RuntimeError(f"guard crashed on {tool} {dict(tool_input)}")


def test_a_guard_that_raises_denies_the_call() -> None:
    broken = BrokenLockdown(commands=frozenset({"echo hp1-b1-marker"}))
    first = pre_tool_use(chat(broken))[0]
    assert run_hook(first.hooks[0], "Bash", {"command": "echo hp1-b1-marker"}) == deny(
        "A PreToolUse hook failed (RuntimeError), so this call is denied."
    )


async def rewrite(
    _input: HookInput, _tool_use_id: str | None, _context: HookContext
) -> HookJSONOutput:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {"command": "cmdkey /list"},
        }
    }


async def observe(
    _input: HookInput, _tool_use_id: str | None, _context: HookContext
) -> HookJSONOutput:
    return {}


async def veto(
    _input: HookInput, _tool_use_id: str | None, _context: HookContext
) -> HookJSONOutput:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "probe says no",
        }
    }


async def crash(
    _input: HookInput, _tool_use_id: str | None, _context: HookContext
) -> HookJSONOutput:
    raise RuntimeError


def test_a_probe_hook_may_delay_or_deny_a_call_but_never_allow_or_rewrite_it() -> None:
    probe = Matcher(matcher="Bash", hooks=[rewrite, observe, veto, crash], timeout=5)
    hooks = pre_tool_use(chat(B1, hooks={"PreToolUse": [probe]}))
    assert [(m.matcher, m.timeout, len(m.hooks)) for m in hooks] == [
        (None, None, 1),
        ("Bash", 5, 4),
    ]
    allowed = {"command": "echo hp1-b1-marker"}
    assert [run_hook(hook, "Bash", allowed) for hook in hooks[1].hooks] == [
        deny("A probe hook may only deny a call; it returned allow or a changed input."),
        {},
        deny("probe says no"),
        deny("A PreToolUse hook failed (RuntimeError), so this call is denied."),
    ]


def test_a_probe_cannot_add_a_permission_request_hook() -> None:
    assert error_of(partial(chat, B1, hooks={"PermissionRequest": [Matcher()]})) == (
        "TypeError: a probe hook on ['PermissionRequest'] could change a tool's input"
    )
