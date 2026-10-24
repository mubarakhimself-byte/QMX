"""The open adapter registry: one static declaration per connection type, and the health walk.

An adapter ships a `Declaration` and, when the type can be checked without a credential
conversation, a `probe`. Built-in declarations register on import; a package found through the
`qmx.connections` entry-point group registers the same way, so a new type is "install the package,
it appears in the list" (56 section 8.3, AD-67).

The health walk answers one reading word per connection (`ok | slowed | maintenance | needs_you |
down`), in the five setup states the plan keeps inside it (`available | configured | authorized |
reachable | healthy`). Only `down` is an incident. A provider's own slow-down signal sets
`slowed_until`, kept per connection or per `(provider, egress IP)` for a provider that limits per
address, and every caller on the machine waits on it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from importlib import metadata
from typing import ClassVar, Final, Literal, Protocol

from qmx_broker.models import Broker, Connection

type Word = Literal["ok", "slowed", "maintenance", "needs_you", "down"]
type Setup = Literal["available", "configured", "authorized", "reachable", "healthy"]
type LimitScope = Literal["connection", "egress"]
type Session = Literal["host", "step"]
type Kind = Literal["broker", "platform", "data"]

SETUP: Final[tuple[Setup, ...]] = (
    "available",
    "configured",
    "authorized",
    "reachable",
    "healthy",
)
WORDS: Final[tuple[Word, ...]] = ("ok", "slowed", "maintenance", "needs_you", "down")
GROUP: Final = "qmx.connections"
"""The entry-point group an adapter package publishes its `describe()` under."""


@dataclass(frozen=True, slots=True)
class PublishedLimit:
    """A limit as the maker states it, with the source and the date it was read."""

    name: str
    value: str
    source: str
    read_on: str


@dataclass(frozen=True, slots=True)
class Declaration:
    """What a connection type declares without a credential (56 section 8.2)."""

    name: str
    kind: Kind
    auth: str
    credential_fields: tuple[str, ...]
    environments: tuple[str, ...]
    reads: tuple[str, ...]
    runs_on: tuple[str, ...]
    session: Session
    limit_signals: tuple[str, ...]
    limit_scope: LimitScope
    error_map: Mapping[str, str] = field(default_factory=dict[str, str])
    """Venue code or HTTP status to `retry` or `unknown`, never a guessed outcome."""
    health_check: str = ""
    published_limits: tuple[PublishedLimit, ...] = ()
    writes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProbeResult:
    latency_ms: int
    clock_offset_ms: int | None = None
    """The provider's clock minus this machine's, when its answer carried a date."""


class Probe(Protocol):
    def __call__(self, provider: Broker, connection: Connection, /) -> ProbeResult: ...


class ConnectionFault(Exception):
    """A health check that did not pass, carrying the reading word it earns."""

    word: ClassVar[Word] = "down"

    def __init__(self, code: str, message: str = "", *, retry_after: float | None = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.retry_after = retry_after


class SlowDown(ConnectionFault):
    word = "slowed"


class NeedsYou(ConnectionFault):
    word = "needs_you"


class Maintenance(ConnectionFault):
    word = "maintenance"


class Down(ConnectionFault):
    word = "down"


@dataclass(frozen=True, slots=True)
class Reading:
    """One word per connection, with the setup state the walk reached and what it measured."""

    connection: str
    setup: Setup
    word: Word
    code: str = ""
    latency_ms: int | None = None
    clock_offset_ms: int | None = None
    slowed_until: float | None = None


class Slowdowns:
    """`slowed_until` per connection, or per `(provider, egress IP)` when the provider limits per
    address. One instance per home process; the health walk and every caller read the same one."""

    def __init__(self) -> None:
        self._until: dict[str, float] = {}

    def key(self, declaration: Declaration, connection: Connection, egress_ip: str = "") -> str:
        if declaration.limit_scope == "egress":
            return f"{declaration.name}:{egress_ip}"
        return connection.id

    def note(
        self,
        declaration: Declaration,
        connection: Connection,
        *,
        retry_after: float,
        now: float,
        egress_ip: str = "",
    ) -> float:
        until = now + max(0.0, retry_after)
        key = self.key(declaration, connection, egress_ip)
        self._until[key] = max(until, self._until.get(key, 0.0))
        return self._until[key]

    def remaining(
        self, declaration: Declaration, connection: Connection, *, now: float, egress_ip: str = ""
    ) -> float:
        key = self.key(declaration, connection, egress_ip)
        return max(0.0, self._until.get(key, 0.0) - now)


_DECLARATIONS: Final[dict[str, Declaration]] = {}
_PROBES: Final[dict[str, Probe]] = {}
BUILTIN_MODULES: Final = ("qmx_broker.adapters", "qmx_broker.providers")


def register(declaration: Declaration) -> Declaration:
    """Add one type; registering the same name twice keeps the first and is not an error."""
    return _DECLARATIONS.setdefault(declaration.name, declaration)


def register_probe(name: str, probe: Probe) -> None:
    _PROBES.setdefault(name, probe)


def declare(*declarations: Declaration) -> None:
    for declaration in declarations:
        register(declaration)


@cache
def _builtins() -> None:
    for module in BUILTIN_MODULES:
        __import__(module)
    for entry_point in metadata.entry_points(group=GROUP):
        describe = getattr(entry_point.load(), "describe", None)
        if describe is None:
            continue
        register(describe())


def declarations() -> Mapping[str, Declaration]:
    _builtins()
    return dict(_DECLARATIONS)


def names() -> tuple[str, ...]:
    return tuple(sorted(declarations()))


def describe(name: str) -> Declaration:
    """The declaration a settings row names; `KeyError` when no package installs it."""
    _builtins()
    return _DECLARATIONS[name]


def probe_for(name: str) -> Probe | None:
    _builtins()
    return _PROBES.get(name)


def walk(
    provider: Broker,
    connection: Connection,
    *,
    probe: Probe | None,
    now: float,
    market_open: bool = True,
    slowdowns: Slowdowns | None = None,
    egress_ip: str = "",
) -> Reading:
    """Walk one connection from `available` to `healthy` and read its word.

    A missing declaration, credential reference or probe reads `needs_you`, because a person has
    to finish the setup; a type whose declaration says `auth == "none"` needs no reference. A
    credential that can trade and is homed on the PC reads `needs_you` before any probe runs: it
    belongs on a trading server. A provider's slow-down signal is a
    `slowed` reading with `slowed_until`; while that wait is live the probe is not called. A
    failed probe reads `down`, or `maintenance` while the instrument's market is closed.
    """

    space = slowdowns or Slowdowns()
    try:
        declaration = describe(provider.adapter)
    except KeyError:
        return Reading(connection.id, "available", "needs_you", code="adapter_unknown")
    configured = (
        (declaration.auth == "none" or bool(connection.credential_ref))
        and bool(connection.home)
        and (declaration.name != "ccxt" or bool(provider.exchange))
    )
    if not configured:
        return Reading(connection.id, "available", "needs_you", code="not_configured")
    if connection.scope == "trade" and connection.environment == "live" and connection.home == "pc":
        return Reading(connection.id, "configured", "needs_you", code="trade_live_on_pc")
    if probe is None:
        return Reading(connection.id, "authorized", "needs_you", code="probe_missing")
    wait = space.remaining(declaration, connection, now=now, egress_ip=egress_ip)
    if wait > 0:
        return Reading(
            connection.id,
            "healthy",
            "slowed",
            code="slowed_until",
            slowed_until=now + wait,
        )
    try:
        result = probe(provider, connection)
    except ConnectionFault as fault:
        setup: Setup = "authorized" if fault.word == "needs_you" else "reachable"
        word: Word = fault.word
        until: float | None = None
        if isinstance(fault, SlowDown):
            until = space.note(
                declaration,
                connection,
                retry_after=fault.retry_after if fault.retry_after is not None else 60.0,
                now=now,
                egress_ip=egress_ip,
            )
        if isinstance(fault, Down) and not market_open:
            word, setup = "maintenance", "reachable"
        return Reading(
            connection.id,
            setup,
            word,
            code=fault.code,
            latency_ms=None,
            slowed_until=until,
        )
    except Exception as error:  # the probe crosses the network; any failure is that connection's
        word = "down" if market_open else "maintenance"
        return Reading(connection.id, "reachable", word, code=type(error).__name__, latency_ms=None)
    return Reading(
        connection.id,
        "healthy",
        "ok",
        latency_ms=result.latency_ms,
        clock_offset_ms=result.clock_offset_ms,
    )


def reading_word(reading: Reading) -> str:
    """The one word a screen shows, and the one preflight reads."""
    return reading.word
