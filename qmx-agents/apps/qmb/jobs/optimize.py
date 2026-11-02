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
from decimal import Decimal, InvalidOperation
from typing import cast

from qmb.optimize.cscv import PBO_SEGMENTS, probability_of_overfitting
from qmb.sweep.cells import cell_document, lay_out, run_cell, unit_cells
from qmf.core.refusal import is_refusal

import qmb_tester as tester

_NS = 1_000_000_000
_PLACES = Decimal("0.0001")


def _ns(day: object) -> int:
    return int(datetime.fromisoformat(str(day)[:10]).replace(tzinfo=UTC).timestamp()) * _NS


def _values(spec: object) -> list[str] | str:
    """One number's candidate values, or why they cannot be read."""
    if isinstance(spec, list):
        return [str(v) for v in cast("list[object]", spec)]
    if not isinstance(spec, dict):
        return "a range is a list of values or {min, max, step}"
    named = cast("dict[str, object]", spec)
    try:
        low, high, step = (Decimal(str(named[k])) for k in ("min", "max", "step"))
    except KeyError, InvalidOperation:
        return "a range names min, max and step as decimal text"
    if step <= 0 or high < low:
        return "a range's step is above zero and its max is not below its min"
    count = int((high - low) / step) + 1
    return [str(low + i * step) for i in range(count)]


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    ranges = asked.get("ranges")
    if not isinstance(ranges, dict) or not ranges:
        return tester.failed(run_id, "an optimize run names the ranges of one number at least")
    grid: dict[str, list[str]] = {}
    for name, spec in cast("dict[str, object]", ranges).items():
        values = _values(spec)
        if isinstance(values, str):
            return tester.failed(run_id, f"{name}: {values}")
        grid[name] = values
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
        or segments < 2
        or type(least) is not int
        or not isinstance(window, dict)
    ):
        return tester.failed(
            run_id,
            "target is expectancy_r or total_r; segments is a whole number of 2 or more and "
            "constraints.min_trades a whole number; the run names its window",
        )
    base = folder / "in"
    document = cast("dict[str, object]", json.loads((base / "unit.json").read_text("utf-8")))
    seconds = int(cast("list[dict[str, dict[str, str]]]", document["streams"])[0]["bar"]["size"])
    cells = unit_cells({"numbers": grid}, unit=str(document["unit_id"]), bar_seconds=seconds)
    if is_refusal(cells):
        return tester.failed(run_id, tester.reason(cells))
    bounds = cast("dict[str, object]", window)
    start, end = _ns(bounds["start"]), _ns(bounds["end"])
    span = (end - start) // segments
    rows: list[dict[str, object]] = []
    spans: list[list[Decimal]] = []
    for cell in cells.value:
        row = cell.fields()
        made = cell_document(document, cell)
        if is_refusal(made):
            rows.append(row | {"status": "failed", "reason": tester.reason(made)})
            continue
        root = folder / "cells" / cell.name / "in"
        lay_out(base, root, made.value)
        ran = run_cell(root, tester.unit_body(asked, f"{run_id}/{cell.name}"))
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
