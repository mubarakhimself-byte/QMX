"""A unit's walk-forward: its run's window cut into folds, each fold one counted try (B14).

The window is cut into ``folds + 1`` equal segments, and fold ``i`` pairs segment ``i`` (in
sample) with segment ``i + 1`` (out of sample), each a span of the one unit run: a trade belongs
to the segment its fill opened in. The fold geometry rides the kept
:func:`~qmb.robustness.walkforward.plan_walk_forward`, so the plan carries the kept identity and
fingerprint, and the spans are the split manifests' content.

The efficiency the judge reads (`judge.md` §3, step 4) is the out-of-sample R over the in-sample
R summed across folds, equal spans making the two rates comparable. With no in-sample edge the
efficiency is 0: a fold that earned nothing in sample has nothing to keep.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Ok, Result, is_refusal

from qmb._refuse import invalid
from qmb.host.unit_handler import UnitTrade
from qmb.robustness.walkforward import WalkForwardWindow, plan_walk_forward

__all__ = ["WALK_FORWARD_FOLDS", "Fold", "WalkForward", "walk_forward"]

WALK_FORWARD_FOLDS: Final = 3
"""Starting default of a walk-forward run's ``split.folds``."""
_PLACES: Final = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class Fold:
    name: str
    in_sample: tuple[int, int]
    out_of_sample: tuple[int, int]
    in_sample_r: Decimal
    out_of_sample_r: Decimal
    in_sample_trades: int
    out_of_sample_trades: int

    def fields(self) -> dict[str, object]:
        return {
            "fold": self.name,
            "in_sample": list(self.in_sample),
            "out_of_sample": list(self.out_of_sample),
            "in_sample_r": str(self.in_sample_r),
            "out_of_sample_r": str(self.out_of_sample_r),
            "in_sample_trades": self.in_sample_trades,
            "out_of_sample_trades": self.out_of_sample_trades,
        }


@dataclass(frozen=True, slots=True)
class WalkForward:
    folds: tuple[Fold, ...]
    efficiency: str
    plan_fp: str

    def evidence(self) -> dict[str, object]:
        return {"efficiency": self.efficiency, "folds": len(self.folds), "plan_fp": self.plan_fp}


def _within(trades: Sequence[UnitTrade], span: tuple[int, int]) -> list[UnitTrade]:
    return [t for t in trades if span[0] <= t.opened_at.value_ns < span[1]]


def walk_forward(
    trades: Sequence[UnitTrade], *, start_ns: int, end_ns: int, folds: int = WALK_FORWARD_FOLDS
) -> Result[WalkForward]:
    """The folds of ``[start_ns, end_ns)``, each fold's R in and out of sample, and the
    efficiency."""
    if folds < 1 or end_ns <= start_ns:
        return invalid("split", "a walk-forward has one fold at least over a window that ends")
    span = (end_ns - start_ns) // (folds + 1)
    edges = [start_ns + i * span for i in range(folds + 1)] + [end_ns]
    made: list[Fold] = []
    windows: list[WalkForwardWindow] = []
    for index in range(folds):
        ins, outs = (edges[index], edges[index + 1]), (edges[index + 1], edges[index + 2])
        in_fp = fingerprint({"segment": "unit-span", "span": list(ins)})
        if is_refusal(in_fp):
            return in_fp
        out_fp = fingerprint({"segment": "unit-span", "span": list(outs)})
        if is_refusal(out_fp):
            return out_fp
        window = WalkForwardWindow.try_create(index, in_fp.value, out_fp.value)
        if is_refusal(window):
            return window
        windows.append(window.value)
        inside, outside = _within(trades, ins), _within(trades, outs)
        made.append(
            Fold(
                f"fold-{index + 1}",
                ins,
                outs,
                sum((t.r for t in inside), Decimal(0)),
                sum((t.r for t in outside), Decimal(0)),
                len(inside),
                len(outside),
            )
        )
    plan = plan_walk_forward(
        windows, window_count=folds, in_sample_span=span, out_of_sample_span=span, step=span
    )
    if is_refusal(plan):
        return plan
    plan_fp = plan.value.fingerprint()
    if is_refusal(plan_fp):
        return plan_fp
    earned = sum((f.in_sample_r for f in made), Decimal(0))
    kept = sum((f.out_of_sample_r for f in made), Decimal(0))
    efficiency = (kept / earned).quantize(_PLACES, ROUND_HALF_EVEN) if earned > 0 else Decimal(0)
    return Ok(WalkForward(tuple(made), str(efficiency), plan_fp.value.value))
