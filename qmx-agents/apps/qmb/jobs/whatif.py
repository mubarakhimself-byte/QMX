"""The `whatif` run kind: scenarios over the unit's run, each with the direction it declares.

The unit trades the window once and each of the request's ``scenarios`` (``{"name",
"params"}``) reads that run's trades (`qmb.analysis.whatif`). A ``base_result`` the caller names
is echoed in the report; the base the scenarios compare against is this run's own, so like is
measured with like. The bundle's ``measures.scenarios`` lists each scenario's direction, base
and value: the core counts every ``may_improve`` one as a `whatif_rerun` try and refuses the
result when a ``worsen_only`` one improved on its base.
"""

from __future__ import annotations

from collections.abc import Mapping

from qmb.analysis.whatif import what_if
from qmb.sweep.cells import run_cell
from qmf.core.refusal import is_refusal

import qmb_tester as tester


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    ran = run_cell(folder / "in", tester.unit_body(asked, run_id))
    if is_refusal(ran):
        return tester.failed(run_id, tester.reason(ran))
    trades = ran.value.result.trades
    outcomes = what_if(trades, asked.get("scenarios"))
    if is_refusal(outcomes):
        return tester.failed(run_id, tester.reason(outcomes))
    scenarios = [outcome.fields() for outcome in outcomes.value]
    return tester.leave(
        run_id,
        "finished",
        measures={
            "trades": len(trades),
            "total_r": str(ran.value.result.total_r),
            "scenarios": scenarios,
        },
        labels={"zero_trades": not trades, "fidelity": "bars"},
        files=[
            tester.write(
                folder,
                "report.json",
                {"base_result": asked.get("base_result"), "scenarios": scenarios},
            )
        ],
        versions={"qmb": tester.TESTER["version"]},
    )
