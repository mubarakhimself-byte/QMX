# ruff: noqa: S101
from __future__ import annotations

import asyncio
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

import common
from common import Lockdown, Marker, Provider, guard, plan_options, provider_env

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
    for name in (
        "tools",
        "allowed_tools",
        "cwd",
        "permission_mode",
        "can_use_tool",
        "add_dirs",
        "setting_sources",
        "plugins",
        "strict_mcp_config",
    ):
        assert error_of(partial(plan_options, Lockdown(), **{name: None})) == (
            f"TypeError: a probe may not set {name}: the lockdown sets it"
        )


def test_a_probe_cannot_set_an_option_no_probe_needs() -> None:
    for name, value in (
        ("sandbox", {"enabled": False}),
        ("agents", {"x": {}}),
        ("skills", "all"),
        ("max_thinking_tokens", 1024),
        ("permission_prompt_tool_name", "mcp__x__y"),
        ("include_hook_events", True),
        ("output_format", {"type": "json_schema"}),
        ("session_store", object()),
        ("no_such_option", 1),
    ):
        assert error_of(partial(chat, B1, **{name: value})) == (
            f"TypeError: a probe may not set {name}: no probe needs it"
        )


SDK_FIELDS = """
import dataclasses, json, claude_agent_sdk as sdk
names = [f.name for f in dataclasses.fields(sdk.ClaudeAgentOptions)]
print(json.dumps({"version": sdk.__version__, "fields": names}))
"""


def test_every_sdk_option_is_locked_checked_or_refused() -> None:
    python = common.PROBE_VENV / "Scripts" / "python.exe"
    done = subprocess.run(
        [str(python), "-I", "-c", SDK_FIELDS], capture_output=True, text=True, check=True
    )
    sdk = json.loads(done.stdout)
    assert sdk["version"] == "0.2.166"
    assert len(sdk["fields"]) == 49
    assert sorted(sdk["fields"]) == sorted(common.OPTION_RULES)


def test_the_options_the_probes_pass_are_accepted() -> None:
    options = chat(
        B1,
        model="sonnet",
        max_turns=3,
        resume="0b5e4c1a-2f3d-4e5f-8a9b-0c1d2e3f4a5b",
        thinking={"type": "enabled", "budget_tokens": 2048},
        effort="max",
        verbatim_prompts=True,
        include_partial_messages=True,
        system_prompt={"type": "preset", "preset": "claude_code", "append": "x"},
        mcp_servers={"probe": {"type": "sdk", "name": "probe"}},
        cli_path=str(common.SHIM_EXE),
    )
    assert (options.model, options.max_turns, options.effort) == ("sonnet", 3, "max")
    assert options.cli_path == str(common.SHIM_EXE)


def test_each_allowed_option_refuses_a_value_outside_its_check() -> None:
    shim = f"it must be the shim {common.SHIM_EXE.as_posix()}"
    thinking = "it must be adaptive, disabled, or enabled with 1024 to 16000 budget tokens"
    stdio = {"pw": {"type": "stdio", "command": "touch"}}
    for name, value, reason in (
        ("model", "opus", "it must be haiku or sonnet"),
        ("max_turns", 50, "it must be 1 to 8"),
        ("max_turns", True, "it must be 1 to 8"),
        ("resume", "../x", "it must be a UUID"),
        ("effort", "turbo", "it must be an effort level"),
        ("verbatim_prompts", "yes", "it must be a bool"),
        ("cli_path", "C:/Windows/System32/cmd.exe", shim),
        ("mcp_servers", stdio, "it must be in-process SDK servers"),
        ("mcp_servers", "D:/x/mcp.json", "its value could not be read (AttributeError)"),
        (
            "system_prompt",
            {"type": "file", "path": "x"},
            "it must be text or the claude_code preset with an append",
        ),
        ("thinking", {"type": "enabled", "budget_tokens": 99999}, thinking),
    ):
        assert error_of(partial(chat, B1, **{name: value})) == (
            f"TypeError: a probe may not set {name}: {reason}"
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


async def rewrite_quietly(
    _input: HookInput, _tool_use_id: str | None, _context: HookContext
) -> HookJSONOutput:
    return {
        "hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": {"command": "cmdkey"}}
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
    probe = Matcher(
        matcher="Bash", hooks=[rewrite, rewrite_quietly, observe, veto, crash], timeout=5
    )
    hooks = pre_tool_use(chat(B1, hooks={"PreToolUse": [probe]}))
    assert [(m.matcher, m.timeout, len(m.hooks)) for m in hooks] == [
        (None, None, 1),
        ("Bash", 5, 5),
    ]
    allowed = {"command": "echo hp1-b1-marker"}
    assert [run_hook(hook, "Bash", allowed) for hook in hooks[1].hooks] == [
        deny("A probe hook may only deny a call; it returned allow or a changed input."),
        deny("A probe hook may only deny a call; it returned allow or a changed input."),
        {},
        deny("probe says no"),
        deny("A PreToolUse hook failed (RuntimeError), so this call is denied."),
    ]


def test_a_probe_may_hook_only_pre_tool_use_and_stop_with_callbacks() -> None:
    assert list(chat(B1, hooks={"Stop": [Matcher(hooks=[observe])]}).hooks) == [
        "Stop",
        "PreToolUse",
    ]
    refusal = "TypeError: a probe may not set hooks: it must be callbacks on ['PreToolUse', 'Stop']"
    for event in ("PermissionRequest", "PostToolUse", "SessionStart"):
        assert error_of(partial(chat, B1, hooks={event: [Matcher(hooks=[observe])]})) == refusal
    command: list[Any] = [Matcher(hooks=[{"type": "command", "command": "touch x"}])]
    assert error_of(partial(chat, B1, hooks={"PreToolUse": command})) == refusal


COMMAND_HOOK = {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "x"}]}]}


def test_probe_settings_may_carry_only_the_login_pin_and_cleanup_period() -> None:
    kept = {"forceLoginMethod": "claudeai", "cleanupPeriodDays": 3650}
    assert json.loads(chat(B1, settings=json.dumps(kept)).settings) == kept
    assert json.loads(chat(B1).settings) == {"forceLoginMethod": "claudeai"}
    for extra in ({"hooks": COMMAND_HOOK}, {"enabledPlugins": {"x@y": True}}, {"sandbox": {}}):
        assert error_of(partial(chat, B1, settings=json.dumps(kept | extra))) == (
            f"TypeError: a probe may not set settings: keys {sorted(extra)}; "
            "hooks go through Lockdown.markers"
        )
    for wrong in ({"forceLoginMethod": "console"}, {"cleanupPeriodDays": "x"}):
        assert error_of(partial(chat, B1, settings=json.dumps(wrong))) == (
            "TypeError: a probe may not set settings: "
            "forceLoginMethod is claudeai and cleanupPeriodDays a whole number"
        )
    for raw in ('{"hooks": {}, "hooks": {}}', "D:/x/settings.json", "[]"):
        assert error_of(partial(chat, B1, settings=raw)).startswith(
            "TypeError: a probe may not set settings: its value could not be read"
        )


def test_probe_cli_flags_may_only_append_a_system_prompt_file() -> None:
    inside = (common.SCRATCH / "append-system-prompt.txt").as_posix()
    assert chat(B1, extra_args={"append-system-prompt-file": inside}).extra_args == {
        "append-system-prompt-file": inside
    }
    refusal = (
        "TypeError: a probe may not set extra_args: it must be append-system-prompt-file "
        f"with a file under {common.SCRATCH.as_posix()}"
    )
    for flag in ("settings", "plugin-dir", "mcp-config", "setting-sources", "add-dir"):
        assert error_of(partial(chat, B1, extra_args={flag: inside})) == refusal
    for value in ("--settings={}", "C:/Users/x/a.txt", f"{common.SCRATCH.as_posix()}/../a.txt"):
        args = {"append-system-prompt-file": value}
        assert error_of(partial(chat, B1, extra_args=args)) == refusal


def row_env(**extra: str) -> dict[str, str]:
    row = Provider("echo", "http://127.0.0.1:8123", "echo-model")
    home = common.SCRATCH / "hp1" / "echo" / "claude"
    return provider_env(os.environ, row, "fake-secret", home) | extra


def test_probe_env_carries_the_provider_row_and_the_probe_knobs() -> None:
    env = row_env(
        CLAUDE_CODE_MAX_OUTPUT_TOKENS="2048",
        MAX_THINKING_TOKENS="1024",
        ENABLE_TOOL_SEARCH="true",
        CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS="1",
        **{"CLAUDE_CODE_OAUTH_TOKEN": "canary"},
        QMA_CHAT_ID="hp0",
    )
    assert chat(B1, env=env).env == env
    assert chat(B1, env=common.home_env()).env == common.home_env()


def test_probe_env_refuses_every_name_that_could_change_what_bash_runs(monkeypatch: Any) -> None:
    monkeypatch.setattr(common, "bundled_cli", lambda: Path("D:/sdk/_bundled/claude.exe"))
    assert chat(B1, env=row_env(QMA_CLI_PATH="D:/sdk/_bundled/claude.exe")).env["QMA_CLI_PATH"]
    path = os.environ.get("PATH", "")
    for extra in (
        {"BASH_ENV": "D:/x/bashenv.sh"},
        {"ENV": "D:/x/env.sh"},
        {"CLAUDE_CODE_SHELL_PREFIX": "D:/x/prefix.sh"},
        {"NODE_OPTIONS": "--require D:/x/a.js"},
        {"HTTPS_PROXY": "http://127.0.0.1:1"},
        {"bash_env": "D:/x/bashenv.sh"},
        {"PATH": f"D:/x;{path}"},
        {"HOME": "C:/Users/someone"},
        {"CLAUDE_CONFIG_DIR": "C:/Users/someone/.claude"},
        {"ANTHROPIC_BASE_URL": "http://example.com"},
        {"ANTHROPIC_API_KEY": "fake-secret"},
        {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "2048 x"},
        {"QMA_CLI_PATH": "C:/Windows/System32/cmd.exe"},
    ):
        error = error_of(partial(chat, B1, env=row_env(**extra)))
        assert error == f"TypeError: a probe may not set env: names or values {sorted(extra)}"
        assert "fake-secret" not in error


def test_a_marker_hook_writes_its_input_to_its_file_and_prints_nothing(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(common, "MARKERS", tmp_path)
    marked = Lockdown(
        commands=B1.commands,
        markers=(Marker("ConfigChange", "config"), Marker("PreToolUse", "pre", "Bash")),
    )
    hooks = json.loads(chat(marked).settings)["hooks"]
    assert [(event, [sorted(m) for m in matchers]) for event, matchers in hooks.items()] == [
        ("ConfigChange", [["hooks"]]),
        ("PreToolUse", [["hooks", "matcher"]]),
    ]
    assert hooks["PreToolUse"][0]["matcher"] == "Bash"
    command = hooks["PreToolUse"][0]["hooks"][0]
    assert command["type"] == "command"
    ran = subprocess.run(
        shlex.split(command["command"]),
        input='{"tool_name": "Bash",\n "tool_input": {}}',
        capture_output=True,
        text=True,
        check=True,
    )
    assert (ran.stdout, ran.stderr) == ("", "")
    assert (tmp_path / "pre.jsonl").read_text() == '{"tool_name": "Bash",  "tool_input": {}}\n'


def test_a_marker_tag_is_a_plain_name() -> None:
    assert error_of(lambda: Marker("PreToolUse", "x'; touch y")) == (
        'ValueError: a marker tag is lowercase letters, digits and dashes, not "x\'; touch y"'
    )


def write_plugin(root: Path, manifest: dict[str, Any]) -> Path:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "commands").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "commands" / "say.md").write_text("Say planted plugin.\n", encoding="utf-8")
    return root


def test_a_plan_chat_loads_only_plugins_that_hold_nothing_but_commands(tmp_path: Path) -> None:
    good = write_plugin(tmp_path / "good", {"name": "good", "version": "0.0.1"})
    assert chat(Lockdown(command_plugins=(good,))).plugins == [
        {"type": "local", "path": good.as_posix()}
    ]
    assert chat(Lockdown()).plugins == []
    for extra in ("hooks/hooks.json", ".mcp.json", "skills/x/SKILL.md", ".claude-plugin/x.json"):
        bad = write_plugin(tmp_path / extra.replace("/", "-"), {"name": "bad"})
        (bad / extra).parent.mkdir(parents=True, exist_ok=True)
        (bad / extra).write_text(json.dumps({"hooks": COMMAND_HOOK}))
        assert error_of(partial(chat, Lockdown(command_plugins=(bad,)))).startswith(
            f"TypeError: {bad.as_posix()} holds more than a manifest and commands"
        )
    bare = tmp_path / "bare"
    (bare / ".claude-plugin").mkdir(parents=True)
    (bare / ".claude-plugin" / "plugin.json").write_text("{}")
    assert error_of(partial(chat, Lockdown(command_plugins=(bare,)))) == (
        f"TypeError: {bare.as_posix()} holds more than a manifest and commands: ['.claude-plugin']"
    )
    named = write_plugin(tmp_path / "named", {"name": "named", "hooks": "./h.json"})
    assert error_of(partial(chat, Lockdown(command_plugins=(named,)))) == (
        f"TypeError: {named.as_posix()} manifest may not set ['hooks']"
    )
    for extra in ("sub/x.md", "x.txt"):
        bad = write_plugin(tmp_path / extra.replace("/", "-"), {"name": "bad"})
        (bad / "commands" / extra).parent.mkdir(exist_ok=True)
        (bad / "commands" / extra).write_text("Say x.\n")
        assert error_of(partial(chat, Lockdown(command_plugins=(bad,)))) == (
            f"TypeError: {(bad / 'commands' / extra.split('/')[0]).as_posix()} "
            "is not a command file"
        )


def junction(link: Path, target: Path) -> Path:
    import _winapi  # noqa: PLC0415

    target.mkdir(parents=True, exist_ok=True)
    _winapi.CreateJunction(str(target), str(link))
    return link


def test_a_plugin_folder_reached_through_a_junction_is_refused(tmp_path: Path) -> None:
    hooks = tmp_path / "hooks-target"
    hooks.mkdir()
    (hooks / "hooks.json").write_text(json.dumps({"hooks": COMMAND_HOOK}))
    for where in ("hooks", "agents", "commands/sub"):
        root = write_plugin(tmp_path / where.replace("/", "-"), {"name": "linked"})
        link = junction(root / where, hooks)
        assert error_of(partial(chat, Lockdown(command_plugins=(root,)))) == (
            f"TypeError: {link.parent.as_posix()} holds links ['{link.name}']"
        )
    real = write_plugin(tmp_path / "real", {"name": "real"})
    linked_root = junction(tmp_path / "linked-root", real)
    assert error_of(partial(chat, Lockdown(command_plugins=(linked_root,)))) == (
        f"TypeError: {linked_root.as_posix()} is a link"
    )


def test_a_plugin_entry_that_is_a_symlink_is_refused(tmp_path: Path, monkeypatch: Any) -> None:
    root = write_plugin(tmp_path / "plugin", {"name": "plugin"})
    command = root / "commands" / "say.md"
    plain_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == command or plain_is_symlink(path))
    assert error_of(partial(chat, Lockdown(command_plugins=(root,)))) == (
        f"TypeError: {command.parent.as_posix()} holds links ['say.md']"
    )


def test_command_frontmatter_may_only_describe_the_command(tmp_path: Path) -> None:
    root = write_plugin(tmp_path / "plugin", {"name": "plugin"})
    command = root / "commands" / "say.md"
    command.write_text("---\ndescription: say\nargument-hint: [word]\n---\nSay $1.\n", "utf-8")
    assert chat(Lockdown(command_plugins=(root,))).plugins == [
        {"type": "local", "path": root.as_posix()}
    ]
    for front, keys in (
        ("allowed-tools: Bash, Write", ["allowed-tools"]),
        ("model: opus", ["model"]),
        (
            "hooks:\n  PreToolUse:\n    - matcher: Bash",
            ["<- matcher: Bash>", "<PreToolUse:>", "hooks"],
        ),
        ("{hooks: {}}", ["<{hooks: {}}>"]),
    ):
        command.write_text(f"\ufeff\n---\ndescription: say\n{front}\n---\nSay.\n", "utf-8")
        assert error_of(partial(chat, Lockdown(command_plugins=(root,)))) == (
            f"TypeError: {command.as_posix()} frontmatter may not set {keys}"
        )
    command.write_text("---\ndescription: say\nmodel: opus\n", "utf-8")
    assert error_of(partial(chat, Lockdown(command_plugins=(root,)))) == (
        f"TypeError: {command.as_posix()} frontmatter may not set ['<unclosed>']"
    )


def test_a_command_body_is_plain_text_with_no_shell_or_file_mention(tmp_path: Path) -> None:
    root = write_plugin(tmp_path / "plugin", {"name": "plugin"})
    command = root / "commands" / "say.md"
    for body in ("Say !`touch x` now.", "Read @D:/QMX-worktrees/qma-ship/home/claude/x.json"):
        command.write_text(f"---\ndescription: say\n---\n{body}\n", "utf-8")
        assert error_of(partial(chat, Lockdown(command_plugins=(root,)))) == (
            f"TypeError: {command.as_posix()} holds more than plain text"
        )


def test_user_settings_load_only_into_a_chat_that_may_run_nothing() -> None:
    assert chat(Lockdown(user_settings=True)).setting_sources == ["user"]
    assert chat(Lockdown()).setting_sources == []
    armed: list[dict[str, Any]] = [
        {"commands": B1.commands},
        {"tools": frozenset({"mcp__probe__ping"})},
        {"markers": (Marker("PreToolUse", "pre"),)},
        {"command_plugins": (Path("D:/Temp/qma-hp0/plugin-market/hp0-sdk-plugin"),)},
    ]
    for fields in armed:
        assert error_of(partial(Lockdown, user_settings=True, **fields)) == (
            "ValueError: user settings load only into a chat that may run nothing"
        )
