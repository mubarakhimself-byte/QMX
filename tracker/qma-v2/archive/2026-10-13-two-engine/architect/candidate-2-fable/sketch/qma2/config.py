"""QMX's own config home and Claude-style layered settings. Never the operator's ~/.claude.

Layout under `<qmx_home>/qma2/` (platform-neutral; `qmx_home` defaults to ~/.qmx):

    claude-home/            CLAUDE_CONFIG_DIR for the one Claude Max account. The operator
                            runs `claude /login` here himself; QMX never reads what's inside.
    settings.json           user layer
    agents/*.md             Claude sub-agent definitions (both engines read these)
    skills/<name>/SKILL.md  skills (both engines)
    hooks/                  hook scripts referenced from settings
    memory/<project-key>/MEMORY.md
    profiles.json           named presets: engine, model, effort, mode, tool set
    agents.db               qma2 store
    traces/<thread>/<turn>.jsonl

Project layers live beside the work: `<cwd>/.qmx/settings.json` (project) and
`<cwd>/.qmx/settings.local.json` (local, where ALLOW_ALWAYS writes rules).

Precedence (Claude's): managed > session (in-memory remembered decisions) > local > project > user.
The managed layer is Python code (`policy.MANAGED_RULES`), not a file, so no settings edit and
no agent can remove the money rules.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qma2.types import Effort, EngineKind, Json, ModelRef, PermissionMode

type SettingsLayer = Literal["user", "project", "local"]


class PermissionRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow: list[str] = Field(default_factory=list)  # Claude syntax: "Bash(npm test *)"
    ask: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class HookEntry(BaseModel):
    """Claude's settings `hooks` shape: event → [{matcher, hooks:[{type, command|url, timeout}]}]."""

    model_config = ConfigDict(extra="forbid")
    matcher: str = ""
    hooks: list[Json]


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    engine: EngineKind
    model: str
    provider: str
    effort: Effort = Effort.MEDIUM
    mode: PermissionMode = PermissionMode.DEFAULT
    tools: list[str] | None = None  # None = engine's full baseline set


class Settings(BaseModel):
    """One layer's document. Validated at the boundary (file read, settings_put); trusted inside."""

    model_config = ConfigDict(extra="forbid")
    permissions: PermissionRules = Field(default_factory=PermissionRules)
    mode: PermissionMode | None = None
    hooks: dict[str, list[HookEntry]] = Field(default_factory=dict)
    model: str | None = None
    provider: str | None = None
    effort: Effort | None = None
    engine: EngineKind | None = None
    profile: str | None = None
    mcp_servers: dict[str, Json] = Field(default_factory=dict)
    auto_compact_window_pct: int | None = None  # default 90 (Codex); Claude native honours its own
    env: dict[str, str] = Field(default_factory=dict)  # extra allow-listed env for child processes
    router: RouterSettings | None = None


class RouterSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    background_cap_pct: int = 50
    prefer: Literal["capable", "cheap"] = "capable"


@dataclass(frozen=True)
class ResolvedConfig:
    """What one segment runs with. Pure data; built by `resolve`."""

    rules: tuple[tuple[str, PermissionRules], ...]  # (layer name, rules) in precedence order
    mode: PermissionMode
    hooks: Mapping[str, Sequence[HookEntry]]
    model: ModelRef
    effort: Effort
    engine: EngineKind
    agents_dirs: tuple[Path, ...]
    skills_dirs: tuple[Path, ...]
    memory_file: Path
    instructions_files: tuple[Path, ...]  # CLAUDE.md + AGENTS.md, root → cwd
    mcp_servers: Mapping[str, Json]
    auto_compact_window_pct: int
    env: Mapping[str, str]
    claude_home: Path


@dataclass(frozen=True)
class ConfigHome:
    root: Path  # <qmx_home>/qma2

    @property
    def claude_home(self) -> Path: ...
    @property
    def db(self) -> Path: ...
    @property
    def agents_dir(self) -> Path: ...
    @property
    def skills_dir(self) -> Path: ...
    @property
    def traces_dir(self) -> Path: ...
    def memory_file(self, cwd: Path) -> Path: ...
    def settings_path(self, layer: SettingsLayer, cwd: Path | None) -> Path: ...

    @classmethod
    def ensure(cls, qmx_home: Path) -> ConfigHome:
        """Create the tree if missing; idempotent."""
        raise NotImplementedError


def load_layer(path: Path) -> Settings:
    """Boundary: parse + validate one settings file. Missing file → empty Settings."""
    raise NotImplementedError


def load_profiles(home: ConfigHome) -> Mapping[str, Profile]:
    raise NotImplementedError


def resolve(
    home: ConfigHome,
    cwd: Path,
    *,
    profile: str | None,
    overrides: Settings | None = None,  # thread_create / thread_switch arguments
) -> ResolvedConfig:
    """Pure merge of user < project < local < overrides, plus profile expansion.
    # TODO: discover CLAUDE.md/AGENTS.md from the git root (marker `.git`) down to cwd, in that
    #       order, like Codex agents_md.rs; AGENTS.override.md wins per directory.
    # TODO: mode from overrides > local > project > user > DEFAULT; never `auto` (H1 fact 1).
    """
    raise NotImplementedError


def write_rule(home: ConfigHome, cwd: Path, bucket: Literal["allow", "deny"], rule: str) -> None:
    """ALLOW_ALWAYS / DENY_ALWAYS → append to `<cwd>/.qmx/settings.local.json`. Idempotent:
    an existing identical rule is not duplicated."""
    raise NotImplementedError
