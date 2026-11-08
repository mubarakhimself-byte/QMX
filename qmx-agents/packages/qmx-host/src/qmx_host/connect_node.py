"""The trading-node kinds of the connect dialog, on This PC and on a server (Part C AD-316, Level 0
AD-37 and AD-45): one click sets the node and the MIS up, and the sign-ins come later (rulings 35
and 37).

The steps run on the shipped step runner (`qmx_host.connect.run_kind`), in `NODE.md` section 11's
order: the cTrader trading-app request, the keys document, the clock, install, his signature,
enable, the sign-in, the round trip to each venue, the self-test, the passport and the place row
last. Two of them wait on something outside QMX: Spotware approving the machine's trading app,
which takes about a day (TN-31), and his demo sign-in, which is his and which the build never
runs. A waiting step does not end the run: it holds its card, the steps that need it say they
wait, every other step runs, and the run ends on the first card still waiting. So the node is
installed, started and in his machines while cTrader still has his request.

On a server the shipped server kind's cards and checked steps run first (`connect_compute.SERVER`:
the firewall with its undo, Tailscale, `qmx-recover`, the host), then chrony and OpenObserve on
the server's Tailscale address, and the node's own steps against the server host's loopback
routes over SSH. His trading app's keys and his signature are typed in windows on the server, so
neither reaches This PC; the round trip and the clock are measured on the server.

Every step checks what is in place before it acts, so a rerun after a kill at any step ends with
the same node and one place row listing the apps homed there: This PC's `[engine.placement.pc]`,
or the server's own row.

The phone alarms are their own kind, so he can name or change a destination at any time: one
card for his ntfy topic and one for his Healthchecks.io check. Each proves what he wrote with one
test send before it lands in the keys document's `alarms`, which the node reads at its start.
"""

from __future__ import annotations

import json
import os
import shlex
import socket
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Protocol, cast
from urllib.parse import urlsplit

from pydantic import ValidationError
from qmx_apps.errors import AppError, Document
from qmx_apps.road.models import STAGES, Stage
from qmx_control import node
from qmx_engine.admission import setting
from qmx_engine.heartbeat import ClockFacts
from qmx_engine.ports.settings import flatten

from qmx_host.clock_probe import SOURCES, clock_line, probe_from
from qmx_host.connect import Card, Kind, Run, Step
from qmx_host.connect_compute import SERVER, server_of
from qmx_host.connect_compute import ports as compute_ports
from qmx_host.connect_logs import MISSING_PROGRAMS, monitor, monitoring_on
from qmx_host.jobs import Stopped
from qmx_host.venue_records import Call as NodeCall
from qmx_host.venue_records import bound_accounts, read_and_land, said, self_test_passed

if TYPE_CHECKING:
    from qmx_apps.supervisor import Supervisor

NODE_APP: Final = "trading-node"
NODE_KEYS: Final = "qmx/trading-node-keys"
"""The node's one declared secret (`apps/trading-node/app.toml`), the keys document of Part C
`CONTRACTS.md` section 5. Its value is never shown or logged."""
KEYS_SCHEMA: Final = "qmx.node.keys/1"
APP_SECRET: Final = "qmx/node-ctrader-app-secret"  # noqa: S105 - an entry name, not a secret
"""Where he writes this PC's trading app's Client secret through the key route. The keys step
folds it into the keys document and deletes it. It sits under `qmx/node-`, which no app other
than the trading node may name (`qmx_apps.manifest`, C-10)."""
APPS_PAGE: Final = "https://openapi.ctrader.com/apps"
"""Spotware's Open API applications page, where a trading app is asked for and approved."""
PLACE: Final = "pc"
"""The place row This PC's practice node is homed in (Part C `NETWORKING.md` section 2)."""
PASSPORT: Final = "trading-node-passport.json"
"""The passport the setup lands in this QMX folder's data, beside the node link's outbox."""
PASSPORT_SCHEMA: Final = "qmx.node.passport/1"
HANDSHAKES: Final = 8.0
"""`[engine] node_setup.handshakes`: TCP handshakes per venue for the round trip (TN-32)."""
HANDSHAKE_TIMEOUT_S: Final = 5.0
"""`[engine] node_setup.handshake_timeout_s`: how long one handshake may take before it counts as
not answered."""
MIS_APP: Final = "mis"
APPS_DIR: Final = Path(__file__).resolve().parents[4] / "apps"
APP_FOLDERS: Final[Mapping[str, Path]] = {app: APPS_DIR / app for app in (NODE_APP, MIS_APP)}
"""The apps the setup installs, starts and homes on the node's machine, as this program ships
them: the trading node and the MIS beside it."""
SELF_TEST_CHECKS: Final = (
    "broker session",
    "feed freshness",
    "demo test trade with its stop placed, observed and closed",
    "kill-switch latency",
    "image digest",
)
"""The self-test's checks that need a demo binding (Part C `CONTRACTS.md` section 4). The clock
band and the disk are checked by the setup itself."""


@dataclass(frozen=True, slots=True)
class Venue:
    """One venue the round trip is measured to: its name, environment and handshake address."""

    name: str
    environment: str
    host: str
    port: int


VENUES: Final = (
    Venue("ctrader", "demo", "demo.ctraderapi.com", 5035),
    Venue("hyperliquid", "testnet", "api.hyperliquid-testnet.xyz", 443),
)


def handshake(host: str, port: int, timeout: float) -> float:
    """One TCP handshake with `host`, in ms. Raises `OSError` when it does not answer."""
    began = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout):
        return (time.perf_counter() - began) * 1000


class RoadPort(Protocol):
    """The road calls the setup makes: the supervisor's road here, a server's over SSH."""

    def active_revision(self, app_id: str) -> str | None: ...

    def publish(
        self,
        app_id: str,
        expected_hash: str,
        expected_active: str | None = None,
        signature: str | None = None,
    ) -> Document: ...

    def advance(self, app_id: str, expected_hash: str, stage: Stage | None = None) -> Document: ...


class AppsPort(Protocol):
    """The supervisor calls the setup makes on the node's machine: This PC's own supervisor, or
    a server host's, reached over SSH on its loopback (`ServerApps`)."""

    @property
    def road(self) -> RoadPort: ...

    def get(self, app_id: str) -> Document: ...

    def status(self, app_id: str) -> Document: ...

    def start(self, app_id: str) -> Document: ...

    def restart(self, app_id: str) -> Document: ...

    def call(self, app_id: str, tool: str, arguments: Document) -> Document: ...


def road_proof(apps: AppsPort, app: str, definition_hash: str) -> None:
    """Advance `definition_hash` through each road stage it has not passed: tests, sandbox and
    shadow, each the road's own proof."""
    while (stage := _stage(apps, app)) not in {"shadow", "live"}:
        apps.road.advance(app, definition_hash, STAGES[STAGES.index(stage or "build") + 1])


@dataclass(frozen=True, slots=True)
class Ports:
    """What the setup reaches beyond the QMX folder. Tests and lanes pass stand-ins."""

    apps: Mapping[str, Path] = field(default_factory=lambda: dict(APP_FOLDERS))
    prove: Callable[[Supervisor, str, str], None] = road_proof
    clock: Callable[[Mapping[str, object]], ClockFacts] = probe_from
    venues: Sequence[Venue] = VENUES
    handshake: Callable[[str, int, float], float] = handshake
    now: Callable[[], float] = time.time


@dataclass(frozen=True, slots=True)
class Setup:
    """One step of the setup. A `waiting` step's card does not end the run; `after` names the
    steps this one needs done first, and while one of them waits this one waits too."""

    step: Step
    waiting: bool = False
    after: tuple[str, ...] = ()


WAITING: Final = "waiting"
"""The runner step after the place row: it ends the run on the first card still waiting."""


def on_runner(setups: Sequence[Setup]) -> tuple[Step, ...]:
    """The setup as the shipped runner's steps: a waiting step keeps its card in the run's facts
    and lets the run go on, a step after a step not done says what it waits for and is not done
    either, and the last step answers the first card still waiting."""

    def held(run: Run) -> dict[str, Card | None]:
        """The steps not done in this run, by name: a waiting step's card, or None for a step
        that waits on another."""
        return cast("dict[str, Card | None]", run.facts.setdefault(WAITING, {}))

    def placed(setup: Setup) -> Step:
        name, who, check, do = setup.step

        def blocked(run: Run) -> list[str]:
            return [after for after in setup.after if after in held(run)]

        def checked(run: Run) -> bool:
            return not blocked(run) and check(run)

        def done(run: Run) -> Card | None:
            waits = blocked(run)
            if waits:
                held(run)[name] = None
                run.say(f"{name}: waits for {', '.join(waits)}")
                return None
            card = do(run)
            if card is None or not setup.waiting:
                return card
            held(run)[name] = card
            run.say(f"{name}: waiting; {card.line}")
            return None

        return Step(name, who, checked, done)

    def cards(run: Run) -> list[Card]:
        return [card for card in held(run).values() if card is not None]

    def nothing_waits(run: Run) -> bool:
        return not cards(run)

    def first_waiting(run: Run) -> Card:
        return cards(run)[0]

    return (*(placed(s) for s in setups), Step(WAITING, "his", nothing_waits, first_waiting))


# What the steps share.


def _supervisor(run: Run) -> Supervisor:
    control = run.world.control
    if control is None:
        raise Stopped("a trading node is set up from a running QMX, not the first-start card")
    return control.app_runtime()


def _on_a_server(run: Run) -> bool:
    return run.kind.id == SERVER_KIND


def _apps(run: Run) -> AppsPort:
    """The supervisor on the node's machine: This PC's, or the server host's over SSH."""
    return server_apps(run) if _on_a_server(run) else _supervisor(run)


def _where(run: Run) -> str:
    return run.place if _on_a_server(run) else "This PC"


def _home(run: Run) -> str:
    """The place row the node's apps are homed in."""
    return run.place if _on_a_server(run) else PLACE


def _engine(run: Run) -> dict[str, object]:
    control = run.world.control
    engine = {} if control is None else control.settings_get(cast("Any", "engine"))
    return dict(flatten(engine, ""))


def _installed(apps: AppsPort, app: str) -> dict[str, Any] | None:
    try:
        return cast("dict[str, Any]", apps.get(app))
    except AppError:
        return None


def _stage(apps: AppsPort, app: str) -> str | None:
    found = _installed(apps, app)
    road = cast("dict[str, Any]", (found or {}).get("road") or {})
    return cast("str | None", road.get("stage"))


def _published(apps: AppsPort, app: str) -> bool:
    found = _installed(apps, app)
    if found is None:
        return False
    active = cast("dict[str, Any]", found.get("road") or {}).get("active")
    if not isinstance(active, dict):
        return False
    return cast("dict[str, Any]", active).get("definition_hash") == found["definition_hash"]


def _ask(run: Run, operation: str) -> dict[str, Any]:
    """One of the node's reads through the supervisor; a refusal stops the run in plain words."""
    try:
        called = _apps(run).call(NODE_APP, operation, {})
    except AppError as error:
        raise Stopped(f"the trading node did not answer {operation}: {error}") from None
    answer = cast("dict[str, Any]", called.get("result") or {})
    if answer.get("ok") is not True:
        raise Stopped(f"the trading node answered {operation} with {answer.get('code')}")
    return cast("dict[str, Any]", answer["value"])


def _keys(run: Run) -> dict[str, Any] | None:
    """The keys document as stored, or None when there is none. One that is not a keys document
    stops the run, because overwriting it would lose what he wrote there."""
    held = run.world.keys.read(NODE_KEYS)
    if held is None:
        return None
    try:
        found = cast("object", json.loads(held))
    except ValueError:
        found = None
    if not isinstance(found, dict) or cast("dict[str, Any]", found).get("schema_version") != (
        KEYS_SCHEMA
    ):
        raise Stopped(
            f"keys: {NODE_KEYS} holds something that is not a {KEYS_SCHEMA} document; remove it "
            "in Credential Manager, then set up the node again"
        )
    return cast("dict[str, Any]", found)


def _pasted(run: Run) -> tuple[str, str] | None:
    """The trading app's id he pasted on the card and its secret he wrote through the key route,
    when both are there and not yet in the keys document."""
    client_id = run.fields().get("client_id")
    secret = run.world.keys.read(APP_SECRET)
    return None if not client_id or not secret else (client_id, secret)


def _app_id(run: Run) -> str | None:
    ctrader = cast("dict[str, Any]", (_keys(run) or {}).get("ctrader") or {})
    found = ctrader.get("client_id")
    return found if isinstance(found, str) and found else None


# The steps, in order.


def _app_known(run: Run) -> bool:
    return _app_id(run) is not None or _pasted(run) is not None


def _app_card(run: Run) -> Card:
    return Card(
        "ctrader-app",
        "Waiting for cTrader to approve your app. Ask cTrader for this PC's own trading app on "
        f"{APPS_PAGE} (Spotware takes about a day). Once it is approved, paste its Client ID "
        f"here and write its Client secret to the key {APP_SECRET}; nothing else waits on it",
        (
            {
                "Name": "client_id",
                "Help": "the Client ID cTrader shows for this PC's trading app",
                "Examples": [],
                "Type": "string",
            },
        ),
        key=APP_SECRET,
        link=APPS_PAGE,
    )


def _keys_written(run: Run) -> bool:
    return _keys(run) is not None and run.world.keys.read(APP_SECRET) is None


def _write_keys(run: Run) -> Card | None:
    """The keys document, empty at first, with the trading app once he has given it. The staged
    secret is deleted whenever the document holds it, so a rerun after a kill between the two
    writes still deletes it, though the pasted id is gone with the host."""
    document = _keys(run) or {"schema_version": KEYS_SCHEMA}
    pasted = _pasted(run)
    if pasted is not None:
        document["ctrader"] = {"client_id": pasted[0], "client_secret": pasted[1]}
    run.world.keys.replace(NODE_KEYS, json.dumps(document, sort_keys=True))
    staged = run.world.keys.read(APP_SECRET)
    ctrader = cast("dict[str, Any]", document.get("ctrader") or {})
    if staged is not None and ctrader.get("client_secret") == staged:
        run.world.keys.delete(APP_SECRET)
    held = "with this PC's cTrader trading app" if "ctrader" in document else "with no venue yet"
    run.say(f"keys: the node's keys document is in Credential Manager as {NODE_KEYS}, {held}")
    _rotate(run)
    return None


def _rotate(run: Run) -> None:
    """A running node is asked to read its keys again (C-11 review L3). The supervisor hands an
    app its keys when it starts it, so the node is restarted once it reads safe to restart; one
    not running yet reads the new document when it starts."""
    apps = _apps(run)
    try:
        running = _installed(apps, NODE_APP) is not None and _running(run)
    except AppError:
        running = False
    if not running:
        return
    try:
        called = apps.call(NODE_APP, "rotate_keys", {})
    except AppError as error:
        raise Stopped(f"keys: the trading node did not take the new keys: {error}") from None
    answer = cast("dict[str, Any]", called.get("result") or {})
    if answer.get("ok") is not True:
        raise Stopped(f"keys: the trading node answered rotate_keys with {answer.get('code')}")
    safe = cast("dict[str, Any]", _ask(run, "status").get("safe_to_restart") or {})
    if safe.get("ok") is not True:
        run.say("keys: the trading node reads its new keys at its next safe restart")
        return
    try:
        apps.restart(NODE_APP)
    except AppError as error:
        raise Stopped(f"keys: the trading node did not restart on its new keys: {error}") from None
    run.say("keys: the trading node restarted on its new keys")


def _never(_run: Run) -> bool:
    return False


def _clock(ports: Ports, run: Run) -> Card | None:
    facts = ports.clock(_engine(run))
    run.facts["clock"] = facts
    line = clock_line(facts)
    run.say(
        f"clock: {line.detail}" + ("" if line.ok else "; the node will not enter on a bad clock")
    )
    return None


def _proved(ports: Ports, run: Run) -> bool:
    apps = _apps(run)
    return all(_stage(apps, app) in {"shadow", "live"} for app in ports.apps)


def _install(ports: Ports, run: Run) -> Card | None:
    apps = _supervisor(run)
    for app, folder in ports.apps.items():
        try:
            found = _installed(apps, app) or cast(
                "dict[str, Any]", apps.install(folder, trust="first_party")
            )
            ports.prove(apps, app, str(found["definition_hash"]))
        except AppError as error:
            raise Stopped(f"install: {app} did not install or pass its proof: {error}") from None
        run.say(f"install: {app} {found['definition']['version']} is installed and proved")
    return None


def _signed(run: Run) -> bool:
    return _published(_apps(run), NODE_APP)


@dataclass(frozen=True, slots=True)
class Unsigned:
    """The node version his signature card is for: its version, hash, the active revision the
    publish replaces, and why he is asked again, if he is."""

    version: str
    definition_hash: str
    active: str | None
    again: str


def _signature_card(line: str, help_text: str) -> Card:
    return Card(
        "signature",
        line,
        ({"Name": "signature", "Help": help_text, "Examples": [], "Type": "string"},),
    )


def _sign_here(_run: Run, asked: Unsigned) -> Card:
    query = f"definition_hash={asked.definition_hash}" + (
        f"&expected_active={asked.active}" if asked.active else ""
    )
    return _signature_card(
        f"Sign the trading node {asked.version} ({asked.definition_hash[:12]}) to publish it on "
        f"This PC; a restart of the signed version needs no new signature.{asked.again}",
        f"what POST /api/apps/{NODE_APP}/sign?{query} answers",
    )


def _sign(card: Callable[[Run, Unsigned], Card], run: Run) -> Card | None:
    """His signature publishes the node's version (`qmx_apps.road`): `card` asks him for what
    the operator-only sign route of the node's machine answers, and his answer is published
    here. Publishing starts the node."""
    apps = _apps(run)
    found = cast("dict[str, Any]", _installed(apps, NODE_APP))
    definition_hash = str(found["definition_hash"])
    active = apps.road.active_revision(NODE_APP)
    signature = run.fields().pop("signature", None)
    again = ""
    if signature:
        try:
            apps.road.publish(NODE_APP, definition_hash, active, signature)
        except AppError as error:
            if error.code != "signature_required":
                raise Stopped(f"signature: the node was not published: {error}") from None
            again = " That signature is not this version's; sign it again."
        else:
            run.say(
                f"signature: trading-node {definition_hash[:12]} is published with your signature"
            )
            return None
    version = str(found["definition"]["version"])
    return card(run, Unsigned(version, definition_hash, active, again))


def _running(run: Run) -> bool:
    return _apps(run).status(NODE_APP).get("status") == "running"


def _all_running(names: Sequence[str], run: Run) -> bool:
    apps = _apps(run)
    return all(apps.status(app).get("status") == "running" for app in names)


def _enable(names: Sequence[str], run: Run) -> Card | None:
    """Start the node and every app beside it that is not running yet; a published node starts
    on its signed version."""
    apps = _apps(run)
    for app in names:
        if apps.status(app).get("status") == "running":
            continue
        try:
            apps.start(app)
        except AppError as error:
            what = "the trading node" if app == NODE_APP else app
            raise Stopped(f"enable: {what} did not start: {error}") from None
    run.say(f"enable: the trading node runs on {_where(run)}")
    others = [app for app in names if app != NODE_APP]
    if others:
        run.say(f"enable: {', '.join(others)} runs beside it")
    return None


def _session(run: Run, venue: str) -> str:
    venues = cast("list[dict[str, Any]]", _ask(run, "status").get("venues") or [])
    return next((str(v.get("session")) for v in venues if v.get("venue") == venue), "not_set_up")


SIGNED_IN: Final = frozenset({"signed_in", "connected", "ready", "down"})
"""The node's cTrader session words that mean it holds a grant it can use. ``not_set_up``,
``signed_out`` and ``expired`` keep the sign-in waiting, so an expired grant never unblocks the
self-test (C-11 review L2)."""


def _signed_in(run: Run) -> bool:
    return _session(run, "ctrader") in SIGNED_IN


def _sign_in_card(_run: Run) -> Card:
    return Card(
        "sign-in",
        "Sign in on cTrader's own page with your demo account when you want this node to trade. "
        "This step waits for you and nothing else waits on it; the node's card starts the "
        "sign-in when you are ready",
    )


Sample = Callable[[Run, Sequence[Venue], int, float], list[list[float]]]
"""Handshakes to each venue from the node's machine: (run, venues, count, timeout) to each
venue's samples in ms, in the venues' order."""


def _round_trip(venues: Sequence[Venue], sample: Sample, run: Run) -> Card | None:
    """`handshakes` TCP handshakes from the node's machine to each venue, with their median and
    spread (TN-32). A venue that does not answer is recorded with no samples and stops nothing."""
    engine = _engine(run)
    count = max(1, int(setting(engine, "node_setup.handshakes", HANDSHAKES)))
    timeout = setting(engine, "node_setup.handshake_timeout_s", HANDSHAKE_TIMEOUT_S)
    rows: list[dict[str, object]] = []
    measured_by = sample(run, venues, count, timeout)
    for venue, samples in zip(venues, measured_by, strict=True):
        median = round(statistics.median(samples)) if samples else None
        spread = round(max(samples) - min(samples)) if samples else None
        rows.append(
            {
                "venue": venue.name,
                "environment": venue.environment,
                "median_ms": median,
                "spread_ms": spread,
                "samples": len(samples),
            }
        )
        measured = (
            f"median {median} ms, spread {spread} ms over {len(samples)} of {count} handshakes"
            if samples
            else f"not reached in {count} handshakes"
        )
        run.say(f"round trip: {venue.name} {venue.environment} {measured}{_from(run)}")
    run.facts["round_trip"] = rows
    return None


def _from(run: Run) -> str:
    return f", measured on {run.place}" if _on_a_server(run) else ""


def handshakes_here(
    handshake: Callable[[str, int, float], float],
    _run: Run,
    venues: Sequence[Venue],
    count: int,
    timeout: float,
) -> list[list[float]]:
    """`count` handshakes from this machine to each venue, in ms; one not answered is left out."""
    measured: list[list[float]] = []
    for venue in venues:
        samples: list[float] = []
        for _ in range(count):
            try:
                samples.append(handshake(venue.host, venue.port, timeout))
            except OSError:
                continue
        measured.append(samples)
    return measured


def _self_test(run: Run) -> Card | None:
    """The self-test's place in the setup. Its checks run on a demo binding through the node's
    `self_test`, which lands them on the passport; this step names them."""
    run.say(f"self-test: on a demo binding the node checks {'; '.join(SELF_TEST_CHECKS)}")
    return None


def _iso(at: float) -> str:
    return datetime.fromtimestamp(at, UTC).isoformat()


def passport_file(place: str) -> str:
    """The passport's file in This PC's QMX folder: This PC's node's, or a server's by name."""
    return PASSPORT if place == PLACE else f"trading-node-passport.{place}.json"


def _passport(now: Callable[[], float], run: Run) -> Card | None:
    """The node's passport with what the setup measured: the round trip, the clock band and the
    disk. It lands in this QMX folder's data, written whole and then moved into place."""
    node = _ask(run, "passport")
    status = _ask(run, "status")
    at = _iso(now())
    facts = cast("ClockFacts | None", run.facts.get("clock"))
    disk = cast("dict[str, Any]", status.get("disk") or {})
    checks = [
        *cast("list[dict[str, object]]", node.get("checks") or []),
        {
            "name": "clock band",
            "ok": facts is not None and facts.band == "ok",
            "value": None if facts is None else facts.band,
            "at": at,
        },
        {
            "name": "disk",
            "ok": int(disk.get("free_bytes") or 0) > int(disk.get("guard_bytes") or 0),
            "value": disk.get("free_bytes"),
            "at": at,
        },
    ]
    passport = {
        **node,
        "schema_version": PASSPORT_SCHEMA,
        "checks": checks,
        "round_trip": run.facts.get("round_trip", []),
        "at": at,
    }
    name = passport_file(_home(run))
    target = run.world.layout.home / name
    part = target.with_suffix(".part")
    part.write_text(json.dumps(passport, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(part, target)
    run.say(f"passport: landed in {name}, node {status['identity'].get('tag')}")
    _land_records(run)
    return None


def _node_call(apps: AppsPort) -> NodeCall:
    """The trading node's operations on its machine; a call its supervisor refuses reads as the
    node's refusal, as `venue_records.node_call` reads one here."""

    def call(operation: str, arguments: Mapping[str, object]) -> Mapping[str, object]:
        try:
            called = apps.call(NODE_APP, operation, cast("Document", dict(arguments)))
        except AppError as error:
            return {"ok": False, "code": error.code, "message": str(error)}
        return cast("Mapping[str, object]", called.get("result") or {})

    return call


def _land_records(run: Run) -> None:
    """Once the node's self-test passed, each bound account's account, venue and instrument
    records land on the Library's main (C-34), so a promote finds them."""
    call = _node_call(_apps(run))
    control = run.world.control
    if control is None or not self_test_passed(call):
        run.say("records: they land on main once the self-test on a bound account passes")
        return
    for account in bound_accounts(call):
        run.say(said(read_and_land(call, control.library.store, account)))


def _apps_here(names: Sequence[str], run: Run) -> list[str]:
    apps = _apps(run)
    return [app for app in names if _installed(apps, app) is not None]


def _row_of(run: Run) -> dict[str, Any]:
    control = run.world.control
    engine = {} if control is None else control.settings_get(cast("Any", "engine"))
    rows = cast("dict[str, Any]", engine.get("placement") or {})
    return cast("dict[str, Any]", rows.get(_home(run)) or {})


def _row_written(names: Sequence[str], run: Run) -> bool:
    listed = cast("list[str]", _row_of(run).get("apps") or [])
    return set(_apps_here(names, run)) <= set(listed)


def _write_row(names: Sequence[str], run: Run) -> Card | None:
    """The node's place row lists the apps homed there, merged inside the settings lock into the
    row as stored, so its other keys (This PC's GPU slots, a server's address) stay."""
    control = run.world.control
    if control is None:
        raise Stopped("a trading node is set up from a running QMX, not the first-start card")
    here = _apps_here(names, run)
    home = _home(run)

    def placed(engine: dict[str, Any]) -> dict[str, Any]:
        rows = dict(cast("dict[str, Any]", engine.get("placement") or {}))
        row = dict(cast("dict[str, Any]", rows.get(home) or {}))
        listed = list(cast("list[str]", row.get("apps") or []))
        row["apps"] = [*listed, *(app for app in here if app not in listed)]
        return {**engine, "placement": {**rows, home: row}}

    control.settings_update(cast("Any", "engine"), cast("Any", placed))
    run.say(f"row: {_where(run)} is home to {', '.join(here)} in your machines")
    return None


def setups(ports: Ports) -> tuple[Setup, ...]:
    """The steps for This PC, in `NODE.md` section 11's order."""
    names = tuple(ports.apps)
    sample = partial(handshakes_here, ports.handshake)
    return (
        Setup(Step("ctrader-app", "his", _app_known, _app_card), waiting=True),
        Setup(Step("keys", "qmx", _keys_written, _write_keys)),
        Setup(Step("clock", "qmx", _never, partial(_clock, ports))),
        Setup(Step("install", "qmx", partial(_proved, ports), partial(_install, ports))),
        Setup(Step("signature", "his", _signed, partial(_sign, _sign_here))),
        Setup(Step("enable", "qmx", partial(_all_running, names), partial(_enable, names))),
        Setup(
            Step("sign-in", "his", _signed_in, _sign_in_card), waiting=True, after=("ctrader-app",)
        ),
        Setup(Step("round-trip", "qmx", _never, partial(_round_trip, ports.venues, sample))),
        Setup(Step("self-test", "qmx", _never, _self_test), after=("sign-in",)),
        Setup(Step("passport", "qmx", _never, partial(_passport, ports.now))),
        Setup(Step("row", "qmx", partial(_row_written, names), partial(_write_row, names))),
    )


def on_this_pc(ports: Ports | None = None) -> Kind:
    """The kind for This PC, over `ports` (the real ones by default)."""
    steps = on_runner(setups(ports or Ports()))
    return Kind("trading-node-pc", "Trading node on This PC", (), False, steps)


# On a server (slice C-17, rulings 27 and 35): the shipped server steps, then the node's own.

SERVER_KIND: Final = "trading-node-server"
SERVER_APPS: Final = "/opt/qmx/qmx-agents/apps"
"""Where the apps sit in the source tree the server steps unpack, which its venv runs from."""
SERVER_KEYS_FILE: Final = f"{node.SERVER_HOME}/vault/{NODE_KEYS.removeprefix('qmx/')}"
"""The server's keys document, which its host's vault reader hands the node as `NODE_KEYS`
(`qmx_host.host.vault_secrets`); owner-only, and written only on the server."""
SERVER_CALL_TIMEOUT_S: Final = 900.0
"""`[engine] node_setup.server_call_timeout_s`: how long one call to the server host's loopback
may take; an install builds the app's environment there."""
CHRONY_CONF: Final = "/etc/chrony/chrony.conf"
CHRONY_STEP: Final = "install chrony"
CHRONY_SOURCES: Final = 4
"""chrony keeps time from four or more sources of one kind (Level 0 AD-43, CK-06)."""
PYTHON: Final = f"{node.SERVER_VENV}/bin/python"

ASK: Final = (
    "import json, sys, urllib.error, urllib.parse, urllib.request\n"
    "port, token = sys.argv[1:]\n"
    "asked = json.load(sys.stdin)\n"
    "with open(token, encoding='utf-8') as held:\n"
    "    bearer = held.read().strip()\n"
    "url = f'http://127.0.0.1:{port}{asked[\"path\"]}'\n"
    "if asked['query']:\n"
    "    url += '?' + urllib.parse.urlencode(asked['query'])\n"
    "body = None if asked['body'] is None else json.dumps(asked['body']).encode()\n"
    "request = urllib.request.Request(url, data=body, method=asked['method'], headers={\n"
    "    'Authorization': f'Bearer {bearer}', 'Content-Type': 'application/json'})\n"
    "try:\n"
    "    with urllib.request.urlopen(request, timeout=asked['timeout']) as answer:\n"
    "        status, text = answer.status, answer.read()\n"
    "except urllib.error.HTTPError as refused:\n"
    "    status, text = refused.code, refused.read()\n"
    "print(json.dumps({'status': status, 'body': json.loads(text or b'null')}))\n"
)
"""One call to the server host's own loopback routes, run there as `qmx` with the bearer the host
keeps in `keys/`, so the host stays the one writer of its apps. The call and its arguments come
on the input, never on a command line."""

KEYS_STATE: Final = (
    "import hashlib, json, os, sys\n"
    "path, ensure = sys.argv[1], sys.argv[2] == 'ensure'\n"
    f"schema = {KEYS_SCHEMA!r}\n"
    "if ensure and not os.path.exists(path):\n"
    "    handle = os.open(path + '.part', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)\n"
    "    with os.fdopen(handle, 'w', encoding='utf-8') as out:\n"
    "        out.write(json.dumps({'schema_version': schema}) + '\\n')\n"
    "    os.replace(path + '.part', path)\n"
    "try:\n"
    "    with open(path, 'rb') as held:\n"
    "        raw = held.read()\n"
    "except FileNotFoundError:\n"
    "    raw = None\n"
    "try:\n"
    "    found = None if raw is None else json.loads(raw)\n"
    "except ValueError:\n"
    "    found = False\n"
    "kept = isinstance(found, dict) and found.get('schema_version') == schema\n"
    "app = found.get('ctrader') if kept else None\n"
    "print(json.dumps({\n"
    "    'document': kept, 'foreign': raw is not None and not kept,\n"
    "    'ctrader': isinstance(app, dict) and bool(app.get('client_id'))\n"
    "    and bool(app.get('client_secret')),\n"
    "    'digest': hashlib.sha256(raw).hexdigest() if kept else ''}))\n"
)
"""What the server's keys document holds, by kind only: whether it is one, whether it names a
cTrader trading app, and a digest that changes when it does. With `ensure`, an empty document is
written first when there is none, owner-only. No value it holds is printed."""

KEYS_WINDOW: Final = (
    "import getpass, json, os, sys\n"
    "path = sys.argv[1]\n"
    'print("QMX: type this server\'s own cTrader trading app. What you type stays on this "\n'
    "      'server; QMX never sees it.')\n"
    "client_id = input('Client ID: ').strip()\n"
    "secret = (getpass.getpass('Client secret: ') if sys.stdin.isatty()\n"
    "          else sys.stdin.readline()).strip()\n"
    "if not client_id or not secret:\n"
    "    print('Nothing was written. Close this window and answer the card to try again.')\n"
    "    raise SystemExit(1)\n"
    f"document = {{'schema_version': {KEYS_SCHEMA!r}}}\n"
    "if os.path.exists(path):\n"
    "    with open(path, encoding='utf-8') as held:\n"
    "        document = json.load(held)\n"
    f"if document.get('schema_version') != {KEYS_SCHEMA!r}:\n"
    "    print('The keys file here is not a QMX keys document; nothing was written.')\n"
    "    raise SystemExit(1)\n"
    "document['ctrader'] = {'client_id': client_id, 'client_secret': secret}\n"
    "handle = os.open(path + '.part', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)\n"
    "with os.fdopen(handle, 'w', encoding='utf-8') as out:\n"
    "    out.write(json.dumps(document, sort_keys=True) + '\\n')\n"
    "os.replace(path + '.part', path)\n"
    "print('Done. Close this window and answer the card in QMX.')\n"
    "if sys.stdin.isatty():\n"
    "    input()\n"
)
"""What his keys window runs on the server as `qmx`: his trading app's id and secret, typed
there, folded into the server's keys document, owner-only. A window that is not a terminal reads
its two lines from its input."""

SIGN_WINDOW: Final = (
    "import json, sys, urllib.parse, urllib.request\n"
    "port, token, app, definition_hash, active, timeout = sys.argv[1:]\n"
    "with open(token, encoding='utf-8') as held:\n"
    "    bearer = held.read().strip()\n"
    "query = {'definition_hash': definition_hash}\n"
    "if active:\n"
    "    query['expected_active'] = active\n"
    "url = f'http://127.0.0.1:{port}/api/apps/{app}/sign?' + urllib.parse.urlencode(query)\n"
    "request = urllib.request.Request(url, data=b'', method='POST',\n"
    "    headers={'Authorization': f'Bearer {bearer}'})\n"
    "with urllib.request.urlopen(request, timeout=float(timeout)) as answer:\n"
    "    signature = json.load(answer)['signature']\n"
    "print(f'Your signature for {app} {definition_hash[:12]} on this server:')\n"
    "print()\n"
    "print(signature)\n"
    "print()\n"
    'print("Paste it in QMX\'s card to publish it, then close this window.")\n'
    "if sys.stdin.isatty():\n"
    "    input()\n"
)
"""What his signature window runs on the server as `qmx`: the server host's operator-only sign
route, which signs with that host's own key, so only the server's road can verify it."""

ROUND_TRIP: Final = (
    "import json, socket, sys, time\n"
    "asked = json.load(sys.stdin)\n"
    "measured = []\n"
    "for venue in asked['venues']:\n"
    "    samples = []\n"
    "    for _ in range(asked['count']):\n"
    "        began = time.perf_counter()\n"
    "        try:\n"
    "            with socket.create_connection((venue['host'], venue['port']),\n"
    "                                          timeout=asked['timeout']):\n"
    "                samples.append((time.perf_counter() - began) * 1000)\n"
    "        except OSError:\n"
    "            continue\n"
    "    measured.append(samples)\n"
    "print(json.dumps(measured))\n"
)
"""The round trip's handshakes, run on the server, so they measure the server's road to each
venue rather than This PC's (TN-32)."""

CLOCK: Final = (
    "import json, sys\n"
    "from qmx_host.clock_probe import probe_from\n"
    "print(probe_from(json.load(sys.stdin)).model_dump_json())\n"
)
"""The shipped clock probe, run on the server with This PC's `[engine]` clock settings, so both
machines prove their clocks the same way (LC-C-22)."""


def as_qmx(script: str, *args: str, given: str | None = None) -> str:
    """A root shell that runs `script` with the server's Python as the user `qmx`, with `given`
    on its input from a quoted heredoc, so no value in it reaches a command line."""
    line = shlex.join(["runuser", "-u", "qmx", "--", PYTHON, "-I", "-c", script, *args])
    if given is None:
        return f"set -eu\n{line}\n"
    return f"set -eu\n{line} <<'QMXIN'\n{given}\nQMXIN\n"


def window_command(server: node.Server, script: str, *args: str) -> list[str]:
    """The ssh command his window on This PC runs: `script` on the server as `qmx`, on a
    terminal there, so what he types goes to the server alone."""
    remote = shlex.join(["sudo", "runuser", "-u", "qmx", "--", PYTHON, "-I", "-c", script, *args])
    return [*server.ssh[:-1], "-t", server.ssh[-1], remote]


def _shell(run: Run, script: str) -> str:
    """`script` as root on the server; a failed run stops the setup with the server named."""
    try:
        return server_of(run).send("sudo bash -s", script)
    except RuntimeError as failed:
        raise Stopped(
            f"{run.place}: the server did not run a setup step ({failed}); check it with: "
            f"sudo {node.RECOVER} status"
        ) from None


def _last_json(said: str) -> Any:
    lines = said.strip().splitlines()
    return json.loads(lines[-1]) if lines else None


@dataclass(frozen=True, slots=True)
class ServerRoad:
    """The server host's road, through its loopback routes."""

    apps: ServerApps

    def active_revision(self, app_id: str) -> str | None:
        road = cast("dict[str, Any]", self.apps.get(app_id).get("road") or {})
        active = road.get("active")
        return str(cast("dict[str, Any]", active)["revision"]) if isinstance(active, dict) else None

    def publish(
        self,
        app_id: str,
        expected_hash: str,
        expected_active: str | None = None,
        signature: str | None = None,
    ) -> Document:
        query = {
            "expected_hash": expected_hash,
            "expected_active": expected_active,
            "signature": signature,
        }
        return self.apps.rest("POST", f"/api/apps/{app_id}/publish", query)

    def advance(self, app_id: str, expected_hash: str, stage: Stage | None = None) -> Document:
        query = {"expected_hash": expected_hash, "stage": stage, "auto_publish": "false"}
        return self.apps.rest("POST", f"/api/apps/{app_id}/test", query)


@dataclass(frozen=True, slots=True)
class ServerApps:
    """The server host's supervisor, reached over SSH on that host's own loopback routes (the
    host route has no install, sign or start verb, `host_route.py`), with the answers and
    refusals its supervisor gives, so the setup's steps read the same on both machines."""

    server: node.Server
    port: int
    timeout_s: float

    @property
    def road(self) -> ServerRoad:
        return ServerRoad(self)

    def rest(
        self,
        method: str,
        path: str,
        query: Mapping[str, str | None] | None = None,
        body: Document | None = None,
    ) -> Document:
        """One loopback call; a refusal raises `AppError` with the server's own code."""
        asked = {
            "method": method,
            "path": path,
            "query": {k: v for k, v in (query or {}).items() if v is not None},
            "body": body,
            "timeout": self.timeout_s,
        }
        token = f"{node.SERVER_KEYS}/control-token"
        script = as_qmx(ASK, str(self.port), token, given=json.dumps(asked))
        try:
            said = self.server.send("sudo bash -s", script)
        except RuntimeError as failed:
            raise Stopped(
                f"{self.server.machine}: the server's host did not answer {method} {path} "
                f"({failed}); check it is running with: sudo {node.RECOVER} status"
            ) from None
        answer = cast("dict[str, Any]", _last_json(said) or {})
        status = int(answer.get("status") or 0)
        found: object = answer.get("body")
        if 200 <= status < 300:
            return cast("Document", found if isinstance(found, dict) else {"value": found})
        refused = cast("dict[str, Any]", found) if isinstance(found, dict) else {}
        error = cast("dict[str, Any]", refused.get("error") or {})
        raise AppError(
            str(error.get("code") or "server_refused"),
            str(error.get("message") or f"{method} {path} answered {status}"),
            status or 502,
        )

    def get(self, app_id: str) -> Document:
        return self.rest("GET", f"/api/apps/{app_id}")

    def status(self, app_id: str) -> Document:
        return cast("Document", self.get(app_id).get("runtime") or {})

    def install(self, app_id: str) -> Document:
        query = {"path": f"{SERVER_APPS}/{app_id}", "trust": "first_party"}
        return self.rest("POST", "/api/apps", query)

    def start(self, app_id: str) -> Document:
        return self.rest("POST", f"/api/apps/{app_id}/start")

    def restart(self, app_id: str) -> Document:
        return self.rest("POST", f"/api/apps/{app_id}/restart")

    def call(self, app_id: str, tool: str, arguments: Document) -> Document:
        return self.rest("POST", f"/api/apps/{app_id}/tools/{tool}", body=arguments)


def server_apps(run: Run) -> ServerApps:
    """The server host's supervisor for this run, built once."""
    found = run.facts.get("server_apps")
    if isinstance(found, ServerApps):
        return found
    timeout = setting(_engine(run), "node_setup.server_call_timeout_s", SERVER_CALL_TIMEOUT_S)
    built = ServerApps(server_of(run), node.host_port(node.host_unit()), timeout)
    run.facts["server_apps"] = built
    return built


@dataclass(frozen=True, slots=True)
class ServerPorts:
    """What the server's steps reach beyond SSH. Tests and lanes pass stand-ins."""

    apps: tuple[str, ...] = tuple(APP_FOLDERS)
    prove: Callable[[AppsPort, str, str], None] = road_proof
    venues: Sequence[Venue] = VENUES
    now: Callable[[], float] = time.time


def _server_keys(run: Run, *, ensure: bool = False) -> dict[str, Any]:
    script = as_qmx(KEYS_STATE, SERVER_KEYS_FILE, "ensure" if ensure else "read")
    found = cast("dict[str, Any]", _last_json(_shell(run, script)) or {})
    if found.get("foreign"):
        raise Stopped(
            f"keys: {SERVER_KEYS_FILE} on {run.place} holds something that is not a "
            f"{KEYS_SCHEMA} document; remove it there, then set up the node again"
        )
    return found


def _server_app_known(run: Run) -> bool:
    return bool(_server_keys(run).get("ctrader"))


def _server_app_card(run: Run) -> Card:
    """Once cTrader approved the app, his window on the server takes its id and secret."""
    fields = cast("dict[str, object]", run.answer.get("fields") or {})
    if fields.get("approved") == "yes":
        server = server_of(run)
        compute_ports(run).terminal.open(
            window_command(server, KEYS_WINDOW, SERVER_KEYS_FILE),
            f"QMX: {run.place}'s cTrader trading app",
        )
        return Card(
            "ctrader-app",
            f"Type the Client ID and Client secret of {run.place}'s own trading app in the window "
            f"QMX opened. They go straight to {run.place}, and QMX never sees them. Then answer "
            "yes here once more; nothing else waits on it",
            ({"Name": "approved", "Help": "yes", "Examples": [], "Type": "string"},),
        )
    return Card(
        "ctrader-app",
        f"Waiting for cTrader to approve {run.place}'s app. Ask cTrader for {run.place}'s own "
        f"trading app on {APPS_PAGE} (Spotware takes about a day). Once it is approved, answer "
        f"yes, and QMX opens a window on {run.place} for its Client ID and Client secret; "
        "nothing else waits on it",
        (
            {
                "Name": "approved",
                "Help": "yes, once cTrader approved it",
                "Examples": [],
                "Type": "string",
            },
        ),
        link=APPS_PAGE,
    )


def _keys_mark(digest: str) -> str:
    return f"keys {digest[:16]}"


def _server_keys_written(run: Run) -> bool:
    found = _server_keys(run)
    return bool(found.get("document")) and node.done(
        server_of(run), _keys_mark(str(found["digest"]))
    )


def _write_server_keys(run: Run) -> Card | None:
    """The server's keys document, empty until his window fills it, written on the server before
    the node is enabled, because the node reads `NODE_KEYS` once at its start. A node already
    running is asked to read new keys, as on This PC; the mark names the document it read."""
    found = _server_keys(run, ensure=True)
    held = "with its cTrader trading app" if found.get("ctrader") else "with no venue yet"
    run.say(f"keys: the node's keys document is on {run.place} in {SERVER_KEYS_FILE}, {held}")
    _rotate(run)
    node.mark(server_of(run), _keys_mark(str(found["digest"])))
    return None


def _chrony_conf(sources: Sequence[str]) -> str:
    rows = "".join(f"server {source} iburst\n" for source in sources)
    return (
        "# QMX: one kind of source, none smeared (CK-06); written by the connect dialog.\n"
        f"{rows}"
        "driftfile /var/lib/chrony/chrony.drift\n"
        "makestep 1 3\n"
        "rtcsync\n"
        "leapsectz right/UTC\n"
    )


def chrony_script(sources: Sequence[str]) -> str:
    """chrony from Ubuntu's packages, keeping time from `sources` alone."""
    return (
        "set -eu\n"
        "if ! command -v chronyc >/dev/null; then\n"
        "  apt-get update\n"
        "  DEBIAN_FRONTEND=noninteractive apt-get install -y chrony\n"
        "fi\n"
        f"cat > {CHRONY_CONF} <<'QMXCHRONY'\n{_chrony_conf(sources)}QMXCHRONY\n"
        "systemctl enable chrony\n"
        "systemctl restart chrony\n"
    )


def _sources(run: Run) -> tuple[str, ...]:
    named = _engine(run).get("clock.sources")
    listed = cast("list[object]", named) if isinstance(named, list) else []
    return tuple(str(item) for item in listed) or SOURCES


def _chrony_on(run: Run) -> bool:
    server = server_of(run)
    if not node.done(server, CHRONY_STEP):
        return False
    try:
        return server.send("systemctl is-active chrony").split() == ["active"]
    except RuntimeError:
        return False


def _chrony(run: Run) -> Card | None:
    sources = _sources(run)
    if len(sources) < CHRONY_SOURCES:
        raise Stopped(
            f"chrony: [engine] clock.sources names {len(sources)}; a server keeps time from "
            f"{CHRONY_SOURCES} or more of one kind, so name more"
        )
    _shell(run, chrony_script(sources))
    node.mark(server_of(run), CHRONY_STEP)
    run.say(f"chrony: {run.place} keeps time from {', '.join(sources)}")
    return None


def _server_clock(run: Run) -> Card | None:
    """The shipped probe on the server: its offset, its band and chrony's word."""
    engine = {k: v for k, v in _engine(run).items() if k.startswith("clock.")}
    said = _shell(run, as_qmx(CLOCK, given=json.dumps(engine, default=str)))
    try:
        facts = ClockFacts.model_validate_json(said.strip().splitlines()[-1])
    except ValidationError, IndexError:
        raise Stopped(f"clock: {run.place} did not answer its clock probe") from None
    run.facts["clock"] = facts
    line = clock_line(facts)
    run.say(
        f"clock: {run.place} {line.detail}"
        + ("" if line.ok else "; the node will not enter on a bad clock")
    )
    return None


def _openobserve(run: Run) -> Card | None:
    """The server's OpenObserve, on its Tailscale address alone. Without its programs this
    step waits for him, because the node trades without it."""
    try:
        monitor(run)
    except RuntimeError:
        return Card(
            "openobserve",
            f"{run.place}: {MISSING_PROGRAMS}, then answer here; the node trades without it",
        )
    return None


def _server_install(ports: ServerPorts, run: Run) -> Card | None:
    apps = server_apps(run)
    for app in ports.apps:
        try:
            found = _installed(apps, app) or cast("dict[str, Any]", apps.install(app))
            ports.prove(apps, app, str(found["definition_hash"]))
        except AppError as error:
            raise Stopped(f"install: {app} did not install or pass its proof: {error}") from None
        run.say(f"install: {app} {found['definition']['version']} is installed on {run.place}")
    return None


def _server_proved(ports: ServerPorts, run: Run) -> bool:
    apps = _apps(run)
    return all(_stage(apps, app) in {"shadow", "live"} for app in ports.apps)


def _sign_there(run: Run, asked: Unsigned) -> Card:
    """His window on the server shows what that host's sign route answers for this version;
    he pastes it here, and the server's road checks it."""
    server = server_of(run)
    fields = cast("dict[str, object]", run.answer.get("fields") or {})
    if run.memory.get("signing") != asked.definition_hash or fields.get("again") == "yes":
        compute_ports(run).terminal.open(
            window_command(
                server,
                SIGN_WINDOW,
                str(node.host_port(node.host_unit())),
                f"{node.SERVER_KEYS}/control-token",
                NODE_APP,
                asked.definition_hash,
                asked.active or "",
                str(server_apps(run).timeout_s),
            ),
            f"QMX: sign the trading node on {run.place}",
        )
        run.memory["signing"] = asked.definition_hash
    return Card(
        "signature",
        f"Sign the trading node {asked.version} ({asked.definition_hash[:12]}) to publish it on "
        f"{run.place}: QMX opened a window there that shows your signature. Paste it here; a "
        f"restart of the signed version needs no new signature.{asked.again}",
        (
            {
                "Name": "signature",
                "Help": f"the signature the window on {run.place} shows",
                "Examples": [],
                "Type": "string",
            },
            {
                "Name": "again",
                "Help": "yes, to open the window again",
                "Examples": [],
                "Type": "string",
            },
        ),
    )


def handshakes_there(
    run: Run, venues: Sequence[Venue], count: int, timeout: float
) -> list[list[float]]:
    asked = {
        "venues": [{"host": venue.host, "port": venue.port} for venue in venues],
        "count": count,
        "timeout": timeout,
    }
    measured = _last_json(_shell(run, as_qmx(ROUND_TRIP, given=json.dumps(asked))))
    if not isinstance(measured, list) or len(cast("list[object]", measured)) != len(venues):
        raise Stopped(f"round trip: {run.place} did not answer its handshakes")
    return [[float(s) for s in cast("list[float]", row)] for row in cast("list[object]", measured)]


def server_setups(ports: ServerPorts) -> tuple[Setup, ...]:
    """The node's steps on a server, after the shipped server steps, in `NODE.md` section 11's
    order with chrony and OpenObserve after the keys."""
    names = ports.apps
    there = partial(_round_trip, ports.venues, handshakes_there)
    return (
        Setup(Step("ctrader-app", "his", _server_app_known, _server_app_card), waiting=True),
        Setup(Step("keys", "qmx", _server_keys_written, _write_server_keys)),
        Setup(Step("chrony", "qmx", _chrony_on, _chrony)),
        Setup(Step("clock", "qmx", _never, _server_clock)),
        Setup(Step("openobserve", "qmx", monitoring_on, _openobserve), waiting=True),
        Setup(
            Step("install", "qmx", partial(_server_proved, ports), partial(_server_install, ports))
        ),
        Setup(Step("signature", "his", _signed, partial(_sign, _sign_there))),
        Setup(Step("enable", "qmx", partial(_all_running, names), partial(_enable, names))),
        Setup(
            Step("sign-in", "his", _signed_in, _sign_in_card), waiting=True, after=("ctrader-app",)
        ),
        Setup(Step("round-trip", "qmx", _never, there)),
        Setup(Step("self-test", "qmx", _never, _self_test), after=("sign-in",)),
        Setup(Step("passport", "qmx", _never, partial(_passport, ports.now))),
        Setup(Step("apps-row", "qmx", partial(_row_written, names), partial(_write_row, names))),
    )


def on_a_server(ports: ServerPorts | None = None) -> Kind:
    """The kind for a server: the server kind's own cards and checked steps first, its place row
    among them, then the node's, which list the node and the MIS on that row last."""
    steps = (*SERVER.steps, *on_runner(server_setups(ports or ServerPorts())))
    return Kind(
        SERVER_KIND, "Trading node on your server", SERVER.can, False, steps, refusal=SERVER.refusal
    )


# The phone alarms' setup cards (Part C AD-318, lead's call LC-X0-10).

Send = Callable[[str, str, Mapping[str, str], bytes | None, float], int]
"""One HTTPS request: method, URL, headers, body and timeout; answers the status, raises when it
does not land."""
ALARM_SEND_TIMEOUT_S: Final = 10.0
"""`[engine] node_setup.alarm_send_timeout_s`: how long a setup card's test send may take."""
LOOPBACK: Final = frozenset({"127.0.0.1", "::1", "localhost"})
"""The only hosts a destination may reach without TLS: this machine."""


def https_send(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout_s: float
) -> int:
    """A destination is an https address or this machine's (`_address`), never a file."""
    request = urllib.request.Request(url, body, dict(headers), method=method)  # noqa: S310
    with urllib.request.urlopen(request, timeout=timeout_s) as answer:  # noqa: S310
        return int(answer.status)


@dataclass(frozen=True, slots=True)
class AlarmPorts:
    """What the alarm cards reach beyond the key store. Tests and lanes pass a local fake."""

    send: Send = https_send


@dataclass(frozen=True, slots=True)
class Alarm:
    """One destination the node's alarms go to: its card, the `qmx/` key he writes it to, its
    place in the keys document's `alarms`, and the one test send that proves it."""

    step: str
    field: str
    staged: str
    line: str
    link: str
    method: str
    headers: Mapping[str, str]
    body: bytes | None
    done: str


ALARMS: Final = (
    Alarm(
        "push",
        "ntfy_topic_url",
        "qmx/node-ntfy-topic",
        "Name an ntfy topic so the node can wake you on your phone while This PC is off. Install "
        "the ntfy app, subscribe to a topic name only you know, then write the topic's address "
        "(https://ntfy.sh/ and your topic) to the key qmx/node-ntfy-topic. A test notification "
        "reaches your phone as soon as it is there. Until the node reads market calendars it "
        "pushes only protection escalations and a long clock hold; risk stops, a broker link "
        "down and failing healing stay quiet",
        "https://docs.ntfy.sh/subscribe/phone/",
        "POST",
        {"Title": "QMX test", "Priority": "3"},
        b"A test from the trading node's setup. Alarms that need you will arrive here.",
        "push: a test notification went to your ntfy topic; from its next start the node pushes "
        "protection escalations and a long clock hold there, and the alarms that follow market "
        "hours once it reads market calendars",
    ),
    Alarm(
        "liveness",
        "healthchecks_ping_url",
        "qmx/node-healthchecks-ping",
        "Name a Healthchecks.io check so you hear when the node goes quiet. Make a check with a "
        "3 minute period and 2 minutes grace, send its alerts to your ntfy topic, then write its "
        "ping URL to the key qmx/node-healthchecks-ping. The setup pings it once to test it",
        "https://healthchecks.io/",
        "GET",
        {},
        None,
        "liveness: the check took a test ping; the node pings it every minute from its next start",
    ),
)


def _address(value: str) -> bool:
    parts = urlsplit(value)
    return (parts.scheme == "https" and bool(parts.hostname)) or (
        parts.scheme == "http" and parts.hostname in LOOPBACK
    )


def _why(error: BaseException) -> str:
    """A failed send in words that never carry the destination, which is a secret."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    return type(error).__name__


def _named(alarm: Alarm, run: Run) -> bool:
    alarms = cast("dict[str, Any]", (_keys(run) or {}).get("alarms") or {})
    return alarm.field in alarms and run.world.keys.read(alarm.staged) is None


def _alarm_card(alarm: Alarm, again: str = "") -> Card:
    return Card(alarm.step, alarm.line + again, key=alarm.staged, link=alarm.link)


def _name_alarm(ports: AlarmPorts, alarm: Alarm, run: Run) -> Card | None:
    """Prove what he wrote with one test send, then fold it into the keys document and delete
    the staged key. A rerun after a kill between the two writes only deletes it."""
    staged = run.world.keys.read(alarm.staged)
    if staged is None:
        return _alarm_card(alarm)
    document = _keys(run) or {"schema_version": KEYS_SCHEMA}
    alarms = dict(cast("dict[str, Any]", document.get("alarms") or {}))
    if alarms.get(alarm.field) != staged:
        if not _address(staged):
            return _alarm_card(alarm, ". That is not an https address; write it again")
        timeout = setting(_engine(run), "node_setup.alarm_send_timeout_s", ALARM_SEND_TIMEOUT_S)
        try:
            ports.send(alarm.method, staged, alarm.headers, alarm.body, timeout)
        except Exception as error:  # any failure is his to fix on the card, in plain words
            return _alarm_card(
                alarm, f". The test send did not land ({_why(error)}); check it and write it again"
            )
        alarms[alarm.field] = staged
        run.world.keys.replace(
            NODE_KEYS, json.dumps({**document, "alarms": alarms}, sort_keys=True)
        )
        run.say(alarm.done)
    run.world.keys.delete(alarm.staged)
    return None


def alarms_on_this_pc(ports: AlarmPorts | None = None) -> Kind:
    """The phone alarms' kind: one waiting card per destination, each on once he names it."""
    used = ports or AlarmPorts()
    steps = on_runner(
        tuple(
            Setup(
                Step(alarm.step, "his", partial(_named, alarm), partial(_name_alarm, used, alarm)),
                waiting=True,
            )
            for alarm in ALARMS
        )
    )
    return Kind("trading-node-alarms", "Phone alarms for the trading node", (), False, steps)


TRADING_NODE: Final = (alarms_on_this_pc(), on_this_pc(), on_a_server())
"""The trading-node kinds, in the order the dialog offers them."""
