from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, PermissionResultDeny
from claude_agent_sdk.types import ToolPermissionContext
from qmx_router.profiles import (
    PLAN,
    BaseUrl,
    KeyProvider,
    ModelId,
    ProfileName,
    Quirks,
    SecretRef,
    TierMap,
)
from qmx_router.relay import GrantSecret, RelayGrant

from qma.harness import guard
from qma.harness.home import QmxHome, SessionId
from qma.harness.launch import (
    CONSTANT_ENV,
    GATE_TIMEOUT_S,
    Background,
    Budgets,
    ChatConfig,
    Child,
    Interactive,
    LaunchRefused,
    PlanLaunch,
    RelayedLaunch,
    TestMode,
    agent_options,
    assert_argv_fits,
    assert_scrubbed,
    build_options,
    launch_env,
    unattended,
    verbatim,
)
from qma.harness.surface import HomeSlots, Supply, Surface, build, declaration

GATE = guard.GuardRules(
    mandatory_asks=frozenset(),
    protected_paths=("/d/qmx/settings.toml",),
    qmx_homes=(),
    writable_paths=(),
    install_paths=(),
    secret_paths=(),
    personal_homes=("/c/Users/Op/.claude",),
    keyring_names=frozenset(),
    delete_zones=(),
    variables={},
    case_insensitive=True,
    unattended=False,
    external_unattended=frozenset(),
)

CHAT = SessionId("0b9c2f4e-1d3a-4c5b-8e7f-6a5b4c3d2e1f")
FILES = Path("D:/qmx/chats") / CHAT


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


def telemetry_names(home: QmxHome, send_to: str) -> dict[str, str]:
    home.root.mkdir(parents=True, exist_ok=True)
    (home.root / "settings.toml").write_text(
        f'[telemetry]\nsend_to = "{send_to}"\n', encoding="utf-8"
    )
    env = launch_env(PlanLaunch(), home=home, session_id=CHAT, cap="c")
    return {name: env[name] for name in env if "OTEL" in name or "TELEMETRY" in name}


def test_a_chat_sends_telemetry_only_where_send_to_names_a_target(home: QmxHome) -> None:
    off = telemetry_names(home, "off")
    this_pc = telemetry_names(home, "this-pc")
    place = telemetry_names(home, "home-server")
    address = telemetry_names(home, "http://10.1.2.3:4318")

    assert (off, address) == ({}, {})
    assert this_pc == {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:5080/api/default",
    }
    assert place["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://home-server:4318"


def surface_of(config: ChatConfig, home: QmxHome) -> Surface:
    supply = Supply((), HomeSlots(home), {}, (home.plugin_dir,), FILES / "qmx-slots" / "skills")
    return build(
        config.kind, config.home, (), declaration(config), supply, workspace=config.workspace
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
    surface = surface_of(config, home)
    options = build_options(
        config,
        surface,
        session_id=CHAT,
        transcript_exists=False,
        env={"CLAUDE_CONFIG_DIR": "D:/qmx/claude"},
        settings_file=FILES / "settings.json",
        system_file=FILES / "system.md",
        launcher=launcher,
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
        budgets=Budgets(),
    )
    [matcher] = options.hooks["PreToolUse"] if options.hooks else []
    assert (matcher.matcher, matcher.timeout, len(matcher.hooks)) == (None, GATE_TIMEOUT_S, 1)
    assert options == ClaudeAgentOptions(
        cli_path=launcher,
        tools=list(surface.builtins),
        agents=agent_options(surface),
        skills=list(surface.skills),
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "exclude_dynamic_sections": True,
            "snapshot": False,
        },
        permission_mode="default",
        model="haiku",
        effort=None,
        cwd=workspace,
        env={"CLAUDE_CONFIG_DIR": "D:/qmx/claude"},
        setting_sources=[],
        settings=str(FILES / "settings.json"),
        plugins=[{"type": "local", "path": str(home.plugin_dir)}],
        strict_mcp_config=True,
        mcp_servers={},
        hooks=options.hooks,
        disallowed_tools=guard.deny_rules(GATE),
        can_use_tool=refuse,
        session_id=CHAT,
        resume=None,
        include_partial_messages=True,
        enable_file_checkpointing=True,
        extra_args={
            "replay-user-messages": None,
            "append-system-prompt-file": (FILES / "system.md").as_posix(),
        },
        verbatim_prompts=False,
        max_turns=None,
        max_budget_usd=None,
    )
    resumed = build_options(
        ChatConfig(PLAN, "haiku", "high", "plan", workspace, Background()),
        surface_of(ChatConfig(PLAN, "haiku", "high", "plan", workspace, Background()), home),
        session_id=CHAT,
        transcript_exists=True,
        env={},
        settings_file=FILES / "settings.json",
        system_file=FILES / "system.md",
        launcher=launcher,
        can_use_tool=refuse,
        mcp_servers={},
        gate=GATE,
        budgets=Budgets(),
        test=TestMode(gate_hook=False, deny_rules=False),
    )
    assert (resumed.hooks, resumed.disallowed_tools) == (None, [])
    seen = (resumed.session_id, resumed.resume, resumed.verbatim_prompts, resumed.effort)
    assert seen == (None, CHAT, True, "high")
    assert (resumed.max_turns, resumed.max_budget_usd) == (None, None)


def test_a_launch_past_the_argv_budget_is_refused_naming_the_largest_part(
    home: QmxHome, workspace: Path
) -> None:
    big: dict[str, Any] = {"big": {"type": "stdio", "command": "x" * 31_000}}
    options = build_options(
        ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()),
        surface_of(ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()), home),
        session_id=CHAT,
        transcript_exists=False,
        env={},
        settings_file=FILES / "settings.json",
        system_file=FILES / "system.md",
        launcher=Path(sys.executable),
        can_use_tool=refuse,
        mcp_servers=big,
        gate=GATE,
        budgets=Budgets(),
    )
    with pytest.raises(LaunchRefused, match=r"largest part is the MCP config"):
        assert_argv_fits(options)
    (workspace / "AGENTS.md").write_text("x" * 31_000, encoding="utf-8")
    assert_argv_fits(
        build_options(
            ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()),
            surface_of(ChatConfig(PLAN, "haiku", None, "default", workspace, Interactive()), home),
            session_id=CHAT,
            transcript_exists=False,
            env={},
            settings_file=FILES / "settings.json",
            system_file=FILES / "system.md",
            launcher=Path(sys.executable),
            can_use_tool=refuse,
            mcp_servers={},
            gate=GATE,
            budgets=Budgets(),
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


def test_the_console_starts_qmx_host_with_its_home_and_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    import qma.console

    ran: list[list[str]] = []

    def start(argv: list[str], **_: Any) -> subprocess.CompletedProcess[bytes]:
        ran.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(qma.console.subprocess, "run", start)
    assert qma.console.serve("start", tmp_path, 8766) == 0
    assert ran == [
        [sys.executable, "-m", "qmx_host", "start", "--home", str(tmp_path), "--port", "8766"]
    ]
