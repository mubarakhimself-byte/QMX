"""The `walk_forward` run kind: the unit's run cut into folds, each fold one counted try (B14).

The request's ``split`` names the folds, ``{"folds": 3}``. The unit trades the whole window once,
so every fold sees the unit as it was warmed up and as its numbers moved; the folds are spans of
that run (`qmb.robustness.unit_walk`). The bundle lists each fold under ``measures.counted``,
and its ``walk_forward`` measure is the efficiency the judge's chain reads, which the core keeps
only from a run whose own kind is `walk_forward`.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast

from qmb.robustness.unit_walk import WALK_FORWARD_FOLDS, walk_forward
from qmb.sweep.cells import run_cell
from qmf.core.refusal import is_refusal

import qmb_tester as tester

_NS = 1_000_000_000


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
    ran = run_cell(folder / "in", tester.unit_body(asked, run_id))
    if is_refusal(ran):
        return tester.failed(run_id, tester.reason(ran))
    trades = ran.value.result.trades
    walked = walk_forward(
        trades, start_ns=_ns(bounds["start"]), end_ns=_ns(bounds["end"]), folds=folds
    )
    if is_refusal(walked):
        return tester.failed(run_id, tester.reason(walked))
    found = walked.value
    return tester.leave(
        run_id,
        "finished",
        measures={
            "counted": [{"name": fold.name} for fold in found.folds],
            "trades": len(trades),
            "total_r": str(ran.value.result.total_r),
            "walk_forward": found.evidence(),
        },
        labels={"zero_trades": not trades, "fidelity": "bars"},
        files=[
            tester.write(
                folder,
                "report.json",
                {"folds": [fold.fields() for fold in found.folds], "plan_fp": found.plan_fp},
            )
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
