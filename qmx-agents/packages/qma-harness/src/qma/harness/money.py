"""The money rule and the credential guards: agents may read money data and can never move
money, and the plan token never leaves this PC through QMA.

Honest layering. Against agent Bash under the operator's own OS user, exactly one thing is
structural: broker credential scope, when proven (`MoneyPosture.STRUCTURAL`, check S27). The
relay's egress stop is a tripwire for plain-text Claude tokens. Everything here is a guard
against accidents and against the model's own tool calls; Bash gets around each of them
(variable expansion, string concatenation, a tool that runs commands):
1. No money-act tool exists. `tools.Effect` has no money-act member, and `check_tool_surface`
   refuses to build the `qmx` server, or to admit an external MCP server, if any tool name or
   metadata names a denied act.
2. Approvals bound to arguments (`tools.Grants`).
3. The PreToolUse callback (`pre_tool_use`), in every mode and inside sub-agents. It covers
   reads as well as writes, because read-only Bash runs without asking in default mode.
4. Deny rules passed in code (`deny_rules`).

The deny-list itself is `qma.core.barriers.money_path`, reached through
`qma.core.barriers.descriptors`; this module holds no second copy (HOW gotcha 11).
"""

from __future__ import annotations

import os
import posixpath
import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, cast

from qma.core.barriers.descriptors import check_descriptor, name_money_act
from qma.core.barriers.money_path import MoneyPathDenyError

if TYPE_CHECKING:
    from claude_agent_sdk.types import HookCallback, HookContext, HookInput, HookJSONOutput

SHELL_TOOLS: Final[frozenset[str]] = frozenset({"Bash", "PowerShell", "Monitor"})
"""Every built-in tool whose input is a command line (02a section 15 for Monitor)."""

READ_TOOLS: Final[frozenset[str]] = frozenset({"Read", "Grep", "Glob"})
WRITE_TOOLS: Final[frozenset[str]] = frozenset({"Edit", "Write", "NotebookEdit"})
PATH_FIELDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "Read": ("file_path",),
        "Grep": ("path",),
        "Glob": ("path",),
        "Edit": ("file_path",),
        "Write": ("file_path",),
        "NotebookEdit": ("notebook_path",),
    }
)

LOGIN_NAME: Final = ".credentials.json"
"""The plan login's file name. A file of this name is a secret in any folder."""

SHELL_WORDS: Final[tuple[str, ...]] = (
    ".credentials",
    "claude_config_dir",
    "claude code-credentials",
)
"""Fragments a shell command may not contain, casefolded. The last is the macOS Keychain item
(DESIGN open question 7)."""

CREDENTIAL_READERS: Final = re.compile(
    r"(?<![\w-])(cmdkey|vaultcmd|get-storedcredential|get-secret|keyring|win32cred|credread\w*"
    r"|credenumerate\w*|passwordvault|secret-tool|find-generic-password|find-internet-password"
    r"|dump-keychain)(?![\w-])"
)
"""Programs, modules and cmdlets that read an OS credential store, matched as whole words in
casefolded command text. No chat reads the store through a shell, whatever the entry name."""

SWEEP: Final = re.compile(
    r"(?<![\w-])(find|rg|fd|tree|du|locate|gci|get-childitem|dir)(?![\w-])"
    r"|(?<=\s)(-r|-rf|-fr|-rl|-rn|-ri|--recursive|-recurse|/s)(?![\w-])"
)
"""A command that walks a folder tree. Aimed at a drive root or a user home, it searches the
operator's whole account (a model ran `find / -name .claude` in HP1)."""

BARE_NAMES: Final[frozenset[str]] = frozenset({".claude", ".claude.json", ".credentials.json"})

DENY_PREFIX: Final = "money rule: "


@dataclass(frozen=True)
class GateRules:
    """Everything the gate needs, fixed at launch. Built by `tools.gate_rules`. Paths are in
    the POSIX form `normalize_path` gives with `case_insensitive=False`, each one both as
    written and as the OS resolves it, so a junction or link to either form matches."""

    proposal_tools: frozenset[str]
    """Exact tool names that always ask although their names end in `order`
    (`mcp__qmx__propose_order`). The only exemption from the name check."""
    mandatory_asks: frozenset[str]
    """Tool names that always ask, derived from `tools.tool_defs`, never listed by hand."""
    protected_paths: tuple[str, ...]
    """No writes: both Claude homes, chats, procs, state, control.db, portfolio.db,
    settings.toml and the plugin folder."""
    secret_paths: tuple[str, ...]
    """No reads and no writes: the plan login in both forms, under each QMX Claude home and
    under the operator's `~/.claude`, and his `~/.claude.json`."""
    personal_homes: tuple[str, ...]
    """His `~/.claude`, as written and as resolved. No reads and no writes (R20)."""
    keyring_names: frozenset[str]
    """Exact `qmx/<name>` entries, casefolded. Whole names, not a `qmx/` prefix, so his repo
    path (`.../Desktop/QMX/...`) never trips."""
    broker_hosts: frozenset[str]
    """Broker host suffixes, casefolded."""
    variables: Mapping[str, str]
    """Values the gate expands in paths and commands: HOME, USERPROFILE, CLAUDE_CONFIG_DIR."""
    case_insensitive: bool
    """True on Windows and macOS. Paths and names are compared casefolded there."""


_VARIABLE = re.compile(r"\$\{(\w+)\}|\$env:(\w+)|\$(\w+)|%(\w+)%", re.IGNORECASE)
_DRIVE = re.compile(r"^([A-Za-z]):(?:/|$)")


def expand(text: str, variables: Mapping[str, str]) -> str:
    """Replace `$NAME`, `${NAME}`, `$env:NAME` and `%NAME%` for the names in `variables`.
    Names compare in upper case; unknown references stay as written."""

    def value(match: re.Match[str]) -> str:
        name = next(group for group in match.groups() if group is not None)
        return variables.get(name.upper(), match.group(0))

    return _VARIABLE.sub(value, text)


def normalize_path(
    raw: str,
    *,
    cwd: str,
    home: str,
    case_insensitive: bool,
    variables: Mapping[str, str] = MappingProxyType({}),
) -> str:
    """Pure. Expand `~` and the known variables, resolve against `cwd`, convert to the POSIX
    form the CLI matches on (`C:\\Users\\x` becomes `/c/Users/x`), and casefold when
    `case_insensitive`. The same function feeds `deny_rules` and `gate`."""
    text = expand(raw.strip().strip("'\""), variables).replace("\\", "/")
    if text == "~" or text.startswith("~/"):
        text = home.replace("\\", "/") + text[1:]
    drive = _DRIVE.match(text)
    if drive:
        text = f"/{drive.group(1).lower()}/{text[3:]}"
    elif not text.startswith("/"):
        base = normalize_path(cwd, cwd="/", home=home, case_insensitive=False)
        text = f"{base}/{text}"
    text = posixpath.normpath(re.sub(r"^/+", "/", text))
    return text.casefold() if case_insensitive else text


def within(path: str, base: str) -> bool:
    return path == base or path.startswith(base.rstrip("/") + "/")


_POSIX_DRIVE = re.compile(r"^/([A-Za-z])(?:/|$)")


def canonical(path: str) -> str:
    """The path the OS opens for `path`, a `normalize_path` result with case kept. The
    longest existing prefix goes through `os.path.realpath`, which on Windows expands 8.3
    names, follows links and junctions, and drops trailing dots, spaces and `::$DATA`; the
    rest is appended as written. Stats the file system, so not pure."""
    drive = _POSIX_DRIVE.match(path)
    if os.name == "nt":
        if drive is None:
            return path
        native = f"{drive.group(1)}:/{path[3:]}"
    else:
        native = path
    try:
        resolved = os.path.realpath(native)
    except OSError, ValueError:
        return path
    return normalize_path(resolved, cwd="/", home="/", case_insensitive=False)


_REMOTE = re.compile(r"^//(?:[?.]/|[^/]+/)")
_DRIVE_STREAM = re.compile(r"^[A-Za-z]:.*:")


def remote_form(raw: str) -> str | None:
    """A device or network prefix (`\\\\?\\`, `\\\\.\\`, `\\\\host\\share`, `//host/share`),
    or an NTFS stream after a drive. Refused outright: the gate never stats a network path,
    and a stream is never compared."""
    text = raw.strip().strip("'\"").replace("\\", "/")
    if _REMOTE.match(text):
        return "a device or network path"
    if _DRIVE_STREAM.match(text):
        return "an NTFS stream"
    return None


def odd_form(raw: str) -> str | None:
    """`remote_form`, a stream on any path, an 8.3 short segment (`CLAUDE~1`), or a segment
    ending in a dot or a space, which Windows drops. File-tool paths only: in shell text
    `HEAD~1:a.py` and a sentence ending `a.py.` are ordinary, so there `canonical` reads them."""
    found = remote_form(raw)
    if found is not None:
        return found
    text = raw.strip().strip("'\"").replace("\\", "/")
    segments = text.split("/")
    if ":" in re.sub(r"^[A-Za-z]:", "", text):
        return "an NTFS stream"
    if any(re.search(r"~\d", segment) for segment in segments):
        return "an 8.3 short name"
    if any(s not in {".", ".."} and s.endswith((".", " ")) for s in segments):
        return "a segment ending in a dot or a space"
    return None


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


@dataclass(frozen=True)
class _Folded:
    """The rules' paths and names in the form `gate` compares, built once per call."""

    protected: tuple[str, ...]
    secrets: tuple[str, ...]
    personal: tuple[str, ...]
    home: str
    fold: Callable[[str], str]

    @classmethod
    def of(cls, rules: GateRules) -> _Folded:
        fold: Callable[[str], str] = str.casefold if rules.case_insensitive else str
        return cls(
            tuple(map(fold, rules.protected_paths)),
            tuple(map(fold, rules.secret_paths)),
            tuple(map(fold, rules.personal_homes)),
            fold(rules.variables.get("HOME", "/")),
            fold,
        )


def _deny(reason: str) -> Deny:
    return Deny(DENY_PREFIX + reason)


def _forms(raw: str, *, cwd: str, rules: GateRules, folded: _Folded) -> tuple[str, ...]:
    """`raw` as written and as the OS resolves it, each in the form the rules compare."""
    literal = normalize_path(
        raw,
        cwd=cwd,
        home=rules.variables.get("HOME", "/"),
        case_insensitive=False,
        variables=rules.variables,
    )
    return tuple(dict.fromkeys(map(folded.fold, (literal, canonical(literal)))))


def _secret(path: str, folded: _Folded) -> bool:
    return path in folded.secrets or posixpath.basename(path).casefold() == LOGIN_NAME


def _read_target(path: str, folded: _Folded, *, folder: bool) -> Deny | None:
    if _secret(path, folded):
        return _deny(f"agents cannot read or write a login file ({path})")
    if any(within(path, home) for home in folded.personal):
        return _deny(f"agents cannot read or write the operator's own Claude home ({path})")
    if folder and any(within(target, path) for target in (*folded.secrets, *folded.personal)):
        return _deny(f"{path} holds a login file or the operator's own Claude home")
    return None


def _file_tool(
    tool_name: str, tool_input: Mapping[str, object], rules: GateRules, cwd: str
) -> Deny | None:
    folded = _Folded.of(rules)
    folder = tool_name in {"Grep", "Glob"}
    raw = [tool_input.get(field) for field in PATH_FIELDS[tool_name]]
    paths = [value for value in raw if isinstance(value, str) and value] or (
        [cwd] if folder else []
    )
    if folder:
        loose = [str(value) for key, value in tool_input.items() if key in {"pattern", "glob"}]
        if any(".credentials" in value.casefold() for value in loose):
            return _deny("agents cannot search for login files")
        pattern = tool_input.get("pattern")
        if tool_name == "Glob" and isinstance(pattern, str):
            fixed = re.split(r"[*?\[{]", pattern, maxsplit=1)[0]
            if fixed:
                paths.append(posixpath.dirname(fixed.replace("\\", "/")) or ".")
    for raw_path in paths:
        odd = odd_form(expand(raw_path, rules.variables))
        if odd is not None:
            return _deny(f"agents cannot use {odd} ({raw_path})")
        for path in _forms(raw_path, cwd=cwd, rules=rules, folded=folded):
            found = _read_target(path, folded, folder=folder)
            if found is not None:
                return found
            if tool_name in WRITE_TOOLS and any(within(path, p) for p in folded.protected):
                return _deny(f"agents cannot write QMX state ({path})")
    return None


_CANDIDATE = re.compile(r"""[^\s'"`;&|<>(){}=,]+""")
_QUOTED = re.compile(r"""'([^']*)'|"([^"]*)\"""")


def _candidates(text: str) -> Iterator[str]:
    """Path-like words of a command: every bare word, and every quoted string."""
    for match in _QUOTED.finditer(text):
        yield match.group(1) if match.group(1) is not None else match.group(2)
    yield from _CANDIDATE.findall(text)


def _pathlike(word: str) -> bool:
    return bool(word) and ("/" in word or "\\" in word or word[0] in "~$%.")


def _roots(folded: _Folded) -> set[str]:
    home = folded.home.rstrip("/") or "/"
    return {"/", home, posixpath.dirname(home), "/home", "/users"}


def _shell(tool_input: Mapping[str, object], rules: GateRules, cwd: str) -> Deny | None:
    text = " ".join(
        str(value) for key, value in tool_input.items() if key != "description" and value
    )
    expanded = expand(text, rules.variables)
    lowered = expanded.casefold()
    for word in SHELL_WORDS:
        if word in lowered or word in text.casefold():
            return _deny(f"agents cannot touch the Claude login or its home ({word})")
    reader = CREDENTIAL_READERS.search(lowered)
    if reader:
        return _deny(f"agents cannot read the OS credential store ({reader.group(1)})")
    for name in rules.keyring_names:
        if name in lowered:
            return _deny(f"agents cannot name a QMX credential ({name})")
    for host in rules.broker_hosts:
        if host in lowered:
            return _deny(f"agents cannot reach a broker ({host})")
    folded = _Folded.of(rules)
    roots = _roots(folded)
    sweep = SWEEP.search(f" {lowered}")
    for word in _candidates(expanded):
        if word.strip("'\"").casefold() in BARE_NAMES:
            return _deny(f"agents cannot search for Claude homes or login files ({word})")
        if not _pathlike(word):
            continue
        remote = remote_form(word)
        if remote is not None:
            return _deny(f"agents cannot use {remote} ({word})")
        for path in _forms(word, cwd=cwd, rules=rules, folded=folded):
            found = _read_target(path, folded, folder=False)
            if found is not None:
                return found
            if any(within(path, p) for p in folded.protected):
                return _deny(f"agents cannot touch QMX state from a shell ({path})")
            if sweep and (path in roots or re.fullmatch(r"/[a-z]", path)):
                return _deny(f"agents cannot sweep a drive root or a user home ({path})")
    return None


def _host(url: str) -> str:
    return re.sub(r"^[a-z][a-z0-9+.-]*://", "", url.strip().casefold()).split("/")[0].split(":")[0]


def gate(
    tool_name: str,
    tool_input: Mapping[str, object],
    rules: GateRules,
    *,
    cwd: str,
    agent_id: str | None,
) -> Verdict:
    """Fast, no network and no writes; it stats paths only to resolve them (`canonical`).
    Total over every tool name, built-in or MCP, main agent or sub-agent. `agent_id` is
    unused until `delegate` lands (gate step 1, R33).

    Order:
    2. proposal identity -> Ask.
    3. an MCP tool whose name ends in a money act -> Deny. Built-in names are the CLI's own
       closed set (`ExitPlanMode` would read as a `mode` act).
    4. READ_TOOLS or WRITE_TOOLS on an odd Windows path form (`odd_form`), a login file,
       inside the personal home, or (Grep, Glob) on a folder holding either -> Deny. Each
       path is compared as written and as resolved.
    5. WRITE_TOOLS into `protected_paths` -> Deny.
    6. SHELL_TOOLS whose command names a login fragment, a credential-store reader, a
       keyring name, a broker host, a protected or secret path, the personal home, a bare
       Claude home name, or sweeps a drive root or user home -> Deny.
    7. WebFetch to a broker host -> Deny.
    8. name in `mandatory_asks` -> Ask.
    9. else Pass.
    """
    del agent_id
    if tool_name in rules.proposal_tools:
        return Ask("an order proposal always asks you")
    if tool_name.startswith("mcp__"):
        act = name_money_act(tool_name)
        if act is not None:
            return _deny(f"agents cannot place, change or cancel orders ({tool_name} is {act})")
    found: Deny | None = None
    if tool_name in PATH_FIELDS:
        found = _file_tool(tool_name, tool_input, rules, cwd)
    elif tool_name in SHELL_TOOLS:
        found = _shell(tool_input, rules, cwd)
    elif tool_name == "WebFetch":
        host = _host(str(tool_input.get("url", "")))
        if any(host == b or host.endswith("." + b) for b in rules.broker_hosts):
            found = _deny(f"agents cannot reach a broker ({host})")
    if found is not None:
        return found
    if tool_name in rules.mandatory_asks:
        return Ask(f"{tool_name} always asks you")
    return Pass()


def hook_output(verdict: Verdict) -> dict[str, Any]:
    match verdict:
        case Pass():
            return {}
        case Ask(reason=reason):
            decision = "ask"
        case Deny(reason=reason):
            decision = "deny"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def pre_tool_use(rules: GateRules) -> HookCallback:
    """Adapter from `gate` to the SDK hook output shape. Reads `cwd` and `agent_id` from the
    hook input. Any exception inside `gate` returns deny (fail closed). A callback past its
    `HookMatcher.timeout` blocks the call (hooks reference); check S38 proves it here. The
    callback does no I/O and awaits nothing."""

    async def callback(
        hook_input: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        del tool_use_id, context
        data = cast("Mapping[str, Any]", hook_input)
        try:
            verdict = gate(
                str(data["tool_name"]),
                data.get("tool_input") or {},
                rules,
                cwd=str(data.get("cwd") or "/"),
                agent_id=data.get("agent_id"),
            )
        except Exception as error:
            verdict = _deny(f"the gate failed ({type(error).__name__}), so the call is blocked")
        return cast("HookJSONOutput", hook_output(verdict))

    return callback


def deny_rules(rules: GateRules) -> list[str]:
    """Claude Code rule strings for `disallowed_tools`, in the `//c/Users/...` form Windows
    matching needs. Read rules also cover Grep and Glob (best effort, permissions page)."""
    found: list[str] = []
    for secret in (*rules.secret_paths, f"/**/{LOGIN_NAME}"):
        found += [f"{tool}(/{secret})" for tool in ("Read", "Edit", "Write")]
    found += [
        f"{tool}(/{home}/**)"
        for home in rules.personal_homes
        for tool in ("Read", "Edit", "Write", "NotebookEdit")
    ]
    for path in rules.protected_paths:
        found += [
            f"{tool}(/{target})"
            for target in (path, f"{path}/**")
            for tool in ("Edit", "Write", "NotebookEdit")
        ]
    return found


class MoneySurfaceError(RuntimeError):
    """A tool surface names a money act. The session, or that MCP server, does not start."""


def check_tool_surface(
    names: Iterable[str], metadata: Mapping[str, Mapping[str, object]], exempt: frozenset[str]
) -> None:
    """Build-time check over every tool name and its metadata, through `check_descriptor`,
    for the `qmx` server and for each external MCP server's tool list. `exempt` holds the
    proposal writer, admitted by identity."""
    for name in names:
        if name in exempt:
            continue
        try:
            check_descriptor(name, dict(metadata.get(name, {})))
        except MoneyPathDenyError as refused:
            raise MoneySurfaceError(str(refused)) from None


@dataclass(frozen=True)
class ExposureTarget:
    kind: Literal["keyring_entry", "read_path", "write_path", "loopback"]
    value: str
    """A `qmx/*` keyring name, a path, or `127.0.0.1:<port>`."""


@dataclass(frozen=True)
class ExposureFinding:
    target: ExposureTarget
    reachable: bool | None
    """None means not measured."""
    detail: str
    """Plain words for the usage page. Never a secret value."""


@dataclass(frozen=True)
class ExposureReport:
    at: datetime
    cli_version: str
    findings: tuple[ExposureFinding, ...]


class MoneyPosture(StrEnum):
    STRUCTURAL = "structural"
    """Every broker credential QMX knows of has a stored S27 proof that it cannot trade."""
    SPEED_BUMP = "speed_bump"
    """Anything else, including anything unknown, unmeasured or unreachable."""


NON_BROKER_REFS: Final[frozenset[str]] = frozenset({"qmx/chatgpt", "qmx/control-token"})
"""Fixed entries known not to be broker credentials."""
