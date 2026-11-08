"""The behaviour check: QML's layer G run as QMB code (Part B slice B5b, R1-B-01).

QMB loads a run folder's unit, checks that its recorded slice covers the unit's derived warm-up
plus the ``[qmb] g_slice_margin`` share more, and calls QML's ``layer_g`` once over it. QML's
function drives the hosted unit and fills the unchanged ``evaluate_layer2``'s observations;
QMB adds nothing to either half. Its answer is the ``qmx.behaviour/1`` report, whose
``safety`` half carries ``evaluate_layer2``'s verdict and whose warnings name each fault.

Isolation is stated only by the child entry: ``python -m qmb.host.behaviour`` reads its job from
standard input, loads the unit's blocks in that fresh process, and writes the report to
standard output. A caller in the same process states ``loaded_in_isolation=False``, and the
safety half then fails as ``evaluate_layer2`` requires.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from pathlib import Path
from typing import Final, TextIO, cast

from qmf.core.refusal import Ok, Result, is_refusal
from qml.check.layer_g import layer_g

from qmb._refuse import invalid
from qmb.host.unit_runner import UnitRunRequest, load_unit_folder, parse_unit_run_request

__all__ = ["G_SLICE_MARGIN", "BehaviourCheck", "check_behaviour", "child_main"]

G_SLICE_MARGIN: Final[Decimal] = Decimal("0.20")
"""``[qmb] g_slice_margin``'s starting default: the slice covers the warm-up and 20% more."""


@dataclass(frozen=True, slots=True)
class BehaviourCheck:
    report: Mapping[str, object]
    """The ``qmx.behaviour/1`` report, its ``safety`` half included."""

    @property
    def safety_passed(self) -> bool:
        return cast("Mapping[str, object]", self.report["safety"])["verdict"] == "pass"

    @property
    def faults(self) -> tuple[str, ...]:
        """The kind of every warning the report names, in its order."""
        warnings = cast("list[Mapping[str, object]]", self.report["warnings"])
        return tuple(str(w["kind"]) for w in warnings)


def check_behaviour(
    folder: Path,
    request: UnitRunRequest,
    *,
    margin: Decimal = G_SLICE_MARGIN,
    loaded_in_isolation: bool,
    may_not_trade_on_slice: bool = False,
) -> Result[BehaviourCheck]:
    """Layer G over the folder's recorded slice, refused when the slice is too short."""
    if not margin.is_finite() or margin < 0:
        return invalid("g_slice_margin", "the slice margin is a share of zero or more")
    loaded = load_unit_folder(folder)
    if is_refusal(loaded):
        return loaded
    compiled = loaded.value.compiled
    warm = compiled.warm_up[compiled.plan.stream]
    needed = int((warm * (1 + margin)).to_integral_value(rounding=ROUND_CEILING))
    bars = loaded.value.bars()
    if is_refusal(bars):
        return bars
    short = {m: len(b) for m, b in bars.value.items() if len(b) < needed}
    if short:
        return invalid(
            "slice",
            f"the behaviour check needs {needed} bars per market: the warm-up of {warm} "
            f"and {margin} more",
            bars=short,
        )
    g = layer_g(
        compiled,
        loaded.value.sources,
        bars.value,
        execution_target=request.execution_target,
        equity=request.equity,
        loaded_in_isolation=loaded_in_isolation,
        may_not_trade_on_slice=may_not_trade_on_slice,
    )
    report = dict(g.report)
    report["slice_bars_needed"] = needed
    return Ok(BehaviourCheck(report))


def child_main(stdin: TextIO | None = None, stdout: TextIO | None = None) -> int:
    """The sandbox child: ``{"run_folder", "request", "margin"}`` in, the report or refusal out."""
    out = stdout or sys.stdout
    try:
        job = cast("Mapping[str, object]", json.loads((stdin or sys.stdin).read()))
        margin = Decimal(str(job.get("margin", G_SLICE_MARGIN)))
    except (json.JSONDecodeError, InvalidOperation, AttributeError) as error:
        json.dump({"ok": False, "refusal": {"field": "job", "reason": str(error)}}, out)
        return 0
    request = parse_unit_run_request(job.get("request"))
    checked = (
        request
        if is_refusal(request)
        else check_behaviour(
            Path(str(job.get("run_folder"))),
            request.value,
            margin=margin,
            loaded_in_isolation=True,
            may_not_trade_on_slice=job.get("may_not_trade_on_slice") is True,
        )
    )
    if is_refusal(checked):
        json.dump({"ok": False, "refusal": {k: str(v) for k, v in checked.context.items()}}, out)
        return 0
    json.dump({"ok": True, "report": checked.value.report}, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(child_main())
