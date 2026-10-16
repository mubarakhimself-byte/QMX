"""Turn a chat's configuration into one CLI launch. Pure functions, no secrets.

Everything not set here is the vanilla CLI default, which is the operator's floor.

- `tools` and `system_prompt` use the `claude_code` presets. The money rule is not enforced
  by removing tools.
- `permission_mode` is always passed. Omitting it can start the session in `auto`.
- Settings in code. `setting_sources=[]`, so the CLI loads no settings file from any home, and
  every Claude setting arrives as one inline JSON string through `settings`
  (`home.code_settings`). Plugins arrive only through `plugins`, MCP servers only through
  `mcp_servers` with `strict_mcp_config=True`.
- `qma.boot` reduced this process's env to an allow-list at startup, and `assert_scrubbed`
  re-checks the banned fragments at every launch. `launch_env` sets exactly the names a launch
  needs; nothing inherited is left to blank out.
- `cli_path` is the QMA launcher, which puts the CLI under the OS limits before it starts.
- `verbatim_prompts` follows the chat kind, so text QMA built from news, files or tool output
  never dispatches a slash command or reads an `@path`.
"""

from __future__ import annotations

import itertools
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal

from claude_agent_sdk import ClaudeAgentOptions
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

from qma.boot import banned_fragment
from qma.harness.profiles import TIER_ENV, ProfileName

if TYPE_CHECKING:
    from claude_agent_sdk.types import CanUseTool

    from qma.harness.home import QmxHome, SessionId
    from qma.harness.relay import RelayGrant

type PermissionMode = Literal[
    "default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"
]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


class LaunchRefused(RuntimeError):
    """A state that could leak billing, credentials or money. Raised before any CLI starts."""


@dataclass(frozen=True)
class Interactive:
    """The operator is at the console or UI. Asks reach him."""


@dataclass(frozen=True)
class Background:
    """Started without the operator present, such as a scheduled news scan."""


@dataclass(frozen=True)
class Child:
    """Started by `mcp__qmx__delegate` from a parent chat. Its prompt was written by a model.
    `unattended` is copied from the parent, so a child of a Background chat is unattended."""

    parent: SessionId
    unattended: bool


type ChatKind = Interactive | Background | Child


def verbatim(kind: ChatKind) -> bool:
    """False only for Interactive. The SDK option is per client, so this one rule decides it."""
    return not isinstance(kind, Interactive)


def unattended(kind: ChatKind) -> bool:
    """True for Background and for a Child whose root is Background. Read by the bounded ask
    wait, the Background limits and the GPT consent check."""
    match kind:
        case Interactive():
            return False
        case Background():
            return True
        case Child(unattended=flag):
            return flag


@dataclass(frozen=True)
class ChatConfig:
    """Everything that decides how a chat's CLI process is launched. A change is a new config."""

    profile: ProfileName
    model: str
    effort: Effort | None
    mode: PermissionMode
    workspace: Path
    kind: ChatKind


@dataclass(frozen=True)
class TestMode:
    """Live checks only: switch one layer off so a check proves another. Only
    `Harness.open(test=...)` accepts it, and a CI check allows `TestMode(` only under
    `scripts/live/` and tests."""

    gate_hook: bool = True
    deny_rules: bool = True
    grants: bool = True
    relay_egress_stop: bool = True
    redaction: bool = True
    loopback_http_provider: bool = False


CONSTANT_ENV: Final[Mapping[str, str]] = {
    "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",
    "CLAUDE_CODE_DISABLE_WORKFLOWS": "1",
    "CLAUDE_AGENT_SDK_CLIENT_APP": "QMA",
    **({"CLAUDE_CODE_USE_POWERSHELL_TOOL": "1"} if os.name == "nt" else {}),
}
"""Nonessential traffic off also stops feature-flag fetching, which drops the PowerShell, Monitor,
DesignSync and PushNotification tools (measured, CLI 2.1.299). On Windows, vanilla Claude Code
offers PowerShell, so it is turned back on by name; the other three stay off."""

LAUNCHER: Final = Path(sys.executable).parent / (
    "qma-cli-launcher.exe" if os.name == "nt" else "qma-cli-launcher"
)
"""The `qma-cli-launcher` console script installed next to this Python."""

GATE_TIMEOUT_S: Final = 10.0
"""Explicit `HookMatcher.timeout` for the money gate. A PreToolUse SDK callback that exceeds
its timeout blocks the tool call."""


@dataclass(frozen=True)
class PlanLaunch:
    """The operator's Max plan. No base URL and no token: the CLI's own /login in the plan home
    owns sign-in, and no QMX process is in the request path."""


@dataclass(frozen=True)
class RelayedLaunch:
    """A key provider through the loopback relay. Only `Relay.grant` mints a grant, and only
    for a key profile, so a third-party base URL without its own token cannot be built and a
    plan launch cannot be relayed. Runs in the relayed home, which holds no login."""

    grant: RelayGrant


type Launch = PlanLaunch | RelayedLaunch

LOOPBACK: Final = "127.0.0.1,localhost"


def launch_env(launch: Launch, *, home: QmxHome, session_id: SessionId, cap: str) -> dict[str, str]:
    """The names this launch needs plus `CONSTANT_ENV`. A relayed launch adds the relay URL,
    the grant secret (never a provider key), the four pinned tiers, `NO_PROXY` for loopback and
    the profile's env quirks. The `QMA_*` names are the launcher's inputs, which it strips
    before the CLI starts."""
    routing: dict[str, str]
    match launch:
        case PlanLaunch():
            routing = {"CLAUDE_CONFIG_DIR": str(home.plan_dir)}
        case RelayedLaunch(grant=grant):
            tiers = grant.profile.tiers
            routing = {
                **grant.profile.quirks.env,
                "CLAUDE_CONFIG_DIR": str(home.relayed_dir),
                "ANTHROPIC_BASE_URL": grant.base_url,
                "ANTHROPIC_AUTH_TOKEN": grant.secret,
                **{name: getattr(tiers, tier) for tier, name in TIER_ENV.items()},
                "NO_PROXY": LOOPBACK,
            }
    return {
        **CONSTANT_ENV,
        **routing,
        "QMA_CHAT_ID": session_id,
        "QMA_PROC_DIR": str(home.procs_dir),
        "QMA_CAP": cap,
    }


def assert_scrubbed(environ: Mapping[str, str]) -> None:
    """Refuse a launch while this process's env holds a name with a banned fragment. The full
    allow-list runs once at boot; here only the banned fragments refuse, so an unrelated name
    a library sets at run time never stops every launch."""
    found = sorted(name for name in environ if banned_fragment(name))
    if found:
        raise LaunchRefused(f"the host environment holds {', '.join(found)}; restart qma.serve")


def instructions(home: QmxHome, workspace: Path) -> str:
    """The QMX-wide rules, then the workspace root's CLAUDE.md and AGENTS.md, for the preset's
    `append`. A missing file adds nothing. `@import` lines stay raw text."""
    sources = (home.plugin_dir / "QMX.md", workspace / "CLAUDE.md", workspace / "AGENTS.md")
    return "\n\n".join(
        f"Contents of {path.as_posix()}:\n\n{path.read_text(encoding='utf-8').strip()}"
        for path in sources
        if path.is_file()
    )


ARGV_BUDGET: Final = 30_000
"""Characters for the whole CLI command line after Windows quoting. Windows caps a command
line at 32,767, and the settings, MCP config, `append` text and deny rules all ride in it."""

ARGV_PARTS: Final[Mapping[str, str]] = {
    "--settings": "the [claude] settings",
    "--append-system-prompt": "QMX.md and the workspace CLAUDE.md and AGENTS.md",
    "--mcp-config": "the MCP config",
    "--disallowedTools": "the deny rules",
}


def argv_length(options: ClaudeAgentOptions) -> tuple[int, dict[str, int]]:
    """The quoted command line length and the size of each large part, as the pinned SDK
    builds it."""
    transport: Any = SubprocessCLITransport(prompt="", options=options)
    transport._cli_path = str(options.cli_path)
    argv: list[str] = transport._build_command()
    parts = {
        ARGV_PARTS[flag]: len(subprocess.list2cmdline([value]))
        for flag, value in itertools.pairwise(argv)
        if flag in ARGV_PARTS
    }
    return len(subprocess.list2cmdline(argv)), parts


def assert_argv_fits(options: ClaudeAgentOptions) -> None:
    """Refuse a launch whose command line exceeds `ARGV_BUDGET`, naming the largest part.
    Nothing is truncated."""
    total, parts = argv_length(options)
    if total > ARGV_BUDGET:
        name, size = max(parts.items(), key=lambda part: part[1], default=("the arguments", total))
        raise LaunchRefused(
            f"the CLI command line is {total} characters, over {ARGV_BUDGET}; "
            f"the largest part is {name} at {size}"
        )


def build_options(
    config: ChatConfig,
    *,
    session_id: SessionId,
    transcript_exists: bool,
    env: Mapping[str, str],
    home: QmxHome,
    settings_json: str,
    launcher: Path,
    can_use_tool: CanUseTool,
) -> ClaudeAgentOptions:
    """One plan chat's `ClaudeAgentOptions`. Resume is keyed on the JSONL on disk, never on
    `ChatRecord.started`."""
    return ClaudeAgentOptions(
        cli_path=launcher,
        tools={"type": "preset", "preset": "claude_code"},
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": instructions(home, config.workspace),
        },
        permission_mode=config.mode,
        model=config.model,
        effort=config.effort,
        cwd=config.workspace,
        env=dict(env),
        setting_sources=[],
        settings=settings_json,
        plugins=[{"type": "local", "path": str(home.plugin_dir)}],
        strict_mcp_config=True,
        can_use_tool=can_use_tool,
        session_id=None if transcript_exists else session_id,
        resume=session_id if transcript_exists else None,
        include_partial_messages=True,
        enable_file_checkpointing=True,
        extra_args={"replay-user-messages": None},
        verbatim_prompts=verbatim(config.kind),
    )
