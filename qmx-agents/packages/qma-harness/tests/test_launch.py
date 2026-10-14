from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, PermissionResultDeny
from claude_agent_sdk.types import ToolPermissionContext

from qma.harness import money
from qma.harness.home import QmxHome, SessionId
from qma.harness.launch import (
    CONSTANT_ENV,
    GATE_TIMEOUT_S,
    Background,
    ChatConfig,
    Child,
    Interactive,
    LaunchRefused,
    PlanLaunch,
    RelayedLaunch,
    TestMode,
    assert_argv_fits,
    assert_scrubbed,
    build_options,
    instructions,
    launch_env,
    unattended,
    verbatim,
)
from qma.harness.profiles import (
    PLAN,
    BaseUrl,
    KeyProvider,
    ModelId,
    ProfileName,
    Quirks,
    SecretRef,
    TierMap,
)
from qma.harness.relay import GrantSecret, RelayGrant

GATE = money.GateRules(
    proposal_tools=frozenset(),
    mandatory_asks=frozenset(),
    protected_paths=("/d/qmx/settings.toml",),
    secret_paths=(),
    personal_home="/c/Users/Op/.claude",
    keyring_names=frozenset(),
    broker_hosts=frozenset(),
    variables={},
    case_insensitive=True,
)

CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")


async def refuse(name: str, _input: dict[str, Any], _context: ToolPermissionContext) -> Any:
    return PermissionResultDeny(message=f"{name}: approvals are not wired yet")


@pytest.fixture
def home(tmp_path: Path) -> QmxHome:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "QMX.md").write_text("Money is read-only.\n", encoding="utf-8")
    return QmxHome(tmp_path / "qmx", plugin_dir=plugin)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    folder = tmp_path / "ws"
    folder.mkdir()
    (folder / "CLAUDE.md").write_text("Use uv.\n@docs/more.md\n", encoding="utf-8")
    return folder


@pytest.mark.parametrize(
    ("kind", "is_verbatim", "is_unattended"),
    [
        (Interactive(), False, False),
        (Background(), True, True),
        (Child(parent=CHAT, unattended=True), True, True),
        (Child(parent=CHAT, unattended=False), True, False),
    ],
)
def test_verbatim_and_unattended_follow_the_chat_kind(
    kind: Interactive | Background | Child, is_verbatim: bool, is_unattended: bool
) -> None:
    assert (verbatim(kind), unattended(kind)) == (is_verbatim, is_unattended)


def test_assert_scrubbed_refuses_a_banned_name_and_keeps_git_bash() -> None:
    assert_scrubbed({"PATH": "x", "CLAUDE_CODE_GIT_BASH_PATH": "D:/Git/bin/bash.exe"})
    with pytest.raises(LaunchRefused, match="holds HTTPS_PROXY, anthropic_base_url"):
        assert_scrubbed({"PATH": "x", "HTTPS_PROXY": "p", "anthropic_base_url": "u"})


def test_a_plan_launch_sets_only_the_plan_home_and_the_launcher_inputs(home: QmxHome) -> None:
    windows = {"CLAUDE_CODE_USE_POWERSHELL_TOOL": "1"} if os.name == "nt" else {}
    assert launch_env(PlanLaunch(), home=home, session_id=CHAT, cap="Local\\qma-cap") == {
        "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",
        "CLAUDE_CODE_DISABLE_WORKFLOWS": "1",
        "CLAUDE_AGENT_SDK_CLIENT_APP": "QMA",
        **windows,
        "CLAUDE_CONFIG_DIR": str(home.root / "claude"),
        "QMA_CHAT_ID": CHAT,
        "QMA_PROC_DIR": str(home.root / "procs"),
        "QMA_CAP": "Local\\qma-cap",
    }


def test_instructions_read_qmx_rules_then_the_workspace_root_files(
    home: QmxHome, workspace: Path
) -> None:
    assert instructions(home, workspace) == (
        f"Contents of {(home.plugin_dir / 'QMX.md').as_posix()}:\n\nMoney is read-only.\n\n"
        f"Contents of {(workspace / 'CLAUDE.md').as_posix()}:\n\nUse uv.\n@docs/more.md"
    )


def test_build_options_for_a_new_plan_chat(home: QmxHome, workspace: Path) -> None:
    config = ChatConfig(
        profile=PLAN,
        model="haiku",
        effort=None,
        mode="default",
        workspace=workspace,
        kind=Interactive(),
    )
    launcher = Path("D:/venv/Scripts/qma-cli-launcher.exe")
    options = build_options(
        config,
        session_id=CHAT,
        transcript_exists=False,
        env={"CLAUDE_CONFIG_DIR": "D:/qmx/claude"},
        home=home,
        settings_json='{"forceLoginMethod":"claudeai"}',
        launcher=launcher,
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
    )
    [matcher] = options.hooks["PreToolUse"] if options.hooks else []
    assert (matcher.matcher, matcher.timeout, len(matcher.hooks)) == (None, GATE_TIMEOUT_S, 1)
    assert options == ClaudeAgentOptions(
        cli_path=launcher,
        tools={"type": "preset", "preset": "claude_code"},
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": instructions(home, workspace),
        },
        permission_mode="default",
        model="haiku",
        effort=None,
        cwd=workspace,
        env={"CLAUDE_CONFIG_DIR": "D:/qmx/claude"},
        setting_sources=[],
        settings='{"forceLoginMethod":"claudeai"}',
        plugins=[{"type": "local", "path": str(home.plugin_dir)}],
        strict_mcp_config=True,
        mcp_servers={},
        hooks=options.hooks,
        disallowed_tools=money.deny_rules(GATE),
        can_use_tool=refuse,
        session_id=CHAT,
        resume=None,
        include_partial_messages=True,
        enable_file_checkpointing=True,
        extra_args={"replay-user-messages": None},
        verbatim_prompts=False,
    )
    resumed = build_options(
        ChatConfig(PLAN, "haiku", "high", "plan", workspace, Background()),
        session_id=CHAT,
        transcript_exists=True,
        env={},
        home=home,
        settings_json="{}",
        launcher=launcher,
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
        test=TestMode(gate_hook=False, deny_rules=False),
    )
    assert (resumed.hooks, resumed.disallowed_tools) == (None, [])
    seen = (resumed.session_id, resumed.resume, resumed.verbatim_prompts, resumed.effort)
    assert seen == (None, CHAT, True, "high")


def test_a_launch_past_the_argv_budget_is_refused_naming_the_largest_part(
    home: QmxHome, workspace: Path
) -> None:
    (workspace / "AGENTS.md").write_text("x" * 31_000, encoding="utf-8")
    options = build_options(
        ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()),
        session_id=CHAT,
        transcript_exists=False,
        env={},
        home=home,
        settings_json="{}",
        launcher=Path(sys.executable),
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
    )
    with pytest.raises(LaunchRefused, match=r"largest part is QMX\.md and the workspace CLAUDE"):
        assert_argv_fits(options)
    (workspace / "AGENTS.md").write_text("short", encoding="utf-8")
    assert_argv_fits(
        build_options(
            ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()),
            session_id=CHAT,
            transcript_exists=False,
            env={},
            home=home,
            settings_json="{}",
            launcher=Path(sys.executable),
            can_use_tool=refuse,
            mcp_servers={},
            gate=GATE,
        )
    )


def test_a_relayed_launch_carries_the_relay_and_its_grant_never_a_key(home: QmxHome) -> None:
    profile = KeyProvider(
        name=ProfileName("openrouter"),
        base_url=BaseUrl("https://openrouter.ai/api"),
        credential=SecretRef("qmx/openrouter"),
        tiers=TierMap(ModelId("a/o"), ModelId("a/s"), ModelId("a/h"), ModelId("a/f")),
        quirks=Quirks(env={"ENABLE_TOOL_SEARCH": "true"}),
    )
    grant = RelayGrant("http://127.0.0.1:5123", GrantSecret("grant-secret"), CHAT, profile)
    assert launch_env(RelayedLaunch(grant), home=home, session_id=CHAT, cap="c") == {
        **CONSTANT_ENV,
        "ENABLE_TOOL_SEARCH": "true",
        "CLAUDE_CONFIG_DIR": str(home.root / "claude-relayed"),
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:5123",
        "ANTHROPIC_AUTH_TOKEN": "grant-secret",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "a/o",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "a/s",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "a/h",
        "ANTHROPIC_DEFAULT_FABLE_MODEL": "a/f",
        "NO_PROXY": "127.0.0.1,localhost",
        "QMA_CHAT_ID": CHAT,
        "QMA_PROC_DIR": str(home.root / "procs"),
        "QMA_CAP": "c",
    }
