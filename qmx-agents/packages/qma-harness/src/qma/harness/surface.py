"""What a chat gets, decided in one place (engine AD-62).

`build` is the one function that decides, for every chat kind, the QMX toolsets, the CLI's
built-in tools, the native sub-agents, the skills filter, the system text by slot, the observed
hook events, the env quirks and the surface digest. `chat.py` calls it at every launch, the
engine's agent node reaches it through the chat's declaration, and a Child is cut to its
parent's surface, so a helper is never wider than the chat that started it.

Toolsets are the home preset for a chat that declares none, the node's declared `toolsets` for
an engine agent, and the parent's for a helper. Then they are cut to what the host serves, to
the parent's surface, and less what the kind denies. Every kind loses the CLI's own scheduling
and remote tools and its `schedule` and `loop` skills, because every schedule is an engine
trigger (H56). Background and Child chats also lose the worktree tools, since their folder is
fixed, and a Child loses the Agent tool.

Slots go in cache order into the `append` text. Each has a size budget (`[agents]
slot_budgets`, context hygiene, not usage). A slot over budget keeps its head and a pointer, and
its full text becomes a skill in the chat's own `qmx-slots` plugin, so nothing is cut silently.
Per-turn state never enters the system text: `render_state` builds the `<qmx_state>` block a
user message carries.

The digest is sha256 over the tool names with a hash of each description and schema, the
built-ins, the skills, the plugins, the system-prompt options and the exact `append` text. It is
recorded per launch on the chat record and on every agent span, so "what did the model see"
has one answer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, Protocol, cast

from qmx_control.catalog import CORE_TOOLSETS

from qma.harness.launch import (
    CHAT_HOOK_EVENTS,
    CHILD_DENIED,
    COMPACT_PCT_ENV,
    PROMPT_OPTIONS,
    Background,
    ChatKind,
    Child,
    Home,
    Interactive,
    SubAgent,
)

if TYPE_CHECKING:
    from qma.harness.home import QmxHome
    from qma.harness.launch import ChatConfig
    from qma.harness.tools import ToolDef

type SlotName = Literal[
    "rules",
    "persona",
    "methodology",
    "pack_layers",
    "skills_index",
    "memory_snapshot",
    "workspace",
    "brief",
]
SLOT_ORDER: Final[tuple[SlotName, ...]] = (
    "rules",
    "persona",
    "methodology",
    "pack_layers",
    "skills_index",
    "memory_snapshot",
    "workspace",
    "brief",
)
"""Cache order: what changes least comes first. `workspace` is the chat folder's CLAUDE.md and
AGENTS.md, and `brief` is the caller's own text, such as an engine node's brief and schema."""

DEFAULT_BUDGETS: Final[Mapping[SlotName, int | None]] = MappingProxyType(
    {
        "rules": 2_000,
        "persona": 4_000,
        "methodology": 8_000,
        "pack_layers": 600,
        "skills_index": 120,
        "memory_snapshot": None,
        "workspace": None,
        "brief": None,
    }
)
"""Claude's defaults (SOLUTION-DESIGN 28.2), in characters. `pack_layers` is per pack, the
toolset listing counting as one, and `skills_index` per skill. None has no budget: the
workspace files load whole as in vanilla Claude Code, the brief is the caller's, and the memory
snapshot is bounded where it is built (AD-18)."""

CLI_BUILTINS: Final[tuple[str, ...]] = (
    "Task",
    "AskUserQuestion",
    "Bash",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Edit",
    "EnterPlanMode",
    "EnterWorktree",
    "ExitPlanMode",
    "ExitWorktree",
    "Glob",
    "Grep",
    "ListAgents",
    "NotebookEdit",
    "Read",
    "RemoteTrigger",
    "ReportFindings",
    "ScheduleWakeup",
    "SendMessage",
    "Skill",
    "TaskCreate",
    "TaskGet",
    "TaskList",
    "TaskStop",
    "TaskUpdate",
    "ToolSearch",
    "WebFetch",
    "WebSearch",
    "Workflow",
    "Write",
    *(("PowerShell",) if os.name == "nt" else ()),
)
"""The `claude_code` tools preset of the pinned CLI 2.1.299 under QMX's env (its `init` in
`tests/fixtures/helper_turn.jsonl`), plus PowerShell, which `CONSTANT_ENV` turns on for
Windows. A chat gets an explicit list, so a tool a later CLI adds joins only through this list."""

CLI_SKILLS: Final[tuple[str, ...]] = (
    "deep-research",
    "dataviz",
    "update-config",
    "verify",
    "debug",
    "code-review",
    "simplify",
    "batch",
    "fewer-permission-prompts",
    "doctor",
    "loop",
    "schedule",
    "claude-api",
    "workflow-authoring",
    "run",
    "run-skill-generator",
    "plugin-authoring",
)
"""The skills the pinned CLI 2.1.299 bundles (the same `init`)."""

SCHEDULING: Final = frozenset(
    {"CronCreate", "CronDelete", "CronList", "ScheduleWakeup", "RemoteTrigger", "Workflow"}
)
SCHEDULING_SKILLS: Final = frozenset({"schedule", "loop"})
WORKTREE: Final = frozenset({"EnterWorktree", "ExitWorktree"})

SLOTS_PLUGIN: Final = "qmx-slots"
"""The chat's own plugin that holds its spilled slots as skills."""

STATE_TAG: Final = "qmx_state"


@dataclass(frozen=True)
class Declaration:
    """What the chat's creator asked for. None is the kind's preset."""

    toolsets: tuple[str, ...] | None = None
    builtins: tuple[str, ...] | None = None
    """`()` with no declared toolsets is a chat with no tool at all."""
    skills: tuple[str, ...] | None = None
    agents: Mapping[str, SubAgent] = field(default_factory=dict[str, SubAgent])
    brief: str | None = None
    observed: bool = False
    """Whether hooks or a named sink observe the chat after the guard."""
    compact_at: float | None = None


def declaration(config: ChatConfig) -> Declaration:
    return Declaration(
        toolsets=config.toolsets,
        builtins=config.tools,
        skills=config.skills,
        agents=config.agents,
        brief=config.append_system_prompt,
        observed=config.hooks is not None or config.hook_sink is not None,
        compact_at=config.compact_at,
    )


class SlotSource(Protocol):
    """Where slot texts come from. `HomeSlots` reads files until the Library holds `persona`,
    `methodology` and skill items (LIB1)."""

    def rules(self) -> str: ...
    def persona(self) -> str: ...
    def methodology(self, home: Home) -> str: ...
    def pack_layer(self, pack: str) -> str: ...
    def memory_snapshot(self, home: Home) -> str: ...
    def workspace(self, workspace: Path) -> str: ...
    def skills(self) -> Mapping[str, str]:
        """QMX's own skills by `plugin:skill` name, each with its one-line description."""
        ...


def _contents(paths: Sequence[Path]) -> str:
    return "\n\n".join(
        f"Contents of {path.as_posix()}:\n\n{path.read_text(encoding='utf-8').strip()}"
        for path in paths
        if path.is_file()
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


FRONT_MATTER: Final = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)


def _description(skill_file: Path) -> str:
    found = FRONT_MATTER.match(skill_file.read_text(encoding="utf-8").replace("\r\n", "\n"))
    for line in (found.group(1) if found else "").splitlines():
        if line.startswith("description:"):
            return line.removeprefix("description:").strip()
    return ""


@dataclass(frozen=True)
class HomeSlots:
    """The rules come from the shipped plugin's `QMX.md`. The slots he edits live under
    `<qmx_home>/slots/`: `persona.md`, `methodology/<home kind>.md` and `packs/<pack>.md`,
    because the plugin folder is locked by its hash. A missing file is an empty slot. No memory
    snapshot exists before the memory packet."""

    home: QmxHome

    @property
    def folder(self) -> Path:
        return self.home.root / "slots"

    def rules(self) -> str:
        return _contents([self.home.plugin_dir / "QMX.md"])

    def persona(self) -> str:
        return _read(self.folder / "persona.md")

    def methodology(self, home: Home) -> str:
        return _read(self.folder / "methodology" / f"{home.kind}.md")

    def pack_layer(self, pack: str) -> str:
        return _read(self.folder / "packs" / f"{pack}.md")

    def memory_snapshot(self, home: Home) -> str:
        del home
        return ""

    def workspace(self, workspace: Path) -> str:
        return _contents([workspace / "CLAUDE.md", workspace / "AGENTS.md"])

    def skills(self) -> Mapping[str, str]:
        found = sorted((self.home.plugin_dir / "skills").glob("*/SKILL.md"))
        return {f"qmx:{path.parent.name}": _description(path) for path in found}


@dataclass(frozen=True)
class Supply:
    """What the host offers a launch: the QMX tools it serves now, the slot texts, the
    `[agents]` settings, the plugin folders every chat loads, and the folder a spilled slot is
    written to."""

    tools: tuple[ToolDef, ...]
    slots: SlotSource
    settings: Mapping[str, object]
    plugins: tuple[Path, ...]
    spill_dir: Path


@dataclass(frozen=True)
class Slot:
    name: SlotName
    text: str
    size: int
    """The full text's length, before any spill."""
    spilled: bool = False


@dataclass(frozen=True)
class Surface:
    toolsets: tuple[str, ...]
    tools: tuple[str, ...]
    """The QMX tools on the surface, by full name."""
    builtins: tuple[str, ...]
    agents: Mapping[str, SubAgent]
    skills: tuple[str, ...]
    plugins: tuple[Path, ...]
    slots: tuple[Slot, ...]
    spills: Mapping[str, str]
    """Each spilled slot's skill folder name and its `SKILL.md` text."""
    hooks: tuple[str, ...]
    env: Mapping[str, str]
    digest: str

    @property
    def append(self) -> str:
        return "\n\n".join(slot.text for slot in self.slots if slot.text)

    def manifest(self) -> dict[str, object]:
        """What the chat's launch folder records as `surface.json`."""
        return {
            "digest": self.digest,
            "toolsets": list(self.toolsets),
            "tools": list(self.tools),
            "builtins": list(self.builtins),
            "agents": sorted(self.agents),
            "skills": list(self.skills),
            "plugins": [path.as_posix() for path in self.plugins],
            "slots": {
                slot.name: {"chars": len(slot.text), "full": slot.size, "spilled": slot.spilled}
                for slot in self.slots
            },
            "hooks": list(self.hooks),
            "env": dict(self.env),
        }


def denied_builtins(kind: ChatKind) -> frozenset[str]:
    match kind:
        case Interactive():
            return SCHEDULING
        case Background():
            return SCHEDULING | WORKTREE
        case Child():
            return SCHEDULING | WORKTREE | frozenset(CHILD_DENIED)


def denied_toolsets(kind: ChatKind) -> frozenset[str]:
    """A Child never starts a helper of its own."""
    return frozenset({"delegate"}) if isinstance(kind, Child) else frozenset()


DYNAMIC_TOOLSETS: Final = ("app:", "mcp:", "run:")
"""Toolsets named per mini app, vetted external server and run (AD-61)."""


def known_toolset(name: str) -> bool:
    """A core toolset, or a dynamic one with a name after its prefix. Pack toolsets join this
    check when packs exist (PACK)."""
    dynamic = any(name.startswith(p) and len(name) > len(p) for p in DYNAMIC_TOOLSETS)
    return name in CORE_TOOLSETS or dynamic


def _names(value: object) -> tuple[str, ...] | None:
    if isinstance(value, list | tuple):
        return tuple(str(name) for name in value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return None


def _table(value: object) -> Mapping[str, object]:
    return cast("Mapping[str, object]", value) if isinstance(value, Mapping) else {}


def home_preset(home: Home, settings: Mapping[str, object]) -> tuple[str, ...]:
    """`[agents] home_toolsets.<kind>`, else every core toolset (Claude's default: the hub has
    every enabled toolset, and he narrows a home in Settings)."""
    table = _table(settings.get("home_toolsets"))
    found = _names(table.get(home.kind))
    return CORE_TOOLSETS if found is None else found


def budgets(settings: Mapping[str, object]) -> dict[SlotName, int | None]:
    """`[agents] slot_budgets`, each a positive whole number of characters, else the default."""
    written = _table(settings.get("slot_budgets"))
    found = dict(DEFAULT_BUDGETS)
    for name in SLOT_ORDER:
        value = written.get(name)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            found[name] = value
    return found


def _ordered(names: Sequence[str], keep: frozenset[str] | set[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for name in names if name in keep))


def _first_sentence(text: str) -> str:
    head = text.split(". ", 1)[0].strip()
    return head if head.endswith(".") else f"{head}."


def _skill_text(name: SlotName, text: str) -> str:
    body = text.replace("!`", "! `")
    return (
        f"---\nname: {name}\ndescription: The full {name} section of this chat's system text. "
        f"Load it when that section points here.\n---\n\n{body}\n"
    )


def _slot(
    name: SlotName, text: str, budget: int | None, spill_dir: Path
) -> tuple[Slot, str | None]:
    """The slot as it goes into the system text, and its spilled skill text when over budget.
    A `!`-backtick pair in a spilled text is broken up, so a skill load runs no shell line."""
    if budget is None or len(text) <= budget:
        return Slot(name, text, len(text)), None
    path = (spill_dir / name / "SKILL.md").as_posix()
    pointer = (
        f"\n\n[This {name} section is cut here. Its full text is the skill "
        f"{SLOTS_PLUGIN}:{name}; load it with the Skill tool, or Read {path}.]"
    )
    head = text[: max(0, budget - len(pointer))].rstrip()
    return Slot(name, head + pointer, len(text), spilled=True), _skill_text(name, text)


def _tool_hash(tool: ToolDef) -> str:
    text = json.dumps(
        [tool.description, tool.input_schema], sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(text.encode()).hexdigest()


def surface_digest(
    tools: Sequence[ToolDef],
    builtins: Sequence[str],
    skills: Sequence[str],
    plugins: Sequence[Path],
    append: str,
) -> str:
    payload = {
        "tools": sorted([tool.full, _tool_hash(tool)] for tool in tools),
        "builtins": sorted(builtins),
        "skills": sorted(skills),
        "plugins": [path.as_posix() for path in plugins],
        "prompt": dict(PROMPT_OPTIONS),
        "append": append,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode()).hexdigest()


def _toolsets(
    kind: ChatKind,
    home: Home,
    wanted: Declaration,
    supply: Supply,
    parent: Surface | None,
) -> tuple[str, ...]:
    if wanted.toolsets is not None:
        asked = wanted.toolsets
    elif wanted.builtins == ():
        asked = ()
    elif parent is not None:
        asked = parent.toolsets
    else:
        asked = home_preset(home, supply.settings)
    keep = {tool.toolset for tool in supply.tools} - denied_toolsets(kind)
    if parent is not None:
        keep &= set(parent.toolsets)
    return _ordered(asked, keep)


def _builtins(
    kind: ChatKind, wanted: Declaration, skills: bool, parent: Surface | None
) -> tuple[str, ...]:
    asked = CLI_BUILTINS if wanted.builtins is None else wanted.builtins
    if skills and wanted.builtins is not None and "Skill" not in asked:
        asked = (*asked, "Skill")
    keep = set(asked) - denied_builtins(kind)
    if parent is not None:
        keep &= {*parent.builtins, "Skill"} if skills else set(parent.builtins)
    return _ordered(asked, keep)


def _skills(wanted: Declaration, own: Mapping[str, str], parent: Surface | None) -> tuple[str, ...]:
    """A chat that declares its built-ins and no skills gets none."""
    if wanted.skills is not None:
        asked = wanted.skills
    elif wanted.builtins is None:
        asked = (*CLI_SKILLS, *own)
    else:
        asked = ()
    keep = set(asked) - SCHEDULING_SKILLS
    if parent is not None:
        keep &= set(parent.skills)
    return _ordered(asked, keep)


def _texts(
    kind: ChatKind,
    home: Home,
    packs: Sequence[str],
    wanted: Declaration,
    supply: Supply,
    toolsets: Sequence[str],
    skills: Sequence[str],
    own: Mapping[str, str],
    workspace: Path,
) -> dict[SlotName, str]:
    source = supply.slots
    counts = dict.fromkeys(toolsets, 0)
    for tool in supply.tools:
        if tool.toolset in counts:
            counts[tool.toolset] += 1
    listing = "\n".join(f"- {name}: {count} tools" for name, count in counts.items())
    layers = [layer for pack in packs if (layer := source.pack_layer(pack))]
    if listing:
        layers.append(f"QMX toolsets on this chat:\n{listing}")
    index = "\n".join(f"- {name}: {_first_sentence(own[name])}" for name in skills if name in own)
    methodology = source.methodology(home)
    persona = source.persona() if isinstance(kind, Interactive) else ""
    memory = source.memory_snapshot(home)
    return {
        "rules": source.rules(),
        "persona": f"# Persona\n\n{persona}" if persona else "",
        "methodology": f"# Methodology for the {home.kind} home\n\n{methodology}"
        if methodology
        else "",
        "pack_layers": "# Packs and toolsets\n\n" + "\n\n".join(layers) if layers else "",
        "skills_index": f"# QMX skills\n\n{index}" if index else "",
        "memory_snapshot": f"# Memory\n\n{memory}" if memory else "",
        "workspace": source.workspace(workspace),
        "brief": wanted.brief or "",
    }


def build(
    kind: ChatKind,
    home: Home,
    packs: Sequence[str],
    wanted: Declaration,
    supply: Supply,
    *,
    workspace: Path,
    parent: Surface | None = None,
) -> Surface:
    """Everything one launch of a chat gets. Pure but for reading slot texts."""
    own = supply.slots.skills()
    skills = list(_skills(wanted, own, parent))
    builtins = _builtins(kind, wanted, bool(skills), parent)
    toolsets = _toolsets(kind, home, wanted, supply, parent)
    texts = _texts(kind, home, packs, wanted, supply, toolsets, skills, own, workspace)
    limits = budgets(supply.settings)
    per_item = {"pack_layers": len(packs) + 1, "skills_index": max(1, len(skills))}
    slots: list[Slot] = []
    spills: dict[str, str] = {}
    for name in SLOT_ORDER:
        limit = limits[name]
        if limit is not None:
            limit *= per_item.get(name, 1)
        slot, spilled = _slot(name, texts[name], limit, supply.spill_dir)
        slots.append(slot)
        if spilled is not None:
            spills[name] = spilled
    plugins = supply.plugins
    if spills:
        plugins = (*plugins, supply.spill_dir.parent)
        skills += [f"{SLOTS_PLUGIN}:{name}" for name in spills]
        if "Skill" not in builtins and "Skill" not in denied_builtins(kind):
            builtins = (*builtins, "Skill")
    on = [tool for tool in supply.tools if tool.toolset in toolsets]
    allowed = {*builtins, *(tool.full for tool in on)}
    agents = {
        name: SubAgent(
            agent.description,
            agent.prompt,
            None if agent.tools is None else _ordered(agent.tools, allowed),
            agent.model,
        )
        for name, agent in wanted.agents.items()
    }
    append = "\n\n".join(slot.text for slot in slots if slot.text)
    return Surface(
        toolsets=toolsets,
        tools=tuple(tool.full for tool in on),
        builtins=builtins,
        agents=MappingProxyType(agents),
        skills=tuple(skills),
        plugins=plugins,
        slots=tuple(slots),
        spills=MappingProxyType(spills),
        hooks=("PreToolUse", *(CHAT_HOOK_EVENTS.values() if wanted.observed else ())),
        env=MappingProxyType(
            {}
            if wanted.compact_at is None
            else {COMPACT_PCT_ENV: str(round(wanted.compact_at * 100))}
        ),
        digest=surface_digest(on, builtins, skills, plugins, append),
    )


def child_scope(parent: Surface) -> Declaration:
    """What a helper declares so it is never wider than `parent`: its toolsets, built-ins and
    skills, less the skills of the parent's own `qmx-slots` plugin, which the helper lacks."""
    skills = tuple(n for n in parent.skills if not n.startswith(f"{SLOTS_PLUGIN}:"))
    return Declaration(parent.toolsets, parent.builtins, skills)


def surface_files(surface: Surface, launch_dir: Path) -> dict[Path, str]:
    """The files a launch writes beside its settings and system text: `surface.json`, and the
    `qmx-slots` plugin when a slot spilled."""
    files = {launch_dir / "surface.json": json.dumps(surface.manifest(), indent=2) + "\n"}
    if surface.spills:
        root = launch_dir / SLOTS_PLUGIN
        manifest = {
            "name": SLOTS_PLUGIN,
            "version": "0.1.0",
            "description": "This chat's system text sections that were over their budget.",
        }
        files[root / ".claude-plugin" / "plugin.json"] = json.dumps(manifest, indent=2) + "\n"
        for name, text in surface.spills.items():
            files[root / "skills" / name / "SKILL.md"] = text
    return files


def render_state(
    subject: str | None = None,
    layout: str | None = None,
    ticked_runs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> str:
    """The `<qmx_state>` block a user message carries: what is open, how the screen is laid
    out, the runs he ticked, and one-shot change notes. Empty when there is nothing to say."""
    lines = [
        *([f"open subject: {subject}"] if subject else []),
        *([f"layout: {layout}"] if layout else []),
        *([f"ticked runs: {', '.join(ticked_runs)}"] if ticked_runs else []),
        *(f"note: {note}" for note in notes),
    ]
    return f"<{STATE_TAG}>\n" + "\n".join(lines) + f"\n</{STATE_TAG}>" if lines else ""
