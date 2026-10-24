"""Preflight before a fire starts a run (SOLUTION-DESIGN 4.2 step 4, AD-10, AD-17), and the
`market_open` precheck.

Roles must resolve to a live candidate the harness has a profile for, every credential a node
names must be a configured `qmx/*` reference (by name; nothing is read), and every skill an
`agent` node names must ship in the QMX plugin. A `qmx/tool/<name>` key is the script's own: the
script node resolves it from the keyring as it starts and fails `credential_missing` there, so
preflight, which reads no secret, does not hold it against the Settings references. The delivery
target is one of the typed `inbox | digest | silent` channels, which always exist.

A failure blocks the fire with no run. A role or skill fault is the workflow's own configuration,
which costs a digest line; only a missing key is a provider failure, which raises an inbox item.

`market_open` is a precheck a trigger names by that word: the market is shut on Saturdays,
Sundays and every `market.holidays` date, each read in the trigger's IANA zone, and a fire while
it is shut is held until the next open day begins (Claude's default calendar).

A fire whose pinned version is built on a quarantined input (Library AD-22: a `consumed`,
`derived-from` or `uses` path up to an item the operator quarantined) is blocked with
`quarantined_input` and the path, a configuration fault; clearing the mark lets the next fire
start.

A placement is checked against the kinds its host's newest heartbeat names (AD-20, AD-65): a
node whose kind that host's code does not know waits `placement` with `node needs update`, and
the fire is held until a newer heartbeat lists the kind. A placement no heartbeat has named yet
is not checked here.

A placement also has the five preflight states of AD-30 (`available | configured | authorized |
reachable | healthy`), and a node placed on a provider's machine is refused when its role resolves
to a plan row: a plan login stays on the machine he signed in on (AD-28, AD-30), and a provider VM
holds key rows by design. That refusal is a configuration fault, so it costs a digest line.

A node that names `connection: <id>` in its parameters fires only when that connection's newest
reading is `ok` and the node runs on the connection's home machine (AD-67). A missing or unhealthy
reading is `blocked_config` with one item and no model call. Readings arrive in `connections` or
from `connection.<id>.word` rows in `settings`; the scheduler passes them from the heartbeat.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Final, Literal, cast
from zoneinfo import ZoneInfo

from qmx_control.service import ControlService

from qmx_engine.definition.lint import TOOL_KEY
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.ledger.signature import signature
from qmx_engine.ports.library import LibraryPort
from qmx_engine.roles import Candidate, order, resolve

type Cause = Literal["config", "provider"]

PLUGIN_SKILLS: Final = Path(__file__).resolve().parents[5] / "plugin" / "skills"
"""`qmx-agents/plugin/skills`, the skills QMX ships."""
MARKET_OPEN: Final = "market_open"
WEEKEND: Final = (5, 6)
PLACEMENT_STATES: Final = ("available", "configured", "authorized", "reachable", "healthy")
"""DEC-0428's order, ratified in AD-20: a placement is a fact checked in this order, never a
sticker on a node."""
PROVIDER_KINDS: Final = frozenset({"managed_vm", "managed_agent_host", "serverless"})
"""Placements QMX does not own. A plan account never resolves on one of these (AD-28, AD-30)."""
PLAN_PROFILE: Final = "claude"
"""The plan rows' profile name in the model registry."""


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
    kinds: Mapping[str, str] | None = None,
    connections: Mapping[str, str] | None = None,
) -> Blocked | None:
    """The first fault, or None. A `None` inventory is not checked. `kinds` is each placement's
    registry kind (`owned`, `managed_vm`, ...); a provider placement refuses a plan-row role.
    `connections` maps a connection id to its reading word; a node that names one fires only on
    `ok`, on the connection's home (AD-67)."""
    words = _connection_words(settings, connections)
    for node in workflow.nodes:
        if node.disabled:
            continue
        named = node.parameters.get("connection")
        if isinstance(named, str) and named:
            blocked = connection_fault(node.name, placements_of(node), named, words, settings)
            if blocked is not None:
                return blocked
        if node.role is not None:
            candidates = order(settings, node.role, "live")
            if not candidates:
                return Blocked(
                    "config", "role_missing", f"{node.name}: role {node.role} has no candidates"
                )
            if kinds is not None:
                refused = plan_on_provider(node.name, node.role, node.runs_on, candidates, kinds)
                if refused is not None:
                    return refused
            if profiles is not None:
                found = resolve(candidates, profiles, None)
                if isinstance(found, str):
                    return Blocked("config", "role_unresolved", f"{node.name}: {found}")
        if credentials is not None:
            for name, ref in sorted(node.credentials.items()):
                if TOOL_KEY.fullmatch(ref) or ref.casefold() in credentials:
                    continue
                message = f"{node.name}: credential {name} names {ref}, which is not configured"
                return Blocked("provider", "credential_missing", message)
        named = node.parameters.get("skills")
        if skills is not None and isinstance(named, list):
            for skill in named:  # pyright: ignore[reportUnknownVariableType]
                if str(skill) not in skills:  # pyright: ignore[reportUnknownArgumentType]
                    message = f"{node.name}: skill {skill} is not installed"
                    return Blocked("config", "skill_missing", message)
    return None


def connection_fault(
    name: str,
    placements: tuple[str, ...],
    connection: str,
    words: Mapping[str, str],
    settings: Mapping[str, object],
) -> Blocked | None:
    """A node that names a connection fires only on an `ok` reading on that connection's home."""
    word = words.get(connection)
    if word is None:
        return Blocked(
            "config",
            "connection_unknown",
            f"{name}: connection {connection} is not configured",
        )
    if word != "ok":
        return Blocked(
            "config",
            "connection_unhealthy",
            f"{name}: connection {connection} reads {word}",
        )
    home = settings.get(f"connection.{connection}.home")
    if isinstance(home, str) and home and placements and home not in placements:
        return Blocked(
            "config",
            "connection_unreachable",
            f"{name}: connection {connection} is homed on {home}, not {' or '.join(placements)}",
        )
    return None


def _connection_words(
    settings: Mapping[str, object], connections: Mapping[str, str] | None
) -> Mapping[str, str]:
    if connections is not None:
        return dict(connections)
    found: dict[str, str] = {}
    for key, value in settings.items():
        if key.startswith("connection.") and key.endswith(".word") and isinstance(value, str):
            found[key.removeprefix("connection.").removesuffix(".word")] = value
    return found


def quarantined_input(object_id: str, library: LibraryPort) -> Blocked | None:
    path = library.quarantine_path(object_id)
    if not path:
        return None
    message = f"{object_id} is built on quarantined input: {' -> '.join(path)}"
    return Blocked("config", "quarantined_input", message)


def placements_of(node: object) -> tuple[str, ...]:
    runs_on = getattr(node, "runs_on", "pc")
    if isinstance(runs_on, str):
        return (runs_on,)
    return tuple(str(name) for name in runs_on)


def placement_kind(settings: Mapping[str, object], placement: str) -> str:
    """A placement's registry kind; `owned` when the row names none, because a row QMX has no
    provider for can only be a machine he owns."""
    found = settings.get(f"placement.{placement}.kind")
    return str(found) if isinstance(found, str) and found else "owned"


NEEDS: Final = ("kind", "attempt_cpus", "attempt_timeout")
"""What an attempt needs a placement's row to name. Memory is not here: an attempt's figure is what
its node declares or what the machine's own heartbeat measured, so a row that carries these three
and no memory figure is configured (D-11)."""


def placement_state(
    settings: Mapping[str, object],
    placement: str,
    *,
    seen: Collection[str] | None = None,
    healthy: Collection[str] | None = None,
) -> str:
    """The last state this placement has reached, in DEC-0428's order.

    `available`: a name the registry can resolve (`pc` always, else a row with any key).
    `configured`: its row names the kind, CPU share and timeout an attempt needs. The memory rows
    are live readings now, so a row is not made unconfigured by leaving them out (D-11).
    `authorized`: it is QMX's own machine, or a provider row whose relay holds no plan login.
    `reachable`: a heartbeat has named it. `healthy`: that heartbeat's kind digest was checked and
    lists every kind the definition uses (`placement_wait` makes that judgement with the kinds).
    """
    if placement == "pc":
        return "healthy"
    prefix = f"placement.{placement}."
    row = {key: value for key, value in settings.items() if key.startswith(prefix)}
    if not row:
        return "unavailable"
    configured = all(any(key.endswith(suffix) for key in row) for suffix in NEEDS)
    if not configured:
        return "configured"
    if placement_kind(settings, placement) in PROVIDER_KINDS:
        return "authorized"
    if seen is None:
        return "authorized"
    if healthy is not None and placement in healthy:
        return "healthy"
    return "reachable" if placement in seen else "authorized"


def plan_on_provider(
    node: str,
    role: str,
    runs_on: str | list[str],
    candidates: Collection[Candidate],
    kinds: Mapping[str, str],
) -> Blocked | None:
    """A plan row asked to run on a machine QMX does not own is refused here, before any fire.

    The check is on the first candidate the role would take, which is the row a live fire resolves
    to when nothing is benched; a role list whose cheap rows are key rows and whose plan row sits
    last is fine, because that candidate is only reached when every key row is unavailable.
    """
    first = next(iter(candidates), None)
    if first is None or first.profile != PLAN_PROFILE:
        return None
    placements = [runs_on] if isinstance(runs_on, str) else runs_on
    for placement in placements:
        kind = kinds.get(placement) or "owned"
        if kind in PROVIDER_KINDS:
            message = (
                f"{node}: role {role} resolves to the plan row "
                f"{first.profile}/{first.model} on {placement} "
                f"({kind}); plan logins stay on his machines"
            )
            return Blocked("config", "plan_on_provider", message)
    return None


def placement_wait(workflow: Workflow, kinds: Mapping[str, Collection[str]]) -> str | None:
    """Why the first node whose host lacks its kind waits, or None. `kinds` is each host's
    node kinds by placement name."""
    for node in workflow.nodes:
        if node.disabled:
            continue
        found = REGISTRY.kind(node.type)
        kind = node.type if found is None else found.name
        for placement in [node.runs_on] if isinstance(node.runs_on, str) else node.runs_on:
            known = kinds.get(placement)
            if known is not None and kind not in known:
                return f"placement: node needs update ({node.name}: {placement} lacks {kind})"
    return None


def market_shut_until(now: datetime, zone: str, holidays: Collection[str]) -> datetime | None:
    """None while the market is open at `now`; else the UTC instant its next open day begins."""
    where = ZoneInfo(zone)

    def shut(day: date) -> bool:
        return day.weekday() in WEEKEND or day.isoformat() in holidays

    day = now.astimezone(where).date()
    if not shut(day):
        return None
    while shut(day):
        day += timedelta(days=1)
    return datetime.combine(day, time(0), where).astimezone(UTC)
