from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
import test_chat
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny
from claude_agent_sdk.types import ToolPermissionContext
from test_chat import FakeClient, run
from test_table import read_plan

from qma.harness import (
    AllowOnce,
    Answer,
    Background,
    ChatHooks,
    ChatPermissions,
    Child,
    Harness,
    Home,
    Interactive,
    LaunchRefused,
    NewChat,
    OperatorText,
    PolicyCall,
    Reject,
    SubAgent,
    money,
)
from qma.harness.home import QmxHome, SessionId, read_record
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
        settings_file=tmp_path / "settings.json",
        system_file=tmp_path / "system.md",
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


FULL = NewChat(
    title="every option",
    model="haiku",
    kind=Background(),
    compact_at=0.4,
    home=Home("agent", "lib-item-7"),
    packs=("lab", "portfolio"),
    tools=(),
    agents={"reviewer": SubAgent("reviews a diff", "Review it.", ("Read",), "haiku")},
    mcp_servers={"sandbox": {"type": "stdio", "command": "sandbox-tools"}},
    append_system_prompt="Node brief: count the rows.",
    hook_sink="spans",
    permissions=ChatPermissions("engine", ("Edit(//d/overlay/**)",), ("Bash(rm *)",)),
    policy_args={"overlay": "D:/overlay", "declared": ["Read"]},
    claude_hooks={"PostToolUse": [{"hooks": [{"type": "command", "command": "echo hi"}]}]},
)


def test_every_new_chat_option_round_trips_through_the_chat_record(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(FULL)
        record = read_record(home, chat)
        assert record is not None
        assert record.config == FULL.config(PLAN, record.config.workspace, FULL.home or Home())
        assert record.config.home == Home("agent", "lib-item-7")
        assert record.config.agents["reviewer"].tools == ("Read",)
        child = await harness.start_chat(
            NewChat(title="helper", model="haiku", kind=Child(chat, unattended=True))
        )
        child_record = read_record(home, child)
        assert child_record is not None
        assert child_record.config.home == Home("agent", "lib-item-7")

    run(body, home)


def test_a_background_chat_keeps_every_option_after_the_host_restarts(home: QmxHome) -> None:
    started: list[SessionId] = []
    seen: list[tuple[SessionId, str]] = []

    async def before(harness: Harness) -> None:
        started.append(await harness.start_chat(FULL))

    async def after(harness: Harness) -> None:
        async def sink(chat: SessionId, data: Any) -> None:
            seen.append((chat, data["hook_event_name"]))

        async def engine(_call: PolicyCall) -> Answer:
            return Reject("not declared")

        harness.register_sink("spans", sink)
        harness.register_policy("engine", engine)
        await harness.send(started[0], OperatorText("go"))

    run(before, home)
    run(after, home)
    (made,) = FakeClient.made
    chat = started[0]
    options = made.options
    assert (options.env[COMPACT], options.tools, options.mcp_servers) == ("40", [], {})
    assert sorted(options.hooks or {}) == sorted(
        ["PreToolUse", "PostToolUse", "PreCompact", "Stop", "SubagentStop"]
    )
    assert options.agents is not None
    assert list(options.agents) == ["reviewer"]
    hooks = options.hooks or {}
    call(hooks["PostToolUse"][0].hooks[0], {"hook_event_name": "PostToolUse"})
    assert seen == [(chat, "PostToolUse")]
    files = home.launch_dir(chat)
    assert options.settings == str(files / "settings.json")
    written = json.loads((files / "settings.json").read_text(encoding="utf-8"))
    assert written["permissions"] == {
        "allow": ["Edit(//d/overlay/**)"],
        "deny": ["Bash(rm *)"],
    }
    assert written["hooks"]["PostToolUse"] == FULL.claude_hooks["PostToolUse"]
    assert written["autoMemoryEnabled"] is False
    system = (files / "system.md").read_text(encoding="utf-8")
    assert system.endswith("Node brief: count the rows.")


def test_a_launch_naming_an_unregistered_sink_or_policy_is_refused(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(FULL)
        with pytest.raises(LaunchRefused, match="no hook sink named 'spans' is registered"):
            await harness.send(chat, OperatorText("go"))

    run(body, home)
    assert FakeClient.made == []


def test_a_named_policy_answers_a_background_ask_in_process(home: QmxHome) -> None:
    calls: list[PolicyCall] = []

    async def body(harness: Harness) -> None:
        async def engine(call: PolicyCall) -> Answer:
            calls.append(call)
            return Reject("not declared") if call.tool == "Bash" else AllowOnce()

        harness.register_policy("engine", engine)
        chat = await harness.start_chat(
            NewChat(
                title="unattended",
                model="haiku",
                kind=Background(),
                permissions=ChatPermissions("engine"),
                policy_args={"overlay": "D:/overlay"},
            )
        )
        await harness.send(chat, OperatorText("go"))
        ask = FakeClient.made[0].options.can_use_tool
        assert ask is not None
        context = ToolPermissionContext(suggestions=[], tool_use_id="t1")
        denied = await ask("Bash", {"command": "ls"}, context)
        allowed = await ask("Write", {"file_path": "D:/overlay/a"}, context)
        assert denied == PermissionResultDeny(message="not declared")
        assert allowed == PermissionResultAllow(updated_input=None)
        assert [(c.session_id, c.tool, dict(c.args)) for c in calls] == [
            (chat, "Bash", {"overlay": "D:/overlay"}),
            (chat, "Write", {"overlay": "D:/overlay"}),
        ]

    run(body, home)


def test_qmx_tools_that_do_not_ask_get_allow_rules_and_manage_tools_do_not(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="copilot", model="haiku"))
        await harness.send(chat, OperatorText("save a draft"))
        written = (home.launch_dir(chat) / "settings.json").read_text(encoding="utf-8")
        allow = json.loads(written)["permissions"]["allow"]
        assert "mcp__qmx__workflow_drafts_put" in allow
        assert "mcp__qmx__workflows_get" in allow
        assert "mcp__qmx__workflows_put" not in allow
        assert "mcp__qmx__propose_order" not in allow

    run(body, home)


def test_closing_a_finished_chat_ends_its_process_and_deletes_nothing(home: QmxHome) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="done", model="haiku", kind=Background()))
        handle = await harness.run_turn(chat, OperatorText("hi"))
        FakeClient.made[0].go.set()
        await handle.result()
        await harness.close_chat(chat)
        assert FakeClient.made[0].disconnected is True
        assert read_record(home, chat) is not None
        test_chat.plant_transcript(home, chat)
        await harness.send(chat, OperatorText("again"))
        assert len(FakeClient.made) == 2

    run(body, home)


def test_a_meter_turn_that_brings_no_reading_runs_no_other_inside_the_cooldown(
    home: QmxHome,
) -> None:
    async def body(harness: Harness) -> None:
        released = asyncio.create_task(release())
        assert await harness.meter() is None
        await released
        assert await harness.meter() is None
        assert len(FakeClient.made) == 1

    async def release() -> None:
        await test_chat.settle(lambda: len(FakeClient.made) == 1)
        FakeClient.made[0].go.set()

    run(body, home)
