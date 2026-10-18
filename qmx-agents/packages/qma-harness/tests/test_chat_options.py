from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
import test_chat
from claude_agent_sdk import PermissionResultDeny
from claude_agent_sdk.types import ToolPermissionContext
from test_chat import FakeClient, run
from test_table import read_plan

from qma.harness import (
    Background,
    ChatHooks,
    Child,
    Harness,
    Interactive,
    LaunchRefused,
    NewChat,
    OperatorText,
    money,
)
from qma.harness.home import QmxHome, SessionId
from qma.harness.launch import COMPACT_PCT_ENV as COMPACT
from qma.harness.launch import Budgets, ChatConfig, ChatKind, build_options
from qma.harness.profiles import PLAN

home = test_chat.home

GATE = money.GateRules(
    proposal_tools=frozenset(),
    mandatory_asks=frozenset(),
    dispatch_targets={},
    protected_paths=("/d/qmx/settings.toml",),
    qmx_homes=(),
    writable_paths=(),
    secret_paths=(),
    personal_homes=("/c/Users/Op/.claude",),
    keyring_names=frozenset(),
    broker_hosts=frozenset(),
    variables={},
    case_insensitive=True,
    unattended=True,
    external_unattended=frozenset(),
)
CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")


async def refuse(name: str, _input: dict[str, Any], _context: ToolPermissionContext) -> Any:
    return PermissionResultDeny(message=name)


def options(
    tmp_path: Path,
    kind: ChatKind,
    *,
    compact_at: float | None = None,
    hooks: ChatHooks | None = None,
) -> Any:
    plugin = tmp_path / "plugin"
    plugin.mkdir(exist_ok=True)
    return build_options(
        ChatConfig(PLAN, "haiku", None, "default", tmp_path, kind, compact_at, hooks),
        session_id=CHAT,
        transcript_exists=False,
        env={"CLAUDE_CONFIG_DIR": "D:/qmx/claude"},
        home=QmxHome(tmp_path / "qmx", plugin_dir=plugin),
        settings_json="{}",
        launcher=Path("D:/venv/Scripts/qma-cli-launcher.exe"),
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
        budgets=Budgets(),
    )


def call(callback: Any, data: dict[str, Any]) -> Any:
    return asyncio.run(callback(data, None, {"signal": None}))


async def observe(_input: Any) -> None:
    return None


@pytest.mark.parametrize(
    "extra",
    [{"compact_at": 0.4}, {"hooks": ChatHooks(stop=observe)}],
)
def test_an_interactive_chat_refuses_compaction_and_hooks(extra: dict[str, Any]) -> None:
    with pytest.raises(LaunchRefused, match="for Background and Child chats only"):
        NewChat(title="t", kind=Interactive(), **extra)


@pytest.mark.parametrize("share", [0.0, 0.004, 1.5])
def test_a_compact_share_outside_the_window_is_refused(share: float) -> None:
    with pytest.raises(LaunchRefused, match=r"from 0\.01 to 1"):
        NewChat(title="t", kind=Background(), compact_at=share)


def test_compact_at_reaches_only_its_own_chats_cli(tmp_path: Path) -> None:
    compacting = options(tmp_path, Background(), compact_at=0.4)
    neighbour = options(tmp_path, Child(parent=CHAT, unattended=True))
    assert compacting.env == {
        "CLAUDE_CONFIG_DIR": "D:/qmx/claude",
        COMPACT: "40",
    }
    assert neighbour.env == {"CLAUDE_CONFIG_DIR": "D:/qmx/claude"}


def test_the_harness_launches_each_chat_with_only_its_own_options(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        read_plan(harness, 0.1)
        tuned = await harness.start_chat(
            NewChat(
                title="tuned",
                model="haiku",
                kind=Background(),
                compact_at=0.4,
                hooks=ChatHooks(stop=observe),
            )
        )
        plain = await harness.start_chat(NewChat(title="plain", model="haiku", kind=Background()))
        await harness.send(tuned, OperatorText("hi"))
        await harness.send(plain, OperatorText("hi"))

    run(body, home)
    tuned, plain = FakeClient.made
    assert tuned.options.env[COMPACT] == "40"
    assert COMPACT not in plain.options.env
    assert sorted(tuned.options.hooks or {}) == ["PreToolUse", "Stop"]
    assert sorted(plain.options.hooks or {}) == ["PreToolUse"]


def test_chat_hooks_run_after_the_money_gate_and_cannot_decide(tmp_path: Path) -> None:
    seen: list[str] = []

    async def record(data: Any) -> None:
        seen.append(f"{data['hook_event_name']} {data.get('tool_name', '')}".strip())

    async def broken(_data: Any) -> None:
        raise RuntimeError("observer bug")

    hooks = ChatHooks(
        pre_tool_use=broken,
        post_tool_use=record,
        pre_compact=record,
        stop=record,
        subagent_stop=record,
    )
    built = options(tmp_path, Background(), hooks=hooks).hooks
    assert {event: len(matchers) for event, matchers in built.items()} == {
        "PreToolUse": 2,
        "PostToolUse": 1,
        "PreCompact": 1,
        "Stop": 1,
        "SubagentStop": 1,
    }
    gate, observer = built["PreToolUse"]
    money_act = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "cmdkey /list"},
        "cwd": "/d/work",
    }
    decision = call(gate.hooks[0], money_act)["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
    assert call(observer.hooks[0], money_act) == {}
    for event in ("PostToolUse", "PreCompact", "Stop", "SubagentStop"):
        data = {"hook_event_name": event, "tool_name": "Read" if event == "PostToolUse" else ""}
        assert call(built[event][0].hooks[0], data) == {}
    assert seen == ["PostToolUse Read", "PreCompact", "Stop", "SubagentStop"]


def test_a_slow_observer_is_cut_off_before_its_matcher_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("qma.harness.launch.OBSERVER_TIMEOUT_S", 0.01)

    async def slow(_data: Any) -> None:
        await asyncio.sleep(5)

    built = options(tmp_path, Background(), hooks=ChatHooks(post_tool_use=slow)).hooks
    assert call(built["PostToolUse"][0].hooks[0], {"hook_event_name": "PostToolUse"}) == {}
