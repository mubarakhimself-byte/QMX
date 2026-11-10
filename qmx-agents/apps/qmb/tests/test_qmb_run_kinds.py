"""QMB's other run kinds as counted jobs, through the real supervisor and the host's `qmb-run`.

A sweep, a walk-forward and an optimize run land one `recorded` try per cell, fold or candidate
in the unit's family; a what-if run lands one `whatif_rerun` try per scenario that can improve
the result and is refused when a worsen-only scenario improves; the judge reads walk-forward,
random-entry and cost-stress evidence only from a run of that kind; and `replay_check` replays a
recorded day with a per-decision diff. The bars are QML's synthetic March 2025 month, so every
literal holds on every machine.
"""

from __future__ import annotations

import io
import json
import runpy
import shutil
import sys
import threading
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq  # pyright: ignore[reportMissingTypeStubs]
import pytest
from qmb.analysis.replay_diff import decision_diff
from qmb.execution.fill import FillKind
from qmb.host.unit_handler import UnitTrade
from qmb.optimize.cscv import probability_of_overfitting
from qmb.robustness.unit_walk import walk_forward
from qmf.core.chrono import Instant
from qmf.core.refusal import is_refusal
from qml.unit.model import Side
from qmx_control.service import ControlError, ControlService, WorkflowEngine
from qmx_engine.ledger import redact
from qmx_host.first_start import land_dummy  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    STUDY_CHECKER,
    landers,
    study_check,
)
from qmx_judge.landing import Lander, Stored
from qmx_judge.runs import BundleRefused, Landing, parse_bundle
from qmx_library.principal import Principal
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

APP = Path(__file__).resolve().parents[1]
SLICES = APP.parents[2] / "qml" / "tests" / "fixtures" / "slices"
OPERATOR = Principal("operator")
CHAT = "agent:chat-9"
MARCH: dict[str, Any] = {"window": {"start": "2025-03-01", "end": "2025-04-01"}, "allow_gaps": True}
"""The synthetic month has a 4-bar Sunday-open hole each week, so every run here allows gaps."""


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
    def principal(self) -> Caller:
        return Caller(CHAT)

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        return []


@dataclass
class World:
    control: ControlService
    store: Store
    dummy: str
    tools: dict[str, Any]


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("qmb-kinds")
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
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        runtime.install(APP, trust="first_party")
        runtime.start("qmb")
        store.register_checker(STUDY_CHECKER, study_check)
        dummy = land_dummy(store)
        assert dummy is not None
        context = DomainContext(root=root / "tools")
        context.control, context.library = control, control.library
        try:
            yield World(control, store, dummy, domain_functions(context)["backtest"])
        finally:
            control.close()


def fields(store: Store, object_id: str) -> dict[str, Any]:
    return dict(store.get(OPERATOR, object_id).fields)


def job(world: World, kind: str, **inputs: Any) -> tuple[str, dict[str, Any]]:
    """Run one job of the dummy over March; its run id and its landed result's fields."""
    ran = world.control.app_job(
        "qmb", f"jobs/{kind}.py", inputs={"unit": world.dummy, **MARCH, **inputs}, principal=CHAT
    )
    run_id = str(ran["run_id"])
    [result] = world.store.with_field("backtest-result", "run_id", run_id)
    return result, fields(world.store, result)


def counted(world: World, run_id: str) -> list[dict[str, Any]]:
    found = [fields(world.store, i) for i in world.store.with_field("try", "state", "recorded")]
    return sorted(
        (row for row in found if str(row["run_id"]).startswith(f"{run_id}/")),
        key=lambda row: str(row["run_id"]),
    )


def report(world: World, result_id: str) -> dict[str, Any]:
    blob = world.store.get(OPERATOR, result_id).blobs["report"]
    return cast("dict[str, Any]", json.loads(world.store.read_blob(blob.blob_id)))


def test_a_six_cell_sweep_lands_six_tries_in_the_units_family(world: World) -> None:
    grid = {
        "markets": ["fx.eurusd", "metal.xauusd"],
        "numbers": {"ema_period": ["50", "100", "150"]},
    }

    result, landed = job(world, "sweep", grid=grid)

    run_id = landed["run_id"]
    [opened] = [
        i
        for i in world.store.with_field("try", "run_id", run_id)
        if fields(world.store, i)["state"] == "opened"
    ]
    family = fields(world.store, opened)["family"]
    rows = counted(world, run_id)
    assert (landed["status"], landed["kind"]) == ("finished", "sweep")
    assert [(r["kind"], r["state"], r["market"]) for r in rows] == [
        ("run", "recorded", "fx.eurusd"),
        ("run", "recorded", "fx.eurusd"),
        ("run", "recorded", "fx.eurusd"),
        ("run", "recorded", "metal.xauusd"),
        ("run", "recorded", "metal.xauusd"),
        ("run", "recorded", "metal.xauusd"),
    ]
    assert {(r["family"], r["principal"], tuple(r["links"])) for r in rows} == {
        (family, CHAT, (opened, result))
    }
    cells = report(world, result)["cells"]
    assert "trades" not in report(world, result)
    assert [(c["markets"], c["numbers"], c["status"]) for c in cells][:2] == [
        (["fx.eurusd"], {"ema_period": "50"}, "finished"),
        (["fx.eurusd"], {"ema_period": "100"}, "finished"),
    ]
    assert len({c["compiled_fp"] for c in cells}) == 6
    assert [(c["trades"], c["total_r"]) for c in cells] == [
        (3, "-1.6964"),
        (6, "-3.2846"),
        (4, "-1.8180"),
        (3, "0.0013"),
        (2, "1.0013"),
        (3, "-1.0258"),
    ]


def test_a_sweep_that_traded_is_judged_on_its_trades(world: World) -> None:
    result, landed = job(world, "sweep", grid={"markets": ["fx.eurusd"]})

    answer = world.tools["backtest_judge_run"](results=[result])["result"]

    assert landed["measures"]["trades"] == 6
    assert answer["overall"] == "too_thin"
    assert answer["per_market"] == [{"market": "fx.eurusd", "outcome": "too_thin", "trades": 6}]
    assert answer["cards"] == {}
    assert [t["market_id"] for t in report(world, result)["trades"]] == ["fx.eurusd"] * 6


def test_a_worsen_only_scenario_that_improves_is_refused_with_its_reason(world: World) -> None:
    improves = [{"name": "cost_shock", "params": {"extra_r": "-0.5"}}]

    with pytest.raises(ControlError) as refused:
        world.control.app_job(
            "qmb",
            "jobs/whatif.py",
            inputs=cast("Any", {"unit": world.dummy, **MARCH, "scenarios": improves}),
            principal=CHAT,
        )

    failed = [
        fields(world.store, i)
        for i in world.store.with_field("backtest-result", "kind", "whatif")
        if fields(world.store, i)["status"] == "failed"
    ]
    assert refused.value.code == "result_refused"
    assert str(refused.value) == WORSEN_REFUSAL
    assert [row["reason"] for row in failed] == [WORSEN_REFUSAL]
    assert counted(world, failed[0]["run_id"]) == []


WORSEN_REFUSAL = (
    "scenario 1-cost_shock is declared worsen only but improved expectancy_r from -0.2854125 to "
    "0.2145875; a scenario that can improve a result is a counted rerun"
)


def test_a_scenario_that_may_improve_is_a_counted_rerun_and_a_view_is_not(
    world: World,
) -> None:
    scenarios = [
        {"name": "skip_weekdays", "params": {"days": ["monday"]}},
        {"name": "skip_weekdays", "params": {"days": ["friday"]}},
        {"name": "drop_top_trades", "params": {"fraction": "0.25"}},
        {"name": "drop_top_trades", "params": {"fraction": "1"}},
    ]

    _, landed = job(world, "whatif", scenarios=scenarios)

    rows = counted(world, landed["run_id"])
    assert landed["status"] == "finished"
    assert [(r["kind"], r["run_id"].rsplit("/", 1)[1]) for r in rows] == [
        ("whatif_rerun", "1-skip_weekdays"),
        ("whatif_rerun", "2-skip_weekdays"),
    ]
    assert [
        (s["name"], s["direction"], s["answer"], s["value"])
        for s in landed["measures"]["scenarios"]
    ] == [
        ("1-skip_weekdays", "may_improve", "measured", "-0.04721666666666666666666666667"),
        ("2-skip_weekdays", "may_improve", "measured", "-0.3850142857142857142857142857"),
        ("3-drop_top_trades", "worsen_only", "measured", "-0.7827333333333333333333333333"),
        ("4-drop_top_trades", "worsen_only", "no_trades", None),
    ]


def test_a_whatif_result_that_names_a_scenario_twice_is_refused(tmp_path: Path) -> None:
    library, lander = in_memory_lander()
    ticket = lander.open("qmb", "1.0.0", "jobs/whatif.py", {"unit": "unit-1"}, CHAT)
    assert ticket is not None
    twice = {"name": "s", "direction": "may_improve", "base": "0", "value": "0.1"}
    bundle = parse_bundle(
        {
            "schema_version": 1,
            "run_id": ticket.run_id,
            "status": "finished",
            "tester": {"app": "qmb"},
            "measures": {"scenarios": [twice, twice]},
        }
    )

    with pytest.raises(BundleRefused) as refused:
        lander.close(Landing(ticket, bundle, tmp_path))

    assert refused.value.problems == ("a whatif result names each thing it tried once",)
    assert list(library.kinds.values()) == ["try"]


def test_the_judge_reads_each_check_from_the_run_of_that_kind(world: World) -> None:
    backtest = world.tools["backtest_run"](unit=world.dummy, **MARCH)["result"]["result_id"]
    walked, walk = job(world, "walk_forward", split={"folds": 3}, ranges=EMA_RANGE)
    stressed, robust = job(world, "robustness", resamples=50)

    verdict = world.tools["backtest_judge_run"](results=[backtest, walked, stressed])

    folds = counted(world, walk["run_id"])
    assert [r["run_id"].rsplit("/", 1)[1] for r in folds] == ["fold-1", "fold-2", "fold-3"]
    assert {m: row["efficiency"] for m, row in walk["measures"]["walk_forward"].items()} == {
        "fx.eurusd": "0.0000"
    }
    assert [(f["pick"], f["out_of_sample_trades"]) for f in report(world, walked)["folds"]] == [
        (None, 0),
        (None, 0),
        ("cell-03", 5),
    ]
    assert report(world, walked)["walk_forward_unmeasured"] == (
        "no fold had a candidate with an in-sample Sharpe to pick on metal.xauusd"
    )
    assert robust["measures"]["random_entries"] == {
        "fx.eurusd": {
            "edge_ratio": "0.4037",
            "p": "0.7059",
            "trades": 6,
            "horizon_bars": 20,
            "resamples": 50,
            "window": MARCH["window"],
        },
        "metal.xauusd": {
            "edge_ratio": "1.0572",
            "p": "0.7255",
            "trades": 2,
            "horizon_bars": 20,
            "resamples": 50,
            "window": MARCH["window"],
        },
    }
    assert robust["measures"]["cost_stress"] == {
        "fx.eurusd": {
            "multiplier": "1.5",
            "expectancy_r": "-0.5685",
            "base_expectancy_r": "-0.5474",
            "trades": 6,
            "window": MARCH["window"],
        },
        "metal.xauusd": {
            "multiplier": "1.5",
            "expectancy_r": "0.4733",
            "base_expectancy_r": "0.5006",
            "trades": 2,
            "window": MARCH["window"],
        },
    }
    assert counted(world, robust["run_id"]) == []
    eurusd, xauusd = fields(world.store, verdict["result"]["verdict_id"])["per_market"]
    assert [(s["name"], s["outcome"], s["detail"]) for s in eurusd["steps"]][1:4] == [
        ("random_entries", "failed", "entry edge ratio 0.4037 at p 0.7059"),
        ("cost_stress", "failed", "expectancy -0.5685R at 1.5x costs"),
        ("walk_forward", "failed", "efficiency 0.0000 of 0.5 needed"),
    ]
    assert [(s["name"], s["outcome"], s["detail"]) for s in xauusd["steps"]][1:4] == [
        ("random_entries", "failed", "entry edge ratio 1.0572 at p 0.7255"),
        ("cost_stress", "passed", "expectancy 0.4733R at 1.5x costs"),
        ("walk_forward", "not_run", "no result in the study walked forward on metal.xauusd"),
    ]


EMA_RANGE = {"ema_period": {"min": "50", "max": "150", "step": "50"}}


def test_a_walk_forward_that_picks_nothing_carries_no_efficiency(world: World) -> None:
    walked, walk = job(world, "walk_forward", split={"folds": 3})

    assert "walk_forward" not in walk["measures"]
    assert len(counted(world, walk["run_id"])) == 3
    assert report(world, walked)["walk_forward_unmeasured"] == (
        "the folds picked among fewer than 2 candidates"
    )


def test_one_random_entry_set_is_too_few_to_measure_a_p(world: World) -> None:
    stressed, robust = job(world, "robustness", resamples=1)

    assert "random_entries" not in robust["measures"]
    reason = "robustness: horizon_bars is a whole number above zero and resamples one of 20 or more"
    assert report(world, stressed)["unmeasured"]["random_entries"] == {
        "fx.eurusd": reason,
        "metal.xauusd": reason,
    }


def test_an_optimize_run_counts_every_candidate_and_measures_its_pbo(world: World) -> None:
    _, landed = job(world, "optimize", ranges=EMA_RANGE, segments=4)

    assert len(counted(world, landed["run_id"])) == 3
    assert landed["measures"]["pbo"] == {"value": "0.8333", "candidates": 3, "segments": 4}


@pytest.mark.parametrize(
    ("asked", "reason"),
    [
        (
            {"window": {"start": "2025-03-01", "end": "2025-03-01"}},
            "an optimize run's window ends after it starts",
        ),
        (
            {"segments": 18},
            "target is expectancy_r or total_r; segments is a whole number from 2 to 16 and "
            "constraints.min_trades a whole number; the run names its window",
        ),
    ],
)
def test_an_optimize_run_refuses_an_empty_window_and_too_many_segments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, asked: dict[str, Any], reason: str
) -> None:
    monkeypatch.setattr(sys, "path", [str(APP), *sys.path])
    optimize = runpy.run_path(str(APP / "jobs" / "optimize.py"))["run"]
    (tmp_path / "in").mkdir()
    request = {"ranges": EMA_RANGE, **MARCH, **asked}
    (tmp_path / "in" / "request.json").write_text(json.dumps(request), "utf-8")

    left = optimize({"run_id": "run-1", "run_folder": str(tmp_path)})["data"]

    assert (left["status"], left["reason"]) == ("failed", reason)


D = 86_400 * 10**9
GOOD, BAD = ("4", "6"), ("-2", "-3")
"""Sharpe 3.5355 and -3.5355: mean 5 and -2.5 R over a spread of 1.4142 and 0.7071."""


def spans(*rs: tuple[str, str]) -> list[UnitTrade]:
    """Two trades in each day-long segment, the segment's R values in order."""
    return [
        UnitTrade(
            f"t{day}-{n}",
            "fx.eurusd",
            Side.LONG,
            Instant(day * D + n),
            Instant(day * D + n + 1),
            Decimal(1),
            Decimal(1),
            Decimal(0),
            Decimal(1),
            FillKind.CLOSE,
            Decimal(r),
            Decimal(r),
        )
        for day, pair in enumerate(rs)
        for n, r in enumerate(pair)
    ]


def test_a_walk_forward_whose_last_quarter_loses_does_not_reach_half() -> None:
    steady = spans(GOOD, GOOD, GOOD, BAD)
    weaker = spans(("1", "2"), ("1", "2"), ("1", "2"), ("1", "2"))

    walked = walk_forward({"a": steady, "b": weaker}, start_ns=0, end_ns=4 * D, folds=3)

    assert not is_refusal(walked)
    assert [f.pick for f in walked.value.folds] == ["a", "a", "a"]
    assert walked.value.evidence()["efficiency"] == "0.3333"


def test_a_walk_forward_of_an_in_sample_only_fit_fails_out_of_sample() -> None:
    odd = spans(GOOD, BAD, GOOD, BAD)
    even = spans(BAD, GOOD, BAD, GOOD)

    walked = walk_forward({"a": odd, "b": even}, start_ns=0, end_ns=4 * D, folds=3)

    assert not is_refusal(walked)
    assert [(f.pick, str(f.out_of_sample_sharpe)[:7]) for f in walked.value.folds] == [
        ("a", "-3.5355"),
        ("b", "-3.5355"),
        ("a", "-3.5355"),
    ]
    assert walked.value.evidence()["efficiency"] == "-1.0000"


def test_two_identical_candidates_are_read_as_overfit() -> None:
    same = [Decimal(1), Decimal(-1), Decimal(2), Decimal(0)]

    pbo = probability_of_overfitting([same, list(same)])

    assert not is_refusal(pbo)
    assert pbo.value == Fraction(1)


def signal_rows(world: World, result_id: str) -> list[dict[str, Any]]:
    blobs = world.store.get(OPERATOR, result_id).blobs
    rows: list[dict[str, Any]] = []
    for slot in sorted(s for s in blobs if s.startswith("journal/signal/")):
        read: Any = pq.read_table(io.BytesIO(world.store.read_blob(blobs[slot].blob_id)))  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        table = cast("list[dict[str, str]]", read.to_pylist())  # pyright: ignore[reportUnknownMemberType]
        rows += [json.loads(r["record"])["body"] for r in table]
    return rows


DAY = "2025-03-12"


def test_a_recorded_day_replays_with_a_per_decision_diff(world: World) -> None:
    recorded = world.tools["backtest_run"](unit=world.dummy, **MARCH)["result"]["result_id"]
    start = int(datetime.fromisoformat(DAY).replace(tzinfo=UTC).timestamp()) * 10**9
    day = [
        r for r in signal_rows(world, recorded) if start <= r["instant"] < start + 86_400 * 10**9
    ]
    changed = {k: v for k, v in day[0].items() if k != "reason"} | {"outcome": "taken"}
    tampered = [changed, *day[1:-1]]

    _, same = job(world, "replay_check", day=DAY, live=day)
    other_id, other = job(world, "replay_check", day=DAY, live=tampered)

    assert len(day) == 14
    assert (same["measures"]["matched"], same["measures"]["differs"]) == (14, 0)
    assert same["labels"]["matches"] is True
    assert (other["measures"]["matched"], other["measures"]["differs"]) == (12, 2)
    assert report(world, other_id)["decisions"] == [
        {
            "instant": 1741747500000000000,
            "market_id": "metal.xauusd",
            "side": "short",
            "occurrence": 0,
            "live": {"outcome": "taken", "reason": None},
            "replay": {"outcome": "no_signal", "reason": "no_signal"},
            "diff": "differs",
        },
        {
            "instant": 1741823100000000000,
            "market_id": "metal.xauusd",
            "side": "short",
            "occurrence": 0,
            "live": None,
            "replay": {"outcome": "no_signal", "reason": "no_signal"},
            "diff": "replay_only",
        },
    ]


class Library:
    """The Library as the lander sees it, held in memory."""

    def __init__(self) -> None:
        self.items: dict[str, str] = {}
        self.kinds: dict[str, str] = {}

    def find(self, item: str) -> str | None:
        return self.items.get(item)

    def put(self, kind: str, fields: Any, blobs: Any, **named: Any) -> Stored:
        object_id = f"obj-{len(self.items) + 1}"
        self.items[str(named["item"])] = object_id
        self.kinds[object_id] = kind
        return Stored(object_id)

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        return f"{from_id}-{relation}-{to_id}"


def in_memory_lander() -> tuple[Library, Lander]:
    library = Library()
    lander = Lander(
        library,
        writer="operator",
        machine="pc",
        provides_of=lambda app, version: {"backtest-result"},
        clock=lambda: datetime(2026, 11, 2, tzinfo=UTC),
        family_of=lambda unit: "family-root",
    )
    return library, lander


def test_a_backtest_that_carries_another_checks_evidence_is_refused(tmp_path: Path) -> None:
    library, lander = in_memory_lander()
    ticket = lander.open("qmb", "1.0.0", "jobs/backtest.py", {"unit": "unit-1"}, CHAT)
    assert ticket is not None
    bundle = parse_bundle(
        {
            "schema_version": 1,
            "run_id": ticket.run_id,
            "status": "finished",
            "tester": {"app": "qmb"},
            "measures": {"trades": 120, "walk_forward": {"efficiency": "0.9"}},
        }
    )

    with pytest.raises(BundleRefused) as refused:
        lander.close(Landing(ticket, bundle, tmp_path))

    assert refused.value.problems == (
        "walk_forward evidence lands only from a walk_forward run, not a backtest run",
    )
    assert list(library.kinds.values()) == ["try"]


def test_two_decisions_of_one_instant_market_and_side_never_overwrite_each_other() -> None:
    first = {"instant": 5, "market_id": "fx.eurusd", "side": "long", "outcome": "taken"}
    second = first | {"outcome": "no_signal", "reason": "no_signal"}

    diff = decision_diff([first, second], [first, first], start_ns=0, end_ns=10)

    assert diff.fields() == {
        "matched": 1,
        "differs": 1,
        "decisions": [
            {
                "instant": 5,
                "market_id": "fx.eurusd",
                "side": "long",
                "occurrence": 1,
                "live": {"outcome": "no_signal", "reason": "no_signal"},
                "replay": {"outcome": "taken", "reason": None},
                "diff": "differs",
            }
        ],
    }
