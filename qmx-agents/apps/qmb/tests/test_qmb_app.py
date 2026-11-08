"""QMB as the first mini app: every door starts one `backtest` job that trades the compiled dummy.

The app is the shipped folder, installed into a real supervisor with its own locked environment,
and `qmb-run` is the host's own composition over a real Library store. The bars are QML's
synthetic March 2025 month (`qml/tests/fixtures/slices`), saved under dukascopy-node's names,
so every literal below holds on every machine.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import threading
import time
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any, cast

import psutil
import pytest
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
from qmx_library.port import Draft
from qmx_library.principal import Principal, drafts_ref
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


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("qmb")
    bars = root / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    control = ControlService(root / "home")
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
            yield World(control, store, runtime, dummy, domain_functions(context)["backtest"])
        finally:
            control.close()


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
    assert landed["tester"] == {"app": "qmb", "version": "1.0.0"}
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


def test_every_fill_is_its_sizer_receipt_rounded_down_to_the_lot_step(world: World) -> None:
    answer = world.backtest["backtest_run"](unit=world.dummy, **GAPS)["result"]

    fills = report(world.store, answer["result_id"])["fills"]
    entries = [fill for fill in fills if fill["kind"] == "entry"]
    assert entries
    assert all(
        Decimal(f["quantity"])
        == Decimal(f["receipt_quantity"]).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        for f in entries
    )


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
