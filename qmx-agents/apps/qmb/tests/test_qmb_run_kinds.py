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
import shutil
import threading
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq
import pytest
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
    assert [(c["markets"], c["numbers"], c["status"]) for c in cells][:2] == [
        (["fx.eurusd"], {"ema_period": "50"}, "finished"),
        (["fx.eurusd"], {"ema_period": "100"}, "finished"),
    ]
    assert len({c["compiled_fp"] for c in cells}) == 6
    assert [(c["trades"], c["total_r"]) for c in cells] == [
        (3, "-1.6852"),
        (6, "-3.2610"),
        (6, "-3.2610"),
        (3, "0.0013"),
        (2, "1.0013"),
        (3, "-1.0258"),
    ]


def test_a_worsen_only_scenario_that_improves_is_refused_with_its_reason(world: World) -> None:
    improves = [{"name": "cost_shock", "params": {"extra_r": "-0.5"}}]

    with pytest.raises(ControlError) as refused:
        world.control.app_job(
            "qmb",
            "jobs/whatif.py",
            inputs={"unit": world.dummy, **MARCH, "scenarios": improves},
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
    "scenario cost_shock is declared worsen only but improved expectancy_r from -0.2824625 to "
    "0.2175375; a scenario that can improve a result is a counted rerun"
)


def test_a_scenario_that_may_improve_is_a_counted_rerun_and_a_view_is_not(
    world: World,
) -> None:
    scenarios = [
        {"name": "skip_weekdays", "params": {"days": ["monday"]}},
        {"name": "drop_top_trades", "params": {"fraction": "0.25"}},
    ]

    _, landed = job(world, "whatif", scenarios=scenarios)

    rows = counted(world, landed["run_id"])
    assert landed["status"] == "finished"
    assert [(r["kind"], r["run_id"].rsplit("/", 1)[1]) for r in rows] == [
        ("whatif_rerun", "skip_weekdays")
    ]
    assert [(s["name"], s["direction"]) for s in landed["measures"]["scenarios"]] == [
        ("skip_weekdays", "may_improve"),
        ("drop_top_trades", "worsen_only"),
    ]


def test_the_judge_reads_each_check_from_the_run_of_that_kind(world: World) -> None:
    backtest = world.tools["backtest_run"](unit=world.dummy, **MARCH)["result"]["result_id"]
    walked, walk = job(world, "walk_forward", split={"folds": 3})
    stressed, robust = job(world, "robustness", resamples=50)

    verdict = world.tools["backtest_judge_run"](results=[backtest, walked, stressed])

    folds = counted(world, walk["run_id"])
    assert [r["run_id"].rsplit("/", 1)[1] for r in folds] == ["fold-1", "fold-2", "fold-3"]
    assert walk["measures"]["walk_forward"]["efficiency"] == "0"
    assert robust["measures"]["cost_stress"]["multiplier"] == "1.5"
    assert robust["measures"]["random_entries"] == {
        "edge_ratio": "0.4833",
        "p": "0.6600",
        "trades": 8,
        "horizon_bars": 20,
        "resamples": 50,
    }
    assert robust["measures"]["cost_stress"] == {
        "multiplier": "1.5",
        "expectancy_r": "-0.3059",
        "base_expectancy_r": "-0.2825",
        "trades": 8,
    }
    assert counted(world, robust["run_id"]) == []
    judged = fields(world.store, verdict["result"]["verdict_id"])["per_market"][0]
    assert [(s["name"], s["outcome"], s["detail"]) for s in judged["steps"]][1:4] == [
        ("random_entries", "failed", "entry edge ratio 0.4833 at p 0.6600"),
        ("cost_stress", "failed", "expectancy -0.3059R at 1.5x costs"),
        ("walk_forward", "failed", "efficiency 0 of 0.5 needed"),
    ]


def test_an_optimize_run_counts_every_candidate_and_measures_its_pbo(world: World) -> None:
    _, landed = job(
        world,
        "optimize",
        ranges={"ema_period": {"min": "50", "max": "150", "step": "50"}},
        segments=4,
    )

    assert len(counted(world, landed["run_id"])) == 3
    assert landed["measures"]["pbo"] == {"value": "0.6667", "candidates": 3, "segments": 4}


def signal_rows(world: World, result_id: str) -> list[dict[str, Any]]:
    blobs = world.store.get(OPERATOR, result_id).blobs
    rows: list[dict[str, Any]] = []
    for slot in sorted(s for s in blobs if s.startswith("journal/signal/")):
        table = pq.read_table(io.BytesIO(world.store.read_blob(blobs[slot].blob_id)))
        rows += [json.loads(r["record"])["body"] for r in table.to_pylist()]
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
            "live": {"outcome": "taken", "reason": None},
            "replay": {"outcome": "no_signal", "reason": "no_signal"},
            "diff": "differs",
        },
        {
            "instant": 1741823100000000000,
            "market_id": "metal.xauusd",
            "side": "short",
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


def test_a_backtest_that_carries_another_checks_evidence_is_refused(tmp_path: Path) -> None:
    library = Library()
    lander = Lander(
        library,
        writer="operator",
        machine="pc",
        provides_of=lambda app, version: {"backtest-result"},
        clock=lambda: datetime(2026, 11, 2, tzinfo=UTC),
        family_of=lambda unit: "family-root",
    )
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
