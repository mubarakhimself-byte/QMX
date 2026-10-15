"""The money rule and the credential guards: agents may read money data and can never move
money, and the plan token never leaves this PC through QMA.

Honest layering. Against agent Bash under the operator's own OS user, exactly one thing is
structural: broker credential scope, when proven (check S27). The
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

import asyncio
import json
import os
import posixpath
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Literal, cast
from urllib.parse import unquote, urlsplit

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
    r"|(?<=\s)(-[a-z]*r[a-z]*|--recursive|/s|/r)(?![\w-])"
)
"""A command that walks a folder tree: a walking program, or a recursion flag in any spelling
(`-alR`, `-ril`, `-Rec`, `/s`, `where /r`). Aimed at a drive root or a user home, it searches
the operator's whole account (a model ran `find / -name .claude` in HP1)."""

EVALUATED: Final = re.compile(
    r"(?<![\w-])(-enc|-enco|-encod|-encode|-encoded|-encodedc\w*|iex|invoke-expression)"
    r"(?![\w-])|(\$\{env:)"
    r"|(?<![\w-])(?:powershell|pwsh)(?:\.exe)?(?![\w-]).*?\s(-e|-ec|-en)(?![\w-])"
)
"""Text the gate cannot read: an encoded PowerShell command (`-EncodedCommand` and the
prefixes PowerShell accepts, the short ones only after `powershell` or `pwsh`, since `-e` is
an everyday flag elsewhere), a string evaluated as code, or a `${env:...}` reference the
expander does not follow. Casefolded text."""

CHANGES_FOLDER: Final = re.compile(
    r"(?<![\w-])(?:cd|pushd|chdir|set-location|sl|push-location)\s+([^\s;&|)]+)", re.IGNORECASE
)
"""A command that moves the shell's working folder. After one, a relative word may resolve
against the moved folder, so it is checked against the call's cwd, the user home and each
target."""

TO_HOME: Final = re.compile(
    r"(?<![\w-])(?:cd|pushd|chdir|set-location|sl|push-location)(?=\s*(?:$|[;&|)]))",
    re.IGNORECASE,
)
"""A folder change with no target, which goes to the user home in bash."""

FOLDER_OPTION: Final = re.compile(
    r"(?<![\w-])(?:(?:-C|--chdir|--directory|--work-tree|(?i:-wo\w*))(?:=|\s+)|-C(?=[~/\\$%.]))"
    r"([^\s;&|)]+)"
)
"""An option that runs a program in another folder (`git -C`, `tar -C~`, `env --chdir`, `make
--directory`, `git --work-tree`, PowerShell `-WorkingDirectory`). Its target counts as a
folder change. `-C` is case-sensitive, so `python -c` is not one, and joined to its target only
before a path character, so `grep -C3` is not one."""

DRIVE_RELATIVE: Final = re.compile(r"^[A-Za-z]:(?![/\\])")
"""`C:x` or `C:` alone: relative to that drive's own current folder, which the gate cannot
know."""

SHELL_DRIVE_RELATIVE: Final = re.compile(r"^[A-Za-z]:(?![/\\])(?:$|[^/\\\s]*[/\\.])")
"""`DRIVE_RELATIVE` in shell text, only where the word looks like a path: the drive alone, or
a remainder that starts with a dot or holds a slash or a dot (`C:.claude.json`,
`C:Users\\Op`). `a:b`, `scp h:file` and `%h:%s` are not paths."""

GLOB: Final = re.compile(r"[*?\[]")

MAX_SHELL_TEXT: Final = 256 * 1024
"""Bytes of shell text the gate reads. Longer text is denied, not scanned."""

MAX_SHELL_BASES: Final = 32
"""Folders a relative word is resolved against after folder changes. Each `cd` can double
them, so more is denied."""

MAX_SHELL_PATHS: Final = 2048
"""Distinct path words times folders to resolve them against. Each costs a file-system
lookup (`canonical`), so more is denied rather than left to run past the hook timeout."""

DENY_PREFIX: Final = "money rule: "

ATTENDED_MODES: Final[frozenset[str]] = frozenset({"default", "acceptEdits", "plan"})
"""Permission modes in which the CLI asks before an MCP tool runs. Every other mode, an unknown
one and a hook input with none run it unasked, so an external tool there needs the operator's
allow-list."""


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
    dispatch_targets: Mapping[str, str]
    """Tool name -> the input field naming another tool it runs (`mcp__qmx__apps_call` ->
    `tool`). The named tool goes through the same name check."""
    protected_paths: tuple[str, ...]
    """No writes: both Claude homes, chats, procs, state, control.db, portfolio.db,
    settings.toml and the plugin folder. Also rendered as deny rules."""
    qmx_homes: tuple[str, ...]
    """The QMX home. No writes anywhere in it outside `writable_paths`. Deny rules cannot
    carve out an exception, so only the gate holds this; the rules list the children."""
    writable_paths: tuple[str, ...]
    """`workspaces/` and `agent-memory/` in the QMX home, written as in vanilla."""
    secret_paths: tuple[str, ...]
    """No reads and no writes: the plan login in both forms, under each QMX Claude home and
    under the operator's `~/.claude`, his `~/.claude.json`, and the QMX home's
    `settings.toml` and `rclone.conf`, which can hold keys."""
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
    unattended: bool
    """The chat runs without the operator (`launch.unattended`): no external MCP tool runs
    unless `external_unattended` lists it, whatever the permission mode."""
    external_unattended: frozenset[str]
    """`settings.toml [claude] external_tools_unattended`: `server/tool` and `server/*` entries
    the operator allows to run without asking. Only the operator writes settings."""
    dropped_servers: set[str] = field(default_factory=set[str])
    """External MCP servers the chat left out after launch. The only field that changes once
    the chat runs: the chat adds a server when it switches it off, and every tool of that
    server is denied from then on, whether or not the switch-off held."""


QMX_SERVER: Final = "qmx"
DELEGATE_TOOL: Final = f"mcp__{QMX_SERVER}__delegate"


def _external_unattended(tool_name: str, server: str, rules: GateRules, mode: str | None) -> bool:
    if server == QMX_SERVER or (mode in ATTENDED_MODES and not rules.unattended):
        return False
    bare = tool_name.removeprefix(f"mcp__{server}__")
    return not {f"{server}/{bare}", f"{server}/*"} & rules.external_unattended


def mcp_server(tool_name: str) -> str | None:
    """The server of an `mcp__<server>__<tool>` name (`tools.SERVER_NAME` has no `__`)."""
    if not tool_name.startswith("mcp__"):
        return None
    server, separator, _ = tool_name.removeprefix("mcp__").partition("__")
    return server if separator else None


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
    """`remote_form`, a drive-relative path (`C:x`), a stream on any path, an 8.3 short
    segment (`CLAUDE~1`), or a segment ending in a dot or a space, which Windows drops.
    File-tool paths only: in shell text `HEAD~1:a.py` and a sentence ending `a.py.` are
    ordinary, so there `canonical` reads them."""
    found = remote_form(raw)
    if found is not None:
        return found
    if DRIVE_RELATIVE.match(raw.strip().strip("'\"")):
        return "a drive-relative path"
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
    qmx_homes: tuple[str, ...]
    writable: tuple[str, ...]
    secrets: tuple[str, ...]
    personal: tuple[str, ...]
    home: str
    fold: Callable[[str], str]

    @classmethod
    def of(cls, rules: GateRules) -> _Folded:
        fold: Callable[[str], str] = str.casefold if rules.case_insensitive else str
        return cls(
            tuple(map(fold, rules.protected_paths)),
            tuple(map(fold, rules.qmx_homes)),
            tuple(map(fold, rules.writable_paths)),
            tuple(map(fold, rules.secret_paths)),
            tuple(map(fold, rules.personal_homes)),
            fold(rules.variables.get("HOME", "/")),
            fold,
        )

    def protects(self, path: str) -> bool:
        if any(within(path, p) for p in self.protected):
            return True
        return any(within(path, h) for h in self.qmx_homes) and not any(
            within(path, w) for w in self.writable
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
        return _deny(f"agents cannot read or write a login file or a key file ({path})")
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
            if tool_name in WRITE_TOOLS and folded.protects(path):
                return _deny(f"agents cannot write QMX state ({path})")
    return None


_CANDIDATE = re.compile(r"""[^\s'"`;&|<>(){}=,]+""")
_QUOTED = re.compile(r"""'([^']*)'|"([^"]*)\"""")


_BOUND = re.compile(r"^-[A-Za-z][\w-]*:(.+)$")
_FILE_URLS = re.compile(r"""file:(?:[^\s'"`;&|<>(){}=,]|(?<=[A-Za-z])\|)+""", re.IGNORECASE)


def _candidates(text: str) -> Iterator[str]:
    """Path-like words of a command: every bare word, every quoted string, every `file:` URL
    (`C|` is a drive there), and the value of a PowerShell parameter bound with a colon
    (`-Path:C:x`)."""
    for match in _QUOTED.finditer(text):
        yield match.group(1) if match.group(1) is not None else match.group(2)
    yield from _FILE_URLS.findall(text)
    for word in _CANDIDATE.findall(text):
        yield word
        bound = _BOUND.match(word)
        if bound is not None:
            yield bound.group(1)


_URL_DRIVE = re.compile(r"^([A-Za-z])[:|]")


def _unurl(word: str) -> str:
    """A `file:` URL in any form as the local path it opens, percent escapes decoded:
    `file:///C:/x`, `file://C:/x`, `file:C:/x`, `file:/C:/x`, `file:///C|/x` and
    `file://localhost/C:/x` all read `C:/x`."""
    if word[:5].casefold() != "file:":
        return word
    rest = unquote(word[5:])
    if rest.startswith("//") and not _URL_DRIVE.match(rest[2:]):
        rest = "/" + rest[2:].partition("/")[2]
    if _URL_DRIVE.match(rest.lstrip("/")):
        rest = _URL_DRIVE.sub(r"\1:", rest.lstrip("/"), count=1)
    return rest


def _pathlike(word: str) -> bool:
    return bool(word) and ("/" in word or "\\" in word or word[0] in "~$%.")


def _roots(folded: _Folded) -> set[str]:
    home = folded.home.rstrip("/") or "/"
    return {"/", home, posixpath.dirname(home), "/home", "/users"}


def _bases(expanded: str, *, cwd: str, rules: GateRules) -> list[str]:
    """Folders a relative word may resolve against: the call's cwd, after a `cd` also the user
    home, and every target of a `cd` or a folder option reached from an earlier base."""
    moves = [match.group(1) for match in CHANGES_FOLDER.finditer(expanded)]
    options = [match.group(1) for match in FOLDER_OPTION.finditer(expanded)]
    home = rules.variables.get("HOME", "/")
    targets = [target.strip("'\"") for target in (*moves, *options)]
    bases = [cwd, home] if moves or TO_HOME.search(expanded) else [cwd]
    for target in targets:
        bases += [
            normalize_path(
                target, cwd=base, home=home, case_insensitive=False, variables=rules.variables
            )
            for base in bases
        ]
        bases = list(dict.fromkeys(bases))
        if len(bases) > MAX_SHELL_BASES:
            break
    return bases


def _word(word: str, *, base: str, rules: GateRules, folded: _Folded, sweep: bool) -> Deny | None:
    glob = GLOB.search(word)
    if glob is not None:
        folder = posixpath.dirname(word[: glob.start()].replace("\\", "/")) or "."
        for path in _forms(folder, cwd=base, rules=rules, folded=folded):
            found = _read_target(path, folded, folder=True)
            if found is not None:
                return found
            if folded.protects(path):
                return _deny(f"agents cannot touch QMX state from a shell ({path})")
        return None
    forms = (
        _forms(word, cwd=base, rules=rules, folded=folded)
        if _pathlike(word)
        else (
            folded.fold(normalize_path(word, cwd=base, home=folded.home, case_insensitive=False)),
        )
    )
    roots = _roots(folded)
    for path in forms:
        found = _read_target(path, folded, folder=False)
        if found is not None:
            return found
        if folded.protects(path):
            return _deny(f"agents cannot touch QMX state from a shell ({path})")
        if sweep and (path in roots or re.fullmatch(r"/[a-z]", path)):
            return _deny(f"agents cannot sweep a drive root or a user home ({path})")
    return None


def _shell(tool_input: Mapping[str, object], rules: GateRules, cwd: str) -> Deny | None:
    text = " ".join(
        str(value) for key, value in tool_input.items() if key != "description" and value
    )
    size = len(text.encode())
    if size > MAX_SHELL_TEXT:
        return _deny(f"the command is too long to check ({size} bytes)")
    expanded = expand(text, rules.variables)
    lowered = expanded.casefold()
    evaluated = EVALUATED.search(f"{text.casefold()} {lowered}")
    if evaluated:
        found = next(group for group in evaluated.groups() if group)
        return _deny(f"agents cannot run encoded or evaluated commands ({found})")
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
    sweep = SWEEP.search(f" {lowered}") is not None
    bases = _bases(expanded, cwd=cwd, rules=rules)
    if len(bases) > MAX_SHELL_BASES:
        return _deny(f"the command changes folder too often to check ({len(bases)} folders)")
    words = list(dict.fromkeys(map(_unurl, _candidates(expanded))))
    paths = sum(map(_pathlike, words)) * len(bases)
    if paths > MAX_SHELL_PATHS:
        return _deny(f"the command names too many paths to check ({paths} path lookups)")
    for word in words:
        remote = remote_form(word) if _pathlike(word) else None
        if remote is not None:
            return _deny(f"agents cannot use {remote} ({word})")
        if SHELL_DRIVE_RELATIVE.match(word):
            return _deny(f"agents cannot use a drive-relative path ({word})")
        for base in bases:
            found = _word(word, base=base, rules=rules, folded=folded, sweep=sweep)
            if found is not None:
                return found
    return None


def _host(url: str) -> str:
    """The host a URL reaches, as `urlsplit` parses it, without a trailing dot, casefolded. A
    URL with no scheme is read as `https://`, as WebFetch upgrades it."""
    text = url.strip()
    if "://" not in text:
        text = f"https://{text}"
    try:
        host = urlsplit(text).hostname or ""
    except ValueError:
        return ""
    return host.rstrip(".").casefold()


def gate(
    tool_name: str,
    tool_input: Mapping[str, object],
    rules: GateRules,
    *,
    cwd: str,
    agent_id: str | None,
    permission_mode: str | None,
) -> Verdict:
    """Fast, no network and no writes; it stats paths only to resolve them (`canonical`).
    Total over every tool name, built-in or MCP, main agent or sub-agent.

    Order:
    1. `mcp__qmx__delegate` with an `agent_id` (a native sub-agent) -> Deny (R33).
    2. proposal identity -> Ask.
    3. an MCP tool whose name, with or without its `mcp__<server>__` prefix, names a money
       act, or a dispatch tool whose target does (`dispatch_targets`) -> Deny, in every mode.
       Built-in names are the CLI's own closed set (`ExitPlanMode` would read as a `mode`
       act).
    3a. a tool of a server the chat left out (`dropped_servers`) -> Deny.
    3b. an external MCP tool in a mode outside `ATTENDED_MODES` (or none) or in an unattended
       chat, unless `external_unattended` lists it -> Deny. The name barrier above is defense
       in depth; this rule does not depend on any vocabulary.
    4. READ_TOOLS or WRITE_TOOLS on an odd Windows path form (`odd_form`), a login file,
       inside the personal home, or (Grep, Glob) on a folder holding either -> Deny. Each
       path is compared as written and as resolved.
    5. WRITE_TOOLS into `protected_paths`, or into the QMX home outside `writable_paths`
       -> Deny.
    6. SHELL_TOOLS whose command names a login fragment, a credential-store reader, a
       keyring name, a broker host, a protected or secret path, the personal home, a
       drive-relative word, or sweeps a drive root or user home -> Deny. Relative words are
       also resolved against the targets of `cd` and folder options, and the home after a
       `cd`.
    7. WebFetch to a broker host -> Deny.
    8. name in `mandatory_asks` -> Ask.
    9. else Pass.
    """
    if agent_id and tool_name.casefold() == DELEGATE_TOOL:
        return _deny("a sub-agent cannot start a helper chat (mcp__qmx__delegate)")
    if tool_name in rules.proposal_tools:
        return Ask("an order proposal always asks you")
    if tool_name.startswith("mcp__"):
        bare = tool_name.removeprefix("mcp__").partition("__")[2]
        act = name_money_act(tool_name) or name_money_act(bare)
        if act is not None:
            return _deny(f"agents cannot place, change or cancel orders ({tool_name} is {act})")
    server = mcp_server(tool_name)
    if server is not None and server in rules.dropped_servers:
        return _deny(f"the MCP server {server} was left out of this chat ({tool_name})")
    if server is not None and _external_unattended(tool_name, server, rules, permission_mode):
        return _deny(
            "agents cannot call an external MCP tool in an unattended chat unless [claude] "
            f"external_tools_unattended lists it ({tool_name})"
        )
    field = rules.dispatch_targets.get(tool_name)
    target = tool_input.get(field) if field else None
    if isinstance(target, str) and (act := name_money_act(target)) is not None:
        short = tool_name.removeprefix("mcp__").split("__")[-1]
        return _deny(
            f"agents cannot place, change or cancel orders ({short} target {target} is {act})"
        )
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
    """Adapter from `gate` to the SDK hook output shape. Reads `cwd`, `agent_id` and
    `permission_mode` from the hook input; a missing mode counts as unattended. Any exception
    inside `gate` returns deny (fail closed). A callback past its `HookMatcher.timeout` blocks
    the call (hooks reference); check S38 proves it here. The callback does no I/O and awaits
    nothing."""

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
                permission_mode=data.get("permission_mode"),
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


NON_BROKER_REFS: Final[frozenset[str]] = frozenset({"qmx/chatgpt", "qmx/control-token"})
"""Fixed entries known not to be broker credentials. Provider `credential_ref`s from
settings.toml [providers] are added at run time."""


# --- posture ---
#
# Names and reachability only. No function here reads, prints, logs or stores a secret value:
# the inventory lists entry names, and the probe decides reachability from where an entry or a
# file lives and from file access rights. Whatever would need a real read is "not measured".


class MoneyPosture(StrEnum):
    STRUCTURAL = "structural"
    """Every broker credential QMX knows of has a stored S27 proof that it cannot trade."""
    SPEED_BUMP = "speed_bump"
    """Anything else, including anything unknown, unmeasured or unreachable."""


UNLISTED: Final = "qmx/? (the keyring could not be listed)"
"""Stands in the inventory for entries nobody could list. It never has a scope proof, so the
posture stays SPEED_BUMP."""

ERROR_NOT_FOUND: Final = 1168


def _windows_store_names() -> list[str]:
    """Target names of the current user's Credential Manager entries, through
    `CredEnumerateW`. Only `TargetName` is read from each entry; the blob is never touched."""
    import ctypes  # noqa: PLC0415
    from ctypes import wintypes  # noqa: PLC0415

    class Credential(ctypes.Structure):
        _fields_ = (
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.c_void_p),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        )

    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    count = wintypes.DWORD()
    found = ctypes.POINTER(ctypes.POINTER(Credential))()
    if not advapi.CredEnumerateW(None, 0, ctypes.byref(count), ctypes.byref(found)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return []
        raise OSError(error, "CredEnumerateW failed")
    try:
        return [str(found[index].contents.TargetName) for index in range(count.value)]
    finally:
        advapi.CredFree(found)


def _linux_store_names() -> list[str]:
    """The `service` attribute of each Secret Service item. Attributes are readable while the
    collection is locked; no secret is requested."""
    import secretstorage  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

    connection = secretstorage.dbus_init()
    try:
        collection = secretstorage.get_default_collection(connection)
        return [
            str(item.get_attributes().get("service", "")) for item in collection.get_all_items()
        ]
    finally:
        connection.close()


def store_names(platform: str = sys.platform) -> frozenset[str] | None:
    """Every `qmx/*` entry name in this user's OS keyring, casefolded, or None when the store
    cannot be listed (macOS, where listing would prompt, or an error). keyring's Windows
    backend may store `<user>@<service>`, so that prefix is dropped."""
    try:
        if platform == "win32":
            raw = _windows_store_names()
        elif platform.startswith("linux"):
            raw = _linux_store_names()
        else:
            return None
    except Exception:
        return None
    names = (name.rpartition("@")[2].casefold() for name in raw)
    return frozenset(name for name in names if name.startswith("qmx/"))


def keyring_inventory(
    configured: Iterable[str], listed: frozenset[str] | None = None
) -> frozenset[str]:
    """Every `qmx/*` entry this PC holds, by name only, plus every configured name (settings.toml
    references). `listed` is `store_names()`; None (macOS, or a store that could not be listed)
    adds `UNLISTED`, so an entry nobody listed still keeps the posture SPEED_BUMP."""
    names = {name.casefold() for name in configured}
    return frozenset(names | (listed if listed is not None else {UNLISTED}))


def money_posture(
    inventory: frozenset[str], non_broker: frozenset[str], scope_proofs: Mapping[str, bool]
) -> MoneyPosture:
    """Pure, fails closed. STRUCTURAL only when each entry outside `non_broker` has
    `scope_proofs[ref] is True`. Reachability plays no part."""
    if unproven(inventory, non_broker, scope_proofs):
        return MoneyPosture.SPEED_BUMP
    return MoneyPosture.STRUCTURAL


def unproven(
    inventory: frozenset[str], non_broker: frozenset[str], scope_proofs: Mapping[str, bool]
) -> tuple[str, ...]:
    """The entries that count as broker credentials and lack a proof, sorted."""
    known = {name.casefold() for name in non_broker}
    return tuple(
        sorted(
            name
            for name in inventory
            if name.casefold() not in known and scope_proofs.get(name.casefold()) is not True
        )
    )


SCOPE_PROOFS_DIR: Final = "scope-proofs"


def load_scope_proofs(state_dir: Path) -> dict[str, bool]:
    """`<state>/scope-proofs/*.json`, one per credential, written by the operator's S27 run:
    `{"credential": "qmx/<name>", "refused_for_scope": bool, ...}`. A file that does not parse
    proves nothing."""
    proofs: dict[str, bool] = {}
    for path in sorted((state_dir / SCOPE_PROOFS_DIR).glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            credential, refused = document["credential"], document["refused_for_scope"]
        except OSError, ValueError, KeyError, TypeError:
            continue
        if isinstance(credential, str) and isinstance(refused, bool):
            proofs[credential.casefold()] = proofs.get(credential.casefold(), True) and refused
    return proofs


def proof_path(state_dir: Path, credential: str) -> Path:
    slug = re.sub(r"[^a-z0-9._-]+", "-", credential.casefold().removeprefix("qmx/"))
    return state_dir / SCOPE_PROOFS_DIR / f"{slug}.json"


def save_scope_proof(
    state_dir: Path, credential: str, *, refused_for_scope: bool, **facts: str | None
) -> Path:
    """One S27 result per credential. `facts` are plain words and ids, never a secret."""
    path = proof_path(state_dir, credential)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "credential": credential.casefold(),
        "refused_for_scope": refused_for_scope,
        "at": datetime.now(UTC).isoformat(),
        **facts,
    }
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return path


type ExposureKind = Literal["keyring_entry", "read_path", "write_path", "loopback"]


@dataclass(frozen=True)
class ExposureTarget:
    kind: ExposureKind
    value: str
    """A `qmx/*` keyring name, a native path, or `127.0.0.1:<port>`."""


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

    def readable(self) -> tuple[str, ...]:
        """What agent Bash can read or reach, in the probe's order."""
        return tuple(
            finding.target.value
            for finding in self.findings
            if finding.reachable and finding.target.kind != "write_path"
        )

    def document(self) -> dict[str, Any]:
        return {
            "at": self.at.isoformat(),
            "cli_version": self.cli_version,
            "findings": [
                {
                    "kind": finding.target.kind,
                    "target": finding.target.value,
                    "reachable": finding.reachable,
                    "detail": finding.detail,
                }
                for finding in self.findings
            ],
        }

    @classmethod
    def parse(cls, document: Mapping[str, Any]) -> ExposureReport:
        return cls(
            at=datetime.fromisoformat(document["at"]),
            cli_version=str(document["cli_version"]),
            findings=tuple(
                ExposureFinding(
                    ExposureTarget(_kind(row["kind"]), str(row["target"])),
                    row["reachable"] if isinstance(row["reachable"], bool) else None,
                    str(row["detail"]),
                )
                for row in document["findings"]
            ),
        )


def _kind(value: object) -> ExposureKind:
    if value in ("keyring_entry", "read_path", "write_path", "loopback"):
        return cast("ExposureKind", value)
    raise ValueError(value)


def exposure_targets(
    home_root: Path,
    keyring_names: Iterable[str],
    control_port: int | None,
    secret_paths: Iterable[Path],
    personal_home: Path,
) -> tuple[ExposureTarget, ...]:
    """Pure. Every inventoried `qmx/*` entry; the QMX home's settings.toml, control.db and
    portfolio.db for read and the QMX home for write; each secret path (read rights only); his
    `~/.claude` for read and write rights; the qmx-control port without a bearer."""
    targets = [
        ExposureTarget("keyring_entry", name) for name in sorted(keyring_names) if name != UNLISTED
    ]
    targets += [
        ExposureTarget("read_path", str(home_root / name))
        for name in ("settings.toml", "control.db", "portfolio.db")
    ]
    targets += [ExposureTarget("read_path", str(path)) for path in secret_paths]
    targets += [
        ExposureTarget("read_path", str(personal_home)),
        ExposureTarget("write_path", str(home_root)),
        ExposureTarget("write_path", str(personal_home)),
    ]
    if control_port is not None:
        targets.append(ExposureTarget("loopback", f"127.0.0.1:{control_port}"))
    return tuple(dict.fromkeys(targets))


KEYRING_READABLE: Final = (
    "agent Bash can read it: Windows lets any process of your user read Credential Manager "
    "entries, and the gate only blocks commands that name it"
)
NOT_MEASURED_KEYRING: Final = (
    "not measured: only reading the value would tell, and the probe never reads one"
)


def measure(
    targets: Iterable[ExposureTarget],
    *,
    listed: frozenset[str] | None,
    platform: str = sys.platform,
) -> tuple[ExposureFinding, ...]:
    """What a process with this environment can reach, decided without reading a secret.
    Keyring: whether the entry is in the store this process lists, and on Windows that any
    process of the user can read it; elsewhere not measured. Paths: `os.access` only, never
    opened. Loopback: one request with no bearer."""
    findings: list[ExposureFinding] = []
    for target in targets:
        match target.kind:
            case "keyring_entry":
                finding = _keyring_finding(target, listed, platform)
            case "read_path" | "write_path":
                finding = _path_finding(target)
            case "loopback":
                finding = _loopback_finding(target)
        findings.append(finding)
    return tuple(findings)


def _keyring_finding(
    target: ExposureTarget, listed: frozenset[str] | None, platform: str
) -> ExposureFinding:
    if listed is None:
        return ExposureFinding(target, None, NOT_MEASURED_KEYRING)
    if target.value.casefold() not in listed:
        return ExposureFinding(target, False, "not in the credential store")
    if platform == "win32":
        return ExposureFinding(target, True, KEYRING_READABLE)
    return ExposureFinding(target, None, NOT_MEASURED_KEYRING)


def _path_finding(target: ExposureTarget) -> ExposureFinding:
    write = target.kind == "write_path"
    if not os.path.lexists(target.value):
        return ExposureFinding(target, False, "absent")
    if os.access(target.value, os.W_OK if write else os.R_OK):
        verb = "write into" if write else "read"
        return ExposureFinding(
            target, True, f"agent Bash can {verb} it; the gate blocks only the file tools"
        )
    return ExposureFinding(target, False, "your OS user has no access right to it")


def _loopback_finding(target: ExposureTarget) -> ExposureFinding:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://{target.value}/api/usage", timeout=3) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except OSError as error:
        return ExposureFinding(target, False, f"nothing answered ({type(error).__name__})")
    if status in (401, 403):
        return ExposureFinding(target, False, f"refused without a bearer ({status})")
    return ExposureFinding(target, True, f"answered without a bearer ({status})")


def guard_opens(targets: Iterable[ExposureTarget]) -> None:
    """Installs an audit hook that fails any `open` of a target path or a login file in this
    process. The probe child runs under it, so a change that opened a secret path would fail
    instead of reading it."""
    fold = str.casefold if sys.platform in ("win32", "darwin") else str
    guarded = {
        fold(os.path.abspath(target.value))
        for target in targets
        if target.kind in ("read_path", "write_path")
    }

    def hook(event: str, args: tuple[object, ...]) -> None:
        if event != "open" or not isinstance(args[0], str | bytes | os.PathLike):
            return
        path = fold(os.path.abspath(os.fsdecode(cast("str", args[0]))))
        if path in guarded or os.path.basename(path).casefold() == LOGIN_NAME:
            raise PermissionError(f"the exposure probe never opens {path}")

    sys.addaudithook(hook)


def probe_child() -> None:
    """The probe subprocess: targets as JSON on stdin, findings as JSON on stdout."""
    rows = json.loads(sys.stdin.read())
    targets = [ExposureTarget(_kind(row["kind"]), str(row["value"])) for row in rows]
    guard_opens(targets)
    findings = measure(targets, listed=store_names())
    print(json.dumps([[f.target.kind, f.target.value, f.reachable, f.detail] for f in findings]))


PROBE_TIMEOUT_S: Final = 30.0


async def run_exposure_probe(
    env: Mapping[str, str], targets: tuple[ExposureTarget, ...], *, cli_version: str
) -> ExposureReport:
    """Informational, inside-out: what an agent's Bash could reach. Runs `python -I` as a
    subprocess with exactly `env` under the agent's OS user. A probe that cannot run reports
    every target as not measured."""
    payload = json.dumps([{"kind": t.kind, "value": t.value} for t in targets]).encode()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-I",
        "-c",
        "from qma.harness.money import probe_child; probe_child()",
        env=dict(env),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        out, _ = await asyncio.wait_for(process.communicate(payload), PROBE_TIMEOUT_S)
        rows = json.loads(out)
        findings = tuple(
            ExposureFinding(
                ExposureTarget(_kind(kind), str(value)),
                reachable if isinstance(reachable, bool) else None,
                str(detail),
            )
            for kind, value, reachable, detail in rows
        )
        if [finding.target for finding in findings] != list(targets):
            raise ValueError("the probe answered for other targets")
    except (TimeoutError, ValueError, TypeError) as error:
        if process.returncode is None:
            process.kill()
            await process.wait()
        reason = f"not measured: the probe did not finish ({type(error).__name__})"
        findings = tuple(ExposureFinding(target, None, reason) for target in targets)
    return ExposureReport(datetime.now(UTC), cli_version, findings)


EXPOSURE_FILE: Final = "exposure.json"


def save_exposure(state_dir: Path, report: ExposureReport) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    draft = state_dir / f"{EXPOSURE_FILE}.tmp"
    draft.write_text(json.dumps(report.document()), encoding="utf-8")
    draft.replace(state_dir / EXPOSURE_FILE)


def load_exposure(state_dir: Path) -> ExposureReport | None:
    try:
        return ExposureReport.parse(
            json.loads((state_dir / EXPOSURE_FILE).read_text(encoding="utf-8"))
        )
    except OSError, ValueError, KeyError, TypeError:
        return None
