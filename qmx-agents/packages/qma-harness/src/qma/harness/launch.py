"""Turn a chat's configuration into one CLI launch. Pure functions, no secrets.

Everything not set here is the vanilla CLI default, which is the operator's floor.

- `tools` and `system_prompt` use the `claude_code` presets. Tools are not removed to keep
  agents safe: the guard callback and the deny rules (`guard`) run on every call.
- `permission_mode` is always passed. Omitting it can start the session in `auto`.
- Settings in code. `setting_sources=[]`, so the CLI loads no settings file from any home, and
  every Claude setting arrives through one per-chat file QMX writes at each launch
  (`home.code_settings`), passed by path. Plugins arrive only through `plugins`, MCP servers
  only through `mcp_servers` with `strict_mcp_config=True`.
- `qma.boot` reduced this process's env to an allow-list at startup, and `assert_scrubbed`
  re-checks the banned fragments at every launch. `launch_env` sets exactly the names a launch
  needs; nothing inherited is left to blank out.
- `cli_path` is the QMA launcher, which puts the CLI under the OS limits before it starts.
- `verbatim_prompts` follows the chat kind, so text QMA built from news, files or tool output
  never dispatches a slash command or reads an `@path`.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import math
import os
import subprocess
import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, cast

import psutil
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

from qma.boot import banned_fragment
from qma.harness import guard
from qma.harness.profiles import TIER_ENV, ProfileName

if TYPE_CHECKING:
    from claude_agent_sdk import McpServerConfig
    from claude_agent_sdk.types import (
        CanUseTool,
        HookCallback,
        HookContext,
        HookEvent,
        HookInput,
        HookJSONOutput,
    )

    from qma.harness.home import QmxHome, SessionId
    from qma.harness.relay import RelayGrant

type PermissionMode = Literal[
    "default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"
]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]

log = logging.getLogger(__name__)


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
    """Started by `mcp__qmx_delegate__run` from a parent chat. Its prompt was written by a model.
    `unattended` is copied from the parent, so a child of a Background chat is unattended.
    It gets no `delegate` tool and no Agent tool, so a child never starts children."""

    parent: SessionId
    unattended: bool


CHILD_DENIED: Final = ("Agent", "Task")
"""`Task` is the Agent tool's older name, denied too in case a CLI build still uses it."""


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


type ChatHook = Callable[[HookInput], Awaitable[None]]


@dataclass(frozen=True)
class ChatHooks:
    """Observe-only SDK hook callbacks for one Background or Child chat, each given the SDK's
    hook input. They run after the guard and cannot allow, deny or change anything: a
    callback's result is dropped, its exception is logged, and one still running after
    `OBSERVER_TIMEOUT_S` is cancelled, so an observer never blocks a tool call."""

    pre_tool_use: ChatHook | None = None
    post_tool_use: ChatHook | None = None
    pre_compact: ChatHook | None = None
    stop: ChatHook | None = None
    subagent_stop: ChatHook | None = None


type HookSink = Callable[[SessionId, HookInput], Awaitable[None]]
"""Observes the hook events of every chat that names it in `hook_sink`, told which chat each
came from. Registered by name on the harness, so a chat reloaded after a restart finds it."""


def sink_hooks(sink: HookSink, chat: SessionId) -> ChatHooks:
    async def observe(hook_input: HookInput) -> None:
        await sink(chat, hook_input)

    return ChatHooks(observe, observe, observe, observe, observe)


CHAT_HOOK_EVENTS: Final[Mapping[str, HookEvent]] = {
    "pre_tool_use": "PreToolUse",
    "post_tool_use": "PostToolUse",
    "pre_compact": "PreCompact",
    "stop": "Stop",
    "subagent_stop": "SubagentStop",
}

OBSERVER_TIMEOUT_S: Final = 5.0
"""Below `GATE_TIMEOUT_S`, so the observer is cancelled before its matcher's timeout could
block the call."""


type HomeKind = Literal["general", "lab", "portfolio", "library", "app", "agent"]


@dataclass(frozen=True)
class Home:
    """Where a session was born (engine AD-35). Fixed at birth; a Child copies its parent's."""

    kind: HomeKind = "general"
    project_id: str | None = None
    """The Library item id of the subject, pod, app or agent the session was born on."""


@dataclass(frozen=True)
class SubAgent:
    """One native sub-agent definition for the SDK `agents` option."""

    description: str
    prompt: str
    tools: tuple[str, ...] | None = None
    model: str | None = None


@dataclass(frozen=True)
class ChatPermissions:
    """`policy` names a policy the host registered on the harness; it answers the asks of a
    Background or Child chat in-process. `allow` and `deny` are CLI permission rules for this
    chat alone, written into its settings file."""

    policy: str | None = None
    allow: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()


type JsonMap = Mapping[str, Any]


@dataclass(frozen=True)
class ChatConfig:
    """Everything that decides how a chat's CLI process is launched. A change is a new config.
    Every field but `hooks` is on the chat record, so a chat read back after a restart launches
    as it was started. `hooks` holds callables and lives only in this process (H16, until the
    engine moves to a named `hook_sink`)."""

    profile: ProfileName
    model: str
    effort: Effort | None
    mode: PermissionMode
    workspace: Path
    kind: ChatKind
    compact_at: float | None = None
    hooks: ChatHooks | None = None
    tools: tuple[str, ...] | None = None
    """None is the `claude_code` preset. A tuple is exactly those built-in tools, and `()` is no
    tool at all: no built-in and no MCP server."""
    home: Home = Home()
    packs: tuple[str, ...] = ()
    toolsets: tuple[str, ...] | None = None
    """QMX toolsets on this chat's surface. None is every core toolset (a copilot); an engine
    node passes the toolsets it declares."""
    agents: Mapping[str, SubAgent] = MappingProxyType({})
    mcp_servers: Mapping[str, JsonMap] = MappingProxyType({})
    """Extra MCP servers for this chat alone, vetted like the operator's."""
    append_system_prompt: str | None = None
    """Background and Child only: after the harness's own system text."""
    hook_sink: str | None = None
    """Background and Child only: the name of a sink the host registered, which observes this
    chat's hook events after the guard."""
    permissions: ChatPermissions = ChatPermissions()
    policy_args: JsonMap = MappingProxyType({})
    """Handed to the named policy with every ask."""
    claude_hooks: JsonMap = MappingProxyType({})
    """Claude Code hooks for this chat alone, in the settings `hooks` shape, checked by
    `HOOK_KEYS` and written into its settings file."""


@dataclass(frozen=True)
class ConfigChange:
    """What the operator asked to change. Unset fields keep their value. Workspace and kind
    are not here: changing either is a new chat."""

    profile: ProfileName | None = None
    model: str | None = None
    effort: Effort | None = None
    mode: PermissionMode | None = None

    def applied_to(self, config: ChatConfig) -> ChatConfig:
        return replace(
            config,
            profile=config.profile if self.profile is None else self.profile,
            model=config.model if self.model is None else self.model,
            effort=config.effort if self.effort is None else self.effort,
            mode=config.mode if self.mode is None else self.mode,
        )


class Step(Enum):
    SET_MODE = "set_mode"
    """`ClaudeSDKClient.set_permission_mode`, at once, even mid-turn."""
    SET_MODEL = "set_model"
    """`ClaudeSDKClient.set_model`, same provider."""
    SET_EFFORT = "set_effort"
    """`/effort <level>` sent as a prompt. HP0 S37 measured that the next model turn uses it,
    so effort needs no relaunch where slash commands run."""
    RELAUNCH = "relaunch"
    """Revoke the grant, end the CLI, launch again with `resume=session_id`."""


def classify_change(old: ChatConfig, new: ChatConfig) -> tuple[Step, ...]:
    """The one table that decides how a change applies. A profile change relaunches, and the
    relaunch carries every other field. Otherwise mode, model and effort each have a native
    step, except effort in a verbatim chat, where `/effort` is plain text, so it relaunches.
    A workspace or kind change raises `ValueError`: that is a new chat."""
    if old.workspace != new.workspace or old.kind != new.kind:
        raise ValueError("a workspace or kind change is a new chat, not a change")
    if old.profile != new.profile:
        return (Step.RELAUNCH,)
    effort_changed = old.effort != new.effort
    if effort_changed and (verbatim(new.kind) or new.effort is None):
        return (Step.RELAUNCH,)
    steps = (
        (Step.SET_MODE, old.mode != new.mode),
        (Step.SET_MODEL, old.model != new.model),
        (Step.SET_EFFORT, effort_changed),
    )
    return tuple(step for step, changed in steps if changed)


def resets_cache(old: ChatConfig, new: ChatConfig) -> bool:
    """True when the next request sends the whole conversation uncached. Each provider and
    each model has its own cache. An effort change counts too: it changes the thinking budget,
    which Anthropic documents as invalidating cached messages (inferred for effort, not
    measured). A permission-mode change keeps the cache."""
    return old.profile != new.profile or old.model != new.model or old.effort != new.effort


@dataclass(frozen=True)
class Budgets:
    """settings.toml [budgets], read at each send so an edit in the UI applies to the next one.
    QMX sets no usage limit of its own (ruling 106): `background_cap`, `max_turns` and
    `max_budget_usd` stay unset unless the operator writes them, and then bound Background and
    Child chats only. `max_live_chats` is machine capacity, not usage: `live_chat_slots`
    derives it from RAM, and a value written here may only lower it (AD-30).
    `interactive_reserve` is how many of those slots Background and Child chats leave for
    Interactive ones (AD-58)."""

    max_live_chats: int | None = None
    session_mb: int = 1536
    overhead_mb: int = 4096
    idle_reap_seconds: float = 900.0
    unattended_ask_seconds: float = 300.0
    background_cap: float | None = None
    """The operator's own share of the plan's five-hour window, above 0 and at most 1."""
    max_turns: int | None = None
    max_budget_usd: float | None = None
    interactive_reserve: int = 2


def live_chat_slots(budgets: Budgets, ram_mb: int) -> int:
    """`floor((ram_mb - overhead_mb) / session_mb)`, at least 1, lowered by a written
    `max_live_chats`."""
    derived = max(1, (ram_mb - budgets.overhead_mb) // budgets.session_mb)
    return derived if budgets.max_live_chats is None else min(derived, budgets.max_live_chats)


def background_slots(budgets: Budgets, ram_mb: int) -> int:
    """The slots a Background or Child chat may hold: `live_chat_slots` less the reserve, and at
    least 1, so unattended work on a small machine still runs one chat at a time."""
    return max(1, live_chat_slots(budgets, ram_mb) - budgets.interactive_reserve)


def machine_ram_mb() -> int:
    return psutil.virtual_memory().total // 2**20


def parse_budgets(raw: Mapping[str, object]) -> Budgets:
    """Each value that is missing falls back to its default; one that is set and out of range
    falls back with a warning."""
    default = Budgets()

    def number(name: str, *, whole: bool = False, at_most: float = math.inf) -> Any:
        fallback = getattr(default, name)
        value = raw.get(name)
        if value is None:
            return fallback
        fits = (
            isinstance(value, int | float)
            and not isinstance(value, bool)
            and (isinstance(value, int) or not whole)
            and 0 < value <= at_most
            and value < math.inf
        )
        if fits:
            return value if whole else float(cast("float", value))
        log.warning("[budgets] %s = %r is out of range; using %s", name, value, fallback)
        return fallback

    found, reserve = raw.get("interactive_reserve"), default.interactive_reserve
    if isinstance(found, int) and not isinstance(found, bool) and found >= 0:
        reserve = found
    elif found is not None:
        log.warning("[budgets] interactive_reserve = %r is out of range; using %s", found, reserve)
    return Budgets(
        max_live_chats=number("max_live_chats", whole=True),
        session_mb=number("session_mb", whole=True),
        overhead_mb=number("overhead_mb", whole=True),
        idle_reap_seconds=number("idle_reap_seconds"),
        unattended_ask_seconds=number("unattended_ask_seconds"),
        background_cap=number("background_cap", at_most=1),
        max_turns=number("max_turns", whole=True),
        max_budget_usd=number("max_budget_usd"),
        interactive_reserve=reserve,
    )


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
"""Explicit `HookMatcher.timeout` for the guard. A PreToolUse SDK callback that exceeds
its timeout blocks the tool call."""

COMPACT_PCT_ENV: Final = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"
"""The CLI's auto-compact trigger as a percentage (1-100) of its auto-compact window. Not
`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, which is a window size in tokens from 100,000 up and cannot
express a share; a key row's window quirk still applies underneath this percentage."""


def chat_options_refusal(config: ChatConfig) -> str | None:
    """Why an option cannot go on a chat of this kind, or None."""
    unattended_only = {
        "compact_at": config.compact_at is not None,
        "hooks": config.hooks is not None,
        "hook_sink": config.hook_sink is not None,
        "append_system_prompt": config.append_system_prompt is not None,
        "a permission policy": config.permissions.policy is not None,
    }
    named = [name for name, given in unattended_only.items() if given]
    if isinstance(config.kind, Interactive) and named:
        return (
            f"{', '.join(named)} are for Background and Child chats only; an Interactive "
            "chat compacts, runs hooks and asks as Claude Code does"
        )
    compact_at = config.compact_at
    if compact_at is not None and not 0.01 <= compact_at <= 1:
        return f"compact_at is a share of the context window from 0.01 to 1, not {compact_at}"
    return None


def compact_env(compact_at: float | None) -> dict[str, str]:
    return {} if compact_at is None else {COMPACT_PCT_ENV: str(round(compact_at * 100))}


def _observer(hook: ChatHook) -> HookCallback:
    async def callback(
        hook_input: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        del tool_use_id, context
        try:
            await asyncio.wait_for(hook(hook_input), OBSERVER_TIMEOUT_S)
        except Exception, asyncio.CancelledError:
            log.exception("a chat hook failed; the chat goes on")
        return {}

    return callback


def chat_hook_matchers(hooks: ChatHooks) -> dict[HookEvent, HookMatcher]:
    return {
        event: HookMatcher(matcher=None, hooks=[_observer(hook)], timeout=GATE_TIMEOUT_S)
        for name, event in CHAT_HOOK_EVENTS.items()
        if (hook := getattr(hooks, name)) is not None
    }


@dataclass(frozen=True)
class PlanLaunch:
    """The operator's Max plan. No base URL and no token: the CLI's own /login in the plan home
    owns sign-in, and no QMX process is in the request path."""


@dataclass(frozen=True)
class RelayedLaunch:
    """A key provider or GPT through the loopback relay. Only the relay mints a grant, and
    only for a key or GPT profile, so a third-party base URL without its own token cannot be
    built and a plan launch cannot be relayed. Runs in the relayed home, which holds no login."""

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


def system_text(home: QmxHome, config: ChatConfig) -> str:
    """What the chat's system text file holds: `instructions`, then the chat's own
    `append_system_prompt`."""
    parts = (instructions(home, config.workspace), config.append_system_prompt or "")
    return "\n\n".join(part for part in parts if part)


ARGV_BUDGET: Final = 30_000
"""Characters for the whole CLI command line after Windows quoting. Windows caps a command
line at 32,767. The MCP config and deny rules ride in it; settings and system text go by file."""

ARGV_PARTS: Final[Mapping[str, str]] = {
    "--settings": "the settings file path",
    "--append-system-prompt-file": "the system text file path",
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
    settings_file: Path,
    system_file: Path,
    launcher: Path,
    can_use_tool: CanUseTool,
    mcp_servers: Mapping[str, McpServerConfig],
    gate: guard.GuardRules,
    budgets: Budgets,
    sink: HookSink | None = None,
    test: TestMode | None = None,
) -> ClaudeAgentOptions:
    """One chat's `ClaudeAgentOptions`. Resume is keyed on the JSONL on disk, never on
    `ChatRecord.started`. `mcp_servers` is `qmx` plus the vetted external servers. The guard
    runs first as a PreToolUse callback on every tool, with an explicit timeout, and the deny
    rules ride in `disallowed_tools`; `test` switches either off for a layer check. The chat's
    own observe-only hooks and its named `sink` are appended after the guard, and `compact_at`
    becomes the CLI's auto-compact percentage for this chat alone.

    Claude settings and the system text go by file path (probes P-SET and P-SYS), so neither
    grows the command line. The preset drops its dynamic sections, so two chats in two folders
    share a cached prefix, and keeps no snapshot, so a changed system text reaches the model at
    the next relaunch by resume (H53)."""
    bounded = not isinstance(config.kind, Interactive)
    gate_hook = test is None or test.gate_hook
    rules_on = test is None or test.deny_rules
    hooks: dict[HookEvent, list[HookMatcher]] = (
        {
            "PreToolUse": [
                HookMatcher(matcher=None, hooks=[guard.pre_tool_use(gate)], timeout=GATE_TIMEOUT_S)
            ]
        }
        if gate_hook
        else {}
    )
    observers = [config.hooks, None if sink is None else sink_hooks(sink, session_id)]
    for observer in observers:
        if observer is not None:
            for event, matcher in chat_hook_matchers(observer).items():
                hooks.setdefault(event, []).append(matcher)
    return ClaudeAgentOptions(
        cli_path=launcher,
        tools={"type": "preset", "preset": "claude_code"}
        if config.tools is None
        else list(config.tools),
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "exclude_dynamic_sections": True,
            "snapshot": False,
        },
        agents={
            name: AgentDefinition(
                description=agent.description,
                prompt=agent.prompt,
                tools=None if agent.tools is None else list(agent.tools),
                model=agent.model,
            )
            for name, agent in config.agents.items()
        }
        or None,
        permission_mode=config.mode,
        model=config.model,
        effort=config.effort,
        cwd=config.workspace,
        env={**env, **compact_env(config.compact_at)},
        setting_sources=[],
        settings=str(settings_file),
        plugins=[{"type": "local", "path": str(home.plugin_dir)}],
        strict_mcp_config=True,
        mcp_servers=dict(mcp_servers),
        hooks=hooks or None,
        disallowed_tools=[
            *(CHILD_DENIED if isinstance(config.kind, Child) else ()),
            *(guard.deny_rules(gate) if rules_on else ()),
        ],
        can_use_tool=can_use_tool,
        session_id=None if transcript_exists else session_id,
        resume=session_id if transcript_exists else None,
        include_partial_messages=True,
        enable_file_checkpointing=True,
        extra_args={
            "replay-user-messages": None,
            "append-system-prompt-file": system_file.as_posix(),
        },
        verbatim_prompts=verbatim(config.kind),
        max_turns=budgets.max_turns if bounded else None,
        max_budget_usd=budgets.max_budget_usd if bounded else None,
    )
