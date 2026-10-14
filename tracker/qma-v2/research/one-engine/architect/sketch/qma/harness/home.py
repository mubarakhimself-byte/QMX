"""QMX's own Claude home and the harness's on-disk state.

Layout under the QMX home (never under the operator's `~/.claude`):

    <qmx_home>/claude/            CLAUDE_CONFIG_DIR for every chat. The CLI keeps the plan
                                  login, sessions (JSONL), auto memory and its user tier here.
    <qmx_home>/claude/settings.json   Native Claude settings: permission rules, settings hooks,
                                  env such as CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH, cleanupPeriodDays.
                                  QMA is its only writer (UI edits and remembered "always" answers).
    <qmx_home>/claude/CLAUDE.md   QMX-wide rules, re-injected on every request by the CLI.
    <qmx_home>/chats/<session_id>.json   One `ChatRecord` per chat. Each chat writes only its own file.
    <qmx_home>/workspaces/        Default working folders, outside any dev repo.
    <repo>/qmx-agents/plugin/     QMX's shipped skills, agents, commands (read-only, versioned).

Single source of truth per setting:
- Claude-native behaviour (rules, hooks, CLI env knobs) lives in `settings.json`.
- QMX-only values (provider rows, background cap, live-chat cap, agent memory cap,
  domain-write ask policy, delegate allow-list)
  live in `settings.toml` through `ControlService`.
The two key sets are disjoint, so nothing is hand-synced.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal

from qma.harness.launch import ChatConfig  # noqa: F401  (type only in the sketch)

SessionId = str  # the qmx-control session UUID; also the SDK session_id (see chat.py)


@dataclass(frozen=True)
class QmxHome:
    root: Path

    @property
    def claude_dir(self) -> Path:
        raise NotImplementedError

    @property
    def chats_dir(self) -> Path:
        raise NotImplementedError

    @property
    def workspaces_dir(self) -> Path:
        raise NotImplementedError

    @property
    def plugin_dir(self) -> Path:
        """QMX's shipped plugin folder (skills, agents, commands, settings hooks)."""
        raise NotImplementedError


# --- settings.json: an external file the agent could touch, so it is parsed at every launch ---

FORBIDDEN_SETTINGS: Final[frozenset[str]] = frozenset(
    {
        "apiKeyHelper",  # would switch billing to an API key
        "awsAuthRefresh",
        "awsCredentialExport",
        "forceLoginMethod",
        "disableAllHooks",  # refused regardless; check S20 records whether it would silence SDK callback hooks
    }
)
"""Top-level keys QMA refuses in `settings.json`. Paired with `launch.ROUTING_KEYS`,
which may not appear under `env`."""


@dataclass(frozen=True)
class UserSettings:
    """The parsed `settings.json`. Unknown keys are preserved untouched (forward compatible)."""

    raw: Mapping[str, object]

    @property
    def permission_rules(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """(allow, deny) rule strings. Read by `build_options` only when the user tier
        leaks and the rules must be passed in code."""
        raise NotImplementedError


class LaunchRefused(RuntimeError):
    """The QMX Claude home is in a state that could leak billing, credentials or money.

    Raised before any CLI process starts. The chat shows a `needs_you` block with the reason.
    """


def load_user_settings(home: QmxHome) -> UserSettings:
    """Parse `settings.json`. Raise `LaunchRefused` on any `FORBIDDEN_SETTINGS` key or any
    `launch.ROUTING_KEYS` entry under `env`. Called on every launch, so an edit made by an
    agent's Bash between chats is caught before it takes effect."""
    raise NotImplementedError


def write_user_settings(home: QmxHome, patch: Mapping[str, object]) -> UserSettings:
    """The only writer of `settings.json`. Used by the UI route and by remembered "always"
    answers. Validates with the same rules as `load_user_settings`, then writes atomically
    (temp file plus `os.replace`). Running chats pick it up at their next launch.
    An allow rule naming a QMX tool whose effect asks is accepted but has no power: the
    tool handler still needs a digest grant (`tools.Grants`)."""
    raise NotImplementedError


# --- user-tier proof (02a section 6: settings follow CLAUDE_CONFIG_DIR; skills, agents and
# commands are UNCONFIRMED) ---


class UserTier(StrEnum):
    ISOLATED = "isolated"
    """S7 passed for this CLI version: a marker skill in `claude_dir` appears in the init
    message and none of the skill names in his `~/.claude/skills` do."""
    LEAKS = "leaks"
    """S7 saw one of his names. `build_options` then uses `setting_sources=[]` and passes
    the `settings.json` rules in code."""


def user_tier(home: QmxHome, cli_version: str) -> UserTier | None:
    """The stored S7 result for this CLI version, or None when it has not run yet.
    `Harness.open` runs `probe_user_tier` when this is None, before any chat launches."""
    raise NotImplementedError


async def probe_user_tier(home: QmxHome, cli_version: str) -> UserTier:
    """Check S7, read-only on his side. Writes a marker skill under `claude_dir`, starts
    one bare CLI with the plan `launch_env` and `setting_sources=["user"]`, reads the init
    message's skill list, and compares it with a directory listing (names only) of his
    `~/.claude/skills`. Never writes, opens or modifies anything under `~/.claude`.
    Stores and returns the result. Idempotent per CLI version."""
    raise NotImplementedError


# --- chat records ---


type TurnState = Literal["idle", "running"]


@dataclass(frozen=True)
class ChatRecord:
    """What QMA must remember about a chat across restarts. Nothing else.

    The transcript is the SDK's own JSONL under `claude_dir` (no QMX copy). The session
    id is shared with qmx-control and the SDK, so there is no id mapping to keep in sync.
    """

    session_id: SessionId
    config: ChatConfig
    started: bool
    """False until the first CLI launch succeeds. Decides `session_id=` versus `resume=`."""
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

    Lines: SDK and bundled CLI versions (pinned build has a win_amd64 wheel, CLI at least
    2.1.248 for `verbatim_prompts`); claude_dir location and that it is not `~/.claude`;
    plan login present (via `claude auth status` run with CLAUDE_CONFIG_DIR, output parsed
    for authMethod only, never the token); settings.json parse result; user tier for this
    CLI version; managed-policy files on Windows, macOS and Linux (HOW gotcha 7);
    the names the boot scrub removed, never values; each profile's last provider probe;
    the GPT probe result. The exposure report and money posture lines are added by
    `Harness.doctor`, which runs the probe (money.py).
    """
    raise NotImplementedError
