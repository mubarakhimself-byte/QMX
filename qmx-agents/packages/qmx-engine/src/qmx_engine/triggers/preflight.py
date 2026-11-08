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
`market_open:<market_id>` checks that market's own calendar instead (Part C AD-320): the
`market.<market_id>.calendar` row names it, because one market id is shared by every venue that
lists it and each venue keeps its own hours. Calendars are versioned data the `qmf-calendar-*`
extensions ship, each read in its market's zone with a maximum age past which it still decides
but says it is stale. Instants stay UTC; only the rule reads local time.

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

import json
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, TypeGuard, cast
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
MARKET_PREFIX: Final = f"{MARKET_OPEN}:"
WEEKEND: Final = (5, 6)
EXTENSIONS: Final = Path(__file__).resolve().parents[6] / "extensions"
"""The repository's `extensions/`, where each `qmf-calendar-*` package ships calendars as data."""
CALENDAR_SCHEMA: Final = "qmx.calendar/1"
CALENDAR_KEYS: Final = frozenset(
    {"schema", "calendar_ref", "name", "zone", "issued", "max_age_days", "source", "sessions"}
    | {"closures", "funding"}
)
CALENDAR_REF: Final = re.compile(r"[a-z0-9][a-z0-9-]*@[1-9][0-9]*")
DAYS: Final = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_MINUTES: Final = 24 * 60
OPEN_HORIZON_DAYS: Final = 400
"""How far ahead a shut calendar is searched for its next open. A calendar that stays shut longer
is a broken calendar, so the fire is blocked as a configuration fault; no shipped closure comes
near it."""
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


@dataclass(frozen=True, slots=True)
class Calendar:
    """One market calendar, read in its own zone. `sessions` are weekly `[open, close)` spans in
    minutes from Monday 00:00 local, a close at or before its open running into the next week;
    `None` is open around the clock. `closures` are `[from, to)` local spans that override them."""

    ref: str
    zone: ZoneInfo
    sessions: tuple[tuple[int, int], ...] | None
    closures: tuple[tuple[datetime, datetime], ...]
    issued: date
    max_age_days: int

    def open_at(self, instant: datetime) -> bool:
        local = instant.astimezone(self.zone)
        if any(start <= local < end for start, end in self.closures):
            return False
        if self.sessions is None:
            return True
        minute = local.weekday() * DAY_MINUTES + local.hour * 60 + local.minute
        return any(_within(minute, opens, closes) for opens, closes in self.sessions)

    def next_open(self, instant: datetime) -> datetime | None:
        """The first UTC instant after `instant` at which it opens, or None when it stays shut
        for `OPEN_HORIZON_DAYS`."""
        day = instant.astimezone(self.zone).date()
        for _ in range(OPEN_HORIZON_DAYS):
            for found in sorted(self._edges(day)):
                if found > instant and self.open_at(found):
                    return found.astimezone(UTC)
            day += timedelta(days=1)
        return None

    def days_past_max_age(self, now: datetime) -> int:
        return max(0, (now.astimezone(self.zone).date() - self.issued).days - self.max_age_days)

    def _edges(self, day: date) -> list[datetime]:
        found = [end for _, end in self.closures if end.date() == day]
        for opens, _ in self.sessions or ():
            if opens // DAY_MINUTES == day.weekday():
                at = time(opens % DAY_MINUTES // 60, opens % 60)
                found.append(datetime.combine(day, at, self.zone))
        return found


@dataclass(frozen=True, slots=True)
class Shut:
    until: datetime
    reason: str


def _within(minute: int, opens: int, closes: int) -> bool:
    if opens < closes:
        return opens <= minute < closes
    return minute >= opens or minute < closes


def _week_minute(text: str) -> int:
    day, _, clock = text.partition(" ")
    hours, minutes = (int(part) for part in clock.split(":"))
    if day not in DAYS or not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"not a weekday and a local HH:MM: {text!r}")
    return DAYS.index(day) * DAY_MINUTES + hours * 60 + minutes


def parse_calendar(document: Mapping[str, object]) -> Calendar:
    """A `qmx.calendar/1` document, refused with the first fault it holds."""
    extra = set(document) - CALENDAR_KEYS
    if extra:
        raise ValueError(f"unknown calendar keys: {sorted(extra)}")
    if document.get("schema") != CALENDAR_SCHEMA:
        raise ValueError(f"schema is not {CALENDAR_SCHEMA}")
    ref, zone, issued = (str(document.get(key, "")) for key in ("calendar_ref", "zone", "issued"))
    if CALENDAR_REF.fullmatch(ref) is None:
        raise ValueError(f"calendar_ref is not id@version: {ref!r}")
    where = ZoneInfo(zone)
    age = document.get("max_age_days")
    if not isinstance(age, int) or age < 1:
        raise ValueError(f"{ref}: max_age_days is not a whole number of days")
    raw = document.get("sessions")
    sessions = None
    if raw != "always":
        if not isinstance(raw, list) or not raw:
            raise ValueError(f"{ref}: sessions is neither 'always' nor a list of spans")
        spans = cast(list[Mapping[str, str]], raw)
        sessions = tuple((_week_minute(s["open"]), _week_minute(s["close"])) for s in spans)
    closures = tuple(
        (
            datetime.fromisoformat(c["from"]).replace(tzinfo=where),
            datetime.fromisoformat(c["to"]).replace(tzinfo=where),
        )
        for c in cast(list[Mapping[str, str]], document.get("closures", []))
    )
    if any(start >= end for start, end in closures):
        raise ValueError(f"{ref}: a closure ends before it starts")
    return Calendar(ref, where, sessions, closures, date.fromisoformat(issued), age)


@cache
def shipped_calendars(folder: Path = EXTENSIONS) -> Mapping[str, Calendar]:
    """Every calendar the `qmf-calendar-*` packages ship, plus the built-in forex week, by ref."""
    found = {FOREX_WEEK.ref: FOREX_WEEK}
    for path in sorted(folder.glob("qmf-calendar-*/src/qmf/calendar_*/calendars/*.json")):
        calendar = parse_calendar(json.loads(path.read_text(encoding="utf-8")))
        if f"{calendar.ref}.json" != path.name:
            raise ValueError(f"{path.name} holds {calendar.ref}")
        found[calendar.ref] = calendar
    return MappingProxyType(found)


def is_market_check(ref: str | None) -> TypeGuard[str]:
    return ref is not None and (ref == MARKET_OPEN or ref.startswith(MARKET_PREFIX))


def market_shut(
    now: datetime, ref: str, zone: str, settings: Mapping[str, object]
) -> Shut | Blocked | None:
    """None while the market is open at `now`. Bare `market_open` keeps the default rule in the
    trigger's zone. `market_open:<market_id>` reads the calendar its `market.<market_id>.calendar`
    row names, in the market's zone; a market with no row, or a row naming a calendar QMX does not
    ship, is the workflow's configuration fault."""
    if ref == MARKET_OPEN:
        until = _weekday_open(now, ZoneInfo(zone), _holidays(settings))
        return None if until is None else Shut(until, f"the market is shut in {zone}")
    market = ref.removeprefix(MARKET_PREFIX)
    named = settings.get(f"market.{market}.calendar")
    if not isinstance(named, str) or not named:
        message = f"{market}: no market.{market}.calendar row names its calendar"
        return Blocked("config", "market_unknown", message)
    calendar = shipped_calendars().get(named)
    if calendar is None:
        return Blocked("config", "calendar_unknown", f"{market}: calendar {named} is not shipped")
    if calendar.open_at(now):
        return None
    until = calendar.next_open(now)
    if until is None:
        message = f"{market}: calendar {named} does not open in the next {OPEN_HORIZON_DAYS} days"
        return Blocked("config", "calendar_shut", message)
    reason = f"{market} is shut on its calendar {named} in {calendar.zone.key}"
    late = calendar.days_past_max_age(now)
    if late:
        reason += f" (the calendar is {late} days past its {calendar.max_age_days}-day maximum age)"
    return Shut(until, reason)


def _holidays(settings: Mapping[str, object]) -> tuple[str, ...]:
    found = settings.get("market.holidays")
    days = cast(tuple[object, ...], found) if isinstance(found, tuple) else ()
    return tuple(str(day) for day in days)


def _weekday_open(now: datetime, where: ZoneInfo, holidays: Collection[str]) -> datetime | None:
    def shut(day: date) -> bool:
        return day.weekday() in WEEKEND or day.isoformat() in holidays

    day = now.astimezone(where).date()
    if not shut(day):
        return None
    while shut(day):
        day += timedelta(days=1)
    return datetime.combine(day, time(0), where).astimezone(UTC)


FOREX_WEEK: Final = parse_calendar(
    {
        "schema": CALENDAR_SCHEMA,
        "calendar_ref": "fx-24x5@1",
        "zone": "America/New_York",
        "issued": "2026-11-02",
        "max_age_days": 31,
        "sessions": [{"open": "sun 17:00", "close": "fri 17:00"}],
        "closures": [
            {"from": "2026-12-24T17:00", "to": "2026-12-27T17:00"},
            {"from": "2026-12-31T17:00", "to": "2027-01-03T17:00"},
        ],
    }
)
"""The 17:00 New York forex week with the two full closes of `qmf-calendar-forex` (25 December and
1 January, each a trading date that starts at 17:00 the day before). The extension ships it as
`fx-24x5@1.json` too, which wins in `shipped_calendars`; this copy serves where that file cannot
be found."""
