"""A unit's walk-forward: each fold picks a candidate in sample and scores it out of sample (B14).

Every candidate trades the whole window once, so each warms up as it would live. The window is
cut into ``folds + 1`` equal segments. Fold ``i`` picks the candidate with the best Sharpe in
segment ``i`` (in sample) and scores that pick in segment ``i + 1`` (out of sample), so no fold
scores its pick on the span it was picked on, and no two out-of-sample spans overlap. A trade
belongs to the segment its fill opened in. The fold geometry rides the kept
:func:`~qmb.robustness.walkforward.plan_walk_forward`, so the plan carries the kept identity and
fingerprint.

The efficiency the judge reads (`judge.md` §3, step 4) is the preset's "validation Sharpe over
in-sample Sharpe": the picks' out-of-sample Sharpe over their in-sample Sharpe, summed across
the folds that picked. A span's Sharpe is its trades' mean R over their sample standard
deviation; a span with fewer than two trades, or trades that all earned the same R, has none. A
candidate with no in-sample Sharpe is never picked, a pick with no out-of-sample Sharpe kept
nothing and scores 0, and a fold where nothing can be picked is left out of both sums. With no
in-sample edge the efficiency is 0, and with no fold that picked there is none.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Ok, Result, is_refusal

from qmb._refuse import invalid
from qmb.host.unit_handler import UnitTrade
from qmb.robustness.walkforward import WalkForwardWindow, plan_walk_forward

__all__ = ["WALK_FORWARD_FOLDS", "Fold", "WalkForward", "sharpe", "walk_forward"]

WALK_FORWARD_FOLDS: Final = 3
"""Starting default of a walk-forward run's ``split.folds``."""
_PLACES: Final = Decimal("0.0001")


def _text(value: Decimal | None) -> str | None:
    return None if value is None else str(value.quantize(_PLACES, ROUND_HALF_EVEN))


def sharpe(rs: Sequence[Decimal]) -> Decimal | None:
    """Mean R over the sample standard deviation of R, or None below two trades or no spread."""
    if len(rs) < 2:
        return None
    mean = sum(rs, Decimal(0)) / len(rs)
    variance = sum(((r - mean) ** 2 for r in rs), Decimal(0)) / (len(rs) - 1)
    return None if variance == 0 else mean / variance.sqrt()


@dataclass(frozen=True, slots=True)
class Fold:
    name: str
    in_sample: tuple[int, int]
    out_of_sample: tuple[int, int]
    pick: str | None
    """The candidate with the best in-sample Sharpe, or None when no candidate has one."""
    in_sample_sharpe: Decimal | None
    out_of_sample_sharpe: Decimal | None
    in_sample_trades: int
    out_of_sample_trades: int

    def fields(self) -> dict[str, object]:
        return {
            "fold": self.name,
            "in_sample": list(self.in_sample),
            "out_of_sample": list(self.out_of_sample),
            "pick": self.pick,
            "in_sample_sharpe": _text(self.in_sample_sharpe),
            "out_of_sample_sharpe": _text(self.out_of_sample_sharpe),
            "in_sample_trades": self.in_sample_trades,
            "out_of_sample_trades": self.out_of_sample_trades,
        }


@dataclass(frozen=True, slots=True)
class WalkForward:
    folds: tuple[Fold, ...]
    candidates: int
    efficiency: Decimal | None
    """None when no fold could pick a candidate."""
    plan_fp: str

    def evidence(self) -> dict[str, object]:
        return {
            "efficiency": _text(self.efficiency),
            "folds": len(self.folds),
            "candidates": self.candidates,
            "plan_fp": self.plan_fp,
        }


def _within(trades: Sequence[UnitTrade], span: tuple[int, int]) -> list[Decimal]:
    return [t.r for t in trades if span[0] <= t.opened_at.value_ns < span[1]]


def _fold(
    name: str,
    candidates: Mapping[str, Sequence[UnitTrade]],
    ins: tuple[int, int],
    outs: tuple[int, int],
) -> Fold:
    scored = [(sharpe(_within(trades, ins)), cand) for cand, trades in candidates.items()]
    eligible = [(s, cand) for s, cand in scored if s is not None]
    if not eligible:
        return Fold(name, ins, outs, None, None, None, 0, 0)
    best, pick = max(eligible, key=lambda pair: pair[0])
    inside, outside = _within(candidates[pick], ins), _within(candidates[pick], outs)
    return Fold(name, ins, outs, pick, best, sharpe(outside), len(inside), len(outside))


def walk_forward(
    candidates: Mapping[str, Sequence[UnitTrade]],
    *,
    start_ns: int,
    end_ns: int,
    folds: int = WALK_FORWARD_FOLDS,
) -> Result[WalkForward]:
    """The folds of ``[start_ns, end_ns)`` over each candidate's trades, by name, and the
    efficiency of the picks. A tie in sample picks the candidate named first."""
    if not candidates:
        return invalid("candidates", "a walk-forward picks among one candidate at least")
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
        made.append(_fold(f"fold-{index + 1}", candidates, ins, outs))
    plan = plan_walk_forward(
        windows, window_count=folds, in_sample_span=span, out_of_sample_span=span, step=span
    )
    if is_refusal(plan):
        return plan
    plan_fp = plan.value.fingerprint()
    if is_refusal(plan_fp):
        return plan_fp
    picked = [f.in_sample_sharpe for f in made if f.in_sample_sharpe is not None]
    efficiency: Decimal | None = None
    if picked:
        earned = sum(picked, Decimal(0))
        kept = sum(
            (f.out_of_sample_sharpe or Decimal(0) for f in made if f.pick is not None), Decimal(0)
        )
        efficiency = kept / earned if earned > 0 else Decimal(0)
    return Ok(WalkForward(tuple(made), len(candidates), efficiency, plan_fp.value.value))
