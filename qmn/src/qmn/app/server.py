"""The trading node's process: what its MCP entry serves (Part C AD-301, AD-302).

:func:`open_node` composes the node in its volume: the store, the identity (minted on first start,
compared on every start), and the node journal with its ``node_lifecycle`` start row.
:meth:`Node.call` is the one way in. It answers every operation of :data:`OPERATIONS` and never
raises, because a tool exception counts toward the supervisor's breaker and a call past its 30 s
timeout stops the app (``qmx_apps/supervisor.py`` ``call``). The FastMCP wiring lives in the app
folder's ``server.py`` (``qmx-agents/apps/trading-node``), so this package needs no MCP library.

:attr:`Node.runtime` is the thread that reconciles ``desired`` with the venues (C-12a). The node
the supervisor starts has no venue set up until his setup steps register one (C-11), so it trades
nothing and reads "Ready, no units yet"; a composition with venues, such as the conformance venue,
trades the units it is asked to deploy.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Final, TypeAlias, cast
from urllib.parse import urlsplit

from qmf.core import Account, AccountRole, Ok, Result, VenueId, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope

from qmn.app.alarms import Senders, attach, calendar_notes, market_hours
from qmn.app.feed_keeper import FeedKeeper, Recording
from qmn.app.grants import (
    CONSENT_EXPIRES_S,
    LIVE_GRANT_CODE,
    LIVE_GRANT_MESSAGE,
    REDIRECT,
    TOKEN_URL,
    Fetch,
    Grant,
    GrantAccount,
    GrantFile,
    Grants,
    GrantStore,
    Registration,
    TokenEndpoint,
    registration,
    trading_profile,
    urllib_fetch,
)
from qmn.app.grants import grant_store as grant_store_for
from qmn.app.identity import (
    INSTALL_ID_BYTES,
    TAG_LENGTH,
    establish,
    install_id_of,
    machine_fingerprint,
)
from qmn.app.operations import (
    CHANGES,
    NOT_SET_UP,
    READS,
    VENUES,
    Answer,
    Context,
    NoVenues,
    Target,
    answer_change,
    answer_read,
    ok,
    refused,
)
from qmn.app.runtime import Runtime, Venue, deploy_preflight, ulid
from qmn.app.store import Json, Store, StoreBusyError
from qmn.protection.ksa import LEVEL_RANK, KsaLevel
from qmn.venue import order_tags
from qmn.venue.ctrader_account import (
    BAR_NS,
    DEMO_HOST,
    Codec,
    CTraderVenue,
    FramedWire,
    Listing,
    OpenApi,
    TestTrade,
    Wire,
    account_listing,
)
from qmn.venue.live import VenueFacts, read_venue_facts
from qmn.venue.proto_runtime import DEFINITIONS

__all__ = [
    "BUILD",
    "OPERATIONS",
    "ROLE",
    "WORLD",
    "CTraderDoor",
    "Endpoints",
    "Node",
    "endpoints",
    "from_environment",
    "open_node",
]

BUILD: Final = "0.1.0"
"""The node shell's build, stamped on its journal rows; the app manifest carries the same."""
ROLE: Final = "node"
WORLD: Final = JournalWorld.DEMO
"""The node's own journal world. The practice node holds demo grants only; a live world needs
a live binding, which arrives with C-21."""
OPERATIONS: Final[tuple[str, ...]] = (*READS, *CHANGES)
HOST_FACTS: Final = Path("road/host/facts.json")


class Node:
    """One running node: every operation answers here."""

    def __init__(
        self,
        context: Context,
        journal: JournalWriter | None,
        runtime: Runtime | None,
        alarms: Callable[[], Senders] = Senders,
    ) -> None:
        self.context = context
        self.journal = journal
        self.runtime = runtime
        self.make_alarms = alarms
        self.alarms = alarms()
        self._started = False

    def start(self) -> None:
        """Start the alarm senders, then the runtime thread; the operations answer whether it
        runs or not."""
        self._started = True
        self.alarms.start()
        if self.runtime is not None:
            self.runtime.start()

    def rekey(self) -> None:
        """Build the alarm senders again from the keys document and hand over to them. The old
        senders stop before the new ones start, on a thread of their own, so the operation
        answers at once and no push goes out twice."""
        fresh = self.make_alarms()
        old, self.alarms = self.alarms, fresh
        if not self._started:
            return

        def hand_over() -> None:
            old.stop()
            fresh.start()

        threading.Thread(target=hand_over, name="node-alarms-rekey", daemon=True).start()

    def stop(self) -> None:
        """Stop the runtime, then close every venue session it held."""
        if self.runtime is not None:
            self.runtime.stop()
            for venue in self.runtime.venues.values():
                venue.feed.source.close()
        self.alarms.stop()

    def call(self, name: str, arguments: object) -> Answer:
        try:
            if not isinstance(arguments, dict):
                return refused("bad_argument", f"{name}: the arguments are one object")
            given = cast(Mapping[str, Json], arguments)
            if name in READS:
                return answer_read(self.context, name, given)
            if name in CHANGES:
                return answer_change(self.context, name, given)
            return refused("unknown_operation", f"the trading node has no operation {name}")
        except StoreBusyError:
            return refused(
                "busy",
                f"{name}: the node's store stayed locked; nothing was changed",
                next_step="Ask again with the same op id.",
            )
        except Exception as error:  # the boundary: a raise would count toward the breaker
            print(
                json.dumps({"event": "operation_failed", "operation": name, "error": repr(error)}),
                file=sys.stderr,
            )
            return refused("internal", f"{name} failed inside the node ({type(error).__name__})")


def _os_random(size: int) -> bytes:
    """``size`` bytes of OS entropy: the node's one random source."""
    return secrets.token_bytes(size)  # ambient-scan: allow - the node's composition root


def open_node(
    data: Path,
    *,
    here: str | None,
    machine: str,
    clock_ns: Callable[[], int] = time.time_ns,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
    sleep: Callable[[float], None] = time.sleep,
    random_bytes: Callable[[int], bytes] = _os_random,
    venues: Mapping[str, Venue] | Callable[[JournalWriter, str], Mapping[str, Venue]] | None = None,
    door: DoorFactory | None = None,
    keys: Callable[[], str | None] = lambda: None,
) -> Node:
    """Compose the node in ``data`` (the volume's ``data/``) on the machine ``here`` names.

    The clock and the random source are read here and nowhere below: every op id, the boot
    epoch and the install id minted on first start come from ``random_bytes``. ``venues`` are
    the account bindings the runtime trades on, keyed by account id, or a factory given the
    node journal and the boot epoch. ``door`` makes the cTrader door the venue operations ask;
    without one they answer ``not_set_up``. The accounts the door kept bound are bound again
    before the runtime starts. ``keys`` reads the keys document whose ``alarms`` turn the
    senders on, at start and on every ``rotate_keys``; their pushes follow the market calendars
    the deployments' instrument snapshots name. The runtime is built but not started;
    ``Node.start`` starts it.
    """
    store = Store(data / "node.sqlite")
    started = clock_ns()
    standing = establish(
        store,
        install_id=install_id_of(random_bytes(INSTALL_ID_BYTES)),
        here=here,
        now_ns=started,
    )
    journal_root = data / "journal"
    scope = WriterScope(JournalStream.NODE, standing.tag, WORLD, machine, ROLE, BUILD)
    boot_epoch = random_bytes(6).hex()
    opened = JournalWriter.open(journal_root, scope, clock=clock_ns, boot_epoch_id=boot_epoch)
    journal: JournalWriter | None = None
    problem: str | None = None
    if is_refusal(opened):
        problem = f"the journal writer refused to open ({opened.category.value})"
    else:
        journal = opened.value
        body: dict[str, object] = {"event": "start", "build": BUILD, "mismatch": standing.mismatch}
        written = journal.append("node_lifecycle", body, RowFacts(ts_recv=started, clock_ok=False))
        if is_refusal(written):
            problem = f"the start row was refused ({written.category.value})"
    store.observe("journal_problem", problem, started)
    store.observe("journal_write", None if problem else started, started)
    waker: list[Runtime] = []
    nodes: list[Node] = []

    def wake() -> None:
        for runtime in waker:
            runtime.wake()

    def rekey() -> None:
        for node in nodes:
            node.rekey()

    made = None if door is None else door(store, data)
    context = Context(
        store=store,
        here=here,
        journal_root=journal_root,
        data=data,
        build=BUILD,
        clock_ns=clock_ns,
        new_id=lambda: random_bytes(16).hex(),
        started_ns=started,
        wake=wake,
        deploy_preflight=lambda document: deploy_preflight(data, document),
        venues=NoVenues() if made is None else made,
        rekey=rekey,
        calendar_notes=lambda: calendar_notes(store, clock_ns()),
    )
    runtime: Runtime | None = None
    if journal is not None:
        bound = venues(journal, boot_epoch) if callable(venues) else venues
        runtime = Runtime(
            context,
            journal,
            bound or {},
            machine=machine,
            build=BUILD,
            clock_ns=clock_ns,
            steady_ns=monotonic_ns,
            sleep=sleep,
            boot_epoch_id=boot_epoch,
        )
        waker.append(runtime)
        if made is not None:
            made.attach(runtime, journal, tag=standing.tag, machine=machine, boot_epoch=boot_epoch)

    def alarms() -> Senders:
        return attach(
            store,
            standing.tag,
            keys(),
            open_at=market_hours(store),
            clock_ns=clock_ns,
            steady_ns=monotonic_ns,
        )

    node = Node(context, journal, runtime, alarms)
    nodes.append(node)
    return node


LIVE_STAGE: Final = "live"
ENDPOINTS: Final = Path("venues") / "endpoints.json"
"""A conformance binding's endpoints in ``data/``: a fake cTrader on this machine. Every host it
names must be loopback, so it can never reach a broker."""
LOOPBACK: Final = frozenset({"127.0.0.1", "::1", "localhost"})
SELF_TEST_MARKET: Final[tuple[str, str]] = ("fx.eurusd", "EURUSD")
"""`[node] self_test_market`: the market id and cTrader symbol the self-test trades."""
SELF_TEST_STOP_POINTS: Final = 500
"""`[node] self_test_stop_points`, starting at 500 points (50 pips on a 5-digit pair): the
test trade's stop distance."""
SELF_TEST_FRESH_NS: Final = 60_000_000_000
"""`[node] self_test_fresh_s`, starting at 60 s: the newest quote is fresh within this."""
KILL_LATENCY_OK_MS: Final = 2_000
"""`[node] kill_latency_ok_ms`, starting at 2,000 ms: the test trade's reduce-only close, the
kill switch's own act, answers within this. A labelled placeholder for the risk session."""
SIGNED_IN: Final = "signed_in"
GRANT_KEPT: Final = "grant.ctrader.kept"
"""The node's own record that it kept a cTrader grant; the grant store is read only after."""

DoorFactory: TypeAlias = "Callable[[Store, Path], CTraderDoor]"


@dataclass(frozen=True, slots=True)
class Endpoints:
    """Where the node's cTrader calls go: cTrader itself, or a loopback fake."""

    open_api: tuple[str, int] = (DEMO_HOST, 5035)
    tls: bool = True
    token_url: str = TOKEN_URL


def endpoints(data: Path) -> Endpoints:
    """cTrader's own endpoints, unless ``data/venues/endpoints.json`` names a fake on this
    machine; a file that names any other host is ignored."""
    try:
        found: object = json.loads((data / ENDPOINTS).read_text("utf-8"))
    except (OSError, ValueError):
        return Endpoints()
    item = cast(dict[str, object], found) if isinstance(found, dict) else {}
    host, port, token = item.get("host"), item.get("port"), item.get("token_url")
    if not isinstance(host, str) or not isinstance(port, int) or not isinstance(token, str):
        return Endpoints()
    if host not in LOOPBACK or (urlsplit(token).hostname or "") not in LOOPBACK:
        return Endpoints()
    return Endpoints((host, port), False, token)


def _image_digest() -> str | None:
    """The installed image the node runs from: the supervisor names each app environment by
    its definition hash. None when the node does not run from an installed image."""
    name = Path(sys.prefix).name
    return name if re.fullmatch(r"[0-9a-f]{64}", name) else None


def _iso(at_ns: int) -> str:
    return datetime.fromtimestamp(at_ns / 1e9, UTC).isoformat()


def _check(name: str, passed: bool, value: Json, at: str) -> Json:
    return {"name": name, "ok": passed, "value": value, "at": at}


@dataclass
class CTraderDoor:
    """The node's cTrader sign-in, its demo bindings and its self-test (Part C AD-306)."""

    store: Store
    data: Path
    keys: Callable[[], str | None]
    """The keys document: the supervisor's ``NODE_KEYS``. The node never reads a key store."""
    grants: Grants
    endpoint: TokenEndpoint
    open_wire: Callable[[str], Result[Wire]]
    codec: Callable[[], Result[Codec]]
    clock_ns: Callable[[], int]
    steady_ns: Callable[[], int]
    host: str = DEMO_HOST
    image_digest: Callable[[], str | None] = _image_digest
    bar_ns: int = BAR_NS
    runtime: Runtime | None = None
    journal: JournalWriter | None = None
    tag: str = ""
    machine: str = "local"
    boot_epoch: str = ""
    redirect: str = REDIRECT
    bound: dict[str, CTraderVenue] = field(default_factory=dict[str, CTraderVenue])
    _app: Registration | None = None
    _codes: dict[str, Answer] = field(default_factory=dict[str, Answer])
    _market: JournalWriter | None = None
    _refreshed: str | None = None

    def __post_init__(self) -> None:
        self._app = registration(self.keys())

    @classmethod
    def compose(
        cls,
        store: Store,
        data: Path,
        *,
        keys: Callable[[], str | None],
        facts: Path,
        clock_ns: Callable[[], int],
        steady_ns: Callable[[], int],
        endpoints: Endpoints,
        grant_store: GrantStore | None = None,
        fetch: Fetch | None = None,
        definitions: Path = DEFINITIONS,
        image_digest: Callable[[], str | None] = _image_digest,
    ) -> CTraderDoor:
        """The door over this machine's stores. The grant store is named by the node's tag,
        which the identity holds before any door is made."""
        identity = store.identity()
        tag = "" if identity is None else identity.install_id[:TAG_LENGTH]
        host, port = endpoints.open_api
        endpoint = TokenEndpoint(fetch=fetch or urllib_fetch, token_url=endpoints.token_url)
        return cls(
            store=store,
            data=data,
            keys=keys,
            grants=Grants(
                grant_store or grant_store_for(data, tag),
                endpoint,
                lambda: trading_profile(facts),
                clock_ns,
                stored=lambda: store.observed(GRANT_KEPT) is True,
                remember=lambda kept: store.observe(GRANT_KEPT, kept, clock_ns()),
            ),
            endpoint=endpoint,
            open_wire=lambda _host: FramedWire.open(host, port=port, tls=endpoints.tls),
            codec=lambda: Codec.load(definitions),
            clock_ns=clock_ns,
            steady_ns=steady_ns,
            image_digest=image_digest,
        )

    def attach(
        self, runtime: Runtime, journal: JournalWriter, *, tag: str, machine: str, boot_epoch: str
    ) -> None:
        """Hand the door the runtime it binds into, then bind again every account he kept
        bound, so a restart trades where it traded."""
        self.runtime, self.journal = runtime, journal
        self.tag, self.machine, self.boot_epoch = tag, machine, boot_epoch
        for account in self._kept():
            self._bind(account)

    # --- the four operations -----------------------------------------------------------

    def begin(self, redirect: str | None) -> Answer:
        app = self._app
        if app is None:
            return _not_set_up()
        self.redirect = redirect or REDIRECT
        return ok(
            {"url": self.endpoint.consent_link(app, self.redirect), "expires_in": CONSENT_EXPIRES_S}
        )

    def code(self, op_id: str, code: str) -> Answer:
        earlier = self._codes.get(op_id)
        if earlier is not None:
            return earlier
        answer = self._exchange(code)
        self._codes[op_id] = answer
        return answer

    def _exchange(self, code: str) -> Answer:
        app = self._app
        if app is None:
            return _not_set_up()
        now = self.clock_ns()
        tokens = self.endpoint.exchange(app, code, self.redirect, now)
        if is_refusal(tokens):
            return refused(
                "sign_in_refused", f"cTrader refused the code ({tokens.context.get('code')})"
            )
        listing = self._listing(app, tokens.value.access.reveal())
        if is_refusal(listing):
            return refused(
                "sign_in_refused",
                f"the grant's accounts could not be read ({listing.context.get('code')})",
            )
        accounts = tuple(
            GrantAccount(ctid, live, login, broker)
            for ctid, live, login, broker in listing.value.accounts
        )
        grant = Grant(app.client_id, tokens.value, listing.value.scope, accounts, now)
        listed: list[Json] = [
            {"account": str(item.ctid), "is_live": item.is_live} for item in accounts
        ]
        kept = self.grants.keep(grant)
        if is_refusal(kept):
            if kept.context.get("code") == LIVE_GRANT_CODE:
                return ok({"accounts": listed, "kept": False, "reason": LIVE_GRANT_MESSAGE})
            return refused("grant_not_stored", str(kept.context.get("reason")))
        return ok({"accounts": listed, "kept": True})

    def _listing(self, app: Registration, access: str) -> Result[Listing]:
        codec = self.codec()
        if is_refusal(codec):
            return codec
        wire = self.open_wire(self.host)
        if is_refusal(wire):
            return wire
        try:
            api = OpenApi(codec.value, wire.value, self.steady_ns)
            return account_listing(api, app.client_id, app.client_secret.reveal(), access)
        finally:
            wire.value.close()

    def bind(self, account: Mapping[str, Json], action: str) -> Answer:
        if self._app is None:
            return _not_set_up()
        account_id = str(account.get("id"))
        if action == "remove":
            self._unbind(account_id)
            return ok({"world": "demo", "state": "removed"})
        return self._bind(account)

    def _bind(self, account: Mapping[str, Json]) -> Answer:
        account_id = str(account.get("id"))
        given = account.get("ctid")
        ctid = (
            given if isinstance(given, int) else (int(account_id) if account_id.isdigit() else None)
        )
        if ctid is None:
            return refused("bad_argument", "bind: account.ctid names the cTrader account number")
        venue_name = account.get("venue")
        if not isinstance(venue_name, str) or not venue_name:
            return refused(
                "bad_argument", "bind: account.venue names the venue as its instrument records do"
            )
        grant = self.grants.held()
        if grant is None:
            return refused(
                "not_signed_in",
                "the node holds no cTrader grant",
                next_step="Sign in on cTrader's own page from the node's card first.",
            )
        listed = grant.account(ctid)
        if listed is None:
            return refused(
                "account_not_in_grant", f"the grant does not reach cTrader account {ctid}"
            )
        stopped = CTraderVenue.refusal(
            host=self.host, is_live=listed.is_live, role=AccountRole.DEMO
        )
        if stopped is not None:
            return refused(str(stopped.context["code"]), str(stopped.context["reason"]))
        if account_id in self.bound:
            return ok({"world": "demo", "state": "bound"})
        codec = self.codec()
        runtime, journal = self.runtime, self.journal
        if is_refusal(codec):
            return refused(
                "definitions_missing", "the pinned cTrader definitions could not be read"
            )
        if runtime is None or journal is None:
            return refused("not_available", "the node's runtime is not running")
        bound_account = Account(account_id, VenueId(venue_name), AccountRole.DEMO)
        venue = CTraderVenue(
            account=bound_account,
            ctid=ctid,
            host=self.host,
            markets=self._markets(),
            codec=codec.value,
            open_wire=self.open_wire,
            credentials=self._credentials,
            clock_ns=self.clock_ns,
            steady_ns=self.steady_ns,
            session_epoch=f"{self.boot_epoch}-{account_id}",
            bar_ns=self.bar_ns,
        )
        venue.renew = self._renew
        feed = FeedKeeper(
            "ctrader",
            "demo",
            venue,
            tuple(venue.markets),
            self.clock_ns,
            Recording.open(self.data / "journal", self._market_writer()),
        )
        self.bound[account_id] = venue
        runtime.venues = {**runtime.venues, account_id: Venue(venue, feed)}
        return ok({"world": "demo", "state": "bound"})

    def _unbind(self, account_id: str) -> None:
        venue = self.bound.pop(account_id, None)
        if self.runtime is not None:
            self.runtime.venues = {k: v for k, v in self.runtime.venues.items() if k != account_id}
        if venue is not None:
            venue.close()

    def self_test(self, account: str) -> Answer:
        venue = self.bound.get(account)
        if self._app is None:
            return _not_set_up()
        if venue is None or self.runtime is None:
            return refused("not_bound", f"account {account} is not bound on this node")
        feed = self.runtime.venues[account].feed
        venue.jobs.append(lambda: self._self_test(account, venue, feed))
        self.runtime.wake()
        return ok({"state": "accepted"})

    def rotate_keys(self) -> Answer:
        """Read the keys document again, as the alarm senders do. The supervisor hands the node
        its keys when it starts it, so a document changed since reaches the node at its next
        start, which the connect dialog makes once the node is safe to restart."""
        self._app = registration(self.keys())
        return ok({"state": "accepted"})

    def records(self, account: str, symbols: Sequence[str]) -> Answer:
        """A bound account's facts and each named symbol's, read on a fresh session beside the
        bound one. The account's world is cTrader's live flag for it, never the binding's."""
        if self._app is None:
            return _not_set_up()
        kept = next((item for item in self._kept() if item["id"] == account), None)
        if kept is None:
            return refused("not_bound", f"account {account} is not bound on this node")
        given = self._credentials()
        if given is None:
            return refused(
                "not_signed_in",
                "the node holds no usable cTrader grant",
                next_step="Sign in on cTrader's own page from the node's card first.",
            )
        codec, wire = self.codec(), self.open_wire(self.host)
        if is_refusal(codec):
            return refused(
                "definitions_missing", "the pinned cTrader definitions could not be read"
            )
        if is_refusal(wire):
            return refused("venue_unreachable", "the cTrader session did not open")
        api = OpenApi(codec.value, wire.value, self.steady_ns)

        def ask(name: str, values: Mapping[str, object]) -> Result[Mapping[str, object]]:
            answered = api.ask(name, values)
            return answered if is_refusal(answered) else Ok(answered.value.body)

        client_id, client_secret, access = given
        ctid = kept.get("ctid")
        try:
            facts = read_venue_facts(
                ask,
                client_id=client_id,
                client_secret=client_secret,
                access=access,
                ctid=ctid if isinstance(ctid, int) else int(account),
                names=symbols,
            )
        finally:
            wire.value.close()
        if is_refusal(facts):
            return refused(
                "venue_refused",
                f"cTrader did not answer the records read: {facts.context.get('reason')}",
            )
        identity = self.store.identity()
        return ok(
            _records_answer(
                facts.value,
                account=account,
                venue=str(kept.get("venue")),
                owner=None
                if identity is None
                else {"install_id": identity.install_id, "tag": self.tag},
                at=_iso(self.clock_ns()),
            )
        )

    # --- the self-test, on the runtime thread ---------------------------------------------

    def _self_test(self, account: str, venue: CTraderVenue, feed: FeedKeeper) -> None:
        now = self.clock_ns()
        at = _iso(now)
        market, _ = SELF_TEST_MARKET
        quote = feed.quote(market)
        age_ms = None if quote is None else (now - quote.receive_time) // 1_000_000
        target = Target.fold(self.store.accepted())
        level = max(
            (target.level_at("all"), target.level_at(f"account:{account}")),
            key=lambda held: LEVEL_RANK[held],
        )
        paused = target.paused.get("all") or target.paused.get(f"account:{account}")
        trade = (
            TestTrade(False, f"the kill switch is at {level.value} or entries are paused")
            if level is not KsaLevel.GREEN or paused
            else self._test_trade(venue, market)
        )
        digest = self.image_digest()
        checks: list[Json] = [
            _check("broker session", venue.ready, venue.reason, at),
            _check(
                "feed freshness",
                age_ms is not None and age_ms * 1_000_000 <= SELF_TEST_FRESH_NS,
                age_ms,
                at,
            ),
            _check(
                "demo test trade with its stop placed, observed and closed",
                trade.ok,
                {
                    "detail": trade.detail,
                    "stop": None if trade.stop is None else str(trade.stop),
                    "entry": None if trade.entry is None else str(trade.entry),
                    "exit": None if trade.exit is None else str(trade.exit),
                },
                at,
            ),
            _check(
                "kill-switch latency",
                trade.close_ms is not None and trade.close_ms <= KILL_LATENCY_OK_MS,
                trade.close_ms,
                at,
            ),
            _check("image digest", digest is not None, digest, at),
        ]
        self.store.observe(
            "passport.self_test", {"account": account, "checks": checks, "at": at}, now
        )

    def _test_trade(self, venue: CTraderVenue, market: str) -> TestTrade:
        at_ms = self.clock_ns() // 1_000_000
        name = f"q{self.tag}-{ulid(at_ms, f'self-test/{self.boot_epoch}/{at_ms}')}"
        tags = order_tags(name, f"qmx:{self.tag}:self-test")
        journal = self.journal
        if is_refusal(tags) or journal is None:
            return TestTrade(False, "the test trade's tags could not be built")

        def note(step: str, body: Mapping[str, object]) -> None:
            journal.append(
                "order",
                {"event_id": f"{name}/{step}", "client_order_id": name, "step": step, **body},
                RowFacts(ts_recv=self.clock_ns(), clock_ok=False),
            )

        return venue.test_trade(market, tags.value, stop_points=SELF_TEST_STOP_POINTS, journal=note)

    # --- reads -------------------------------------------------------------------------

    def sessions(self, observed: list[Json]) -> list[Json]:
        rows: list[Json] = []
        for venue, environment in VENUES:
            row: dict[str, Json] = {
                "venue": venue,
                "environment": environment,
                "session": "not_set_up",
                "since": None,
                "last_contact": None,
            }
            if venue == "ctrader":
                row.update(self._ctrader(observed))
            rows.append(row)
        return rows

    def _ctrader(self, observed: list[Json]) -> dict[str, Json]:
        if self._app is None:
            return {"session": "not_set_up"}
        grant = self.grants.held()
        if grant is None:
            return {"session": "signed_out"}
        if grant.expired(self.clock_ns()):
            return {"session": "expired"}
        shown: dict[str, Json] = {
            "session": SIGNED_IN,
            "grant": {
                "scope": grant.scope,
                "expires_at": _iso(grant.tokens.expires_at_ns)
                if grant.tokens.expires_at_ns
                else None,
            },
            "accounts": cast(Json, sorted(self.bound)),
        }
        for row in observed:
            found = cast(dict[str, Json], row) if isinstance(row, dict) else {}
            if found.get("venue") == "ctrader" and self.bound:
                shown.update(
                    {
                        "session": found.get("session"),
                        "reason": found.get("reason"),
                        "last_contact": found.get("last_contact_ns"),
                    }
                )
        return shown

    def passport(self) -> dict[str, Json]:
        landed = self.store.observed("passport.self_test")
        held = cast(dict[str, Json], landed) if isinstance(landed, dict) else {}
        grant = self.grants.held() if self._app is not None else None
        grants: list[Json] = (
            []
            if grant is None
            else [
                {
                    "venue": "ctrader",
                    "expires_at": _iso(grant.tokens.expires_at_ns)
                    if grant.tokens.expires_at_ns
                    else None,
                }
            ]
        )
        return {"checks": held.get("checks") or [], "grants": grants, "at": held.get("at")}

    # --- the grant behind a session ----------------------------------------------------

    def _credentials(self) -> tuple[str, str, str] | None:
        app = self._app
        grant = self.grants.held()
        if app is None or grant is None:
            return None
        if grant.due(self.clock_ns()):
            refreshed = self.grants.refresh(app)
            if not is_refusal(refreshed):
                grant = refreshed.value
            elif self.grants.held() is not None:
                grant = cast(Grant, self.grants.held())
        if grant.expired(self.clock_ns()):
            return None
        return app.client_id, app.client_secret.reveal(), grant.tokens.access.reveal()

    def _renew(self) -> str | None:
        """A refreshed access token for a bound session, when its grant fell due."""
        app = self._app
        grant = self.grants.held()
        if app is None or grant is None or not grant.due(self.clock_ns()):
            return None
        refreshed = self.grants.refresh(app)
        if is_refusal(refreshed):
            held = self.grants.held()
            return (
                None if held is None or held.tokens == grant.tokens else held.tokens.access.reveal()
            )
        return refreshed.value.tokens.access.reveal()

    def _kept(self) -> list[Mapping[str, Json]]:
        """Each account whose newest accepted ``bind`` added it, as his snapshot gave it."""
        latest: dict[str, Mapping[str, Json]] = {}
        for change in self.store.accepted():
            if change.kind == "bind":
                latest[str(change.args["account"])] = change.args
        return [
            {"id": account, **{key: args[key] for key in ("ctid", "venue") if key in args}}
            for account, args in latest.items()
            if args.get("action") == "add"
        ]

    def _markets(self) -> dict[str, str]:
        """The self-test's market, then each market a kept deployment chose, by symbol. A
        deployment the node refused keeps its markets: a position it left open is still the
        session's to name, and R21's kill reaches it by that name."""
        markets: dict[str, str] = {SELF_TEST_MARKET[0]: SELF_TEST_MARKET[1]}
        for change in Target.fold(self.store.accepted()).deployments.values():
            document = change.args.get("document")
            if not isinstance(document, dict):
                continue
            unit = document.get("unit_document")
            traded = unit.get("markets") if isinstance(unit, dict) else None
            by_market = {
                str(item.get("market_id")): cast("dict[str, Json]", item.get("instrument_ref")).get(
                    "symbol"
                )
                for item in (cast("list[Json]", traded) if isinstance(traded, list) else [])
                if isinstance(item, dict) and isinstance(item.get("instrument_ref"), dict)
            }
            chosen = document.get("markets")
            for item in cast("list[Json]", chosen) if isinstance(chosen, list) else []:
                market = cast("dict[str, Json]", item) if isinstance(item, dict) else {}
                market_id = market.get("market_id")
                symbol = by_market.get(str(market_id))
                if isinstance(market_id, str) and isinstance(symbol, str):
                    markets.setdefault(market_id, symbol)
        return markets

    def _market_writer(self) -> JournalWriter | None:
        if self._market is None:
            scope = WriterScope(JournalStream.MARKET, self.tag, WORLD, self.machine, ROLE, BUILD)
            opened = JournalWriter.open(
                self.data / "journal", scope, clock=self.clock_ns, boot_epoch_id=self.boot_epoch
            )
            self._market = None if is_refusal(opened) else opened.value
        return self._market


def _not_set_up() -> Answer:
    return refused("not_set_up", "no venue is set up on this node yet", next_step=NOT_SET_UP)


def _records_answer(
    facts: VenueFacts, *, account: str, venue: str, owner: Json, at: str
) -> dict[str, Json]:
    """The ``records`` answer: cTrader's facts in its own units, volumes in cents of the base
    unit and leverage as a ratio, for the host to map onto its record kinds."""
    trader = facts.trader
    row: dict[str, Json] = {
        "id": account,
        "ctid": facts.account.ctid,
        "world": "live" if facts.account.is_live else "demo",
        "broker": trader.broker
        if trader is not None and trader.broker
        else facts.account.broker_title,
        "grant_scope": facts.grant_scope,
        "owner": owner,
    }
    if trader is not None:
        row["position_mode"] = trader.position_mode
        row["base_currency"] = facts.assets.get(trader.deposit_asset_id)
        row["leverage"] = None if trader.leverage is None else f"{trader.leverage.normalize():f}"
    return {
        "schema_version": "qmx.node.records/1",
        "venue": {"name": venue, "platform": "ctrader", "sandbox": "demo"},
        "account": row,
        "instruments": [
            {
                "symbol": symbol.name,
                "symbol_id": symbol.symbol_id,
                "quote_currency": None
                if symbol.quote_asset_id is None
                else facts.assets.get(symbol.quote_asset_id),
                "digits": symbol.digits,
                "pip_position": symbol.pip_position,
                "lot_size": symbol.lot_size,
                "step_volume": symbol.step_volume,
                "min_volume": symbol.min_volume,
                "max_volume": symbol.max_volume,
                "schedule_zone": symbol.schedule_zone,
                "trading_mode": symbol.trading_mode,
            }
            for symbol in facts.symbols
        ],
        "missing": list(facts.missing),
        "at": at,
    }


def from_environment() -> Node:
    """The node the supervisor started: its ``data/`` from ``QMX_DATA_DIR``, its machine from
    the host facts the host wrote into the volume (C-05c), and this machine's fingerprint. Its
    alarm senders and its cTrader door read the one keys document in ``NODE_KEYS`` (C-18), and
    the senders follow the shipped market calendars (C-30).

    Only a node whose ``QMX_STAGE`` is the road's ``live`` stage gets its cTrader door: its
    trading app from ``NODE_KEYS``, its grant from this machine's store, and each account he
    bound. Under ``QMX_STAGE=shadow`` (and the tests and sandbox stages), or with no stage at
    all, the node reads no grant and binds nothing, so a proof run on a copied volume never
    opens a venue session. The supervisor always names the stage."""
    data = Path(os.environ["QMX_DATA_DIR"])
    volume = Path(os.environ.get("QMX_VOLUME") or data.parent)
    machine = "local"
    try:
        facts: object = json.loads((volume / HOST_FACTS).read_text("utf-8"))
        placement = (
            cast(dict[str, object], facts).get("placement") if isinstance(facts, dict) else None
        )
        if isinstance(placement, str) and placement:
            machine = placement
    except (OSError, ValueError):
        pass
    initial = os.environ.get("NODE_KEYS")

    def keys() -> str | None:
        return initial

    door: DoorFactory | None = None
    if os.environ.get("QMX_STAGE") == LIVE_STAGE:
        where = endpoints(data)
        door = partial(
            CTraderDoor.compose,
            keys=keys,
            facts=volume / HOST_FACTS,
            clock_ns=time.time_ns,
            steady_ns=time.monotonic_ns,
            endpoints=where,
            # A loopback fake's grant is no credential, so it stays out of the machine's store.
            grant_store=None if where.tls else GrantFile(data / "grants" / "ctrader.json"),
        )
    node = open_node(data, here=machine_fingerprint(), machine=machine, door=door, keys=keys)
    node.start()
    return node
