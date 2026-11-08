"""The `walk_forward` run kind: each fold picks among the unit's candidates in sample and scores
the pick out of sample, each fold one counted try (B14).

The request's ``split`` names the folds, ``{"folds": 3}``, and its ``ranges`` the numbers to
pick among, as an optimize run names them. Every candidate is one cell of the kept sweep
expansion (`qmb.sweep.cells`) and trades the whole window once, so it warms up as it would live;
the folds are spans of those runs (`qmb.robustness.unit_walk`). The bundle lists each fold under
``measures.counted``, and its ``walk_forward`` measure is the efficiency the judge's chain reads,
which the core keeps only from a run whose own kind is `walk_forward`.

A request with no ranges, or ranges of one value each, picks nothing, so its folds are a
stability view of the unit's own run in the report and the bundle carries no `walk_forward`
measure: a walk-forward that selected nothing cannot fail on numbers fit in sample.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import cast

from qmb.host.unit_handler import UnitTrade
from qmb.robustness.unit_walk import WALK_FORWARD_FOLDS, walk_forward
from qmb.sweep.cells import range_grid, run_cell, trade_cell, unit_cells
from qmf.core.refusal import is_refusal

import qmb_tester as tester

_NS = 1_000_000_000
_PICKS_FROM = 2
"""A walk-forward measures its efficiency only when each fold picks among this many candidates."""


def _ns(day: object) -> int:
    return int(datetime.fromisoformat(str(day)[:10]).replace(tzinfo=UTC).timestamp()) * _NS


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    split = asked.get("split", {})
    folds = (
        cast("dict[str, object]", split).get("folds", WALK_FORWARD_FOLDS)
        if isinstance(split, dict)
        else None
    )
    window = asked.get("window")
    if type(folds) is not int or not isinstance(window, dict):
        return tester.failed(run_id, "a walk-forward names its window and split.folds as a number")
    bounds = cast("dict[str, object]", window)
    start, end = _ns(bounds["start"]), _ns(bounds["end"])
    base = folder / "in"
    candidates: dict[str, Sequence[UnitTrade]] = {}
    rows: list[dict[str, object]] = []
    if "ranges" in asked:
        grid = range_grid(asked["ranges"])
        if is_refusal(grid):
            return tester.failed(run_id, tester.reason(grid))
        document = cast("dict[str, object]", json.loads((base / "unit.json").read_text("utf-8")))
        bar = cast("list[dict[str, dict[str, str]]]", document["streams"])[0]["bar"]
        cells = unit_cells(
            {"numbers": grid.value}, unit=str(document["unit_id"]), bar_seconds=int(bar["size"])
        )
        if is_refusal(cells):
            return tester.failed(run_id, tester.reason(cells))
        for cell in cells.value:
            root = folder / "cells" / cell.name / "in"
            body = tester.unit_body(asked, f"{run_id}/{cell.name}")
            ran = trade_cell(base, root, document, cell, body)
            if is_refusal(ran):
                rows.append(cell.fields() | {"status": "failed", "reason": tester.reason(ran)})
                continue
            candidates[cell.name] = ran.value.result.trades
            rows.append(
                cell.fields() | {"status": "finished", "trades": len(candidates[cell.name])}
            )
    else:
        ran = run_cell(base, tester.unit_body(asked, run_id))
        if is_refusal(ran):
            return tester.failed(run_id, tester.reason(ran))
        candidates["base"] = ran.value.result.trades
    if not candidates:
        return tester.failed(run_id, "no candidate of the walk-forward's ranges traded")
    walked = walk_forward(candidates, start_ns=start, end_ns=end, folds=folds)
    if is_refusal(walked):
        return tester.failed(run_id, tester.reason(walked))
    found = walked.value
    measures: dict[str, object] = {
        "counted": [{"name": fold.name} for fold in found.folds],
        "candidates": len(candidates),
        "trades": sum(len(trades) for trades in candidates.values()),
    }
    unmeasured = None
    if len(candidates) < _PICKS_FROM:
        unmeasured = f"the folds picked among fewer than {_PICKS_FROM} candidates"
    elif found.efficiency is None:
        unmeasured = "no fold had a candidate with an in-sample Sharpe to pick"
    else:
        measures["walk_forward"] = found.evidence()
    return tester.leave(
        run_id,
        "finished",
        measures=measures,
        labels={
            "zero_trades": not any(candidates.values()),
            "fixture_records": asked.get("fixture_records", []),
            "fidelity": "quotes",
        },
        files=[
            tester.write(
                folder,
                "report.json",
                {
                    "candidates": rows,
                    "folds": [fold.fields() for fold in found.folds],
                    "efficiency": found.evidence()["efficiency"],
                    "walk_forward_unmeasured": unmeasured,
                    "plan_fp": found.plan_fp,
                },
            )
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
