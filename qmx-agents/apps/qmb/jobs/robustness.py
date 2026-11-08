"""The `robustness` run kind: the unit's entries against random entries, and its costs stressed.

The unit trades the run's window once; the battery then reads that run's trades and bars
(`qmb.robustness.unit_battery`). The request's ``battery`` lists what to run, both by default:

- ``random_entries``, with ``horizon_bars`` and ``resamples``;
- ``cost_stress``, with ``cost_multiplier`` as decimal text.

Each lands under its own name in the measures, which is where the judge's chain reads them, and
the core keeps them only from a run whose own kind is `robustness`. A battery entry the run
cannot measure (no trades, no bars after a fill) is left out with its reason in the report, so
the judge's step stays not run rather than passing on nothing. These are views of one run, so
the core counts the run once.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import cast

from qmb.robustness.unit_battery import (
    EDGE_HORIZON_BARS,
    EDGE_RESAMPLES,
    STRESS_MULTIPLIER,
    cost_stress,
    entry_edge,
)
from qmb.sweep.cells import run_cell
from qmf.core.refusal import is_refusal

import qmb_tester as tester

BATTERY = ("random_entries", "cost_stress")


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    battery = asked.get("battery", list(BATTERY))
    if not isinstance(battery, list) or not set(cast("list[object]", battery)) <= set(BATTERY):
        return tester.failed(run_id, f"a robustness battery lists some of {', '.join(BATTERY)}")
    horizon = asked.get("horizon_bars", EDGE_HORIZON_BARS)
    resamples = asked.get("resamples", EDGE_RESAMPLES)
    seed = asked.get("seed", 0)
    try:
        multiplier = Decimal(str(asked.get("cost_multiplier", STRESS_MULTIPLIER)))
    except InvalidOperation:
        return tester.failed(run_id, "cost_multiplier is decimal text")
    if not all(type(n) is int for n in (horizon, resamples, seed)):
        return tester.failed(run_id, "horizon_bars, resamples and seed are whole numbers")
    ran = run_cell(folder / "in", tester.unit_body(asked, run_id))
    if is_refusal(ran):
        return tester.failed(run_id, tester.reason(ran))
    held = ran.value.loaded.bars()
    if is_refusal(held):
        return tester.failed(run_id, tester.reason(held))
    trades = ran.value.result.trades
    measured: dict[str, object] = {}
    unmeasured: dict[str, str] = {}
    if "random_entries" in battery:
        edge = entry_edge(
            trades,
            held.value,
            horizon=cast("int", horizon),
            resamples=cast("int", resamples),
            seed=cast("int", seed),
        )
        if is_refusal(edge):
            unmeasured["random_entries"] = tester.reason(edge)
        else:
            measured["random_entries"] = edge.value.evidence()
    if "cost_stress" in battery:
        stressed = cost_stress(trades, held.value, ran.value.loaded.costs, multiplier=multiplier)
        if is_refusal(stressed):
            unmeasured["cost_stress"] = tester.reason(stressed)
        else:
            measured["cost_stress"] = stressed.value.evidence()
    result = ran.value.result
    return tester.leave(
        run_id,
        "finished",
        measures={"trades": len(trades), "total_r": str(result.total_r), **measured},
        labels={
            "zero_trades": not trades,
            "fixture_records": asked.get("fixture_records", []),
            "fidelity": "quotes",
        },
        files=[
            tester.write(folder, "report.json", {"measured": measured, "unmeasured": unmeasured})
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
