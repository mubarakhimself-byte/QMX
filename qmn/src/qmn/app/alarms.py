"""The node's two outbound senders that reach him while This PC is off (Part C AD-318, Level 0
AD-42, lead's call LC-X0-10).

- :class:`PushSender` wakes him through ntfy. It reads the rows the runtime already writes for
  ``status`` (``runtime.alarms``, ``runtime.stand_downs``, ``runtime.positions``) and the
  deployments kept in ``desired``, picks out the short list in :data:`SHORT_LIST`, and hands each
  one to the kept :class:`~qmn.observability.alerts.AlertPublisher`, whose closed push list
  decides what may leave the node. The ntfy channel is a ``NotificationChannel`` adapter.
- :class:`LivenessSender` drives the kept :class:`~qmn.observability.liveness.LivenessHeartbeat`
  to a Healthchecks.io check through a ``LivenessHttpSink`` adapter. Healthchecks.io alarms him
  when the pings stop.

Both run on their own threads and read the node only through its store, so a send that raises
or hangs holds nothing the runtime needs: the order path and the kill switch never wait on them.
A failed push is counted and tried again on the next pass. Each is on once the node's keys
document names its destination (``alarms {ntfy_topic_url?, healthchecks_ping_url?}``), which
the setup cards write (``qmx_host.connect_node``).

Pushes fire only while a market they concern is open on its calendar, except protection
escalation and the clock halt. Node down is the watcher's. A market's calendar is the one its
deployment's instrument snapshot names, read from the shipped ``qmx.calendar/1`` files
(:func:`qmn.time.calendars.market_calendars`).
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, cast
from urllib.parse import urlsplit

from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal

from qmn.app.operations import Target
from qmn.app.runtime import deployment_records, parse_deployment
from qmn.app.store import Json, Store
from qmn.observability.alerts import (
    AlertAllowList,
    AlertPayload,
    AlertPublisher,
    load_alert_allow_list,
)
from qmn.observability.liveness import LivenessHeartbeat
from qmn.time.calendars import MarketCalendar, market_calendars

__all__ = [
    "HALT_BAND_ALARM_AFTER_NS",
    "LIVENESS_INTERVAL_NS",
    "OPEN_SETTLE_NS",
    "PUSHED",
    "PUSH_PASS_S",
    "SEND_TIMEOUT_S",
    "SHORT_LIST",
    "WAITING_MAX",
    "Destinations",
    "HealthchecksSink",
    "LivenessSender",
    "NtfyChannel",
    "PushSender",
    "Raised",
    "Rule",
    "Senders",
    "View",
    "Wake",
    "attach",
    "calendar_notes",
    "calendar_refs",
    "market_hours",
    "raised",
]

PUSH_PASS_S: Final = 5.0
"""`[node] alarm_pass_s`, starting at 5 s: how often the push sender reads the node's rows and
tries the pushes still waiting."""
SEND_TIMEOUT_S: Final = 10.0
"""`[node] alarm_send_timeout_s`, starting at 10 s: how long one push or ping may take."""
LIVENESS_INTERVAL_NS: Final = 60_000_000_000
"""`[node] liveness_interval_s`, starting at 60 s. The watcher's period is 3 minutes with 2
minutes grace (Part C DEVOPS-CLOCKS section 7)."""
HALT_BAND_ALARM_AFTER_NS: Final = 300_000_000_000
"""`[node] halt_band_alarm_after_s`, starting at 300 s: how long the clock stand-down holds
before it wakes him."""
OPEN_SETTLE_NS: Final = 120_000_000_000
"""`[node] alarm_open_settle_s`, starting at 120 s: how long a market must have been open before
a push that follows its calendar fires, so feeds and sessions coming back after a closure do
not wake him."""
WAITING_MAX: Final = 100
"""`[node] alarm_waiting_max`, starting at 100: how many failed pushes wait to be tried again;
past it the oldest is dropped and counted."""
PING_REFERENCE: Final = "qmx/trading-node-keys#alarms.healthchecks_ping_url"
"""Where the ping URL is kept, by name; the heartbeat never holds the URL itself."""
LOOPBACK: Final = frozenset({"127.0.0.1", "::1", "localhost"})
"""The only hosts a destination may reach without TLS: this machine."""
PUSHED: Final = "alarms.pushed"
"""The store row holding the keys of the occurrences already pushed that the node still shows,
so a restart pushes what it had not pushed yet and nothing twice."""


class Wake(StrEnum):
    """The short list that wakes him (Part C DEVOPS-CLOCKS section 6). Node down is the
    watcher's; everything else waits for the morning digest."""

    PROTECTION = "protection escalation"
    RISK_STOP = "risk stop with open trades"
    BROKER_LINK = "broker link down with open trades"
    CLOCK_HALT = "clock stand-down past its alarm time"
    HEALING = "healing that keeps failing"


@dataclass(frozen=True, slots=True)
class Rule:
    """One row of the short list: the registered failure the kept publisher checks against its
    closed push list, the ntfy priority, and whether it fires while every market it concerns is
    shut."""

    wake: Wake
    failure_id: str
    priority: int
    any_hours: bool


SHORT_LIST: Final[Mapping[Wake, Rule]] = {
    rule.wake: rule
    for rule in (
        Rule(Wake.PROTECTION, "protection.ksa.escalation", 5, any_hours=True),
        Rule(Wake.RISK_STOP, "lifecycle.stand_down", 4, any_hours=False),
        Rule(Wake.BROKER_LINK, "lifecycle.stand_down", 4, any_hours=False),
        Rule(Wake.CLOCK_HALT, "clock.band.halt", 4, any_hours=True),
        Rule(Wake.HEALING, "supervision.fail_closed", 4, any_hours=False),
    )
}
PRIORITY: Final[Mapping[str, int]] = {
    rule.failure_id: max(r.priority for r in SHORT_LIST.values() if r.failure_id == rule.failure_id)
    for rule in SHORT_LIST.values()
}


@dataclass(frozen=True, slots=True)
class Raised:
    """One occurrence on the short list. ``key`` names it across passes, so it is pushed once;
    ``markets`` are the markets whose calendars decide whether it fires."""

    wake: Wake
    key: str
    summary: str
    markets: frozenset[str]


@dataclass(frozen=True, slots=True)
class Position:
    deployment_id: str
    market_id: str


@dataclass(frozen=True, slots=True)
class View:
    """What the push sender reads from the node, as the runtime wrote it for ``status``."""

    alarms: tuple[Mapping[str, object], ...] = ()
    stand_downs: tuple[Mapping[str, object], ...] = ()
    positions: tuple[Position, ...] = ()
    accounts: Mapping[str, str] = field(default_factory=dict[str, str])
    """The account each deployment trades on, by deployment id."""
    traded: frozenset[str] = frozenset()
    """Every market a kept deployment trades."""

    @classmethod
    def read(cls, store: Store) -> View:
        accounts: dict[str, str] = {}
        traded: set[str] = set()
        for change in Target.fold(store.accepted()).deployments.values():
            document = change.args.get("document")
            if not isinstance(document, dict):
                continue
            try:
                deployment = parse_deployment(document)
            except ValueError:
                continue
            accounts[deployment.deployment_id] = deployment.account_id
            traded.update(
                str(market["market_id"])
                for market in _rows(deployment.unit_document.get("markets"))
                if isinstance(market.get("market_id"), str)
            )
        positions = tuple(
            Position(str(row["deployment_id"]), str(row["market_id"]))
            for row in _rows(store.observed("runtime.positions"))
            if isinstance(row.get("deployment_id"), str) and isinstance(row.get("market_id"), str)
        )
        return cls(
            alarms=_rows(store.observed("runtime.alarms")),
            stand_downs=_rows(store.observed("runtime.stand_downs")),
            positions=positions,
            accounts=accounts,
            traded=frozenset(traded),
        )

    def open_in(self, scope: str) -> frozenset[str]:
        """The markets of the node's open positions inside a stand-down's scope."""
        kind, _, rest = scope.partition(":")
        found: set[str] = set()
        for held in self.positions:
            inside = {
                "all": True,
                "account": self.accounts.get(held.deployment_id) == rest,
                "deployment_id": held.deployment_id == rest,
                "instrument": held.market_id == rest,
                "unit": f"{held.deployment_id}:{held.market_id}" == rest,
            }.get(kind, False)
            if inside:
                found.add(held.market_id)
        return frozenset(found)


def _rows(value: object) -> tuple[Mapping[str, object], ...]:
    items = cast("list[object]", value) if isinstance(value, list) else []
    return tuple(cast("Mapping[str, object]", row) for row in items if isinstance(row, dict))


def raised(
    view: View, now_ns: int, *, halt_after_ns: int = HALT_BAND_ALARM_AFTER_NS
) -> list[Raised]:
    """Every occurrence on the short list in ``view`` at ``now_ns``, before the calendars."""
    found: list[Raised] = []
    for alarm in view.alarms:
        name, market = alarm.get("alarm"), str(alarm.get("market_id", ""))
        position = alarm.get("position")
        if name == "protection_escalation":
            then = (
                "closed it reduce-only"
                if alarm.get("action") == "closed_reduce_only"
                else "is still closing it"
            )
            summary = (
                f"Protection escalation on {market}: the venue held no stop on {position}, "
                f"so the node {then}."
            )
        elif name == "close_refused":
            summary = (
                f"Protection escalation on {market}: the venue refused {alarm.get('refusals')} "
                f"closes of {position}; the node keeps closing it."
            )
        else:
            continue
        key = json.dumps(alarm, sort_keys=True, default=str)
        found.append(Raised(Wake.PROTECTION, key, summary, frozenset({market})))
    for row in view.stand_downs:
        kind, scope = row.get("stand_down"), str(row.get("scope", ""))
        since = row.get("since_ns")
        key = f"{kind}/{scope}/{since}"
        cause = row.get("cause")
        if kind == "risk_stop" and (markets := view.open_in(scope)):
            summary = f"Risk stop with open trades on {', '.join(sorted(markets))}: {cause}."
            found.append(Raised(Wake.RISK_STOP, key, summary, markets))
        elif kind in {"venue_not_ready", "stale_feed"} and (markets := view.open_in(scope)):
            what = "The broker link is down" if kind == "venue_not_ready" else "The feed is stale"
            summary = f"{what} with open trades on {', '.join(sorted(markets))} ({scope}): {cause}."
            found.append(Raised(Wake.BROKER_LINK, key, summary, markets))
        elif kind == "clock_band" and isinstance(since, int) and now_ns - since >= halt_after_ns:
            minutes = (now_ns - since) // 60_000_000_000
            summary = f"The clock has held new entries for {minutes} minutes: {cause}."
            found.append(Raised(Wake.CLOCK_HALT, key, summary, view.traded))
        elif kind == "repeated_fault":
            summary = f"Healing keeps failing and the node stood down: {cause}."
            found.append(Raised(Wake.HEALING, key, summary, view.traded))
    return found


# --- the senders' wire ------------------------------------------------------------------------

Send = Callable[[str, str, Mapping[str, str], bytes | None, float], int]
"""One HTTPS request: method, URL, headers, body and timeout; answers the status, raises when
it does not land."""


def https_send(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout_s: float
) -> int:
    """A destination is an https address or this machine's (`_destination`), never a file."""
    request = urllib.request.Request(url, body, dict(headers), method=method)  # noqa: S310
    with urllib.request.urlopen(request, timeout=timeout_s) as answer:  # noqa: S310
        return int(answer.status)


def _why(error: BaseException) -> str:
    """A failed send in words that never carry the destination, which is a secret."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    return type(error).__name__


def _unavailable(field_name: str, reason: str) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
        retryability=Retryability.YES,
        context={"field": field_name, "reason": reason},
    )


@dataclass(frozen=True, slots=True)
class NtfyChannel:
    """The kept publisher's ``NotificationChannel`` for ntfy: one POST to his topic with a
    title, the priority and the summary as the body (Part C CONTRACTS section 10)."""

    url: str = field(repr=False)
    node_tag: str
    send: Send = https_send
    timeout_s: float = SEND_TIMEOUT_S

    def deliver(self, alert: AlertPayload, /) -> Result[None]:
        headers = {
            "Title": f"QMX node {self.node_tag}: {alert.alert_class}",
            "Priority": str(PRIORITY.get(alert.failure_id, 4)),
        }
        try:
            self.send("POST", self.url, headers, alert.summary.encode("utf-8"), self.timeout_s)
        except Exception as error:  # every failure is a count, never a raise into the sender
            return _unavailable("ntfy", f"the push did not land ({_why(error)})")
        return Ok(None)


@dataclass(frozen=True, slots=True)
class HealthchecksSink:
    """The kept heartbeat's ``LivenessHttpSink`` for Healthchecks.io: a GET to the check's ping
    URL with no body. The URL is held here; the heartbeat carries only a label and a key
    reference."""

    url: str = field(repr=False)
    send: Send = https_send
    timeout_s: float = SEND_TIMEOUT_S

    def post_alive(
        self, *, endpoint: str, token_reference: str, emitted_at_ns: int
    ) -> Result[None]:
        del endpoint, token_reference, emitted_at_ns
        try:
            self.send("GET", self.url, {}, None, self.timeout_s)
        except Exception as error:  # a missed ping is the watcher's to notice
            return _unavailable("healthchecks", f"the ping did not land ({_why(error)})")
        return Ok(None)


# --- the senders ------------------------------------------------------------------------------


class PushSender:
    """Pushes each new occurrence on the short list once, while its calendar allows.

    ``open_at(market_id, utc_ns)`` answers whether that market is open on its calendar; a push
    that follows the calendar waits until a market it concerns has been open ``settle_ns``. A
    market whose calendar raises reads open, so the push goes rather than wait on a calendar
    that cannot answer, and is named once on stderr. A push that fails stays waiting and is
    tried again on every pass, in the order it arose; past ``waiting_max`` the oldest is dropped
    and counted in ``dropped``. With a ``store``, the keys pushed are kept in its
    :data:`PUSHED` row, so a restart pushes what was still waiting and nothing twice."""

    def __init__(
        self,
        read: Callable[[], View],
        publisher: AlertPublisher,
        open_at: Callable[[str, int], bool],
        clock_ns: Callable[[], int],
        *,
        store: Store | None = None,
        pass_s: float = PUSH_PASS_S,
        halt_after_ns: int = HALT_BAND_ALARM_AFTER_NS,
        settle_ns: int = OPEN_SETTLE_NS,
        waiting_max: int = WAITING_MAX,
    ) -> None:
        self.read = read
        self.publisher = publisher
        self.open_at = open_at
        self.clock_ns = clock_ns
        self.store = store
        self.pass_s = pass_s
        self.halt_after_ns = halt_after_ns
        self.settle_ns = settle_ns
        self.waiting_max = waiting_max
        self.sent = 0
        self.failed = 0
        self.dropped = 0
        self.waiting: list[Raised] = []
        self._seen: set[str] = set()
        self._pushed: set[str] = set()
        self._uncalendared: set[str] = set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Take the keys an earlier run pushed, then pass on a thread. Called before the runtime
        starts; an occurrence the earlier run never pushed is pushed now."""
        kept = None if self.store is None else self.store.observed(PUSHED)
        found = cast("list[object]", kept) if isinstance(kept, list) else []
        self._pushed.update(key for key in found if isinstance(key, str))
        self._seen.update(self._pushed)
        self._thread = threading.Thread(target=self._run, name="node-alarms-push", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.pass_s + SEND_TIMEOUT_S)

    def _settled(self, market: str, now: int) -> bool:
        try:
            return self.open_at(market, now) and self.open_at(market, now - self.settle_ns)
        except Exception as error:  # a calendar that cannot answer never silences a push
            if market not in self._uncalendared:
                self._uncalendared.add(market)
                note = {"event": "alarm_calendar_failed", "market_id": market}
                print(json.dumps({**note, "error": type(error).__name__}), file=sys.stderr)
            return True

    def pass_once(self) -> None:
        now = self.clock_ns()
        found = raised(self.read(), now, halt_after_ns=self.halt_after_ns)
        for item in found:
            if item.key in self._seen:
                continue
            if not SHORT_LIST[item.wake].any_hours and not any(
                self._settled(m, now) for m in sorted(item.markets)
            ):
                continue
            self._seen.add(item.key)
            self.waiting.append(item)
        while len(self.waiting) > self.waiting_max:
            oldest = self.waiting.pop(0)
            self.dropped += 1
            note = {"event": "alarm_dropped", "wake": oldest.wake.value, "dropped": self.dropped}
            print(json.dumps(note), file=sys.stderr)
        landed = False
        for item in list(self.waiting):
            published = self.publisher.publish(
                failure_id=SHORT_LIST[item.wake].failure_id, summary=item.summary
            )
            if is_refusal(published):
                self.failed += 1
                continue
            self.waiting.remove(item)
            self.sent += 1
            self._pushed.add(item.key)
            landed = True
        if landed and self.store is not None:
            self._pushed &= {item.key for item in found}
            kept: list[Json] = [*sorted(self._pushed)]
            self.store.observe(PUSHED, kept, now)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.pass_once()
            except Exception as error:  # the sender keeps going; trading never sees it
                self.failed += 1
                print(
                    json.dumps({"event": "alarm_pass_failed", "error": repr(error)}),
                    file=sys.stderr,
                )
            self._stop.wait(self.pass_s)


class LivenessSender:
    """Pings the watcher every ``LivenessHeartbeat.cadence_ns`` while the node runs, and stops
    when the node stops, which is what lets the watcher see node down."""

    def __init__(self, heartbeat: LivenessHeartbeat, steady_ns: Callable[[], int]) -> None:
        self.heartbeat = heartbeat
        self.steady_ns = steady_ns
        self.failed = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="node-alarms-liveness", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=SEND_TIMEOUT_S + 1)

    def ping_once(self) -> None:
        if is_refusal(self.heartbeat.maybe_emit(self.steady_ns())):
            self.failed += 1

    def _run(self) -> None:
        while not self._stop.is_set():
            self.ping_once()
            self._stop.wait(self.heartbeat.cadence_ns / 1e9)


# --- the destinations and the composition -----------------------------------------------------


def calendar_refs(store: Store) -> dict[str, str]:
    """The calendar each market a kept deployment trades names, through its instrument
    snapshot, by market id."""
    found: dict[str, str] = {}
    for change in Target.fold(store.accepted()).deployments.values():
        document = change.args.get("document")
        if not isinstance(document, dict):
            continue
        try:
            records = deployment_records(parse_deployment(document))
        except ValueError:
            continue
        if not isinstance(records, str):
            found.update((market, record.calendar_ref) for market, record in records.items())
    return found


def market_hours(
    store: Store, calendars: Mapping[str, MarketCalendar] | None = None
) -> Callable[[str, int], bool]:
    """``open_at`` over the shipped calendars (``market_calendars()`` by default). A market no
    deployment names a shipped calendar for raises ``LookupError``, which the push sender reads
    as open."""
    shipped = market_calendars() if calendars is None else calendars

    def open_at(market_id: str, at_ns: int) -> bool:
        ref = calendar_refs(store).get(market_id)
        calendar = None if ref is None else shipped.get(ref)
        if calendar is None:
            raise LookupError(f"no shipped calendar for {market_id} ({ref})")
        return calendar.open_at(at_ns)

    return open_at


def calendar_notes(
    store: Store, now_ns: int, calendars: Mapping[str, MarketCalendar] | None = None
) -> list[str]:
    """A status line for each calendar the node's markets read that is within
    ``CALENDAR_WARN_DAYS`` of the last day its data covers, or past it."""
    shipped = market_calendars() if calendars is None else calendars
    notes: list[str] = []
    for ref in sorted(set(calendar_refs(store).values())):
        calendar = shipped.get(ref)
        note = None if calendar is None else calendar.note(now_ns)
        if note is not None:
            notes.append(note)
    return notes


@dataclass(frozen=True, slots=True)
class Destinations:
    """The two destinations the node's keys document names; None is a sender that is off."""

    ntfy_topic_url: str | None = None
    healthchecks_ping_url: str | None = None

    @classmethod
    def from_keys(cls, text: str | None) -> Destinations:
        """The keys document's ``alarms``. A document that is not one, or a destination that is
        not an address, refuses in words that never carry its value."""
        if not text:
            return cls()
        try:
            document: object = json.loads(text)
        except ValueError:
            raise ValueError("the node's keys document is not JSON") from None
        if not isinstance(document, dict):
            raise ValueError("the node's keys document is not an object")
        alarms: object = cast("Mapping[str, object]", document).get("alarms") or {}
        if not isinstance(alarms, dict):
            raise ValueError("the keys document's alarms is not an object")
        named = cast("Mapping[str, object]", alarms)
        return cls(
            _destination(named.get("ntfy_topic_url"), "ntfy_topic_url"),
            _destination(named.get("healthchecks_ping_url"), "healthchecks_ping_url"),
        )


def _destination(value: object, name: str) -> str | None:
    if value is None:
        return None
    parts = urlsplit(value) if isinstance(value, str) else None
    secure = parts is not None and parts.scheme == "https" and bool(parts.hostname)
    local = parts is not None and parts.scheme == "http" and parts.hostname in LOOPBACK
    if not (secure or local):
        raise ValueError(f"alarms.{name} is not an https address")
    return cast("str", value)


@dataclass
class Senders:
    """The node's push and liveness senders; either is None while its destination is unnamed."""

    push: PushSender | None = None
    liveness: LivenessSender | None = None

    def start(self) -> None:
        for sender in (self.push, self.liveness):
            if sender is not None:
                sender.start()

    def stop(self) -> None:
        for sender in (self.push, self.liveness):
            if sender is not None:
                sender.stop()


def attach(
    store: Store,
    node_tag: str,
    keys_text: str | None,
    *,
    open_at: Callable[[str, int], bool],
    clock_ns: Callable[[], int],
    steady_ns: Callable[[], int],
    send: Send = https_send,
    allow_list: AlertAllowList | None = None,
    pass_s: float = PUSH_PASS_S,
    liveness_interval_ns: int = LIVENESS_INTERVAL_NS,
) -> Senders:
    """The senders the keys document turns on, over the node's ``store``. A keys document or
    register that cannot be read turns the senders off with one stderr line; it never stops
    the node."""
    try:
        named = Destinations.from_keys(keys_text)
    except ValueError as error:
        return _off(str(error))
    senders = Senders()
    if named.ntfy_topic_url is not None:
        loaded = Ok(allow_list) if allow_list is not None else load_alert_allow_list()
        if is_refusal(loaded):
            return _off(f"the failure register did not load ({loaded.category.value})")
        publisher = AlertPublisher(loaded.value, NtfyChannel(named.ntfy_topic_url, node_tag, send))
        senders.push = PushSender(
            lambda: View.read(store), publisher, open_at, clock_ns, store=store, pass_s=pass_s
        )
    if named.healthchecks_ping_url is not None:
        heartbeat = LivenessHeartbeat.try_create(
            endpoint="healthchecks",
            cadence_ns=liveness_interval_ns,
            token_reference=PING_REFERENCE,
            sink=HealthchecksSink(named.healthchecks_ping_url, send),
        )
        if is_refusal(heartbeat):
            return _off(f"the liveness heartbeat refused ({heartbeat.category.value})")
        senders.liveness = LivenessSender(heartbeat.value, steady_ns)
    return senders


def _off(reason: str) -> Senders:
    print(json.dumps({"event": "alarms_off", "reason": reason}), file=sys.stderr)
    return Senders()
