"""The judge cannot be talked round: a study written after a result pays a counted try and keeps
every market under the luckiest-market pull, and each market answers for its own evidence."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qmf.core import fingerprint_bytes
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    LanderLibrary,
    register_checkers,
)
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store
from qmx_tools import DomainContext
from qmx_tools.functions import domain_functions

from qmx_judge.judge import JudgedResult, Verdict, judge, parse_spec, quick_spec
from qmx_judge.landing import Lander
from qmx_judge.runs import Landing, parse_bundle

OPERATOR = Principal("operator")
DAY = 86_400 * 10**9
START = 1_735_689_600 * 10**9
"""2025-01-01 00:00 UTC."""
WRITTEN: JsonObject = {
    "origin": "written",
    "claim": {"edge": "pullbacks"},
    "markets": "admitted",
    "preset": "shipped",
}
TINY_K: JsonObject = {"shrinkage": {"estimator": "fixed", "k": "0.000001"}}


@dataclass
class World:
    """One real result of 20 markets of +0.06R, landed through the real lander."""

    store: Store
    judge_run: Any
    result: str
    land: Any
    trades: list[dict[str, object]]


def landed_world(root: Path, *, study: JsonObject = WRITTEN) -> World:
    context = DomainContext(root=root / "home")
    store = context.library.store
    register_checkers(store)
    library = LanderLibrary(store)
    lander = Lander(
        library,
        "operator",
        "pc",
        lambda _app, _version: {"backtest-result"},
        lambda: datetime(2026, 11, 2, tzinfo=UTC),
        family_of=library.family_of,
    )
    unit = put(store, "note", "unit", {"text": "v"})
    before = put(store, "study-spec", "study", study)

    def land(trades: list[dict[str, object]], **asked: object) -> str:
        request = {"unit": unit, "study": before, **asked}
        ticket = lander.open("qmb", "0.1.0", "jobs/backtest.py", request, "x")
        assert ticket is not None
        report = json.dumps({"trades": trades}).encode()
        folder = root / ticket.run_id
        folder.mkdir(parents=True)
        (folder / "report.json").write_bytes(report)
        bundle = parse_bundle(
            {
                "run_id": ticket.run_id,
                "status": "finished",
                "tester": {"app": "qmb", "version": "0.1.0"},
                "measures": {"trades": len(trades)},
                "labels": {"zero_trades": False, "fidelity": "bars"},
                "files": [
                    {"slot": "report", "path": "report.json", "fp": fingerprint_bytes(report).value}
                ],
                "consumed": [],
            }
        )
        return lander.close(Landing(ticket, bundle, folder))

    draw = random.Random(24)  # noqa: S311 - a seeded fixture, not a secret
    trades: list[dict[str, object]] = [
        {
            "trade_id": f"t{market}-{day}",
            "market_id": f"fx.m{market:02d}",
            "closed_at": START + day * DAY,
            "r": f"{draw.gauss(0.06, 1):.4f}",
        }
        for market in range(20)
        for day in range(150)
    ]
    judge_run = domain_functions(context)["backtest"]["backtest_judge_run"]
    return World(store, judge_run, land(trades), land, trades)


def put(store: Store, kind: str, item: str, fields: JsonObject, head: str | None = None) -> str:
    draft = Draft(kind, item, item, fields=fields)
    return store.put(OPERATOR, draft, on=MAIN, expected_head=head).object_id


def spec_edits(store: Store) -> int:
    return len(store.with_field("try", "kind", "spec_edit"))


def verdict_of(world: World, **asked: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """The answer of the judge door, and the landed verdict's markets by name."""
    answer = world.judge_run(**{"results": [world.result], **asked})["result"]
    landed = world.store.get(OPERATOR, answer["verdict_id"]).fields["per_market"]
    return answer, {str(m["market"]): m for m in landed}  # pyright: ignore


def deflated(market: dict[str, Any]) -> Decimal:
    step = next(s for s in market["steps"] if s["name"] == "try_corrected")
    found = re.match(r"deflated Sharpe (\S+) ", step["detail"])
    assert found is not None
    return Decimal(found[1])


def test_a_study_written_after_the_result_counts_a_try(tmp_path: Path) -> None:
    world = landed_world(tmp_path / "new")
    honest, _ = verdict_of(world)
    assert (honest["raw_tries"], spec_edits(world.store)) == (20, 0)

    later = put(
        world.store, "study-spec", "study-later", {**WRITTEN, "markets": ["fx.m02"], **TINY_K}
    )
    with pytest.raises(ValueError, match="is given 2 times"):
        world.judge_run(results=[world.result, world.result], study=later)
    assert spec_edits(world.store) == 0

    answer, markets = verdict_of(world, study=later)
    again, _ = verdict_of(world, study=later)

    assert len(markets) == 20
    assert (markets["fx.m02"]["raw_r"], markets["fx.m02"]["shrunk_r"]) == ("0.2193", "0.0558")
    assert markets["fx.m02"]["weight"] == "0.0000"
    assert deflated(markets["fx.m02"]) <= Decimal("0.1024")
    assert (answer["raw_tries"], answer["effective_tries"]) == (21, 21)
    assert spec_edits(world.store) == 1
    assert again["verdict_id"] == answer["verdict_id"]
    assert answer["says"].endswith(
        "This study was written after these results' first try, so it counted as a try and "
        "its own k was not used. Behind it: 21 tries, 21 effective."
    )

    older = landed_world(tmp_path / "older")
    idle = put(older.store, "study-spec", "study-idle", WRITTEN)
    assert verdict_of(older, study=idle)[0]["raw_tries"] == 21
    edited = put(older.store, "study-spec", "study-idle", {**WRITTEN, **TINY_K}, head=idle)
    answer, markets = verdict_of(older, study=edited)

    assert (markets["fx.m02"]["shrunk_r"], markets["fx.m02"]["weight"]) == ("0.0558", "0.0000")
    assert deflated(markets["fx.m02"]) <= Decimal("0.1024")
    assert spec_edits(older.store) == 2

    written_first = landed_world(tmp_path / "first", study={**WRITTEN, **TINY_K})
    answer, markets = verdict_of(written_first)

    assert (markets["fx.m02"]["shrunk_r"], markets["fx.m02"]["weight"]) == ("0.2193", "1.0000")
    assert (answer["raw_tries"], spec_edits(written_first.store)) == (20, 0)
    assert "written after" not in answer["says"]


def test_rerunning_the_lucky_market_alone_keeps_the_others_in_the_pull(tmp_path: Path) -> None:
    world = landed_world(tmp_path)
    alone = world.land([t for t in world.trades if t["market_id"] == "fx.m02"], markets=["fx.m02"])

    answer, markets = verdict_of(world, results=[alone])

    assert list(markets) == ["fx.m02"]
    assert (markets["fx.m02"]["raw_r"], markets["fx.m02"]["shrunk_r"]) == ("0.2193", "0.0558")
    assert markets["fx.m02"]["weight"] == "0.0000"
    assert (answer["overall"], answer["raw_tries"], answer["effective_tries"]) == ("fail", 21, 20)
    assert spec_edits(world.store) == 0

    naming = put(world.store, "study-spec", "study-names", {**WRITTEN, "markets": ["fx.m03"]})
    _, named = verdict_of(world, results=[alone], study=naming)
    assert {m: found["outcome"] for m, found in named.items()} == {
        "fx.m02": "fail",
        "fx.m03": "no_trades",
    }

    only = JudgedResult.read("result-1", landed_fields(1, {}, MARCH), trades_of("fx.a", 3))
    variant = JudgedResult.read(
        "result-2", {**landed_fields(2, {}, MARCH), "unit": "unit-v2"}, trades_of("fx.b", 4)
    )
    tries = [
        {"kind": "run", "state": "opened", "run_id": run_id(n), "family": "unit-v1"} for n in (1, 2)
    ]
    other_code = judge(
        parse_spec(WRITTEN),
        study="study-v1",
        results=[only],
        tries=tries,
        family=[variant],
        principal="agent:chat",
        versions={},
    )
    assert [(m.market, m.weight) for m in other_code.per_market] == [("fx.a", Decimal("0.6"))]


def test_quick_spec_lands_no_try(tmp_path: Path) -> None:
    world = landed_world(tmp_path)
    quick = quick_spec(None)
    keeps = put(world.store, "study-spec", "study-quick-mine", quick)  # pyright: ignore

    answer, markets = verdict_of(world, study=keeps)

    assert (markets["fx.m02"]["shrunk_r"], answer["raw_tries"]) == ("0.0558", 20)
    assert spec_edits(world.store) == 0

    forged = put(
        world.store,
        "study-spec",
        "study-mine",
        {**quick, **TINY_K},  # pyright: ignore
    )
    named_quick = put(
        world.store,
        "study-spec",
        "study-quick-forged",
        {**quick, **TINY_K},  # pyright: ignore
    )
    for study in (forged, named_quick):
        _, markets = verdict_of(world, study=study)
        assert (markets["fx.m02"]["shrunk_r"], markets["fx.m02"]["weight"]) == ("0.0558", "0.0000")
    assert spec_edits(world.store) == 2


MARCH = {"start": "2025-03-01", "end": "2025-04-01"}
FEBRUARY = {"start": "2025-02-01", "end": "2025-03-01"}
PASSING = {
    "random_entries": {"edge_ratio": "1.4", "p": "0.01"},
    "walk_forward": {"efficiency": "0.7"},
}


def run_id(n: int) -> str:
    return f"qmbr-pc-{n:026d}"


def landed_fields(n: int, measures: dict[str, object], window: dict[str, str]) -> dict[str, Any]:
    return {
        "run_id": run_id(n),
        "status": "finished",
        "unit": "unit-v1",
        "tester": {"app": "qmb", "version": "1.0.0"},
        "window": window,
        "measures": measures,
    }


def trades_of(market: str, seed: int) -> list[dict[str, object]]:
    draw = random.Random(seed)  # noqa: S311 - a seeded fixture, not a secret
    return [
        {"market_id": market, "closed_at": START + day * DAY, "r": f"{draw.gauss(0.5, 1):.4f}"}
        for day in range(150)
    ]


def judged_with(
    cost_rows: dict[str, object],
    *,
    windows: dict[str, dict[str, str]] | None = None,
    second_run: dict[str, object] | None = None,
) -> Verdict:
    """One backtest of two markets beside the robustness run that stressed them, as landed."""
    rows = {
        name: {
            market: {**row, "window": (windows or {}).get(name, MARCH)}
            for market in ("fx.good", "fx.bad")
        }
        for name, row in PASSING.items()
    }
    backtest = JudgedResult.read(
        "result-1",
        landed_fields(1, {}, MARCH),
        [*trades_of("fx.good", 3), *trades_of("fx.bad", 4)],
    )
    robust = JudgedResult.read(
        "result-2", landed_fields(2, {**rows, "cost_stress": cost_rows}, MARCH), []
    )
    results = [backtest, robust]
    if second_run is not None:
        measures: dict[str, object] = {"cost_stress": second_run}
        results.append(JudgedResult.read("result-3", landed_fields(3, measures, MARCH), []))
    tries = [
        {"kind": "run", "state": "opened", "run_id": r.run_id, "family": "unit-v1"} for r in results
    ]
    return judge(
        parse_spec(WRITTEN),
        study="study-v1",
        results=results,
        tries=tries,
        principal="agent:chat",
        versions={},
    )


def cost_step(verdict: Verdict, market: str, name: str = "cost_stress") -> tuple[str, str, str]:
    found = next(m for m in verdict.per_market if m.market == market)
    step = next(s for s in found.steps if s.rule.name == name)
    return found.outcome, step.outcome, step.detail


def test_a_market_that_loses_under_doubled_costs_does_not_pass_on_another() -> None:
    good: dict[str, object] = {"multiplier": "2", "expectancy_r": "0.3", "window": MARCH}
    bad: dict[str, object] = {"multiplier": "2", "expectancy_r": "-0.1", "window": MARCH}

    both = judged_with({"fx.good": good, "fx.bad": bad})
    assert cost_step(both, "fx.good") == ("pass", "passed", "expectancy 0.3R at 2x costs")
    assert cost_step(both, "fx.bad") == ("fail", "failed", "expectancy -0.1R at 2x costs")

    no_row = judged_with({"fx.good": good})
    assert cost_step(no_row, "fx.bad") == (
        "incomplete",
        "not_run",
        "no result in the study stressed its costs on fx.bad",
    )

    other_window = judged_with({"fx.good": good, "fx.bad": {**good, "window": FEBRUARY}})
    assert cost_step(other_window, "fx.bad") == (
        "incomplete",
        "not_run",
        "fx.bad's evidence ran over 2025-02-01 to 2025-03-01, its trades over "
        "2025-03-01 to 2025-04-01",
    )

    flat = judged_with({"multiplier": "2", "expectancy_r": "0.3", "trades": 5})
    assert cost_step(flat, "fx.bad") == (
        "incomplete",
        "not_run",
        "no result in the study stressed its costs on fx.bad",
    )

    worst = judged_with({"fx.good": good, "fx.bad": good}, second_run={"fx.bad": bad})
    assert cost_step(worst, "fx.bad") == ("fail", "failed", "expectancy -0.1R at 2x costs")

    wider = {"start": "2025-01-01", "end": "2025-04-01"}
    too_wide = (
        "incomplete",
        "not_run",
        "fx.bad's evidence ran over 2025-01-01 to 2025-04-01, its trades over "
        "2025-03-01 to 2025-04-01",
    )
    wide_cost = judged_with({"fx.good": good, "fx.bad": {**good, "window": wider}})
    assert cost_step(wide_cost, "fx.bad") == too_wide

    wide_entries = judged_with({"fx.good": good, "fx.bad": good}, windows={"random_entries": wider})
    assert cost_step(wide_entries, "fx.bad", "random_entries") == too_wide

    wide_walk = judged_with({"fx.good": good, "fx.bad": good}, windows={"walk_forward": wider})
    assert cost_step(wide_walk, "fx.bad", "walk_forward") == (
        "pass",
        "passed",
        "efficiency 0.7 of 0.5 needed",
    )
