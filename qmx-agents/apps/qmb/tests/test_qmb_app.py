"""QMB as the first mini app: every door starts one `backtest` job that trades the compiled dummy.

The app is the shipped folder, installed into a real supervisor with its own locked environment,
and `qmb-run` is the host's own composition over a real Library store. The bars are QML's
synthetic March 2025 month (`qml/tests/fixtures/slices`), saved under dukascopy-node's names,
so every literal below holds on every machine.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import shutil
import threading
import time
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import psutil
import pytest
from qmf.core import fingerprint_bytes, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.store.engines.typed import BAR_COLUMNS, TICK_COLUMNS, TypedWriter
from qmx_apps.errors import AppError, Document
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_control.service import ControlError, ControlService, WorkflowEngine
from qmx_engine.ledger import redact
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import NodeJob, Ok
from qmx_host import first_start  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.first_start import (  # pyright: ignore[reportMissingTypeStubs]
    Places,
    enable_first_party,
    land_dummy,
    make_new,
)
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    STUDY_CHECKER,
    LanderLibrary,
    landers,
    study_check,
)
from qmx_host.market_data import (  # pyright: ignore[reportMissingTypeStubs]
    MarketDoor,
    Placement,
)
from qmx_host.venue_records import (  # pyright: ignore[reportMissingTypeStubs]
    Market,
    land,
    records_of,
)
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.gather import DUMMY, template
from qmx_tools.service import DomainContext

APP = Path(__file__).resolve().parents[1]
REPO = APP.parents[2]
SLICES = REPO / "qml" / "tests" / "fixtures" / "slices"
OPERATOR = Principal("operator")
MARCH: dict[str, Any] = {"start": "2025-03-01", "end": "2025-04-01"}
GAPS: dict[str, Any] = {"window": MARCH, "allow_gaps": True}
"""The synthetic month opens the forex week at 22:00 UTC, an hour late on Sundays after the 9 March
clock change: a 4-bar hole each week on `fx-24x5@1`, one more than `[qmb] gap_bars_refuse`."""
SUNDAY_HOLE = (
    "data: fx.eurusd misses 4 bars in open time after the bar opening 2025-03-07 21:45 UTC, more "
    "than the 3 a run allows unless its study allows gaps"
)
CHAT = "agent:chat-7"
SETTLE_SECONDS = 120.0
"""Test bound: how long a test waits for QMB to start again after a crash trips its breaker."""


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


@dataclass(frozen=True)
class Caller:
    principal: str


class Chat:
    """The engine door as the host attaches it, naming one chat as the caller."""

    def principal(self) -> Caller:
        return Caller(CHAT)

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        return []


def soon(seconds: float, cancel: threading.Event) -> bool:
    """QMB's back-off, shortened to a second so a test sees the restart."""
    return cancel.wait(min(seconds, 1.0))


@dataclass
class World:
    control: ControlService
    store: Store
    runtime: Supervisor
    dummy: str
    backtest: Mapping[str, Callable[..., dict[str, Any]]]
    tools: Mapping[str, Mapping[str, Callable[..., dict[str, Any]]]]


def a_world(root: Path, *, bars: Path | None) -> Generator[World]:
    """QMB installed on a real supervisor over a real store, in `root`, the dummy landed."""
    control = ControlService(root / "home")
    if bars is not None:
        control.settings_put("qmb", {"bars": str(bars)})
    control.attach_workflow_engine(cast(WorkflowEngine, Chat()))
    with Store.open(root / "library", redactor=redact, wall=Clock()) as store:
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.restart_wait = soon
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        runtime.install(APP, trust="first_party")
        runtime.start("qmb")
        dummy = land_dummy(store)
        assert dummy is not None
        context = DomainContext(root=root / "tools")
        context.control, context.library = control, control.library
        try:
            tools = domain_functions(context)
            yield World(control, store, runtime, dummy, tools["backtest"], tools)
        finally:
            control.close()


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("qmb")
    bars = root / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    yield from a_world(root, bars=bars)


def fields(store: Store, object_id: str) -> dict[str, Any]:
    return dict(store.get(OPERATOR, object_id).fields)


def reports(store: Store, kind: str = "test-report") -> list[dict[str, Any]]:
    return [fields(store, found) for found in store.with_field(kind, "check", "qml-g/1")]


def tries(store: Store, run_id: str) -> list[tuple[str, str]]:
    found = [fields(store, i) for i in store.with_field("try", "run_id", run_id)]
    return [(str(row["kind"]), str(row["state"])) for row in found]


def report(store: Store, result_id: str) -> dict[str, Any]:
    blob = store.get(OPERATOR, result_id).blobs["report"]
    return cast("dict[str, Any]", json.loads(store.read_blob(blob.blob_id)))


def asked(unit: str, window: dict[str, Any]) -> Document:
    return cast("Document", {"unit": unit, **GAPS, "window": window})


def until(check: Callable[[], bool], what: str) -> None:
    deadline = time.monotonic() + SETTLE_SECONDS
    while not check():
        assert time.monotonic() < deadline, what
        time.sleep(0.1)


def a_new_unit(world: World) -> str:
    """The dummy with its EMA period one bar longer: another unit, another compiled fingerprint."""
    document = template(DUMMY)
    numbers = cast("dict[str, dict[str, Any]]", document["numbers"])
    numbers["ema_period"]["default"] = "101"
    draft = Draft("unit", "unit-ema-101", "ema 101", fields=cast("Any", document))
    return world.store.put(
        OPERATOR, draft, on=drafts_ref("unit-ema-101"), expected_head=None
    ).object_id


def test_the_copilot_backtests_the_dummy_after_its_behaviour_check_and_lands_money_and_r(
    world: World,
) -> None:
    before = len(reports(world.store))

    answer = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]
    again = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]

    run_id, result_id = answer["run_id"], answer["result_id"]
    landed = fields(world.store, result_id)
    checks = reports(world.store)[before:]
    assert (answer["status"], again["status"]) == ("finished", "finished")
    assert (landed["status"], landed["kind"], landed["principal"]) == ("finished", "backtest", CHAT)
    assert landed["tester"] == {"app": "qmb", "version": "1.0.4"}
    assert landed["measures"]["trades"] == 8
    assert landed["labels"]["zero_trades"] is False
    assert len(checks) == 1
    assert checks[0]["safety"]["verdict"] == "pass"
    assert checks[0]["compiled_fingerprint"] == landed["compiled_fp"]
    assert tries(world.store, checks[0]["run_id"]) == [("check", "opened"), ("check", "landed")]
    assert tries(world.store, run_id) == [("run", "opened"), ("run", "landed")]
    trades = report(world.store, result_id)["trades"]
    assert sum(Decimal(t["r"]) for t in trades) == Decimal(landed["measures"]["total_r"])
    assert sum(Decimal(t["money"]) for t in trades) == Decimal(landed["measures"]["net_money"])


def test_a_long_only_unit_makes_no_short_fills(world: World) -> None:
    document = template(DUMMY)
    document["direction"] = "long"
    draft = Draft("unit", "unit-long-only", "long only", fields=cast("Any", document))
    unit = world.store.put(
        OPERATOR, draft, on=drafts_ref("unit-long-only"), expected_head=None
    ).object_id

    long_only = world.backtest["backtest_run"](unit=unit, **GAPS)["result"]
    both = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]

    def trades(answer: dict[str, Any]) -> dict[str, int]:
        sides = [t["side"] for t in report(world.store, answer["result_id"])["trades"]]
        return {side: sides.count(side) for side in ("long", "short")}

    assert (long_only["status"], both["status"]) == ("finished", "finished")
    assert trades(long_only)["short"] == 0
    assert trades(long_only)["long"] >= 1
    assert trades(both)["short"] >= 1


def test_an_agent_writes_adx_above_25_and_a_job_runs_it(world: World) -> None:
    def pin(entry_id: str) -> dict[str, Any]:
        entry = world.tools["blocks"]["blocks_get"](entry_id=entry_id)["entry"]
        return {key: entry[key] for key in ("entry_id", "version", "fingerprint")}

    slot = {
        "role": "filter",
        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
        "bindings": [
            {
                "name": "adx",
                "block": "adx@1",
                "params": {"period": {"value": "14"}},
                "inputs": {"series": "m15"},
            },
            {
                "name": "strong",
                "block": "value-above@1",
                "params": {"level": {"number": "adx_level"}, "below": {"value": "0"}},
                "inputs": {"series": "adx"},
            },
        ],
    }
    number = {
        "kind": "fixed",
        "measure": "ratio",
        "range": {"min": "0", "max": "100", "step": "1"},
        "default": "25",
        "motion": {"mode": "fixed"},
        "authority": "motion_inside_range",
        "origin": "builder_chosen",
    }
    unit_new, unit_check = world.tools["unit"]["unit_new"], world.tools["unit"]["unit_check"]
    made = unit_new(
        overrides={
            "/logic/long/slots/strength": slot,
            "/logic/short/slots/strength": slot,
            "/numbers/adx_level": number,
            "/pins": [
                *cast("list[object]", template(DUMMY)["pins"]),
                pin("adx"),
                pin("value-above"),
            ],
        },
        title="ADX above 25",
    )

    def run_at(level: str) -> dict[str, Any]:
        document = made["document"]
        document["numbers"]["adx_level"]["default"] = level
        checked = unit_check(document=document, item=made["item"])
        assert checked["verdict"] == "pass", checked["errors"]
        answer = world.backtest["backtest_run"](unit=checked["saved"]["object_id"], **GAPS)
        assert answer["result"]["status"] == "finished"
        return fields(world.store, answer["result"]["result_id"])

    at_25, at_99 = run_at("25"), run_at("99")

    assert at_25["labels"]["zero_trades"] is False
    assert at_25["measures"]["trades"] == 1
    assert at_99["labels"]["zero_trades"] is True


def test_a_workflow_app_op_lands_the_same_trades_and_the_rows_read_the_core(
    world: World,
) -> None:
    by_chat = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]
    node = NodeJob(
        run_id="wf1",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition=cast(
            "Any",
            {
                "type": "app_op",
                "parameters": {
                    "app": "qmb",
                    "job": "jobs/backtest.py",
                    "inputs": {"unit": world.dummy, **GAPS},
                },
            },
        ),
        inputs={},
        now=None,
    )

    asked = asyncio.run(AppOp(world.runtime.run_job, dispatch=world.runtime.run_job).run(node))

    assert isinstance(asked, Ok)
    run_id = str(cast("dict[str, Any]", asked.outputs["main"])["run_id"])
    status = world.backtest["backtest_status"](run_id=run_id)["result"]
    by_workflow = str(status["result_id"])
    assert (status["state"], status["principal"], status["kind"]) == ("landed", "run:wf1", "run")
    assert fields(world.store, by_workflow)["principal"] == "run:wf1"
    read = world.backtest["backtest_results"](result_id=by_workflow)
    assert read["summary"]["measures"]["trades"] == 8
    assert len(read["result"]) == 8
    compared = world.backtest["backtest_compare"](left=by_chat["result_id"], right=by_workflow)
    assert (compared["same_trades"], compared["measures"]) == (True, {})


def test_a_run_longer_than_the_wait_answers_its_run_id_and_lands_later(world: World) -> None:
    world.backtest["backtest_run"](unit=world.dummy, **GAPS)
    world.control.settings_put("qmb", {"agent_wait_s": 1})
    try:
        answer = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]
    finally:
        world.control.settings_put("qmb", {"remove": ["agent_wait_s"]})
    status = world.backtest["backtest_status"]

    until(lambda: status(run_id=answer["run_id"])["result"]["state"] == "landed", "the run lands")
    assert (answer["status"], answer["result_id"], answer["waited_s"]) == ("running", None, 1.0)
    assert answer["run_id"].startswith("qmbr-pc-")


def test_a_blank_and_a_dummy_library_search_answer_the_draft_and_the_try_rows(
    world: World,
) -> None:
    run_id = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]["run_id"]

    found = {str(row["id"]): row for row in world.control.library_search("", limit=1000)}
    named = [str(row["id"]) for row in world.control.library_search("dummy")]

    draft = found[world.dummy]
    assert (draft["kind"], draft["sha256"], draft["ref"], draft["size"]) == ("unit", None, None, 0)
    assert cast("dict[str, Any]", draft["content"])["unit_id"] == DUMMY
    assert world.dummy in named
    try_rows = [found[i] for i in world.store.with_field("try", "run_id", run_id)]
    assert [(row["kind"], row["size"]) for row in try_rows] == [("try", 0), ("try", 0)]


def test_a_fingerprint_mismatch_lands_a_failed_result_and_counts_no_job_error(
    world: World,
) -> None:
    wrong = "fp1:sha256:" + "0" * 64

    answer = world.backtest["backtest_run"](unit=world.dummy, **GAPS, compiled_fp=wrong)["result"]

    landed = fields(world.store, answer["result_id"])
    assert (answer["status"], landed["status"], landed["compiled_fp"]) == (
        "failed",
        "failed",
        wrong,
    )
    assert landed["reason"].startswith("compiled_fingerprint:")
    assert cast("dict[str, Any]", world.runtime.status("qmb")["metrics"])["errors"] == 0


def test_a_failing_safety_verdict_refuses_the_run_with_its_report(world: World) -> None:
    unit = a_new_unit(world)
    compiled = LanderLibrary(world.store).compiled_fingerprint(unit)
    assert compiled is not None
    failing = Draft(
        "test-report",
        "g-failing",
        "g failing",
        fields={
            "check": "qml-g/1",
            "status": "finished",
            "compiled_fingerprint": compiled,
            "safety": {"verdict": "fail"},
        },
    )
    planted = world.store.put(OPERATOR, failing, on="main", expected_head=None).object_id

    with pytest.raises(ControlError) as refused:
        world.control.app_job("qmb", "jobs/backtest.py", inputs=asked(unit, MARCH), principal=CHAT)

    assert refused.value.code == "run_refused"
    assert str(refused.value).endswith(f"its report is {planted}")


def test_a_month_with_no_bars_is_refused_by_name_before_any_try(world: World) -> None:
    with pytest.raises(ControlError) as refused:
        world.control.app_job(
            "qmb",
            "jobs/backtest.py",
            inputs=asked(world.dummy, {"start": "2025-01-01", "end": "2025-02-01"}),
            principal=CHAT,
        )

    assert refused.value.code == "run_refused"
    assert "eurusd-m15-bid-2025-01-01-2025-02-01.csv is missing" in str(refused.value)


def test_a_crash_that_trips_the_breaker_fails_the_run_and_qmb_starts_again(
    world: World,
) -> None:
    world.backtest["backtest_run"](unit=world.dummy, **GAPS)
    queue = Volume(world.runtime.home, "qmb").root / "data" / "jobs"
    failed: list[BaseException] = []

    def run() -> None:
        try:
            world.runtime.run_job(
                "qmb",
                "jobs/backtest.py",
                inputs=asked(world.dummy, MARCH),
                principal=CHAT,
            )
        except AppError as error:
            failed.append(error)

    started = threading.Thread(target=run)
    started.start()
    until(lambda: any(queue.glob("*.request.json")), "the backtest queues")
    pid = int(cast("int", world.runtime.status("qmb")["pid"]))
    for process in [*psutil.Process(pid).children(recursive=True), psutil.Process(pid)]:
        process.kill()
    started.join(SETTLE_SECONDS)
    until(lambda: world.runtime.status("qmb")["status"] == "running", "QMB starts again")
    after = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]

    killed = [
        row
        for row in (
            fields(world.store, i)
            for i in world.store.with_field("backtest-result", "status", "killed")
        )
        if row["principal"] == CHAT
    ]
    assert [getattr(error, "code", None) for error in failed] == ["not_running"]
    assert len(killed) == 1
    assert after["status"] == "finished"


def test_a_study_that_allows_gaps_runs_the_month_the_hole_rule_fails(world: World) -> None:
    spec = {"origin": "written", "preset": "shipped", "markets": "admitted", "allow_gaps": True}
    draft = Draft("study-spec", "study-gaps", "gaps allowed", fields=cast("Any", spec))
    world.store.register_checker(STUDY_CHECKER, study_check)
    study = world.store.put(OPERATOR, draft, on="main", expected_head=None).object_id
    run = world.backtest["backtest_run"]

    refused = run(unit=world.dummy, window=MARCH)["result"]
    allowed = run(unit=world.dummy, window=MARCH, study=study)["result"]

    assert (refused["status"], fields(world.store, refused["result_id"])["reason"]) == (
        "failed",
        SUNDAY_HOLE,
    )
    assert (allowed["status"], fields(world.store, allowed["result_id"])["study"]) == (
        "finished",
        study,
    )
    holes = report(world.store, allowed["result_id"])["holes"]
    # The Sundays of 9, 16 and 23 March: the month's last bar opens on Friday 28 March.
    assert [(hole["market_id"], hole["bars_missing"]) for hole in holes] == [("fx.eurusd", 4)] * 3


def test_the_hole_limit_and_fill_count_in_settings_reach_the_run(world: World) -> None:
    world.control.settings_put("qmb", {"gap_bars_refuse": 4, "calibrated_min_fills": 7})
    try:
        answer = world.backtest["backtest_run"](unit=world.dummy, window=MARCH)["result"]
    finally:
        world.control.settings_put("qmb", {"remove": ["gap_bars_refuse", "calibrated_min_fills"]})

    run = Volume(world.runtime.home, "qmb").root / "data" / "runs" / answer["run_id"]
    written = json.loads((run / "in" / "request.json").read_text("utf-8"))
    assert answer["status"] == "finished"
    assert report(world.store, answer["result_id"])["holes"] == []
    assert (written["gap_bars_refuse"], written["calibrated_min_fills"]) == (4, 7)


type OnMain = Callable[..., str]


@pytest.fixture
def on_main(world: World) -> Generator[OnMain]:
    """What the node read lands on the real store through the host's own `venue_records`. Each item
    is withdrawn after its test, so the module's other literals stay on the fixtures."""
    items: set[str] = set()

    def on_this_store(market: Market, **symbol: int) -> str:
        item = node_read(world.store, market, **symbol)
        items.add(item)
        return item

    yield on_this_store
    for item in items:
        world.store.archive(OPERATOR, item, "the test is over")


def node_read(store: Store, market: Market, **symbol: int) -> str:
    answer = {
        "schema_version": "qmx.node.records/1",
        "venue": {"name": "icmarkets-ctrader", "platform": "ctrader", "sandbox": "demo"},
        "account": {"id": "9000", "world": "demo", "leverage": "30"},
        "instruments": [
            {
                "symbol": market.symbol,
                "quote_currency": "USD",
                "schedule_zone": "UTC",
                "trading_mode": "ENABLED",
                **symbol,
            }
        ],
    }
    rows = {row.kind: row for row in land(store, records_of(answer, [market]))}
    assert rows["instrument"].outcome == "landed"
    return rows["instrument"].item


GOLD = Market("XAUUSD", "gold", "metal", "metals-24x5@1", "America/New_York", "17:00")
GOLD_SYMBOL = {"digits": 2, "pip_position": 1, "lot_size": 10_000}
EURUSD = Market("EURUSD", "eurusd", "fx", "fx-24x5@1", "America/New_York", "17:00")
GBPUSD = Market("GBPUSD", "gbpusd", "fx", "fx-24x5@1", "America/New_York", "17:00")
AUDUSD = Market("AUDUSD", "audusd", "fx", "fx-24x5@1", "America/New_York", "17:00")
NZDUSD = Market("NZDUSD", "nzdusd", "fx", "fx-24x5@1", "America/New_York", "17:00")
USDCAD = Market("USDCAD", "usdcad", "fx", "fx-24x5@1", "America/New_York", "17:00")
EURGBP = Market("EURGBP", "eurgbp", "fx", "fx-24x5@1", "America/New_York", "17:00")
FX_SYMBOL = {"digits": 5, "pip_position": 4, "lot_size": 10_000_000}
EURUSD_ON_THE_FIXTURE = (
    "no Library record for this market, so it reads QML's test fixture: fx.eurusd reads eurusd.json"
)


def laid_record(world: World, run_id: str, market_id: str) -> dict[str, Any]:
    """The record a finished run's folder holds, as the tester read it."""
    folder = Volume(world.runtime.home, "qmb").root / "data" / "runs" / run_id / "in" / "records"
    return cast("dict[str, Any]", json.loads((folder / f"{market_id}.json").read_text("utf-8")))


def on_main_now(world: World, item: str) -> dict[str, Any]:
    """An item's fields at its head on `main`, with the version the Library counts for it."""
    head = world.store.head(item, MAIN)
    assert head is not None
    return {**fields(world.store, head[0]), "record_version": head[1]}


def test_a_record_on_main_reaches_the_run_and_its_fills(world: World, on_main: OnMain) -> None:
    item = on_main(GOLD, **GOLD_SYMBOL, step_volume=1_000, min_volume=1_000)

    answer = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]

    laid = laid_record(world, answer["run_id"], "metal.xauusd")
    gold = [
        fill
        for fill in report(world.store, answer["result_id"])["fills"]
        if fill["market_id"] == "metal.xauusd"
    ]
    assert laid == on_main_now(world, item)
    assert (laid["lot_step"], laid["record_version"]) == ("0.1", 1)
    assert gold
    assert {Decimal(fill["quantity"]) % Decimal("0.1") for fill in gold} == {Decimal(0)}
    assert fields(world.store, answer["result_id"])["labels"]["fixture_records"] == [
        EURUSD_ON_THE_FIXTURE
    ]


def test_a_market_with_only_a_library_record_runs(world: World, on_main: OnMain) -> None:
    item = on_main(GBPUSD, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)
    bars = Path(str(world.control.settings_get("qmb")["bars"]))
    for side in ("bid", "ask"):
        month = f"m15-{side}-2025-03-01-2025-04-01.csv"
        shutil.copyfile(bars / f"eurusd-{month}", bars / f"gbpusd-{month}")
    document = template(DUMMY)
    document["markets"] = [
        {
            "market_id": "fx.gbpusd",
            "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "GBPUSD"},
        }
    ]
    draft = Draft("unit", "unit-gbpusd", "gbpusd", fields=cast("Any", document))
    unit = world.store.put(
        OPERATOR, draft, on=drafts_ref("unit-gbpusd"), expected_head=None
    ).object_id

    answer = world.backtest["backtest_run"](unit=unit, **GAPS)["result"]

    assert answer["status"] == "finished"
    assert laid_record(world, answer["run_id"], "fx.gbpusd") == on_main_now(world, item)
    assert fields(world.store, answer["result_id"])["labels"]["fixture_records"] == []


def test_a_record_moved_on_main_shows_in_the_next_run(world: World, on_main: OnMain) -> None:
    on_main(EURUSD, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)
    run = world.backtest["backtest_run"]

    first = run(unit=world.dummy, **GAPS)["result"]
    on_main(EURUSD, **FX_SYMBOL, step_volume=100_000, min_volume=500_000)
    second = run(unit=world.dummy, **GAPS)["result"]

    before = laid_record(world, first["run_id"], "fx.eurusd")
    after = laid_record(world, second["run_id"], "fx.eurusd")
    assert (before["min_lot"], before["record_version"]) == ("0.01", 1)
    assert (after["min_lot"], after["record_version"]) == ("0.05", 2)


def test_a_study_forbidding_gaps_beats_a_chat_allowing_them(world: World) -> None:
    spec = {"origin": "written", "preset": "shipped", "markets": "admitted", "allow_gaps": False}
    draft = Draft("study-spec", "study-no-gaps", "no gaps", fields=cast("Any", spec))
    world.store.register_checker(STUDY_CHECKER, study_check)
    study = world.store.put(OPERATOR, draft, on="main", expected_head=None).object_id

    answer = world.backtest["backtest_run"](unit=world.dummy, study=study, **GAPS)["result"]

    assert (answer["status"], fields(world.store, answer["result_id"]).get("reason")) == (
        "failed",
        SUNDAY_HOLE,
    )


@pytest.fixture(scope="module")
def fresh(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    """A fresh home: no `[qmb] bars`, no CSV anywhere, only what a test puts through the door."""
    yield from a_world(tmp_path_factory.mktemp("fresh"), bars=None)


TICK_OFFSETS_MS = (0, 200_000, 400_000, 880_000)
"""Open, high, low and close, each at its own moment inside a bar, as `bridge.py` cuts them."""
APRIL = {"start": "2025-04-01", "end": "2025-05-01"}
THIRTY_ONE_DAYS_MS = 31 * 86_400_000


def month_door(world: World) -> MarketDoor:
    opened = MarketDoor.open(world.runtime.home / "market", {}, placement=Placement.PC)
    assert not is_refusal(opened)
    return opened.value


def ticks_in_the_store(
    world: World,
    cut_from: str,
    symbol: str,
    *,
    scale: int | None = 5,
    moved_ms: int = 0,
    month: int = 3,
) -> tuple[str, Path]:
    """QML's synthetic month of `cut_from`, four ticks a bar, committed as `symbol`'s through the
    real door. Answers the fingerprint and where the store keeps the month's file."""
    door = month_door(world)
    pair = [
        (SLICES / f"synthetic-{cut_from}-m15-{side}-2025-03-01-2025-04-01.csv").read_text("utf-8")
        for side in ("bid", "ask")
    ]
    bids, asks = (csv.DictReader(io.StringIO(text)) for text in pair)
    rows: list[tuple[int, int, int, float, float]] = []
    for bid, ask in zip(bids, asks, strict=True):
        for offset, name in zip(TICK_OFFSETS_MS, ("open", "high", "low", "close"), strict=True):
            digits = len(bid[name].partition(".")[2])
            rows.append(
                (
                    int(bid["timestamp"]) + offset + moved_ms,
                    int(Decimal(bid[name]).scaleb(digits)),
                    int(Decimal(ask[name]).scaleb(digits)),
                    1.0,
                    1.0,
                )
            )
    key = SeriesKey.try_create("dukascopy", symbol, "ticks", 2025, month)
    assert not is_refusal(key)
    staging = world.runtime.home / "staging"
    staged = staging / "dukascopy" / symbol / "ticks" / "-" / f"2025-{month:02d}.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    TypedWriter(staged, key.value.text, TICK_COLUMNS).add(sorted(rows)).finish()
    landed = door.commit([staged], staging=staging, born_on=Placement.PC)
    assert not is_refusal(landed)
    if scale is not None:
        assert not is_refusal(door.state_scale(key.value.series, scale))
    series = door.series_store()
    return landed.value[0].fingerprint, next(series.folder(key.value).glob("*.parquet"))


def a_unit_on(world: World, market: Market, **symbol: int) -> str:
    """A record for `market` on `main`, as the node's read lands it, and the dummy on it alone."""
    node_read(world.store, market, **symbol)
    market_id = f"{market.klass}.{market.symbol.lower()}"
    document = template(DUMMY)
    document["markets"] = [
        {
            "market_id": market_id,
            "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": market.symbol},
        }
    ]
    name = f"unit-{market.symbol.lower()}"
    draft = Draft("unit", name, market.symbol, fields=cast("Any", document))
    return world.store.put(OPERATOR, draft, on=drafts_ref(name), expected_head=None).object_id


def run_folder(world: World, run_id: str) -> Path:
    return Volume(world.runtime.home, "qmb").root / "data" / "runs" / run_id


def run_tries(store: Store) -> list[str]:
    return sorted(store.with_field("try", "kind", "run"))


def test_a_fresh_home_with_ticks_in_the_store_lands_a_result(fresh: World) -> None:
    fingerprint, _ = ticks_in_the_store(fresh, "eurusd", "GBPUSD")
    unit = a_unit_on(fresh, GBPUSD, **FX_SYMBOL, step_volume=500_000, min_volume=500_000)

    answer = fresh.backtest["backtest_run"](unit=unit, **GAPS)["result"]

    landed = fields(fresh.store, answer["result_id"])
    laid = run_folder(fresh, answer["run_id"]) / "in"
    consumed = fresh.store.walk(OPERATOR, [answer["result_id"]], ("consumed",), "out", depth=1)
    cards = [fresh.store.get(OPERATOR, found.object_id) for found in consumed]
    fills = report(fresh.store, answer["result_id"])["fills"]
    assert answer["status"] == "finished"
    assert [(card.kind, card.fields["partition_digests"]) for card in cards] == [
        ("dataset", [fingerprint])
    ]
    assert landed["request_fp"] == fingerprint_bytes((laid / "request.json").read_bytes()).value
    assert landed["labels"]["datasets"] == ["dukascopy/GBPUSD/ticks/-"]
    assert (landed["fidelity"], landed["labels"]["fixture_records"]) == ("quotes", [])
    assert not (laid / "bars").exists()
    assert json.loads((laid / "data" / "fx.gbpusd" / "card.json").read_text("utf-8"))["scale"] == 5
    assert fills
    assert {Decimal(fill["quantity"]) % Decimal("0.05") for fill in fills} == {Decimal(0)}


def test_a_month_of_bid_and_ask_bars_is_read_before_its_ticks(fresh: World) -> None:
    ticks_in_the_store(fresh, "eurusd", "EURGBP")
    door = month_door(fresh)
    staging = fresh.runtime.home / "staging"
    staged: list[Path] = []
    for side in ("bid", "ask"):
        key = SeriesKey.try_create("dukascopy", "EURGBP", "bar-m1", 2025, 3, side)
        assert not is_refusal(key)
        with (SLICES / f"synthetic-eurusd-m15-{side}-2025-03-01-2025-04-01.csv").open(
            encoding="utf-8", newline=""
        ) as month:
            rows = [
                (
                    int(bar["timestamp"]) + 14 * 60_000,
                    *(int(Decimal(bar[n]).scaleb(5)) for n in ("open", "high", "low", "close")),
                    1.0,
                )
                for bar in csv.DictReader(month)
            ]
        path = staging / "dukascopy" / "EURGBP" / "bar-m1" / side / "2025-03.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        TypedWriter(path, key.value.text, BAR_COLUMNS).add(rows).finish()
        staged.append(path)
        assert not is_refusal(door.state_scale(key.value.series, 5))
    assert not is_refusal(door.commit(staged, staging=staging, born_on=Placement.PC))
    unit = a_unit_on(fresh, EURGBP, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)

    answer = fresh.backtest["backtest_run"](unit=unit, **GAPS)["result"]

    landed = fields(fresh.store, answer["result_id"])
    laid = run_folder(fresh, answer["run_id"]) / "in" / "data" / "fx.eurgbp"
    assert answer["status"] == "finished"
    assert json.loads((laid / "card.json").read_text("utf-8"))["kind"] == "bar-m1"
    assert landed["labels"]["datasets"] == [
        "dukascopy/EURGBP/bar-m1/bid",
        "dukascopy/EURGBP/bar-m1/ask",
    ]


def test_no_month_is_refused_naming_the_month_and_the_template(fresh: World) -> None:
    before = run_tries(fresh.store)

    with pytest.raises(ControlError) as refused:
        fresh.control.app_job(
            "qmb",
            "jobs/backtest.py",
            inputs=asked(fresh.dummy, {"start": "2025-01-01", "end": "2025-02-01"}),
            principal=CHAT,
        )

    assert refused.value.code == "run_refused"
    assert str(refused.value) == (
        "no data for 2025-01-01 to 2025-02-01: fx.eurusd 2025-01, metal.xauusd 2025-01 not in the "
        "market store under dukascopy; run the download-dukascopy template for each month"
    )
    assert run_tries(fresh.store) == before


def test_a_month_through_a_csv_and_through_the_store_gives_the_same_trades(
    fresh: World, tmp_path: Path
) -> None:
    ticks_in_the_store(fresh, "eurusd", "EURUSD")
    ticks_in_the_store(fresh, "xauusd", "XAUUSD", scale=3)
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, tmp_path / source.name.removeprefix("synthetic-"))
    run = fresh.backtest["backtest_run"]

    fresh.control.settings_put("qmb", {"bars": str(tmp_path)})
    try:
        by_csv = run(unit=fresh.dummy, **GAPS)["result"]
    finally:
        fresh.control.settings_put("qmb", {"remove": ["bars"]})
    by_store = run(unit=fresh.dummy, **GAPS)["result"]

    csv_fields = fields(fresh.store, by_csv["result_id"])
    store_fields = fields(fresh.store, by_store["result_id"])
    assert (by_csv["status"], by_store["status"]) == ("finished", "finished")
    assert (csv_fields["measures"]["trades"], store_fields["measures"]["trades"]) == (8, 8)
    assert csv_fields["measures"]["trade_list_fp"] == store_fields["measures"]["trade_list_fp"]
    assert "request_fp" not in csv_fields
    assert "datasets" not in csv_fields["labels"]


def test_a_sealed_month_is_refused_and_no_sealed_file_sits_in_a_run_folder(fresh: World) -> None:
    fingerprint, _ = ticks_in_the_store(fresh, "eurusd", "AUDUSD")
    unit = a_unit_on(fresh, AUDUSD, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)
    fresh.store.register_checker(STUDY_CHECKER, study_check)
    sealed_spec = {"origin": "written", "holdout": {"boundary": "2025-03", "months": 12}}
    draft = Draft("study-spec", "study-sealed", "sealed", fields=cast("Any", sealed_spec))
    study = fresh.store.put(OPERATOR, draft, on="main", expected_head=None).object_id
    runs = Volume(fresh.runtime.home, "qmb").root / "data" / "runs"
    before = run_tries(fresh.store)

    with pytest.raises(ControlError) as refused:
        fresh.control.app_job(
            "qmb",
            "jobs/backtest.py",
            inputs=cast("Document", {**asked(unit, MARCH), "study": study}),
            principal=CHAT,
        )
    sealed_files = list(runs.rglob(f"{fingerprint}.parquet"))
    tries_after_the_refusal = run_tries(fresh.store)
    unsealed = fresh.backtest["backtest_run"](unit=unit, **GAPS)["result"]

    assert refused.value.code == "run_refused"
    assert str(refused.value) == "this month is sealed for the final look: 2025-03"
    assert tries_after_the_refusal == before
    assert sealed_files == []
    assert unsealed["status"] == "finished"
    assert [path.parent.name for path in runs.rglob(f"{fingerprint}.parquet")] == ["ticks", "ticks"]


def test_one_market_of_a_two_market_unit_lands_naming_that_market(fresh: World) -> None:
    ticks_in_the_store(fresh, "eurusd", "EURUSD")

    answer = fresh.backtest["backtest_run"](unit=fresh.dummy, markets=["fx.eurusd"], **GAPS)[
        "result"
    ]

    landed = fields(fresh.store, answer["result_id"])
    laid = run_folder(fresh, answer["run_id"]) / "in"
    assert (answer["status"], landed["markets"]) == ("finished", ["fx.eurusd"])
    assert landed["measures"]["trades"] == 6
    assert [folder.name for folder in (laid / "data").iterdir()] == ["fx.eurusd"]
    assert json.loads((laid / "request.json").read_text("utf-8"))["markets"] == ["fx.eurusd"]
    assert {t["market_id"] for t in report(fresh.store, answer["result_id"])["trades"]} == {
        "fx.eurusd"
    }


def test_every_other_data_refusal_comes_before_any_try(fresh: World) -> None:
    ticks_in_the_store(fresh, "eurusd", "NZDUSD", scale=None)
    unsaid = a_unit_on(fresh, NZDUSD, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)
    ticks_in_the_store(fresh, "eurusd", "EURUSD")
    source = month_door(fresh)
    staged = fresh.runtime.home / "staging" / "other" / "EURUSD" / "ticks" / "-" / "2025-03.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        next(source.series_store().root.glob("dukascopy/EURUSD/ticks/-/2025-03/*.parquet")),
        staged,
    )
    landed = source.commit([staged], staging=fresh.runtime.home / "staging", born_on=Placement.PC)
    assert not is_refusal(landed)
    assert not is_refusal(source.state_scale("other/EURUSD/ticks/-", 5))
    fresh.store.register_checker(STUDY_CHECKER, study_check)
    other_spec = {"origin": "written", "source": "other"}
    draft = Draft("study-spec", "study-other", "other", fields=cast("Any", other_spec))
    study = fresh.store.put(OPERATOR, draft, on="main", expected_head=None).object_id
    before = run_tries(fresh.store)

    def refused(inputs: dict[str, Any]) -> str:
        with pytest.raises(ControlError) as answer:
            fresh.control.app_job(
                "qmb", "jobs/backtest.py", inputs=cast("Document", inputs), principal=CHAT
            )
        assert answer.value.code == "run_refused"
        return str(answer.value)

    assert refused({**asked(unsaid, MARCH)}) == (
        "dukascopy/NZDUSD/ticks/- states no price scale; run the download-dukascopy template's "
        "check on its card, or download the month again"
    )
    assert refused(
        {
            **asked(fresh.dummy, MARCH),
            "markets": ["fx.eurusd"],
            "source": "dukascopy",
            "study": study,
        }
    ) == (
        "fx.eurusd holds this window under both dukascopy and other; the request and the study "
        "name different sources, so name one"
    )
    assert refused({**asked(fresh.dummy, MARCH), "markets": ["fx.gbpusd"]}) == (
        "this unit does not trade fx.gbpusd; it trades fx.eurusd, metal.xauusd"
    )
    assert run_tries(fresh.store) == before


def test_a_copy_that_fails_after_the_try_opened_closes_that_try(fresh: World) -> None:
    _, stored = ticks_in_the_store(fresh, "eurusd", "USDCAD", moved_ms=THIRTY_ONE_DAYS_MS, month=4)
    unit = a_unit_on(fresh, USDCAD, **FX_SYMBOL, step_volume=100_000, min_volume=100_000)
    compiled = LanderLibrary(fresh.store).compiled_fingerprint(unit)
    passing = Draft(
        "test-report",
        "g-usdcad",
        "g passing",
        fields={
            "check": "qml-g/1",
            "status": "finished",
            "compiled_fingerprint": compiled,
            "safety": {"verdict": "pass"},
        },
    )
    fresh.store.put(OPERATOR, passing, on="main", expected_head=None)
    stored.unlink()
    before = run_tries(fresh.store)

    with pytest.raises(ControlError) as refused:
        fresh.control.app_job(
            "qmb",
            "jobs/backtest.py",
            inputs=asked(unit, APRIL),
            principal=CHAT,
        )

    new = [fields(fresh.store, i) for i in run_tries(fresh.store) if i not in before]
    assert refused.value.code == "run_refused"
    assert str(refused.value) == "fx.usdcad: the series state names a file that is not there"
    assert sorted(str(row["state"]) for row in new) == ["failed", "opened"]


def test_the_first_start_click_keeps_qmb_running_at_every_host_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = tmp_path / "profile"
    with monkeypatch.context() as scoped:
        for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
            (profile / part).mkdir(parents=True)
            scoped.setenv(name, str(profile / part))
        scoped.setattr(first_start, "_fixed_drives", list)
        layout = make_new(tmp_path / "QMX", Places({"APPDATA": str(profile / "Roaming")}))
    assert (profile / "Roaming" / "QMX" / "home.toml").is_file()
    runtime = Supervisor(layout.home)
    with Store.open(layout.home / "library", redactor=redact, wall=Clock()) as store:
        runtime.attach_landers(landers(store, runtime, "pc"))
        try:
            first = enable_first_party(layout.home, runtime)
            again = enable_first_party(layout.home, runtime)
        finally:
            runtime.close()
        next_start = Supervisor(layout.home)
        next_start.attach_landers(landers(store, next_start, "pc"))
        try:
            started = enable_first_party(layout.home, next_start)
            status = next_start.status("qmb")["status"]
        finally:
            next_start.close()

    enabled = ["qmb", "mis"]
    assert (first, again, started, status) == (enabled, enabled, enabled, "running")
