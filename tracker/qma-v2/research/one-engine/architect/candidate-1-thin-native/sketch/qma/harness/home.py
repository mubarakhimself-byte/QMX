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
- QMX-only values (provider rows, background cap, live-chat cap, delegate allow-list)
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
        "disableAllHooks",  # until S-check M5 proves it cannot silence SDK callback hooks
    }
)
"""Top-level keys QMA refuses in `settings.json`. Paired with `launch.ROUTING_KEYS`,
which may not appear under `env`."""


@dataclass(frozen=True)
class UserSettings:
    """The parsed `settings.json`. Unknown keys are preserved untouched (forward compatible)."""

    raw: Mapping[str, object]


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
    (temp file plus `os.replace`). Running chats pick it up at their next launch."""
    raise NotImplementedError


# --- user-tier proof (02a section 6: UNCONFIRMED whether the user tier follows CLAUDE_CONFIG_DIR) ---


class UserTier(StrEnum):
    PROVEN = "proven"
    """S7 showed a marker skill in `claude_dir` loads and one in `~/.claude` does not."""
    UNPROVEN = "unproven"


def user_tier(home: QmxHome) -> UserTier:
    """Read the stored S7 result. `launch.build_options` uses `setting_sources=["user"]`
    only when PROVEN, else `[]` (QMX plugin still loads). Never `project` or `local`:
    a workspace `.claude/settings.json` is agent-writable and unvalidated."""
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


def doctor(home: QmxHome) -> list[DoctorLine]:
    """One read-only page of facts the operator or a check script can read.

    Lines: SDK and bundled CLI versions (pinned build has a win_amd64 wheel); claude_dir
    location and that it is not `~/.claude`; plan login present (via `claude auth status`
    run with CLAUDE_CONFIG_DIR, output parsed for authMethod only, never the token);
    settings.json parse result; user tier; managed-policy files on Windows, macOS and Linux;
    no routing key in the parent environment; money posture (see money.py); each profile's
    last provider probe; the GPT probe result.
    """
    raise NotImplementedError
