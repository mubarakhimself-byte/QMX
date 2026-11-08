"""The `optimize` run kind: every candidate of the unit's number ranges, the best, and its PBO.

The request's ``ranges`` names each number to search, as a list of values or ``{"min", "max",
"step"}`` as decimal text; ``target`` is ``expectancy_r`` (default) or ``total_r``; and
``constraints.min_trades`` keeps thinner candidates out of the pick. Every candidate is one cell
of the kept sweep expansion (`qmb.sweep.cells`), traded over the whole window, and one counted
try. The window is cut into ``segments`` equal spans, and each candidate's R per span gives the
probability of backtest overfitting (`qmb.optimize.cscv`), the `pbo` measure the judge reads,
which the core keeps only from a run whose own kind is `optimize`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from qmb.optimize.cscv import PBO_SEGMENTS, PBO_SEGMENTS_MOST, probability_of_overfitting
from qmb.sweep.cells import range_grid, trade_cell, unit_cells
from qmf.core.refusal import is_refusal

import qmb_tester as tester

_NS = 1_000_000_000
_PLACES = Decimal("0.0001")


def _ns(day: object) -> int:
    return int(datetime.fromisoformat(str(day)[:10]).replace(tzinfo=UTC).timestamp()) * _NS


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    grid = range_grid(asked.get("ranges"))
    if is_refusal(grid):
        return tester.failed(run_id, tester.reason(grid))
    target = asked.get("target", "expectancy_r")
    segments = asked.get("segments", PBO_SEGMENTS)
    constraints = asked.get("constraints", {})
    least = (
        cast("dict[str, object]", constraints).get("min_trades", 0)
        if isinstance(constraints, dict)
        else None
    )
    window = asked.get("window")
    if (
        target not in ("expectancy_r", "total_r")
        or type(segments) is not int
        or not 2 <= segments <= PBO_SEGMENTS_MOST
        or type(least) is not int
        or not isinstance(window, dict)
    ):
        return tester.failed(
            run_id,
            "target is expectancy_r or total_r; segments is a whole number from 2 to "
            f"{PBO_SEGMENTS_MOST} and constraints.min_trades a whole number; the run names its "
            "window",
        )
    bounds = cast("dict[str, object]", window)
    start, end = _ns(bounds["start"]), _ns(bounds["end"])
    span = (end - start) // segments
    if span < 1:
        return tester.failed(run_id, "an optimize run's window ends after it starts")
    base = folder / "in"
    document = cast("dict[str, object]", json.loads((base / "unit.json").read_text("utf-8")))
    seconds = int(cast("list[dict[str, dict[str, str]]]", document["streams"])[0]["bar"]["size"])
    cells = unit_cells({"numbers": grid.value}, unit=str(document["unit_id"]), bar_seconds=seconds)
    if is_refusal(cells):
        return tester.failed(run_id, tester.reason(cells))
    rows: list[dict[str, object]] = []
    spans: list[list[Decimal]] = []
    for cell in cells.value:
        row = cell.fields()
        root = folder / "cells" / cell.name / "in"
        ran = trade_cell(base, root, document, cell, tester.unit_body(asked, f"{run_id}/{cell.name}"))
        if is_refusal(ran):
            rows.append(row | {"status": "failed", "reason": tester.reason(ran)})
            continue
        trades = ran.value.result.trades
        total = ran.value.result.total_r
        per_span = [Decimal(0)] * segments
        for trade in trades:
            at = min(max((trade.opened_at.value_ns - start) // span, 0), segments - 1)
            per_span[at] += trade.r
        spans.append(per_span)
        rows.append(
            row
            | {
                "status": "finished",
                "trades": len(trades),
                "total_r": str(total),
                "expectancy_r": str(total / len(trades)) if trades else "0",
            }
        )
    eligible = [r for r in rows if r["status"] == "finished" and cast("int", r["trades"]) >= least]
    best = max(eligible, key=lambda r: Decimal(str(r[target])), default=None)
    measures: dict[str, object] = {
        "counted": [cell.counted() for cell in cells.value],
        "candidates": len(rows),
        "best": None if best is None else best["cell"],
    }
    pbo = probability_of_overfitting(spans)
    if not is_refusal(pbo):
        value = Decimal(pbo.value.numerator) / pbo.value.denominator
        measures["pbo"] = {
            "value": str(value.quantize(_PLACES)),
            "candidates": len(spans),
            "segments": segments,
        }
    return tester.leave(
        run_id,
        "finished",
        measures=measures,
        labels={"zero_trades": not any(r.get("trades") for r in rows), "fidelity": "bars"},
        files=[
            tester.write(
                folder,
                "report.json",
                {
                    "candidates": rows,
                    "target": target,
                    "pbo_unmeasured": tester.reason(pbo) if is_refusal(pbo) else None,
                },
            )
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
