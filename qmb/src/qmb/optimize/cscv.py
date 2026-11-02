"""The probability of backtest overfitting of a unit's candidates, by combinatorial cross-checks.

An optimize run trades every candidate over one window cut into ``segments`` equal spans and
hands each candidate's R per span here (B14, the judge's `pbo` step). Every way of choosing half
the spans is one in-sample set and the rest its out-of-sample set: the candidate best in sample
is ranked among all out of sample, a tie at its mid-rank, and the PBO is the share of splits
where it lands in the bottom half (Bailey, Borwein, Lopez de Prado and Zhu, "The Probability of
Backtest Overfitting"). Exact rationals throughout; no candidate is dropped.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
from typing import Final

from qmf.core.refusal import Ok, Result

from qmb._refuse import invalid

__all__ = ["PBO_SEGMENTS", "PBO_SEGMENTS_MOST", "probability_of_overfitting"]

PBO_SEGMENTS: Final = 8
"""Starting default of an optimize run's ``segments``: even, so each split halves the spans."""
PBO_SEGMENTS_MOST: Final = 16
"""Starting default of the most ``segments`` an optimize run takes: 16 spans make 12,870 splits,
while the split count grows near fourfold with each two spans more (40 spans make 1.4e11)."""


def probability_of_overfitting(rows: Sequence[Sequence[Decimal]]) -> Result[Fraction]:
    """``rows`` holds each candidate's R per span, every row the same even length."""
    if len(rows) < 2:
        return invalid("candidates", "the PBO compares two candidates at least")
    width = len(rows[0])
    if width < 2 or width % 2 or any(len(row) != width for row in rows):
        return invalid("segments", "every candidate has the same even number of spans")
    below = 0
    splits = list(combinations(range(width), width // 2))
    for chosen in splits:
        rest = [i for i in range(width) if i not in chosen]
        inside = [sum((row[i] for i in chosen), Decimal(0)) for row in rows]
        outside = [sum((row[i] for i in rest), Decimal(0)) for row in rows]
        best = inside.index(max(inside))
        below_pick = sum(1 for value in outside if value < outside[best])
        tied = sum(1 for value in outside if value == outside[best]) - 1
        rank = below_pick + 1 + Fraction(tied, 2)
        if rank / (len(rows) + 1) <= Fraction(1, 2):
            below += 1
    return Ok(Fraction(below, len(splits)))
