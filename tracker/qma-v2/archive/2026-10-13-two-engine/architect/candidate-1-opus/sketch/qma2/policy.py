"""The one policy point. Claude's rules, Claude's order, both engines.

Runs only in the qmx-control process. Hosts never decide; they ask over the link and
enforce the Verdict. That is why the chain below is identical on both engines, for
sub-agents (same callback / same wrappers, with agent_path), and for MCP tools.

Order (Claude's documented order with the money rule in front):

    money(original input)          -> Deny(MONEY)            never approvable
    PreToolUse hooks               -> deny | ask | allow + updatedInput + context
    money(updated input)           -> Deny(MONEY)
    caps (depth, live sub-agents)  -> Deny(LIMIT)
    deny rules                     -> Deny(RULE)
    ask rules / hook ask           -> NeedsOperator   (dontAsk: Deny)
    protected paths (.git .claude .qmx writes) -> NeedsOperator
    mode                           -> bypass: Allow; plan: Deny writes/exec;
                                      acceptEdits: Allow edits inside workspace roots
    allow rules / hook allow       -> Allow
    read-only built-ins in roots   -> Allow   (Claude default behaviour)
    otherwise                      -> NeedsOperator   (dontAsk: Deny)

`decide` is pure. `evaluate` is the only async wrapper (it runs hooks), and the thread
actor is its only caller.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePath

from qma2.hooks import HookOutcome, HookRunner, PreToolUse
from qma2.model import (
    AgentPath,
    Allow,
    Decision,
    Deny,
    DenySource,
    Mode,
    NeedsOperator,
    ThreadId,
    ToolCall,
)
from qma2.money import MoneySurface, ToolCatalog


class Behavior(StrEnum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class RuleScope(StrEnum):
    """Precedence: managed > (cli) > local > project > user, as Claude.
    THREAD rules come from ALLOW_THREAD answers and live only in harness.db."""

    MANAGED = "managed"
    LOCAL = "local"
    PROJECT = "project"
    USER = "user"
    THREAD = "thread"


@dataclass(frozen=True, slots=True)
class Rule:
    """A parsed Claude permission rule: `Tool` or `Tool(specifier)`.

    Examples: Bash(npm run *), Read(./src/**), Edit(//abs/**), WebFetch(domain:x),
    mcp__server__tool, Agent(Explore), PowerShell(Get-ChildItem *).
    Parsed once at the boundary (config load or answer); matching works on this type.
    """

    behavior: Behavior
    tool: str
    specifier: str | None
    scope: RuleScope
    source: str  # file path or "approval:<id>", shown in the UI

    @staticmethod
    def parse(text: str, behavior: Behavior, scope: RuleScope, source: str) -> Rule:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class RuleSnapshot:
    """Immutable view of every rule that applies to one thread right now:
    file layers (ResolvedConfig) + harness.db rules (user/project/thread).
    The RuleBook (harness.py) is the only writer and swaps snapshots atomically."""

    deny: tuple[Rule, ...]
    ask: tuple[Rule, ...]
    allow: tuple[Rule, ...]


@dataclass(frozen=True, slots=True)
class Workspace:
    """Roots the acceptEdits boundary uses: cwd + additionalDirectories.
    Paths are normalised per OS before any comparison (see `normalize`)."""

    roots: tuple[Path, ...]
    protected: tuple[str, ...] = (".git", ".claude", ".qmx")


@dataclass(frozen=True, slots=True)
class Caps:
    max_depth: int = 3  # Claude default
    max_live_subagents: int = 6  # Codex default, configurable


@dataclass(frozen=True, slots=True)
class PolicyState:
    """Everything `decide` needs, captured by the thread actor at call time."""

    thread: ThreadId
    mode: Mode
    rules: RuleSnapshot
    workspace: Workspace
    caps: Caps
    live_subagents: int


def effective_mode(parent: Mode, requested: Mode | None) -> Mode:
    """Sub-agent inheritance: never escalate; bypass only if the parent has it."""
    raise NotImplementedError


def decide(call: ToolCall, pre: HookOutcome, state: PolicyState) -> Decision:
    """Pure core of the chain above, after money and hooks have run.

    # TODO pseudocode
    # if call.name == "Agent" and call.agent_path.depth + 1 > state.caps.max_depth: Deny(LIMIT)
    # if call.name == "Agent" and state.live_subagents >= state.caps.max_live_subagents: Deny(LIMIT)
    # matches = lambda rules: [r for r in rules if matches_rule(r, call, state.workspace)]
    # if pre.decision == "deny" or matches(state.rules.deny): Deny(HOOK|RULE)
    # if pre.decision == "ask" or matches(state.rules.ask):
    #     return Deny(MODE, "dontAsk") if mode is DONT_ASK else NeedsOperator(...)
    # if writes_protected(call, state.workspace): NeedsOperator (even in bypass, like Codex)
    # if call.name == "ExitPlanMode": NeedsOperator(kind=PLAN)
    # if call.name in {"AskUserQuestion", "AskUser"}: NeedsOperator(kind=QUESTION)
    # mode: BYPASS -> Allow; PLAN and is_mutating(call) -> Deny(MODE);
    #       ACCEPT_EDITS and is_edit(call) and inside roots -> Allow
    # if pre.decision == "allow" or matches(state.rules.allow): Allow(call.input, pre.context)
    # if is_read_only(call) and inside roots: Allow
    # return Deny(MODE) if DONT_ASK else NeedsOperator(TOOL, reason, suggest_rule(call))
    """
    raise NotImplementedError


async def evaluate(
    call: ToolCall,
    state: PolicyState,
    hooks: HookRunner,
    catalog: ToolCatalog,
    surface: MoneySurface,
) -> Decision:
    """The full chain. Only `_ThreadActor.gate` calls this.

    # TODO pseudocode
    # m = money.classify(call, catalog, surface)
    # if MoneyHit: return Deny(m.why, DenySource.MONEY)
    # pre = await hooks.run(PreToolUse(call, state.thread, state.mode))
    # if pre.updated_input is not None:
    #     call = call.with_input(pre.updated_input)
    #     if money.classify(call, ...) is MoneyHit: return Deny(..., MONEY)
    # return decide(call, pre, state)
    """
    raise NotImplementedError


def matches_rule(rule: Rule, call: ToolCall, workspace: Workspace) -> bool:
    """Claude matching semantics. For shell tools, the rule must match every
    sub-command for allow, and any sub-command for deny/ask (cc:permissions:221-227)."""
    raise NotImplementedError


def shell_split(command: str, shell: str) -> Sequence[str]:
    """Split a compound command on && || ; | and newlines, respecting quotes.
    `shell` is "bash" or "powershell". Unparseable input returns the whole string as one
    sub-command so it can only match broad rules (fails toward asking)."""
    raise NotImplementedError


def normalize(path: PurePath, cwd: Path) -> Path:
    """Platform-neutral path key. Keeps the PR #35 defence and generalises it:
    Windows: expand 8.3 short names (refuse if unexpandable), strip trailing dots and
    spaces, fold case, resolve \\\\?\\ prefixes; macOS: fold case on case-insensitive
    volumes; all: resolve symlinks and '..'."""
    raise NotImplementedError


def suggest_rule(call: ToolCall) -> str | None:
    """The rule an ALLOW_ALWAYS answer writes by default: Bash -> first two tokens + ' *'
    (Codex prefix_rule mapping), WebFetch -> domain, Edit -> directory glob, MCP -> exact."""
    raise NotImplementedError


def default_rules() -> Mapping[Behavior, tuple[str, ...]]:
    """Shipped user-layer defaults that match vanilla Claude Code's out-of-the-box
    behaviour: read-only shell commands allowed, everything mutating asks."""
    raise NotImplementedError
