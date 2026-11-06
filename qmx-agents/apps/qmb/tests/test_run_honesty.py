"""A run reports what happened: its costs, its failures, its first answer and its folder.

The app is the shipped folder on a real supervisor, the Library a real store, and the bars QML's
synthetic March 2025 month, as in `test_qmb_app.py`, so every literal holds on every machine.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Generator
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from qml.catalogue.loader import block_fingerprint
from qmx_apps.supervisor import Supervisor
from qmx_control.models import LibraryInput
from qmx_control.service import ControlError
from qmx_engine.ledger import redact
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    LanderLibrary,
    landers,
    register_checkers,
)
from qmx_host.market_data import MarketDoor, Placement  # pyright: ignore[reportMissingTypeStubs]
from qmx_judge.judge import quick_spec
from qmx_library.port import Draft
from qmx_library.principal import drafts_ref
from qmx_library.store import Store
from qmx_tools.gather import DUMMY, STDLIB, template
from test_qmb_app import (
    CHAT,
    GAPS,
    MARCH,
    OPERATOR,
    SLICES,
    Clock,
    World,
    a_world,
    fields,
    report,
    reports,
    run_folder,
    until,
)

COMMISSION = {"schema": "qmx.qmb.cost-profile/1", "broker": "ic", "account_type": "raw", "fills": 0}
"""A stated profile's head. `hours` and `market_id` are each market's own."""


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("honesty")
    bars = root / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    for made in a_world(root, bars=bars):
        register_checkers(made.store)
        yield made


def a_unit(world: World, name: str, ema_period: str) -> str:
    """The dummy with another EMA period: another compiled unit, with no behaviour check yet."""
    document = template(DUMMY)
    numbers = cast("dict[str, dict[str, Any]]", document["numbers"])
    numbers["ema_period"]["default"] = ema_period
    draft = Draft("unit", name, name, fields=cast("Any", document))
    return world.store.put(OPERATOR, draft, on=drafts_ref(name), expected_head=None).object_id


def a_stated_profile(world: World, per_lot: str) -> str:
    """A cost profile as an agent saves it, charging `per_lot` on every fill, every hour."""
    hours = [
        {"hour_of_week": hour, "slippage": "0", "commission_per_lot": per_lot}
        for hour in range(168)
    ]
    content = {
        "costs": {
            market: {**COMMISSION, "market_id": market, "hours": hours}
            for market in ("fx.eurusd", "metal.xauusd")
        },
        "funding": {"fx.eurusd": "timestamp,rate\n1740787200000,0.0001\n"},
    }
    saved = world.control.library_save(
        LibraryInput(title="commission", kind="cost-profile", content=cast("Any", content))
    )
    return str(saved["id"])


def job(world: World, kind: str = "backtest", **inputs: Any) -> dict[str, Any]:
    return world.control.app_job(
        "qmb", f"jobs/{kind}.py", inputs=cast("Any", inputs), principal=CHAT
    )


def landed_of(world: World, ran: dict[str, Any]) -> dict[str, Any]:
    [found] = world.store.with_field("backtest-result", "run_id", str(ran["run_id"]))
    return {"id": found, **fields(world.store, found)}


def test_a_stated_cost_profile_changes_money_and_not_r(world: World) -> None:
    profile = a_stated_profile(world, "3.50")

    plain = landed_of(world, job(world, unit=world.dummy, **GAPS))
    costed = landed_of(world, job(world, unit=world.dummy, **GAPS, cost_profile=profile))

    rows = report(world.store, costed["id"])
    laid = run_folder(world, costed["run_id"]) / "in"
    assert (plain["measures"]["total_r"], costed["measures"]["total_r"]) == ("-2.2597", "-2.2597")
    assert (plain["measures"]["net_money"], costed["measures"]["net_money"]) == (
        "-114.97",
        "-161.39",
    )
    assert [t["r"] for t in rows["trades"]] == [
        t["r"] for t in report(world.store, plain["id"])["trades"]
    ]
    assert len(rows["cash_events"]) == 16
    assert sum(Decimal(t["cash"]) for t in rows["trades"]) == Decimal("-47.38")
    assert costed["labels"]["costs_uncalibrated"] is True
    assert costed["labels"]["cost_profile"] == profile
    assert json.loads((laid / "costs" / "fx.eurusd.json").read_text("utf-8"))["fills"] == 0
    assert (laid / "funding" / "fx.eurusd.csv").read_text("utf-8").startswith("timestamp,rate")

    verdict = world.backtest["backtest_judge_run"](results=[costed["id"]])["result"]

    assert "costs uncalibrated" in verdict["says"]


def test_a_block_that_raises_lands_a_failed_result_with_its_reason(world: World) -> None:
    entry = json.loads((STDLIB / "rsi-cross-back" / "1" / "entry.json").read_text("utf-8"))
    source = (STDLIB / "rsi-cross-back" / "1" / "block.py").read_bytes().replace(b"\r\n", b"\n")
    update = b"    def update(self, evidence: Mapping[str, object]) -> Signal | None:\n"
    assert update in source
    raising = source.replace(update, update + b"        return 1 / 0\n")
    fingerprint = block_fingerprint(raising).value
    kind = entry.pop("component_type")
    face = {**entry, "entry_id": "rsi-raises", "fingerprint": fingerprint}
    world.store.put(
        OPERATOR,
        Draft(
            "component",
            "rsi-raises",
            fields=cast("Any", {"component_type": kind, "entry": face}),
            blobs={"code": raising},
        ),
        on=drafts_ref("rsi-raises"),
        expected_head=None,
    )
    document = template(DUMMY)
    text = json.dumps(document).replace("rsi-cross-back", "rsi-raises")
    pinned = json.loads(text)
    for pin in pinned["pins"]:
        if pin["entry_id"] == "rsi-raises":
            pin["fingerprint"] = fingerprint
    draft = Draft("unit", "unit-raises", "raises", fields=cast("Any", pinned))
    unit = world.store.put(
        OPERATOR, draft, on=drafts_ref("unit-raises"), expected_head=None
    ).object_id
    compiled = LanderLibrary(world.store).compiled_fingerprint(unit)
    assert compiled is not None
    passing = {
        "check": "qml-g/1",
        "run_id": "qmbr-g-raises",
        "status": "finished",
        "compiled_fingerprint": compiled,
        "behaviour": {"slice": {"market_ids": ["fx.eurusd", "metal.xauusd"]}},
        "safety": {"verdict": "pass"},
    }
    world.store.put(
        OPERATOR,
        Draft("test-report", "g-raises", "g", fields=cast("Any", passing)),
        on="main",
        expected_head=None,
    )
    errors = cast("dict[str, Any]", world.runtime.status("qmb")["metrics"])["errors"]

    landed = landed_of(world, job(world, unit=unit, **GAPS))

    assert (landed["status"], landed["reason"]) == (
        "failed",
        "ZeroDivisionError: division by zero",
    )
    assert cast("dict[str, Any]", world.runtime.status("qmb")["metrics"])["errors"] == errors


def test_a_slow_first_run_answers_something_to_poll(world: World) -> None:
    unit = a_unit(world, "unit-slow-first", "103")
    status = world.backtest["backtest_status"]
    world.control.settings_put("qmb", {"agent_wait_s": 2})
    try:
        answer = world.backtest["backtest_run"](unit=unit, **GAPS)["result"]
    finally:
        world.control.settings_put("qmb", {"remove": ["agent_wait_s"]})
    check = answer["run_id"]

    assert (answer["status"], answer["result_id"], answer["waited_s"]) == ("checking", None, 2.0)
    assert status(run_id=check)["result"]["kind"] == "check"
    until(lambda: status(run_id=check)["result"]["run"] is not None, "the poll names the run")
    run = status(run_id=check)["result"]["run"]
    assert run != check
    until(lambda: status(run_id=run)["result"]["state"] == "landed", "the run lands")
    assert status(run_id=run)["result"]["kind"] == "run"


def test_motion_both_runs_from_the_row(world: World) -> None:
    unit = a_unit(world, "unit-both", "104")

    answer = world.backtest["backtest_run"](unit=unit, motion="both", **GAPS)["result"]

    landed = fields(world.store, answer["result_id"])
    assert (answer["status"], landed["motion"]) == ("finished", "both")
    assert landed["measures"]["trades"] == 8
    assert landed["measures"]["motion_off"]["trades"] == 8


def test_a_run_folder_loses_its_bars_after_landing(world: World) -> None:
    profile = a_stated_profile(world, "1.00")
    unit = a_unit(world, "unit-folder", "105")
    before = {row["run_id"] for row in reports(world.store)}

    landed = landed_of(world, job(world, unit=unit, **GAPS, cost_profile=profile))

    laid = run_folder(world, landed["run_id"]) / "in"
    [check] = [row for row in reports(world.store) if row["run_id"] not in before]
    checked = run_folder(world, str(check["run_id"])) / "in"
    assert sorted(path.name for path in laid.iterdir()) == [
        "blocks",
        "costs",
        "funding",
        "records",
        "request.json",
        "unit.json",
    ]
    assert sorted(path.name for path in checked.iterdir()) == [
        "blocks",
        "costs",
        "funding",
        "records",
        "request.json",
        "unit.json",
    ]


def test_a_failed_run_loses_its_bars_too(world: World) -> None:
    landed = landed_of(world, job(world, unit=world.dummy, window=MARCH))

    laid = run_folder(world, landed["run_id"]) / "in"
    assert landed["status"] == "failed"
    assert not (laid / "bars").exists()


def test_each_market_answers_for_its_own_behaviour_check(world: World) -> None:
    unit = a_unit(world, "unit-markets", "106")
    before = len(reports(world.store))

    one = job(world, unit=unit, markets=["fx.eurusd"], **GAPS)
    after_one = reports(world.store)[before:]
    whole = job(world, unit=unit, **GAPS)
    after_whole = reports(world.store)[before:]
    again = job(world, unit=unit, markets=["metal.xauusd"], **GAPS)

    assert [row["behaviour"]["slice"]["market_ids"] for row in after_one] == [["fx.eurusd"]]
    assert [row["behaviour"]["slice"]["market_ids"] for row in after_whole] == [
        ["fx.eurusd"],
        ["fx.eurusd", "metal.xauusd"],
    ]
    assert len(reports(world.store)[before:]) == 2
    assert [landed_of(world, ran)["status"] for ran in (one, whole, again)] == ["finished"] * 3


def test_a_quick_study_keeps_his_settings_seal(tmp_path: Path) -> None:
    sealed = {"holdout": True, "holdout_boundary": "2025-03"}
    runtime = Supervisor(tmp_path / "home")
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as store:
        register_checkers(store)
        door = MarketDoor.open(
            runtime.home / "market", sealed, placement=Placement.PC, settings=lambda: sealed
        )
        assert not isinstance(door, Exception)
        run = landers(store, runtime, "pc", door=door.value)["qmb-run"]
        draft = Draft("unit", "unit-seal", "seal", fields=cast("Any", template(DUMMY)))
        unit = store.put(OPERATOR, draft, on=drafts_ref("unit-seal"), expected_head=None).object_id

        def refusal(name: str, spec: dict[str, Any]) -> str:
            study = Draft("study-spec", name, name, fields=cast("Any", spec))
            pin = store.put(OPERATOR, study, on="main", expected_head=None).object_id
            with pytest.raises(ValueError) as refused:
                run.open(
                    "qmb",
                    "1.0.0",
                    "jobs/backtest.py",
                    {"unit": unit, "window": MARCH, "study": pin},
                    CHAT,
                )
            return str(refused.value)

        quick = refusal("study-quick-seal", quick_spec(None))
        written = refusal("study-off", {"origin": "written", "holdout": "off"})
        runtime.close()

    assert quick == "this month is sealed for the final look: 2025-03"
    assert written.startswith("no data for 2025-03-01 to 2025-04-01")


def test_nothing_starts_on_a_cost_profile_that_is_not_one(world: World) -> None:
    with pytest.raises(ControlError) as refused:
        job(world, unit=world.dummy, **GAPS, cost_profile=world.dummy)

    assert refused.value.code == "run_refused"
    assert str(refused.value) == f"cost_profile {world.dummy} is a unit, not a cost-profile"
