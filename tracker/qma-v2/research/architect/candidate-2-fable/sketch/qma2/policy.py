"""Pure permission policy: Claude's rule syntax, Claude's evaluation order, plus the managed tier.

No IO here. `evaluate` is a pure function from (policy, call) to a RuleVerdict. The shell
around it is `gate.py` (hooks and approvals). Per boundary-discipline.

Evaluation order (cc:agent-sdk/permissions): hooks → deny → ask → mode → allow → ask the user.
Hooks run in gate.py before this function; this function covers deny → ask → mode → allow.

Managed tier (cannot be edited or overridden; `Deny(final=True)`):
- effect MONEY_ACT → deny. Name-based classification (copied from money_path.py, minus the
  LangChain/qmx_broker imports) is applied to BUILTIN/MCP calls to derive the effect; QMX tools
  carry their effect on the ToolSpec.
- Secret reach: `Bash(*keyring*)`, `Bash(*cmdkey*)`, `Bash(*security find-generic-password*)`,
  `Bash(*secret-tool*)`, `Read(<qma2 home>/sealed.json)`, `Read(<claude-home>/**)`,
  `Edit(<claude-home>/**)`, `Write(<claude-home>/**)`. Speed bumps, stated as such.
- Protected paths always ask (Codex WritableRoot): `.git/**`, `.claude/**`, `.qmx/**`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from qma2.types import Allow, Ask, Deny, PermissionMode, RuleVerdict, ToolCall, ToolEffect

type Bucket = Literal["allow", "ask", "deny"]


@dataclass(frozen=True)
class Rule:
    """Parsed `Tool` or `Tool(specifier)`. Specifier semantics follow cc:permissions:
    Bash prefix with `*`, path globs for Read/Edit/Write (`./`, `//`, `~/`), `domain:` for
    WebFetch, `mcp__server__tool`, `Agent(name)`."""

    tool: str
    specifier: str | None
    bucket: Bucket
    layer: str  # "managed" | "session" | "local" | "project" | "user"


@dataclass(frozen=True)
class Policy:
    rules: tuple[Rule, ...]  # already in precedence order; first match in a bucket wins
    mode: PermissionMode


def parse_rule(text: str, bucket: Bucket, layer: str) -> Rule:
    """Boundary parse; raises `RuleSyntaxError`."""
    raise NotImplementedError


def build(layers: Sequence[tuple[str, Mapping[Bucket, Sequence[str]]]], mode: PermissionMode) -> Policy:
    """MANAGED_RULES are prepended; caller passes session/local/project/user."""
    raise NotImplementedError


def matches(rule: Rule, call: ToolCall) -> bool:
    """# TODO: Bash: split on `&&`, `||`, `;`, `|` and require every sub-command to match
    #       (cc:permissions:221-227). Paths: resolve, reject DOS 8.3 short names and stripped
    #       suffixes (PR #35 incident), normalise per OS before globbing."""
    raise NotImplementedError


def evaluate(policy: Policy, call: ToolCall) -> RuleVerdict:
    """Pure. Exhaustive over ToolEffect:
    MONEY_ACT → Deny(final=True) regardless of rules or mode.
    Then deny bucket → ask bucket → mode → allow bucket → Ask(default).
    Mode table:
      PLAN: WRITE/EXTERNAL/MONEY_PROPOSE → Deny("plan mode"); READ/MONEY_READ → Allow.
      ACCEPT_EDITS: WRITE inside cwd → Allow; outside → Ask.
      DONT_ASK: anything that would Ask → Deny (returned to the model, never to the operator).
      BYPASS: everything not denied → Allow (deny and ask rules still apply, as Claude).
      DEFAULT: READ/MONEY_READ → Allow; WRITE/EXTERNAL/MONEY_PROPOSE → Ask.
    """
    raise NotImplementedError


# ----------------------------------------------------------------- money classification

MONEY_ACT_TOKENS: frozenset[str] = frozenset()  # copied from money_path.MoneyPathDeniedAct + aliases
MONEY_READ_TOKENS: frozenset[str] = frozenset({"balance", "positions", "proposals", "quotes"})


def classify_by_name(name: str, metadata: Mapping[str, object]) -> ToolEffect:
    """Copied rules of `money_path.check_descriptor`, turned into a classifier.
    Any `money_path` metadata or an act token after splitting on `_ . : /` → MONEY_ACT.
    `propose_order` from a remote MCP server classifies as MONEY_ACT here on purpose; the only
    proposal path is QMX's registered ToolSpec (tools/registry.py)."""
    raise NotImplementedError


MANAGED_RULES: tuple[Rule, ...] = ()  # built at import from the docstring list above
