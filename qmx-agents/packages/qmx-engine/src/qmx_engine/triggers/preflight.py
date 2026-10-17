"""Preflight before a fire starts a run (SOLUTION-DESIGN 4.2 step 4, AD-10, AD-17).

Roles must resolve to a live candidate the harness has a profile for, every credential a node
names must be a configured `qmx/*` reference (by name; nothing is read), and every skill an
`agent` node names must ship in the QMX plugin. The delivery target is one of the typed
`inbox | digest | silent` channels, which always exist.

A failure blocks the fire with no run. A role or skill fault is the workflow's own configuration,
which costs a digest line; only a missing key is a provider failure, which raises an inbox item.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

from qmx_control.service import ControlService

from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.signature import signature
from qmx_engine.roles import order, resolve

type Cause = Literal["config", "provider"]

PLUGIN_SKILLS: Final = Path(__file__).resolve().parents[5] / "plugin" / "skills"
"""`qmx-agents/plugin/skills`, the skills QMX ships."""


@dataclass(frozen=True, slots=True)
class Blocked:
    cause: Cause
    code: str
    message: str

    @property
    def signature(self) -> str:
        return signature(self.code, self.message)


def shipped_skills(folder: Path = PLUGIN_SKILLS) -> frozenset[str]:
    if not folder.is_dir():
        return frozenset()
    return frozenset(p.name for p in folder.iterdir() if (p / "SKILL.md").is_file())


def configured_refs(control: ControlService) -> frozenset[str]:
    """Every `qmx/*` name in `[providers]` and `[mcp_servers]`, casefolded. Names only."""
    found: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str) and value.casefold().startswith("qmx/"):
            found.add(value.casefold())
        elif isinstance(value, Mapping):
            for item in cast(Mapping[str, object], value).values():
                walk(item)
        elif isinstance(value, list):
            for item in cast(list[object], value):
                walk(item)

    for section in ("providers", "mcp_servers"):
        walk(control.settings_get(section))
    return frozenset(found)


def preflight(
    workflow: Workflow,
    settings: Mapping[str, object],
    *,
    profiles: Collection[str] | None,
    credentials: Collection[str] | None,
    skills: Collection[str] | None,
) -> Blocked | None:
    """The first fault, or None. A `None` inventory is not checked."""
    for node in workflow.nodes:
        if node.disabled:
            continue
        if node.role is not None:
            candidates = order(settings, node.role, "live")
            if not candidates:
                return Blocked(
                    "config", "role_missing", f"{node.name}: role {node.role} has no candidates"
                )
            if profiles is not None:
                found = resolve(candidates, profiles, None)
                if isinstance(found, str):
                    return Blocked("config", "role_unresolved", f"{node.name}: {found}")
        if credentials is not None:
            for name, ref in sorted(node.credentials.items()):
                if ref.casefold() not in credentials:
                    message = f"{node.name}: credential {name} names {ref}, which is not configured"
                    return Blocked("provider", "credential_missing", message)
        named = node.parameters.get("skills")
        if skills is not None and isinstance(named, list):
            for skill in named:  # pyright: ignore[reportUnknownVariableType]
                if str(skill) not in skills:  # pyright: ignore[reportUnknownArgumentType]
                    message = f"{node.name}: skill {skill} is not installed"
                    return Blocked("config", "skill_missing", message)
    return None
