"""The `sweep` run kind: every cell of a grid over the unit's numbers and markets (QB-22, B14).

The request's ``grid`` names values for some of the unit's numbers and, optionally, the markets
to run one at a time: ``{"numbers": {"ema_period": ["50", "100"]}, "markets": ["fx.eurusd"]}``.
"Run on every market" is a grid of the unit's markets alone. Each cell trades its own copy of
the unit, compiled in its own folder under ``cells/``, over the run's whole window. The bundle
lists every cell under ``measures.counted``, and the core lands one try per cell in the unit's
family, a cell that failed included.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from qmb.sweep.cells import trade_cell, unit_cells
from qmf.core.refusal import is_refusal

import qmb_tester as tester


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    base = folder / "in"
    document = cast("dict[str, object]", json.loads((base / "unit.json").read_text("utf-8")))
    seconds = int(cast("list[dict[str, dict[str, str]]]", document["streams"])[0]["bar"]["size"])
    cells = unit_cells(asked.get("grid"), unit=str(document["unit_id"]), bar_seconds=seconds)
    if is_refusal(cells):
        return tester.failed(run_id, tester.reason(cells))
    rows: list[dict[str, object]] = []
    for cell in cells.value:
        row = cell.fields()
        root = folder / "cells" / cell.name / "in"
        ran = trade_cell(
            base, root, document, cell, tester.unit_body(asked, f"{run_id}/{cell.name}")
        )
        if is_refusal(ran):
            rows.append(row | {"status": "failed", "reason": tester.reason(ran)})
            continue
        result = ran.value.result
        count = len(result.trades)
        rows.append(
            row
            | {
                "status": "finished",
                "compiled_fp": result.compiled_fingerprint,
                "trades": count,
                "total_r": str(result.total_r),
                "expectancy_r": str(result.total_r / count) if count else "0",
                "net_money": str(result.net_money),
            }
        )
    finished = [row for row in rows if row["status"] == "finished"]
    return tester.leave(
        run_id,
        "finished",
        measures={
            "counted": [cell.counted() for cell in cells.value],
            "cells": len(rows),
            "cells_finished": len(finished),
            "trades": sum(cast("int", row["trades"]) for row in finished),
            "total_r": str(sum((Decimal(str(row["total_r"])) for row in finished), Decimal(0))),
        },
        labels={
            "zero_trades": not any(row.get("trades") for row in finished),
            "fixture_records": asked.get("fixture_records", []),
            "fidelity": "quotes",
        },
        files=[tester.write(folder, "report.json", {"cells": rows})],
        versions={"qmb": tester.TESTER["version"]},
    )
