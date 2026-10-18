"""Turn a chat's configuration into one CLI launch. Pure functions, no secrets.

This is the whole of "QMA configures Claude Code". Everything not set here is the
vanilla CLI default, which is the operator's floor (hard rule 3).

Load-bearing choices:
- `tools` and `system_prompt` use the `claude_code` presets. The money rule is not
  enforced by removing tools (the old daemon recipe did that with `tools=[]`).
- `permission_mode` is always passed. Omitting it can start the session in `auto` (02a section 4).
- Settings in code. `setting_sources=[]`, so the CLI loads no settings file from any home,
  and every Claude setting arrives as one inline JSON string through `settings`
  (`home.code_settings`). Plugins arrive only through `plugins`. MCP servers arrive only
  through `mcp_servers` with `strict_mcp_config=True`.
- Routing is a `Launch`: `PlanLaunch` or `RelayedLaunch`. A relayed launch needs a
  `RelayGrant`, which only the relay mints and only for key and GPT profiles. No provider
  key passes through this module, because no key goes into any env.
- The environment. `qma.boot` reduced this process's env to an allow-list at startup, and
  `assert_scrubbed` re-checks the banned fragments at every launch. `launch_env` then sets exactly the names a
  launch needs; there is nothing inherited left to blank out.
- `cli_path` is the QMA launcher (`qma.launcher`), which puts the CLI under the OS limits
  before the CLI starts.
- `verbatim_prompts` follows the chat kind: every non-Interactive chat is verbatim, so text
  QMA built from news, files or tool output cannot dispatch a slash command or read an
  `@path` (02a sections 6 and 15).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from qma.harness.profiles import GptPlan, KeyProvider, ProfileName

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, McpServerConfig, McpSdkServerConfig
    from claude_agent_sdk.types import CanUseTool

    from qma.harness.home import ClaudeSettings, QmxHome, SessionId
    from qma.harness.money import GateRules
    from qma.harness.relay import RelayGrant

type PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"]
type Effort = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Interactive:
    """The operator is at the console or UI. Asks reach him."""


@dataclass(frozen=True)
class Background:
    """Started without the operator present (scheduled jobs, news scans). Gated by the
    background cap (usage.py). Launched with `verbatim_prompts=True`. Unattended."""


@dataclass(frozen=True)
class Child:
    """Started by `mcp__qmx__delegate` from a parent chat, usually on another provider.

    Gets no `delegate` tool and no Agent tool, so a child never starts children
    (operator rule: sub-agents never spawn sub-agents). Its prompt was written by a
    model, so it runs with `verbatim_prompts=True`. `unattended` is copied from the
    parent at delegate time, so a child of a Background chat is unattended too.
    """

    parent: SessionId
    unattended: bool


type ChatKind = Interactive | Background | Child


def verbatim(kind: ChatKind) -> bool:
    """Pure. False only for Interactive. The SDK option is per client, so this one rule
    decides it; `Chat.send` refuses `InjectedText` into a chat where this is False."""
    raise NotImplementedError


def unattended(kind: ChatKind) -> bool:
    """Pure. True for Background and for a Child whose root is Background. Decides the
    bounded ask wait (chat.py), turn and budget limits (`build_options`) and the SIWC
    background-consent check at grant time (relay.py). One rule, three readers."""
    raise NotImplementedError


@dataclass(frozen=True)
class ChatConfig:
    """Everything that decides how a chat's CLI process is launched. Immutable.

    A change is a new `ChatConfig`; `classify_change` decides whether it applies in
    place or needs a relaunch with `resume=`.
    """

    profile: ProfileName
    model: str
    """A tier alias ("opus", "sonnet", "haiku", "fable") or a model id. Accepted only if
    `profiles.resolve_model` accepts it for `profile`, the same function the relay's family
    guard uses, so a model `quote` accepts is never refused by the relay."""
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

    profile changed -> RELAUNCH (new routing env and home). effort changed -> RELAUNCH (no
    Python setter, 02a "Where H1 was wrong" item 4) unless check S37 shows `/effort` works
    headless. model changed within a profile -> SET_MODEL. mode changed -> SET_MODE.
    workspace or kind changed -> ValueError (that is a new chat, not a change).
    """
    raise NotImplementedError


def resets_cache(steps: tuple[Step, ...], old: ChatConfig, new: ChatConfig) -> bool:
    """True when the change makes the next request recompute the conversation uncached
    (each model has its own cache, 02a section 8). Drives whether a `Quote` warns."""
    raise NotImplementedError


# --- test-only switches ---


@dataclass(frozen=True)
class TestMode:
    """Live checks only. Each layer can be switched off so a check proves one layer with the
    others off (interrogate B9), and a plain-http loopback provider is allowed so S9 and S21
    can use a local echo server (B22).

    Only `Harness.open(test=...)` accepts it, and only check scripts under `scripts/live/`
    build one; `qma.serve` never does. A CI grep allows `TestMode(` only there and in tests,
    so no setting, file or agent can switch a layer off at run time.
    """

    gate_hook: bool = True
    deny_rules: bool = True
    grants: bool = True
    relay_egress_stop: bool = True
    redaction: bool = True
    loopback_http_provider: bool = False


# --- environment ---

CONSTANT_ENV: Final[Mapping[str, str]] = {
    "ENABLE_CLAUDEAI_MCP_SERVERS": "false",  # his claude.ai connectors never load (02a section 6)
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",  # no telemetry, no auto-update of the pinned CLI
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",  # feeds the UI `plan` block (04 T13)
    "CLAUDE_AGENT_SDK_CLIENT_APP": "QMA",
}

GATE_TIMEOUT_S: Final = 10.0
"""Explicit `HookMatcher.timeout` for the money gate (the SDK default is 60). A PreToolUse
SDK callback that exceeds its timeout blocks the tool call (Claude Code hooks reference,
Timeouts, read 2026-10-14). Check S38 proves it on this CLI."""


type Env = Mapping[str, str]
type SecretLookup = Callable[[str], str]
"""Reads a `qmx/*` keyring entry. Raises if missing. Never logs the value. Used by the
relay and the GPT sign-in, never by `launch_env`."""


@dataclass(frozen=True)
class PlanLaunch:
    """The operator's Max plan. No base URL, no token: the CLI's own /login in the plan home
    owns sign-in, and no QMX process is in the request path."""


@dataclass(frozen=True)
class RelayedLaunch:
    """A key provider or GPT through the loopback relay. `grant` is required, and only
    `Relay.grant` mints one, so a third-party base URL without its own token cannot be
    built (02a trap 7) and a plan launch cannot be relayed. Runs in the relayed home, which
    holds no login, so the CLI has no plan credential to fall back on."""

    profile: KeyProvider | GptPlan
    grant: RelayGrant


type Launch = PlanLaunch | RelayedLaunch


def launch_env(launch: Launch, *, home: QmxHome, session_id: SessionId, cap: str) -> Env:
    """The names this launch needs, nothing else, plus `CONSTANT_ENV`.

    PlanLaunch: CLAUDE_CONFIG_DIR = `home.plan_dir`.
    RelayedLaunch: CLAUDE_CONFIG_DIR = `home.relayed_dir`; ANTHROPIC_BASE_URL =
        grant.base_url; ANTHROPIC_AUTH_TOKEN = grant.secret (never a provider key); the four
        tier variables from the profile; NO_PROXY = "127.0.0.1,localhost" so loopback
        traffic and its grant secret never go to a proxy; the profile's `quirks.env`
        (KeyProvider rows and GptPlan's fixed quirks alike, ENABLE_TOOL_SEARCH included).
    Both: the launcher inputs QMA_REAL_CLI, QMA_CHAT_ID, QMA_PROC_DIR, QMA_CAP, which the
    launcher strips before the CLI starts.
    """
    raise NotImplementedError


def assert_scrubbed(environ: Mapping[str, str]) -> None:
    """Raise `home.LaunchRefused` if this process's environment holds a name carrying a
    `qma.boot.BANNED_FRAGMENTS` fragment (except `CLAUDE_CODE_GIT_BASH_PATH`). The full
    allow-list runs once, at boot; at launch only the banned fragments refuse, so a library or
    the mini-app supervisor setting an unrelated name never stops every launch (fix check
    2.18, fixed with 2.9). Tests and `scripts/live` that import `qma.harness` directly get the
    same check as `qma.serve`."""
    raise NotImplementedError


def instructions(home: QmxHome, workspace: Path) -> str:
    """QMX-wide rules plus the CLAUDE.md and AGENTS.md text at the workspace root, for
    `system_prompt.append`. No setting source loads CLAUDE.md files, so this is how both
    reach the model. The preset snapshots `append` until compaction (02a section 2), while
    vanilla re-reads CLAUDE.md. `@import` lines stay raw text; parent and subfolder CLAUDE.md,
    `.claude/rules/` and CLAUDE.local.md are not read. Each is a listed departure (DESIGN,
    departures from vanilla)."""
    raise NotImplementedError


ARGV_BUDGET: Final = 30_000
"""Characters for the whole CLI command line after Windows quoting (every `"` gains a
backslash). Windows caps a command line at 32,767. The SDK puts `--settings`,
`--mcp-config`, `--append-system-prompt` and `--disallowedTools` all on argv
(`subprocess_cli._build_command`), so the budget covers all four (fix check 2.2)."""


def assert_argv_fits(options: ClaudeAgentOptions) -> None:
    """Raise `home.LaunchRefused` when the rendered argv exceeds `ARGV_BUDGET`, naming the
    largest part (`[claude]` settings, workspace CLAUDE.md and AGENTS.md, MCP config or deny
    rules) and its size. A clear refusal, never a truncated rule set. `doctor` and S20 report
    the full length, not only the settings."""
    raise NotImplementedError


def build_options(
    config: ChatConfig,
    *,
    session_id: SessionId,
    transcript_exists: bool,
    env: Env,
    home: QmxHome,
    settings_json: str,
    launcher: Path,
    tools: McpSdkServerConfig,
    external_mcp: Mapping[str, McpServerConfig],
    gate: GateRules,
    can_use_tool: CanUseTool,
    budgets: Mapping[str, float],
    test: TestMode,
) -> ClaudeAgentOptions:
    """Pure assembly of one `ClaudeAgentOptions`. Values, in one place:

    cli_path=launcher
    tools={"type": "preset", "preset": "claude_code"}
    system_prompt={"type": "preset", "preset": "claude_code",
                   "append": instructions(home, config.workspace)}
    permission_mode=config.mode
    model=config.model, effort=config.effort
    cwd=config.workspace
    env=env
    setting_sources=[]
    settings=settings_json                 (home.code_settings: inline, never a path)
    plugins=[{"type": "local", "path": str(home.plugin_dir)}]
    strict_mcp_config=True
    mcp_servers={"qmx": tools, **external_mcp}   (external servers already vetted, tools.py)
    hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[money.pre_tool_use(gate)],
                                      timeout=GATE_TIMEOUT_S)]}   (omitted if not test.gate_hook)
    can_use_tool=can_use_tool
    disallowed_tools=money.deny_rules(gate) (empty if not test.deny_rules)
                     + (["Agent"] if Child)
    session_id=session_id if not transcript_exists else None
    resume=session_id if transcript_exists else None
        (keyed on the JSONL on disk, not on `ChatRecord.started`; `chat._connect` refuses a
        started chat whose transcript is gone before this runs. Fix check 2.8.)
    include_partial_messages=True        (live token deltas for the UI)
    enable_file_checkpointing=True, extra_args={"replay-user-messages": None}  (/rewind)
    verbatim_prompts=verbatim(config.kind)
    max_turns, max_budget_usd from `budgets` for Background and Child chats; none for
    Interactive chats, matching Claude Code.
    """
    raise NotImplementedError
