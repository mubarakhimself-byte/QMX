"""`qmx app check` for a pack's plugin view (AD-19, AD-55; H43).

The doctor and the publish gate read this. It refuses a view that would not load as a Claude
plugin, lists every `!` shell line the pack would run, refuses a `hooks/` folder or a
`.mcp.json`, and refuses a pack whose server serves tools other than the rows `app.toml`
declares.

One name rule comes from the catalog (AD-61): a declared row's wire name
`mcp__qmx__<toolset>_<op>` must fit `MAX_TOOL_NAME`.

A `!` line is listed, not refused: it runs under the guard like any other shell call, so the
operator sees it before he publishes. A hook and an MCP server are refused outright, because
neither passes through the guard and a pack's tools are catalog rows on the chat's one `qmx`
server.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qmx_apps.errors import Document

PLUGIN_JSON: Final = ".claude-plugin/plugin.json"
CONTENT: Final = ("skills", "agents", "commands")
REFUSED: Final = frozenset({"hooks", ".mcp.json"})
"""What a pack may ship and a view may not: neither reaches the guard (AD-55)."""
NAME: Final = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_-]*\Z")
"""A plugin name is the `plugin:skill` prefix the CLI reports and the folder the pack set names."""
SHELL: Final = re.compile(r"!`([^`\n]*)`")
MAX_TOOL_NAME: Final = 64
"""The bound on `mcp__qmx__<toolset>_<op>`; the catalog's `MAX_TOOL_NAME` and the same number."""
CORE_SERVER: Final = "qmx"


@dataclass(frozen=True, slots=True)
class PackCheck:
    """One pack view's check: what it would run, what it would load, and every refusal."""

    folder: Path
    refusals: tuple[str, ...] = ()
    shell_lines: tuple[str, ...] = ()
    """Every `!` line the pack would run, as `<file>: <command>`, so a publish card lists them."""
    tools: tuple[str, ...] = ()
    """The declared rows, when the pack's server serves exactly them."""
    name: str = ""
    skills: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.refusals

    def document(self) -> Document:
        return {
            "folder": self.folder.as_posix(),
            "ok": self.ok,
            "name": self.name,
            "refusals": list(self.refusals),
            "shell_lines": list(self.shell_lines),
            "tools": list(self.tools),
            "skills": list(self.skills),
            "agents": list(self.agents),
            "commands": list(self.commands),
        }


def wire_toolset(toolset: str) -> str:
    """The toolset part of a wire name. The catalog names a pack's toolset `app:<id>`; a wire name
    holds letters, digits, underscores and hyphens only, so `:` becomes `_`."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", toolset)


def wire_name(toolset: str, op: str) -> str:
    """`mcp__qmx__<toolset>_<op>`, the name the CLI gives the tool."""
    return f"mcp__{CORE_SERVER}__{wire_toolset(toolset)}_{op}"


def _manifest(folder: Path, refusals: list[str]) -> str:
    path = folder / PLUGIN_JSON
    try:
        found = cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
    except OSError:
        refusals.append(f"not_a_plugin: {folder} has no {PLUGIN_JSON}")
        return ""
    except ValueError as error:
        refusals.append(f"not_a_plugin: {PLUGIN_JSON} does not parse ({error})")
        return ""
    name = found.get("name")
    if not isinstance(name, str) or not NAME.match(name):
        refusals.append(
            f"not_a_plugin: {PLUGIN_JSON} names no plugin a chat can load ({name!r} is not a "
            "word of letters, digits, hyphens and underscores)"
        )
        return ""
    return name


def _stray(folder: Path) -> list[str]:
    """Anything at the view's top level that is not the plugin manifest or a content folder. A
    refused path is named by its own refusal, not twice."""
    return sorted(
        path.name
        for path in folder.iterdir()
        if path.name not in (".claude-plugin", *CONTENT) and path.name not in REFUSED
    )


def _refused_paths(folder: Path) -> list[str]:
    return sorted(
        path.relative_to(folder).as_posix()
        for path in folder.rglob("*")
        if path.is_file() and path.relative_to(folder).parts[0] in REFUSED
    )


def _shell_lines(folder: Path) -> list[str]:
    found: list[str] = []
    for path in sorted(folder.rglob("*.md")):
        for match in SHELL.finditer(path.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{path.relative_to(folder).as_posix()}: {match.group(1).strip()}")
    return found


def _skills(folder: Path) -> tuple[str, ...]:
    return tuple(sorted(path.parent.name for path in (folder / "skills").glob("*/SKILL.md")))


def _stems(folder: Path, part: str) -> tuple[str, ...]:
    return tuple(sorted(path.stem for path in (folder / part).glob("*.md")))


def _names(rows: Sequence[str], toolset: str) -> list[str]:
    """Why a declared row's wire name is refused: a name the CLI cannot carry."""
    problems: list[str] = []
    for op in rows:
        name = wire_name(toolset, op)
        if len(name) > MAX_TOOL_NAME:
            problems.append(
                f"wire_name: {name} is longer than {MAX_TOOL_NAME} characters ({len(name)})"
            )
    return problems


def check(
    folder: Path,
    *,
    declared: Sequence[str] = (),
    served: Sequence[str] | None = None,
    toolset: str = CORE_SERVER,
) -> PackCheck:
    """Check one materialised pack view. `declared` is the rows `app.toml [operations]` names
    and `served` what the pack's server answers; the two must be the same set, which is what
    stops a pack serving a tool it never declared (AD-61). `toolset` names the server's toolset,
    `qmx` for the core one and `app:<id>` for an app's pack."""
    refusals: list[str] = []
    name = _manifest(folder, refusals)
    refused = _refused_paths(folder)
    if refused:
        refusals.append(
            f"hook_or_server: a pack ships no hooks and no .mcp.json; remove {', '.join(refused)}"
        )
    stray = _stray(folder)
    if stray:
        refusals.append(
            "not_a_plugin: a plugin view holds .claude-plugin, skills, agents and commands only; "
            f"found {', '.join(stray)}"
        )
    rows = list(declared)
    refusals.extend(_names(rows, toolset))
    answered = None if served is None else list(served)
    if answered is None and rows:
        refusals.append(
            f"tools_not_served: the pack declares {len(rows)} rows and no server reported its tools"
        )
    elif answered is not None and sorted(rows) != sorted(answered):
        missing = sorted(set(rows) - set(answered))
        extra = sorted(set(answered) - set(rows))
        refusals.append(
            "tools_differ: the server's tools differ from the declared rows "
            f"(declared and not served: {', '.join(missing) or 'none'}; served and not "
            f"declared: {', '.join(extra) or 'none'})"
        )
    return PackCheck(
        folder=folder,
        refusals=tuple(refusals),
        shell_lines=tuple(_shell_lines(folder)),
        tools=tuple(sorted(rows)),
        name=name,
        skills=_skills(folder),
        agents=_stems(folder, "agents"),
        commands=_stems(folder, "commands"),
    )
