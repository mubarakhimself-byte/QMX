"""QMX's own Claude homes, the Claude settings QMA passes in code, and on-disk chat state.

Layout under the QMX home (never under the operator's `~/.claude`):

    <qmx_home>/claude/              Plan home. CLAUDE_CONFIG_DIR for plan chats. The CLI keeps
                                    the plan login here (`.credentials.json`, or a Keychain
                                    item keyed to this folder on macOS), and the transcripts.
    <qmx_home>/claude-relayed/      Relayed home. CLAUDE_CONFIG_DIR for key and GPT chats.
                                    It never holds a login. Its `projects/` is a directory link
                                    (a junction on Windows) to `claude/projects/`, so the
                                    transcript folder is the only thing the two homes share and
                                    a provider switch still resumes the same session.
    <qmx_home>/chats/<session_id>.json   One `ChatRecord` per chat. Each chat writes only its own.
    <qmx_home>/procs/<session_id>.json   Pid file, written only by that chat's launcher.
    <qmx_home>/state/               Exposure report, GPT probe result. Correctness records,
                                    under the protected paths; not security gates.
    <qmx_home>/workspaces/          Default working folders, outside any dev repo.
    <repo>/qmx-agents/plugin/       QMX's shipped skills, agents, commands (read-only, versioned).

Settings in code (interrogate verdict, premise change). QMA writes no `settings.json` that
the CLI loads, and `setting_sources=[]` means the CLI loads none from either home. Every
Claude setting reaches the CLI as one inline JSON string through the SDK `settings` option
(the `--settings` "flag settings" layer, above user, project and local files; SDK types.py
and the Claude Code settings page, read 2026-10-14). An inline string lives only in the CLI's
arguments, so nothing an agent edits during a session can change it. A ConfigChange command
hook in the same JSON blocks every settings change during a session as a second guard.

Single source per setting:
- Operator-editable Claude settings (permission rules, operator hooks, a few CLI env knobs)
  live in `settings.toml [claude]`, written only through `ControlService`, validated by
  `parse_claude_settings` on write and again at every launch.
- Fixed Claude settings (`forceLoginMethod`, `cleanupPeriodDays`, the ConfigChange guard)
  live in `code_settings` and cannot be edited.
- QMX-only values (providers, budgets, caps, policies) live in other `settings.toml` sections.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from qma.harness.launch import ChatConfig  # noqa: F401  (type only in the sketch)

if TYPE_CHECKING:
    from qmx_control.service import ControlService

SessionId = str  # the qmx-control session UUID; also the SDK session_id (see chat.py)


@dataclass(frozen=True)
class QmxHome:
    root: Path

    @property
    def plan_dir(self) -> Path:
        """`<root>/claude`. Holds the plan login."""
        raise NotImplementedError

    @property
    def relayed_dir(self) -> Path:
        """`<root>/claude-relayed`. Never holds a login."""
        raise NotImplementedError

    @property
    def chats_dir(self) -> Path:
        raise NotImplementedError

    @property
    def procs_dir(self) -> Path:
        raise NotImplementedError

    @property
    def state_dir(self) -> Path:
        raise NotImplementedError

    @property
    def workspaces_dir(self) -> Path:
        raise NotImplementedError

    @property
    def plugin_dir(self) -> Path:
        """QMX's shipped plugin folder (skills, agents, commands)."""
        raise NotImplementedError


def ensure_homes(home: QmxHome) -> None:
    """Create both homes and the `projects/` link from the relayed home to the plan home.
    Idempotent. Raises `LaunchRefused` if a login file is found in the relayed home."""
    raise NotImplementedError


# --- Claude settings, passed in code ---

CLAUDE_SETTING_KEYS: Final[frozenset[str]] = frozenset({"permissions", "env", "hooks"})
"""Top-level keys allowed in `settings.toml [claude]`. Everything else refuses, including
`apiKeyHelper`, `forceLoginMethod`, `disableAllHooks`, `enabledPlugins` and marketplaces.
`permissions` may hold only `allow`, `ask`, `deny` and `additionalDirectories`."""

CLAUDE_ENV_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH",
        "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS",
        "BASH_DEFAULT_TIMEOUT_MS",
        "BASH_MAX_TIMEOUT_MS",
        "MCP_TOOL_TIMEOUT",
        "CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS",
    }
)
"""The only names allowed under `[claude] env`. No routing, proxy, CA or wrapper name can
be written there, because none is listed."""

CLEANUP_PERIOD_DAYS: Final = 3650
"""Transcripts outlive the CLI's 30-day default sweep. The settings reference says `0`
fails validation and suggests a large value such as 3650."""


@dataclass(frozen=True)
class ClaudeSettings:
    """The validated `settings.toml [claude]` section."""

    raw: Mapping[str, object]


class LaunchRefused(RuntimeError):
    """A state that could leak billing, credentials or money. Raised before any CLI starts.
    The chat shows a `needs_you` block with the reason."""


def parse_claude_settings(raw: Mapping[str, object]) -> ClaudeSettings:
    """Allow-list validation: keys in `CLAUDE_SETTING_KEYS`, `env` names in
    `CLAUDE_ENV_NAMES`, rule strings that parse. Anything else raises `LaunchRefused`."""
    raise NotImplementedError


def code_settings(user: ClaudeSettings, *, launcher: Path) -> str:
    """The one inline JSON string for the SDK `settings` option. Pure.

    The operator's validated keys, then these fixed values, which win:
        forceLoginMethod   "claudeai" (no Console login, so no API billing through /login)
        cleanupPeriodDays  CLEANUP_PERIOD_DAYS
        env                CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH "1" unless the operator set it
        hooks.ConfigChange [{"hooks": [{"type": "command", "command": <launcher>,
                             "args": ["--qma-block-config-change"], "timeout": 10}]}]
    The ConfigChange entry has no matcher, so it blocks every source the CLI lets a hook
    block (`policy_settings` cannot be blocked, by design of the CLI).
    """
    raise NotImplementedError


def remember_rule(control: ControlService, rule: str) -> None:
    """Append an allow rule to `settings.toml [claude] permissions.allow` through
    `ControlService` (the one writer), after `parse_claude_settings` accepts the result.
    Running chats pick it up at their next launch; `chat.py` also hands the rule back to
    the live CLI with destination "session"."""
    raise NotImplementedError


def plan_auth_method(home: QmxHome, settings_json: str) -> str:
    """Run the bundled CLI's `auth status` with CLAUDE_CONFIG_DIR = `plan_dir` and the same
    inline settings. Parse and return the auth method only, never the token. `chat._connect`
    refuses a plan launch unless it is the claude.ai subscription method (the exact string
    is recorded by S2)."""
    raise NotImplementedError


# --- chat records ---


type TurnState = Literal["idle", "running"]


@dataclass(frozen=True)
class ChatRecord:
    """What QMA must remember about a chat across restarts. Nothing else.

    The transcript is the SDK's own JSONL under the shared `projects/` folder (no QMX copy).
    The session id is shared with qmx-control and the SDK, so there is no id mapping.
    """

    session_id: SessionId
    config: ChatConfig
    started: bool
    """False until the first `ResultMessage` of this chat. Decides `session_id=` versus
    `resume=`. A connect, crash or relaunch before the first result leaves it False, so the
    next send starts the session fresh instead of resuming a transcript that never existed."""
    turn: TurnState
    """Written "running" before a prompt is sent and "idle" on its ResultMessage.
    "running" found at boot means the outcome is unknown."""


def read_record(home: QmxHome, session_id: SessionId) -> ChatRecord | None:
    raise NotImplementedError


def write_record(home: QmxHome, record: ChatRecord) -> None:
    """Atomic replace of one chat's file. Idempotent: writing the same record twice is a no-op."""
    raise NotImplementedError


def list_records(home: QmxHome) -> list[ChatRecord]:
    raise NotImplementedError


# --- doctor ---


@dataclass(frozen=True)
class DoctorLine:
    name: str
    ok: bool
    detail: str


def doctor(home: QmxHome, *, scrubbed: tuple[str, ...]) -> list[DoctorLine]:
    """One read-only page of facts the operator or a check script can read.

    Lines: SDK and bundled CLI versions (win_amd64 wheel, CLI at least 2.1.248); both homes
    and that neither is `~/.claude`; no login file in the relayed home; plan auth method
    (subscription or not); `[claude]` parse result; the plugins and MCP servers the last
    connect reported; managed-policy files on Windows, macOS and Linux (HOW gotcha 7); the
    names the boot scrub removed, never values; whether Git Bash resolves on Windows
    (`CLAUDE_CODE_GIT_BASH_PATH` or the default); the launcher cap per OS; each profile's
    last provider probe; the GPT probe result; each departure from vanilla Claude Code.
    The stored exposure report and money posture are added by `Harness.doctor`.
    """
    raise NotImplementedError
