"""The money rule and the credential guards: agents may read money data and can never move
money, and the plan token never leaves this PC through QMA.

Honest layering. Against agent Bash under the operator's own OS user, exactly one thing is
structural: broker credential scope, when proven (`MoneyPosture.STRUCTURAL`). If no broker
credential on this PC can trade, no Bash or Python path can place an order. Measured by check
S27 (M1) per credential, never assumed. The cTrader scope names come from the runner's own
knowledge of the Open API, not from the grounding, so S27 settles them.

The relay's egress stop (`relay.py`) is a tripwire for plain-text Claude tokens: a request
body matching a full token shape never reaches a key or GPT provider. It is not structural.
An encoded, split or reversed token passes it, and a plan chat can send a token out with
WebFetch, curl or an MCP server without touching the relay (fix check 2.4).

Everything else in this module is a guard against accidents and against the model's own tool
calls. Bash can get around each of them (variable expansion, string concatenation, a tool
that runs commands), so none is described as a proof:
1. No money-act tool exists. `tools.Effect` has no money-act member, and
   `check_tool_surface` refuses to build the `qmx` server, or to admit an external MCP
   server, if any tool name or metadata names a denied act.
2. Approvals bound to arguments (`tools.Grants`).
3. The PreToolUse callback (`pre_tool_use`), in every mode and inside sub-agents.
4. Deny rules passed in code (`deny_rules`).

In month one the trading node shares this PC (R25), so the posture is SPEED_BUMP, which the
operator accepted on 10-13 (R21).

The deny-list itself is `qma.core.barriers.money_path` (pure, AD-16). This module adds no
second copy of it (the drift HOW gotcha 11 warns about).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from claude_agent_sdk.types import HookCallback

SHELL_TOOLS: Final[frozenset[str]] = frozenset({"Bash", "PowerShell", "Monitor"})
"""Every built-in tool whose input is a command line (02a section 15 for Monitor)."""

READ_TOOLS: Final[frozenset[str]] = frozenset({"Read", "Grep", "Glob"})
WRITE_TOOLS: Final[frozenset[str]] = frozenset({"Edit", "Write", "NotebookEdit"})


@dataclass(frozen=True)
class GateRules:
    """Everything the gate needs, fixed at launch. Built by `tools.gate_rules`."""

    proposal_tools: frozenset[str]
    """Exact tool names allowed by identity although their names end in `order`
    (`mcp__qmx__propose_order`). The only exemption from the name check."""
    mandatory_asks: frozenset[str]
    """Tool names that always ask: every QMX tool whose `Effect` asks (MANAGE,
    PROPOSE_MONEY, and DOMAIN_WRITE when the UI sets it to ask; R35). Derived from
    `tools.tool_defs`, never listed by hand."""
    protected_paths: tuple[str, ...]
    """No writes. The QMX home: both Claude homes, chats, procs, state, control.db,
    portfolio.db, settings.toml, the plugin folder. Stored normalized (`normalize_path`)."""
    secret_paths: tuple[str, ...]
    """No reads and no writes. The plan login in both forms the CLI uses
    (`<plan_dir>/.credentials.json`, `<plan_dir>/.claude.json`), the same two under his
    `~/.claude` and his `~/.claude.json`. Stored normalized."""
    personal_home: str
    """His `~/.claude`, normalized. No reads and no writes (R20, both directions)."""
    keyring_names: frozenset[str]
    """Exact `qmx/<name>` entries from `exposure_targets`, casefolded. Matched as whole
    names, not as a `qmx/` prefix, so his own repo path (`.../Desktop/QMX/...`) never trips."""
    broker_hosts: frozenset[str]
    """Hostnames from settings.toml [brokers], plus the cTrader Open API hosts."""
    case_insensitive: bool
    """True on Windows and macOS. Paths and names are compared casefolded there."""


def normalize_path(raw: str, *, cwd: str, home: str, case_insensitive: bool) -> str:
    """Pure. Expand `~`, `$HOME`, `${HOME}`, `%USERPROFILE%` and `$CLAUDE_CONFIG_DIR`
    references we know the value of, resolve against `cwd`, convert to the POSIX form the
    CLI matches on (`C:\\Users\\x` becomes `/c/Users/x`; Claude Code permissions page), and
    casefold when `case_insensitive`. The same function feeds `deny_rules` and `gate`."""
    raise NotImplementedError


@dataclass(frozen=True)
class Pass:
    """No opinion. The CLI's own rules, mode and `can_use_tool` decide."""


@dataclass(frozen=True)
class Ask:
    reason: str


@dataclass(frozen=True)
class Deny:
    reason: str


type Verdict = Pass | Ask | Deny
"""There is no Allow. A hook allow does not skip deny and ask rules anyway (02a section 4),
and the gate must never be the reason a call runs."""


def gate(tool_name: str, tool_input: Mapping[str, object], rules: GateRules, *, cwd: str, agent_id: str | None) -> Verdict:
    """Pure, fast, no I/O. Total over every tool name, built-in or MCP, main agent or sub-agent.

    Order:
    1. `mcp__qmx__delegate` with an `agent_id` (a native sub-agent) -> Deny (R33).
    2. proposal identity -> Ask.
    3. money-act token in the name (`qma.core.barriers.money_path.match_money_path_act`
       over name segments) -> Deny.
    4. READ_TOOLS or WRITE_TOOLS whose target is a secret path, inside the personal home,
       or (Grep, Glob) a folder that contains a secret path -> Deny.
    5. WRITE_TOOLS into `protected_paths` -> Deny.
    6. SHELL_TOOLS whose command text, after `normalize_path` on every path-like token,
       names a keyring name, a broker host, a protected or secret path, the personal home,
       `.credentials`, `CLAUDE_CONFIG_DIR`, or the Claude Code Keychain item on macOS
       -> Deny. A tripwire: variable tricks and concatenation get past it.
    7. WebFetch to a broker host -> Deny.
    8. name in `mandatory_asks` -> Ask.
    9. else Pass.
    """
    raise NotImplementedError


def pre_tool_use(rules: GateRules) -> HookCallback:
    """Adapter from `gate` to the SDK hook output shape. Reads `cwd` and `agent_id` from the
    hook input.

    Deny -> {"hookSpecificOutput": {"hookEventName": "PreToolUse",
             "permissionDecision": "deny", "permissionDecisionReason": reason}}
    Ask  -> same with "ask". Pass -> {}.
    Any exception inside `gate` returns deny (fail closed). A callback past its
    `HookMatcher.timeout` blocks the call (hooks reference); check S38 proves it here.
    The callback does no I/O and awaits nothing, so a busy event loop delays it only by
    the loop's own latency.
    """
    raise NotImplementedError


def deny_rules(rules: GateRules) -> list[str]:
    """Claude Code rule strings for `disallowed_tools`, from normalized paths
    (`//c/Users/...` on Windows):
    `Read(//<secret>)`, `Edit(//<secret>)`, `Write(//<secret>)` per secret path;
    `Read(//<personal_home>/**)`, `Edit(...)`, `Write(...)`, `NotebookEdit(...)`;
    `Edit(//<p>/**)`, `Write(//<p>/**)`, `NotebookEdit(//<p>/**)` per protected path.
    Read rules also cover Grep and Glob (best effort, Claude Code permissions page)."""
    raise NotImplementedError


class MoneySurfaceError(RuntimeError):
    """A tool surface names a money act. The session, or that MCP server, does not start."""


def check_tool_surface(names: Iterable[str], metadata: Mapping[str, Mapping[str, object]], exempt: frozenset[str]) -> None:
    """Build-time check, on top of the `Effect` type (HOW gotcha 11 says names alone are not
    enough, so both run). Used for the `qmx` server and for every external MCP server's
    tool list (`tools.vet_mcp_servers`). Calls the LangChain-free `check_descriptor`, which
    deletion step 0 moves to `qma.core.barriers.descriptors`, so the mini-app supervisor
    and the harness share one copy (HOW deletable table: Split)."""
    raise NotImplementedError


# --- posture ---


@dataclass(frozen=True)
class ExposureTarget:
    kind: Literal["keyring_entry", "read_path", "write_path", "loopback"]
    value: str
    """A `qmx/*` keyring name, a path, or `127.0.0.1:<port>`."""


@dataclass(frozen=True)
class ExposureFinding:
    target: ExposureTarget
    reachable: bool | None
    """None means not measured (macOS keyring entries, or the probe could not run)."""
    detail: str
    """Plain words for the usage page. Never a secret value."""


@dataclass(frozen=True)
class ExposureReport:
    at: datetime
    cli_version: str
    findings: tuple[ExposureFinding, ...]


def keyring_inventory(configured: Iterable[str]) -> frozenset[str]:
    """Every `qmx/*` entry this PC holds, by name only: `CredEnumerateW` with the filter
    `qmx/*` on Windows, the Secret Service item listing on Linux. On macOS, the names in
    `configured` only, because the probe never touches the Keychain. `configured` also
    carries the secret names in QMN's config when the node shares this PC (its file vault
    is not a keyring). Never reads a value."""
    raise NotImplementedError


def exposure_targets(home_root: Path, keyring_names: Iterable[str], control_port: int, secret_paths: Iterable[str]) -> tuple[ExposureTarget, ...]:
    """Pure. Every inventoried `qmx/*` entry; QMX home files (settings.toml, control.db,
    portfolio.db for read; the QMX home for write); each secret path (read rights only);
    his `~/.claude` (read and write rights); the qmx-control port without a bearer."""
    raise NotImplementedError


async def run_exposure_probe(env: Mapping[str, str], targets: tuple[ExposureTarget, ...]) -> ExposureReport:
    """Informational, inside-out: what an agent's Bash could reach. Runs `python -I` as a
    subprocess with exactly `env` (the plan `launch_env`) under the agent's OS user.

    Runs at boot once per CLI version and when the operator asks (`Harness.doctor(probe=
    True)`), never on a GET. Keyring entries (Windows, Linux): `get_password`, recording
    only whether a value came back; the value is dropped inside the subprocess. macOS: no
    Keychain call at all, so no prompt can appear; those findings are `None`. Paths:
    `os.access` only, plus a create-and-delete for write targets in QMX's own folders. It
    never opens a secret path. Loopback: one request with no bearer.
    """
    raise NotImplementedError


class MoneyPosture(StrEnum):
    STRUCTURAL = "structural"
    """Every broker credential QMX knows of has a stored S27 proof that it cannot trade."""
    SPEED_BUMP = "speed_bump"
    """Anything else, including anything unknown, unmeasured or unreachable."""


NON_BROKER_REFS: Final[frozenset[str]] = frozenset({"qmx/chatgpt", "qmx/control-token"})
"""Fixed entries known not to be broker credentials. Provider `credential` refs from
settings.toml [providers] are added at run time."""


def money_posture(inventory: frozenset[str], non_broker: frozenset[str], scope_proofs: Mapping[str, bool]) -> MoneyPosture:
    """Pure, fails closed. Every inventoried entry not in `non_broker` counts as a broker
    credential. STRUCTURAL only when each of them has `scope_proofs[ref] is True`.
    Reachability plays no part, so an entry the probe could not reach is never counted as
    safe. Shown on the usage page with the unproven entries named."""
    raise NotImplementedError
