"""K7: from an empty store to one filled paper entry, with no judge run (K9 7, RC-19).

The walk SPINE section 6 gives a stranger, in the section's ten steps: ``practice_start``,
``unit_new``, check, backtest, his click, stage, warm up, first signal, the decision row, the
fill. Everything between the store and the fill is the shipped code: the Library, the lifecycle
writer, the promote route's own promoter, the node link's staging, the node's runtime, its order
path, the paper lane, and the journals on disk.

The venue is the fake broker: the node's cTrader door over ``FakeCTrader``, the wire fake QMX's
own binding tests drive. It is not the practice venue, and :class:`K7` says why in ``shortfall``:
the practice account row names ``world: paper``, the Library's `account` kind accepts only
``demo`` or ``live``, so a practice account can only be landed by claiming a world it is not, and
a click on it would stamp the run ``real_tick_share: 1``. K7 asks for the practice rows first and
keeps the Library's own refusal as the evidence. The practice venue is built in
``qmn/app/practice.py``, and its rows and its card are held by
``test_practice_says_it_is_practice``.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

REPO = Path(__file__).resolve().parents[4]
QMN_TESTS = REPO / "qmn" / "tests"
if str(QMN_TESTS) not in sys.path:
    sys.path.insert(0, str(QMN_TESTS))

import test_app_binding as broker  # noqa: E402 - qmn's fake broker lives with qmn's rig

from qmx_control.service import ControlService, WorkflowEngine  # noqa: E402
from qmx_engine.ledger import redact  # noqa: E402
from qmx_host.host import LanderLibrary, landers, register_checkers  # noqa: E402
from qmx_host.lifecycle import LifecycleWriter  # noqa: E402
from qmx_host.node_link import NodeLink  # noqa: E402
from qmx_host.practice_start import practice_start  # noqa: E402
from qmx_host.promote import (  # noqa: E402
    AccountRef,
    Click,
    NodeRef,
    Promoter,
    UnitRef,
    harvested_calibrations,
)
from qmx_host.venue_records import Stated, land, stated  # noqa: E402
from qmx_library.store import Store  # noqa: E402
from qmx_tools.functions import domain_functions  # noqa: E402
from qmx_tools.service import DomainContext  # noqa: E402

from qmn.app.practice import ACCOUNT as PRACTICE_ACCOUNT  # noqa: E402
from qmn.app.practice import PRACTICE  # noqa: E402

APP = REPO / "qmx-agents" / "apps" / "qmb"
MARKET = "fx.eurusd"
MARKET_VENUE = "icmarkets-ctrader"
MARCH = {"start": "2025-03-01", "end": "2025-04-01"}
BAR = 900_000_000_000
DAY = 86_400_000_000_000
LIVE_FROM = 1_742_500_000_000_000_000
"""2025-03-20 19:46:40 UTC: the bars before it are the venue's history, the day after it plays."""
RUN_DAYS = 11
"""The days after `LIVE_FROM` the walk may play before it calls the signal missing; the shipped
month ends inside this bound."""
CLICKED = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)
CHAT = "agent:k7"
DEMO_ACCOUNT = "demo-1"
PRACTICE_SANDBOX = "none"


@dataclass(frozen=True, slots=True)
class Step:
    """One named step of the walk, with the one line it says."""

    name: str
    said: str


@dataclass(frozen=True, slots=True)
class K7:
    """What the walk left behind: its steps, the paper fills, the decision row, and the reason
    the click could not be made on the practice venue."""

    steps: tuple[Step, ...]
    fills: tuple[Mapping[str, object], ...]
    decision: Mapping[str, object] | None
    shortfall: str = ""


class Clock:
    """The Library's wall clock, a second a read, so no two writes share a time."""

    def __init__(self) -> None:
        self.now = CLICKED
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


class Caller:
    def __init__(self, principal: str) -> None:
        self.principal = principal


class Chat:
    """The workflow engine the app runtime asks: no runs, no models, no network."""

    def principal(self) -> Caller:
        return Caller(CHAT)

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        del workflow_id
        return []


@dataclass(frozen=True)
class Supervisor:
    """The node as the host's node link reaches it here: in this process, over no socket."""

    node: Any
    home: Path

    def get(self, app: str) -> dict[str, Any]:
        return {"id": app}

    def call(
        self,
        app: str,
        operation: str,
        arguments: Mapping[str, Any],
        *,
        pin: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        del app, pin
        return {"result": dict(self.node.call(operation, dict(arguments)))}


def run(home: Path) -> K7:
    """Walk `home`, an empty QMX folder, to one filled paper entry. Answers its evidence."""
    home = home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    clock = Clock()
    steps: list[Step] = []
    control = ControlService(home)
    control.attach_workflow_engine(cast(WorkflowEngine, Chat()))
    with Store.open(home / "library", redactor=redact, wall=clock) as store:
        register_checkers(store)
        try:
            control.attach_library(store)
            apps = control.app_runtime()
            apps.attach_landers(
                landers(store, apps, "pc", settings=lambda: control.settings_get("qmb"))
            )
            apps.install(APP, trust="first_party")
            apps.start("qmb")
            walked = _walk(home, store, control, steps)
        finally:
            control.close()
    return walked


def _walk(home: Path, store: Store, control: ControlService, steps: list[Step]) -> K7:
    tools = _tools(home, control)
    started = practice_start(home, store)
    steps.append(
        Step(
            "practice_start",
            f"{started.source}: {len(started.months)} month, {len(started.series)} series,"
            f" {sum(one.outcome == 'landed' for one in started.instruments)} instruments",
        )
    )
    unit = tools["unit"]["unit_new"]("canary", {})
    steps.append(Step("unit_new", f"canary as {unit['item']}"))
    checked = tools["unit"]["unit_check"](document=unit["document"], item=unit["item"])
    steps.append(Step("check", f"{checked['verdict']}: {checked['counts']['errors']} errors"))
    backtest = tools["backtest"]["backtest_run"](
        unit=unit["object_id"], window=MARCH, allow_gaps=True, source="practice"
    )["result"]
    steps.append(Step("backtest", f"{backtest['status']} as {backtest.get('result_id')}"))
    rig = _broker(home, steps)
    shortfall = _practice_shortfall(store)
    land(store, stated(Stated(MARKET_VENUE, DEMO_ACCOUNT, "demo", "demo")))
    deployment = _click(home, store, rig, unit["object_id"])
    _staged(rig.data, deployment, steps)
    fills, decision = _filled(rig, deployment, steps)
    return K7(tuple(steps), fills, decision, shortfall)


def _tools(home: Path, control: ControlService) -> dict[str, Any]:
    context = DomainContext(root=home / "tools")
    context.control, context.library = control, control.library
    return domain_functions(context)


def _broker(home: Path, steps: list[Step]) -> broker.Bound:
    """The node on its volume bound to the fake broker, its history seeded, its session ready."""
    made = broker.bound_rig(
        home / "apps" / "trading-node", broker=broker.FakeCTrader(broker.codec())
    )
    broker.signed_in(made)
    broker.bind(made)
    feed = broker.runtime(made).venues[DEMO_ACCOUNT].feed
    for at, market, bar in broker.base.month().bars:
        if at < LIVE_FROM:
            feed.recording.keep(market, bar)
    broker.tick_quotes(made)
    assert feed.ready, feed.reason
    steps.append(
        Step(
            "stage_warm",
            f"{DEMO_ACCOUNT} ready, {len(feed.recording.recent(MARKET, 100_000))} bars of"
            f" history on {MARKET}",
        )
    )
    return made


def _practice_shortfall(store: Store) -> str:
    """Land the practice rows; answer the Library's own refusal of the account, if it refuses."""
    found = land(
        store, stated(Stated(PRACTICE, PRACTICE_ACCOUNT, "paper", PRACTICE_SANDBOX))
    )
    refused = [one.why for one in found if one.kind == "account" and one.outcome == "refused"]
    return refused[0] if refused else ""


def _click(home: Path, store: Store, rig: broker.Bound, version: str) -> str:
    """His click: the real promoter, the real node link, the real staging, the node's own deploy."""
    standing = cast("dict[str, Any]", rig.node.call("status", {}))["value"]
    writer = LifecycleWriter(home / "journals", "pc", "test")
    store.lifecycle = writer
    promoter = Promoter(
        store,
        writer,
        NodeLink(
            home,
            here="pc",
            apps=cast("Any", Supervisor(rig.node, home)),
            settings=dict,
            pass_keys=dict,
            clock=lambda: rig.now[0] / 1e9,
            blobs=lambda fingerprint: [store.read_blob(fingerprint)],
        ),
        LanderLibrary(store),
        calibrations=harvested_calibrations(home, lambda: time.time_ns() + 10**18),
        trading_profile=lambda _place: False,
        now=lambda: CLICKED,
    )
    answer = promoter.promote(
        Click(
            schema_version="qmx.units.promote/1",
            op_id="k7-click-1",
            unit=UnitRef(id="canary", version=version),
            market_id=MARKET,
            to="paper",
            node=NodeRef(tag=str(cast("dict[str, Any]", standing["identity"])["tag"])),
            account=AccountRef(id=DEMO_ACCOUNT),
        )
    )
    writer.close()
    return str(cast("dict[str, Any]", answer["value"])["deployment_id"])


def _staged(data: Path, deployment: str, steps: list[Step]) -> None:
    folder = data / "deployments" / deployment
    lock = cast("list[dict[str, str]]", json.loads((folder / "lock.json").read_text("utf-8")))
    missing = [item["path"] for item in lock if not (folder / "in" / item["path"]).is_file()]
    assert not missing, missing
    steps.append(Step("stage", f"{len(lock)} files staged for {deployment}"))


def _filled(
    rig: broker.Bound, deployment: str, steps: list[Step]
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object] | None]:
    """Play bars until the unit holds its first paper position, then read what the journals say."""
    runtime = broker.runtime(rig)
    at = max(rig.now[0], LIVE_FROM)
    last = LIVE_FROM + RUN_DAYS * DAY
    while _held(runtime, deployment) is None:
        assert at < last, f"no signal in {RUN_DAYS} days for {deployment}"
        broker.play_spots(rig, at, at + BAR)
        at += BAR
    steps.append(Step("warm_up", f"{_held(runtime, deployment)} open"))
    steps.append(Step("first_signal", f"{MARKET} at {at - BAR} ns"))
    ordered = [row for row in _rows(rig.node, "node") if row["kind"] == "order"]
    fills = tuple(
        cast("dict[str, object]", row["body"])
        for row in ordered
        if row["world"] == "paper"
        and cast("dict[str, object]", row["body"]).get("step") == "filled"
    )
    decision = next(
        (
            cast("dict[str, object]", row["body"])
            for row in _rows(rig.node, "unit")
            if row["kind"] == "signal"
            and cast("dict[str, object]", row["body"]).get("outcome") == "taken"
        ),
        None,
    )
    steps.append(Step("row", "none" if decision is None else str(decision.get("row_id"))))
    steps.append(
        Step("fill", f"{len(fills)} fill, quantity {fills[0].get('quantity') if fills else '0'}")
    )
    runtime.stop()
    return fills, decision


def _held(runtime: Any, deployment: str) -> str | None:
    hosted = runtime.hosted.get(deployment)
    unit = None if hosted is None else hosted.unit
    if unit is None:
        return None
    held = unit.venue_open()
    return next(iter(held), None)


def _rows(node: Any, stream: str) -> list[Mapping[str, object]]:
    answer = node.call("journal_tail", {"streams": [stream]})
    assert answer["ok"] is True, answer
    return cast("list[Mapping[str, object]]", cast("dict[str, object]", answer["value"])["rows"])


def main(argv: list[str] | None = None) -> int:
    """Run the walk on a folder of its own and print one PASS line per step."""
    given = list(sys.argv[1:] if argv is None else argv)
    home = Path(given[0]) if given else Path(tempfile.mkdtemp(prefix="k7-", dir="D:/Temp"))
    try:
        found = run(home)
        for step in found.steps:
            print(f"PASS {step.name}: {step.said}")
        if found.shortfall:
            print(f"SHORT the click is not the practice venue: {found.shortfall}")
        print(f"FILL {len(found.fills)}")
        print(f"DECISION {None if found.decision is None else found.decision.get('row_id')}")
        return 0 if len(found.fills) == 1 and found.decision is not None else 1
    finally:
        if not given:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
