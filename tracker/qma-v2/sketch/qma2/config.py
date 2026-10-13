"""QMX's own config home, its layers, and what each engine receives.

Layout (QMX home defaults to ~/.qmx; nothing is read from the operator's ~/.claude):

    ~/.qmx/
      harness.db                  harness state (single writer, store.py)
      control.db                  qmx-control sessions/blocks/events (unchanged)
      config/                     QMX's "user" scope, in Claude's formats
        settings.json             permissions, hooks, profiles (QMX extension key)
        CLAUDE.md                 user-level instructions
        agents/*.md               sub-agent definitions (Claude frontmatter)
        skills/<name>/SKILL.md
        plugins/<name>/           Claude plugin layout
        .mcp.json
      claude-home/                CLAUDE_CONFIG_DIR for the Claude engine: the operator's
                                  /login, Claude's session JSONL, auto memory. No settings.
      run/claude-plugin/<hash>/   materialised plugin handed to the Claude engine
      traces/                     local OTLP JSONL (both engines)

Project layers come from the workspace as Claude reads them (.claude/settings.json,
.claude/settings.local.json, .claude/agents, .claude/skills, CLAUDE.md, AGENTS.md,
.mcp.json) plus `.agents/skills` (Codex/SDK convention).

One loader produces one ResolvedConfig. The Claude engine gets a *materialisation* of
it (explicit options + a generated hook-free plugin dir); the OpenAI engine gets the
same object in memory. Neither engine loads config on its own, so rules and hooks are
evaluated only by QMX (policy.py, hooks.py).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from qma2.hooks import HookHandler
from qma2.model import Effort, JsonValue, Mode
from qma2.policy import Caps, Rule


@dataclass(frozen=True, slots=True)
class ConfigHome:
    root: Path

    @property
    def claude_home(self) -> Path:
        raise NotImplementedError

    @property
    def user_dir(self) -> Path:
        raise NotImplementedError

    def memory_file(self, cwd: Path) -> Path:
        """Claude's auto-memory location for `cwd`, inside claude_home. Both engines read
        and (through gated Edit calls) write the same file."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class AgentDef:
    """Claude sub-agent frontmatter, parsed once. Passed to Claude as AgentDefinition,
    to the OpenAI Agent tool as a nested agent."""

    name: str
    description: str
    prompt: str
    tools: tuple[str, ...] | None
    disallowed_tools: tuple[str, ...]
    model: str | None  # alias, full id, or "inherit"
    effort: Effort | None
    permission_mode: Mode | None
    max_turns: int | None
    skills: tuple[str, ...]
    background: bool
    source: Path


@dataclass(frozen=True, slots=True)
class SkillDef:
    name: str
    description: str
    path: Path  # folder with SKILL.md; body loaded on invocation only


@dataclass(frozen=True, slots=True)
class McpServerDef:
    name: str  # "qmx" is reserved; the loader refuses it
    transport: str  # stdio | http | sse
    spec: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class Profile:
    """Codex-style named preset: one click changes model, effort, mode and tool set."""

    name: str
    model: str | None
    effort: Effort
    mode: Mode
    tools: tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class CompactionPolicy:
    threshold: float = 0.90  # of the model window (Codex default)
    window_override: Mapping[str, int] | None = None  # per model, like autoCompactWindow


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The first-user-message block on both engines (H9, H10): CLAUDE.md + AGENTS.md
    from repo root down to cwd, AGENTS.override.md wins, plus MEMORY.md head
    (200 lines / 25 KB) and the skill listing. Built once per segment; editing these
    files mid-segment applies after compaction or a new segment (Claude behaviour)."""

    text: str
    digest: str  # changes only when content changes; part of the cache epoch


@dataclass(frozen=True, slots=True)
class ResolvedConfig:
    rules: tuple[Rule, ...]  # file layers only; harness.db rules are merged by the RuleBook
    hooks: tuple[HookHandler, ...]
    agents: Mapping[str, AgentDef]
    skills: Mapping[str, SkillDef]
    mcp: Mapping[str, McpServerDef]
    profiles: Mapping[str, Profile]
    caps: Caps
    compaction: CompactionPolicy
    context: ProjectContext


def load(home: ConfigHome, cwd: Path, *, control_settings: Mapping[str, JsonValue]) -> ResolvedConfig:
    """Merge managed > local > project > user (QMX config dir) as Claude does.

    `control_settings` is qmx-control's settings.toml sections (mcp_servers, router),
    passed in by the caller so qma2 never imports qmx_control.
    """
    raise NotImplementedError


def materialize_claude_plugin(config: ResolvedConfig, home: ConfigHome) -> Path:
    """Write run/claude-plugin/<digest>/ with skills and agents only: no hooks.json,
    no .mcp.json (MCP is passed as options). Content-addressed, so the same config
    yields the same path and the Claude prompt cache is not broken by a new directory.
    Idempotent: an existing digest directory is reused untouched."""
    raise NotImplementedError
