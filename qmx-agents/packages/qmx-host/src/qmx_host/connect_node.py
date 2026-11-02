"""The trading-node kind of the connect dialog, on This PC (Part C AD-316, Level 0 AD-37 and
AD-45): one click sets the practice node up, and the sign-ins come later (rulings 35 and 37).

The steps run on the shipped step runner (`qmx_host.connect.run_kind`), in `NODE.md` section 11's
order: the cTrader trading-app request, the keys document, the clock, install, his signature,
enable, the sign-in, the round trip to each venue, the self-test, the passport and the place row
last. Two of them wait on something outside QMX: Spotware approving this PC's trading app, which
takes about a day (TN-31), and his demo sign-in, which is his and which the build never runs. A
waiting step does not end the run: it holds its card, the steps that need it say they wait, every
other step runs, and the run ends on the first card still waiting. So the node is installed,
started and in his machines while cTrader still has his request.

Every step checks what is in place before it acts, so a rerun after a kill at any step ends with
the same node and one place row, This PC's `[engine.placement.pc]`, listing the apps homed here.
"""

from __future__ import annotations

import json
import os
import socket
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from qmx_apps.errors import AppError
from qmx_apps.road.models import STAGES
from qmx_engine.admission import setting
from qmx_engine.heartbeat import ClockFacts
from qmx_engine.ports.settings import flatten

from qmx_host.clock_probe import clock_line, probe_from
from qmx_host.connect import Card, Kind, Run, Step
from qmx_host.jobs import Stopped

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
APPS_DIR: Final = Path(__file__).resolve().parents[4] / "apps"
APP_FOLDERS: Final[Mapping[str, Path]] = {NODE_APP: APPS_DIR / NODE_APP}
"""The apps the setup installs and homes here, as this program ships them. The MIS joins when its
app lands (slice C-09)."""
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


def road_proof(apps: Supervisor, app: str, definition_hash: str) -> None:
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
    waiting steps this one needs done first."""

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


def _apps(run: Run) -> Supervisor:
    control = run.world.control
    if control is None:
        raise Stopped("a trading node is set up from a running QMX, not the first-start card")
    return control.app_runtime()


def _engine(run: Run) -> dict[str, object]:
    control = run.world.control
    engine = {} if control is None else control.settings_get(cast("Any", "engine"))
    return dict(flatten(engine, ""))


def _installed(apps: Supervisor, app: str) -> dict[str, Any] | None:
    try:
        return cast("dict[str, Any]", apps.get(app))
    except AppError:
        return None


def _stage(apps: Supervisor, app: str) -> str | None:
    found = _installed(apps, app)
    road = cast("dict[str, Any]", (found or {}).get("road") or {})
    return cast("str | None", road.get("stage"))


def _published(apps: Supervisor, app: str) -> bool:
    found = _installed(apps, app)
    if found is None:
        return False
    active = cast("dict[str, Any]", found.get("road") or {}).get("active")
    return isinstance(active, dict) and active.get("definition_hash") == found["definition_hash"]


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
        found = json.loads(held)
    except ValueError:
        found = None
    if not isinstance(found, dict) or found.get("schema_version") != KEYS_SCHEMA:
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
    return _keys(run) is not None and _pasted(run) is None


def _write_keys(run: Run) -> Card | None:
    """The keys document, empty at first, with the trading app once he has given it. The staged
    secret is deleted only after the document holds it."""
    document = _keys(run) or {"schema_version": KEYS_SCHEMA}
    pasted = _pasted(run)
    if pasted is not None:
        document["ctrader"] = {"client_id": pasted[0], "client_secret": pasted[1]}
    run.world.keys.replace(NODE_KEYS, json.dumps(document, sort_keys=True))
    if pasted is not None:
        run.world.keys.delete(APP_SECRET)
    held = "with this PC's cTrader trading app" if "ctrader" in document else "with no venue yet"
    run.say(f"keys: the node's keys document is in Credential Manager as {NODE_KEYS}, {held}")
    return None


def _never(_run: Run) -> bool:
    return False


def _clock(ports: Ports, run: Run) -> Card | None:
    facts = ports.clock(_engine(run))
    run.facts["clock"] = facts
    line = clock_line(facts)
    run.say(f"clock: {line.detail}" + ("" if line.ok else "; the node will not enter on a bad clock"))
    return None


def _proved(ports: Ports, run: Run) -> bool:
    apps = _apps(run)
    return all(_stage(apps, app) in {"shadow", "live"} for app in ports.apps)


def _install(ports: Ports, run: Run) -> Card | None:
    apps = _apps(run)
    for app, folder in ports.apps.items():
        try:
            found = _installed(apps, app) or apps.install(folder, trust="first_party")
            ports.prove(apps, app, str(found["definition_hash"]))
        except AppError as error:
            raise Stopped(f"install: {app} did not install or pass its proof: {error}") from None
        run.say(f"install: {app} {found['definition']['version']} is installed and proved")
    return None


def _signed(run: Run) -> bool:
    return _published(_apps(run), NODE_APP)


def _sign(run: Run) -> Card | None:
    """His signature publishes the node's version (`qmx_apps.road`): the dialog asks the
    operator-only sign route for it and answers it here. Publishing starts the node."""
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
            run.say(f"signature: trading-node {definition_hash[:12]} is published with your signature")
            return None
    asked = f"definition_hash={definition_hash}" + (f"&expected_active={active}" if active else "")
    version = found["definition"]["version"]
    return Card(
        "signature",
        f"Sign the trading node {version} ({definition_hash[:12]}) to publish it on This PC; "
        f"a restart of the signed version needs no new signature.{again}",
        (
            {
                "Name": "signature",
                "Help": f"what POST /api/apps/{NODE_APP}/sign?{asked} answers",
                "Examples": [],
                "Type": "string",
            },
        ),
    )


def _running(run: Run) -> bool:
    return _apps(run).status(NODE_APP).get("status") == "running"


def _enable(run: Run) -> Card | None:
    try:
        _apps(run).start(NODE_APP)
    except AppError as error:
        raise Stopped(f"enable: the trading node did not start: {error}") from None
    run.say("enable: the trading node runs on This PC")
    return None


def _session(run: Run, venue: str) -> str:
    venues = cast("list[dict[str, Any]]", _ask(run, "status").get("venues") or [])
    return next((str(v.get("session")) for v in venues if v.get("venue") == venue), "not_set_up")


def _signed_in(run: Run) -> bool:
    return _session(run, "ctrader") != "not_set_up"


def _sign_in_card(_run: Run) -> Card:
    return Card(
        "sign-in",
        "Sign in on cTrader's own page with your demo account when you want this node to trade. "
        "This step waits for you and nothing else waits on it; the node's card starts the "
        "sign-in when you are ready",
    )


def _round_trip(ports: Ports, run: Run) -> Card | None:
    """`handshakes` TCP handshakes to each venue, with their median and spread (TN-32). A venue
    that does not answer is recorded with no samples and stops nothing."""
    engine = _engine(run)
    count = max(1, int(setting(engine, "node_setup.handshakes", HANDSHAKES)))
    timeout = setting(engine, "node_setup.handshake_timeout_s", HANDSHAKE_TIMEOUT_S)
    rows: list[dict[str, object]] = []
    for venue in ports.venues:
        samples: list[float] = []
        for _ in range(count):
            try:
                samples.append(ports.handshake(venue.host, venue.port, timeout))
            except OSError:
                continue
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
        run.say(f"round trip: {venue.name} {venue.environment} {measured}")
    run.facts["round_trip"] = rows
    return None


def _self_test(run: Run) -> Card | None:
    """The self-test's place in the setup. Its checks run on a demo binding through the node's
    `self_test`, which lands them on the passport; this step names them."""
    run.say(f"self-test: on a demo binding the node checks {'; '.join(SELF_TEST_CHECKS)}")
    return None


def _iso(at: float) -> str:
    return datetime.fromtimestamp(at, UTC).isoformat()


def _passport(ports: Ports, run: Run) -> Card | None:
    """The node's passport with what the setup measured: the round trip, the clock band and the
    disk. It lands in this QMX folder's data, written whole and then moved into place."""
    node = _ask(run, "passport")
    status = _ask(run, "status")
    at = _iso(ports.now())
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
    target = run.world.layout.home / PASSPORT
    part = target.with_suffix(".part")
    part.write_text(json.dumps(passport, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(part, target)
    run.say(f"passport: landed in {PASSPORT}, node {status['identity'].get('tag')}")
    return None


def _apps_here(ports: Ports, run: Run) -> list[str]:
    apps = _apps(run)
    return [app for app in ports.apps if _installed(apps, app) is not None]


def _row_of(run: Run) -> dict[str, Any]:
    control = run.world.control
    engine = {} if control is None else control.settings_get(cast("Any", "engine"))
    rows = cast("dict[str, Any]", engine.get("placement") or {})
    return cast("dict[str, Any]", rows.get(PLACE) or {})


def _row_written(ports: Ports, run: Run) -> bool:
    listed = _row_of(run).get("apps") or []
    return set(_apps_here(ports, run)) <= set(cast("list[str]", listed))


def _write_row(ports: Ports, run: Run) -> Card | None:
    """This PC's place row lists the apps homed here, merged inside the settings lock into the
    row as stored, so its other keys (its GPU slots) stay."""
    control = run.world.control
    if control is None:
        raise Stopped("a trading node is set up from a running QMX, not the first-start card")
    here = _apps_here(ports, run)

    def placed(engine: dict[str, Any]) -> dict[str, Any]:
        rows = dict(cast("dict[str, Any]", engine.get("placement") or {}))
        row = dict(cast("dict[str, Any]", rows.get(PLACE) or {}))
        listed = list(cast("list[str]", row.get("apps") or []))
        row["apps"] = [*listed, *(app for app in here if app not in listed)]
        return {**engine, "placement": {**rows, PLACE: row}}

    control.settings_update(cast("Any", "engine"), cast("Any", placed))
    run.say(f"row: This PC is home to {', '.join(here)} in your machines")
    return None


def setups(ports: Ports) -> tuple[Setup, ...]:
    """The steps for This PC, in `NODE.md` section 11's order."""
    return (
        Setup(Step("ctrader-app", "his", _app_known, _app_card), waiting=True),
        Setup(Step("keys", "qmx", _keys_written, _write_keys)),
        Setup(Step("clock", "qmx", _never, partial(_clock, ports))),
        Setup(Step("install", "qmx", partial(_proved, ports), partial(_install, ports))),
        Setup(Step("signature", "his", _signed, _sign)),
        Setup(Step("enable", "qmx", _running, _enable)),
        Setup(
            Step("sign-in", "his", _signed_in, _sign_in_card), waiting=True, after=("ctrader-app",)
        ),
        Setup(Step("round-trip", "qmx", _never, partial(_round_trip, ports))),
        Setup(Step("self-test", "qmx", _never, _self_test), after=("sign-in",)),
        Setup(Step("passport", "qmx", _never, partial(_passport, ports))),
        Setup(Step("row", "qmx", partial(_row_written, ports), partial(_write_row, ports))),
    )


def on_this_pc(ports: Ports | None = None) -> Kind:
    """The kind for This PC, over `ports` (the real ones by default)."""
    steps = on_runner(setups(ports or Ports()))
    return Kind("trading-node-pc", "Trading node on This PC", (), False, steps)


TRADING_NODE: Final = (on_this_pc(),)
"""The trading-node kinds, in the order the dialog offers them; a server's comes with C-17."""
