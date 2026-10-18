"""Turn a chat's configuration into one CLI launch. Pure functions plus one secret lookup.

This is the whole of "QMA configures Claude Code". Everything not set here is the
vanilla CLI default, which is the operator's floor (hard rule 3).

Load-bearing choices:
- `tools` and `system_prompt` use the `claude_code` presets. The money rule is not
  enforced by removing tools (the old daemon recipe did that with `tools=[]`).
- `permission_mode` is always passed. Omitting it can start the session in `auto` (02a section 4).
- The routing environment is total over `ROUTING_KEYS`. Python merges `env` over the
  parent environment (02a trap 6), so every routing key is assigned on every launch,
  with "" for unused ones. A stray `ANTHROPIC_API_KEY` in the parent cannot win.
- `setting_sources` is `["user"]` (proven) or `[]`. Never `project` or `local`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal


from qma.harness.profiles import Profile, ProfileName

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, McpSdkServerConfig
    from claude_agent_sdk.types import CanUseTool

    from qma.gpt.server import TranslatorHandle
    from qma.harness.home import QmxHome, SessionId, UserTier
    from qma.harness.money import GateRules

type PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Interactive:
    """The operator is at the console or UI. Asks reach him."""


@dataclass(frozen=True)
class Background:
    """Started without the operator present. Gated by the background cap (usage.py)."""


@dataclass(frozen=True)
class Child:
    """Started by `mcp__qmx__delegate` from a parent chat, usually on another provider.

    Gets no `delegate` tool and no Agent tool, so a child never starts children
    (operator rule: sub-agents never spawn sub-agents). Its prompt was written by a
    model, so it runs with `verbatim_prompts=True`.
    """

    parent: SessionId


type ChatKind = Interactive | Background | Child


@dataclass(frozen=True)
class ChatConfig:
    """Everything that decides how a chat's CLI process is launched. Immutable.

    A change is a new `ChatConfig`; `classify_change` decides whether it applies in
    place or needs a relaunch with `resume=`.
    """

    profile: ProfileName
    model: str
    """A tier alias ("opus", "sonnet", "haiku", "fable") or a model id the profile serves."""
    effort: Effort | None
    mode: PermissionMode
    workspace: Path
    kind: ChatKind


@dataclass(frozen=True)
class ConfigChange:
    """What the operator asked to change. Unset fields keep their value."""

    profile: ProfileName | None = None
    model: str | None = None
    effort: Effort | None = None
    mode: PermissionMode | None = None


class Step(Enum):
    SET_MODE = "set_mode"  # native ClaudeSDKClient.set_permission_mode, no cache loss
    SET_MODEL = "set_model"  # native ClaudeSDKClient.set_model, same provider, cache recomputed
    RELAUNCH = "relaunch"  # disconnect, launch again with resume=session_id


def classify_change(old: ChatConfig, new: ChatConfig) -> tuple[Step, ...]:
    """Pure. The one table that decides how a change applies.

    profile changed -> RELAUNCH (new routing env). effort changed -> RELAUNCH (no Python
    setter, 02a "Where H1 was wrong" item 4) unless check S19 shows `/effort` works headless.
    model changed within a profile -> SET_MODEL. mode changed -> SET_MODE.
    workspace or kind changed -> ValueError (that is a new chat, not a change).
    """
    raise NotImplementedError


def resets_cache(steps: tuple[Step, ...], old: ChatConfig, new: ChatConfig) -> bool:
    """True when the change makes the next request recompute the conversation uncached
    (each model has its own cache, 02a section 8). Drives whether a `Quote` is required."""
    raise NotImplementedError


# --- environment ---

ROUTING_KEYS: Final[tuple[str, ...]] = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    "CLAUDE_CONFIG_DIR",
    "ENABLE_TOOL_SEARCH",
)
"""Every variable that changes where requests go, who pays, or which Claude home loads.
`launch_env` assigns all of them on every launch. `home.load_user_settings` refuses any
of them under `settings.json` `env`."""

CONSTANT_ENV: Final[Mapping[str, str]] = {
    "ENABLE_CLAUDEAI_MCP_SERVERS": "false",  # his claude.ai connectors never load (02a section 6)
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",  # no telemetry, no auto-update of the pinned CLI
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",  # feeds the UI `plan` block (04 T13)
    "CLAUDE_AGENT_SDK_CLIENT_APP": "QMA",
}


type Env = Mapping[str, str]
type SecretLookup = Callable[[str], str]
"""Reads a `qmx/*` keyring entry. Raises if missing. Never logs the value."""


def launch_env(
    profile: Profile,
    *,
    home: QmxHome,
    secrets: SecretLookup,
    translator: TranslatorHandle | None,
) -> Env:
    """Total over `ROUTING_KEYS`, plus `CONSTANT_ENV` and the profile's quirks.

    ClaudePlan: every routing key "" except CLAUDE_CONFIG_DIR. The CLI uses its /login.
    KeyProvider: BASE_URL and AUTH_TOKEN from the row and keyring, API_KEY "", all four
        tier variables pinned, ENABLE_TOOL_SEARCH="true", quirks from `extra_env`.
    GptPlan: BASE_URL and AUTH_TOKEN from the `TranslatorHandle`. Passing `None` raises:
        a GPT chat cannot launch unless the translator started, and it starts only with a
        `ProbePassed` (qma.gpt.probe).
    Raises `home.LaunchRefused` if a key provider's secret lookup returns "".
    """
    raise NotImplementedError


def workspace_instructions(workspace: Path) -> str:
    """CLAUDE.md and AGENTS.md text found at the workspace root, for `system_prompt.append`.

    The `project` setting source stays off (it would load the folder's `.claude/` hooks and
    settings), so this is how a repo's own instructions still reach the model, as vanilla
    Claude Code would load them. The preset snapshots `append` until compaction (02a section 2).
    """
    raise NotImplementedError


def build_options(
    config: ChatConfig,
    *,
    session_id: SessionId,
    started: bool,
    env: Env,
    home: QmxHome,
    tier: UserTier,
    tools: McpSdkServerConfig,
    gate: GateRules,
    can_use_tool: CanUseTool,
) -> ClaudeAgentOptions:
    """Pure assembly of one `ClaudeAgentOptions`. Values, in one place:

    tools={"type": "preset", "preset": "claude_code"}
    system_prompt={"type": "preset", "preset": "claude_code",
                   "append": workspace_instructions(config.workspace)}
    permission_mode=config.mode
    model=config.model, effort=config.effort
    cwd=config.workspace
    env=env
    setting_sources=["user"] if tier is PROVEN else []
    plugins=[{"type": "local", "path": home.plugin_dir}]
    strict_mcp_config=True
    mcp_servers={"qmx": tools, **operator MCP servers from settings.toml [mcp_servers]}
    hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[money.pre_tool_use(gate)])]}
    can_use_tool=can_use_tool
    disallowed_tools=money.deny_rules(gate) + (["Agent"] if Child else [])
    session_id=session_id if not started else None
    resume=session_id if started else None
    include_partial_messages=True        (live token deltas for the UI)
    enable_file_checkpointing=True, extra_args={"replay-user-messages": None}  (/rewind)
    verbatim_prompts=isinstance(config.kind, Child)

    No `max_turns`, no `max_budget_usd` for Interactive chats, matching Claude Code.
    Background chats get both from settings.toml [budgets].
    """
    raise NotImplementedError
