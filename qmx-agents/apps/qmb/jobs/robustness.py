"""The `robustness` run kind: the unit's entries against random entries, and its costs stressed.

The unit trades the run's window once; the battery then reads that run's trades and bars
(`qmb.robustness.unit_battery`). The request's ``battery`` lists what to run, both by default:

- ``random_entries``, with ``horizon_bars`` and ``resamples``;
- ``cost_stress``, with ``cost_multiplier`` as decimal text.

Each lands under its own name in the measures as a table keyed by market, each row that market's
own trades measured, with the run's window. That is where the judge's chain reads them, and the
core keeps them only from a run whose own kind is `robustness`. A market the run cannot measure
(no bars after a fill) is left out with its reason in the report, so the judge's step stays not
run rather than passing on nothing. These are views of one run, so the core counts the run once.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Protocol, cast

from qmb.host.unit_handler import UnitTrade
from qmb.robustness.unit_battery import (
    EDGE_HORIZON_BARS,
    EDGE_RESAMPLES,
    STRESS_MULTIPLIER,
    by_market,
    compact_bars,
    cost_stress,
    entry_edge,
)
from qmb.sweep.cells import run_cell
from qmf.core.refusal import Result, is_refusal

import qmb_tester as tester

BATTERY = ("random_entries", "cost_stress")


class Evidence(Protocol):
    def evidence(self) -> dict[str, object]: ...


def _per_market[T: Evidence](
    trades: Sequence[UnitTrade],
    window: object,
    measure: Callable[[Sequence[UnitTrade]], Result[T]],
) -> tuple[dict[str, object], dict[str, str]]:
    """One battery entry over each market's own trades: its rows, and why a market has none."""
    rows: dict[str, object] = {}
    reasons: dict[str, str] = {}
    for market, own in by_market(trades).items():
        found = measure(own)
        if is_refusal(found):
            reasons[market] = tester.reason(found)
        else:
            rows[market] = found.value.evidence() | {"window": window}
    return rows, reasons


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
    body = tester.unit_body(asked, run_id) | {"window": asked.get("window")}
    ran = run_cell(folder / "in", body)
    if is_refusal(ran):
        return tester.failed(run_id, tester.reason(ran))
    held = compact_bars(ran.value.loaded.feeds)
    if is_refusal(held):
        return tester.failed(run_id, tester.reason(held))
    trades = ran.value.result.trades
    window = asked.get("window")
    tables: dict[str, tuple[dict[str, object], dict[str, str]]] = {}
    if "random_entries" in battery:
        tables["random_entries"] = _per_market(
            trades,
            window,
            lambda own: entry_edge(
                own,
                held.value,
                horizon=cast("int", horizon),
                resamples=cast("int", resamples),
                seed=cast("int", seed),
            ),
        )
    if "cost_stress" in battery:
        tables["cost_stress"] = _per_market(
            trades,
            window,
            lambda own: cost_stress(own, held.value, ran.value.loaded.costs, multiplier=multiplier),
        )
    measured = {name: rows for name, (rows, _) in tables.items() if rows}
    unmeasured = {
        name: reasons or "the run placed no trades"
        for name, (rows, reasons) in tables.items()
        if reasons or not rows
    }
    result = ran.value.result
    return tester.leave(
        run_id,
        "finished",
        measures={"trades": len(trades), "total_r": str(result.total_r), **measured},
        labels={
            "zero_trades": not trades,
            "fixture_records": asked.get("fixture_records", []),
            "data_short": tester.data_short(result.short),
            "fidelity": "quotes",
        },
        files=[
            tester.write(folder, "report.json", {"measured": measured, "unmeasured": unmeasured})
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
