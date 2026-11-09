"""The control runner: each brake row runs in the unit, and no row reaches an exit (AD-12, AD-9).

The runner is one loop over the compiled rows. Each row is fed the facts its block declares. A row
whose facts are absent answers its cold rule: warn, or run in shadow. A row whose block raises
writes ``link_fault`` and stands its scope down for the rest of the run. A row that fires answers
its verb. Nothing here reads a chain, a fold, a reading or an exit: one plain ``try`` around one
block call is the whole fault wall, so a raise can never become a refusal into ``close_frontier``.

``own_facts`` computes the unit's own statistics from its journal here, in QML, so both hosts feed
a brake the same numbers by construction (AD-15). Until sessions compile, a session is the UTC
calendar day, a labelled placeholder owned by "numbers talk".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from qmf.core.chrono import Instant
from qmf.risk.controls import (
    ENTRY_SCOPES,
    Answer,
    ColdRule,
    ControlRow,
    gate_open,
    refuses_entries,
)
from qmf.risk.journal import LINK_FAULT

from qml.blocks.api import Halt, Instance
from qml.motion.engine import ClosedTrade

__all__ = [
    "Cold",
    "ControlRun",
    "Fired",
    "Raised",
    "Runner",
    "own_facts",
]

_NS_PER_DAY: Final[int] = 86_400_000_000_000
"""One UTC day in nanoseconds: the session boundary until sessions compile (RC-33)."""


@dataclass(frozen=True, slots=True)
class Fired:
    """One row that answered a halt, with the answer it runs and whether it is only in shadow."""

    row: ControlRow
    answer: Answer
    shadowed: bool


@dataclass(frozen=True, slots=True)
class Raised:
    """One row whose block raised: the code its risk-event row carries."""

    row: ControlRow
    code: str


@dataclass(frozen=True, slots=True)
class Cold:
    """One row whose declared facts are not there, and which facts they are."""

    row: ControlRow
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ControlRun:
    """One step's answers from every brake row."""

    fired: tuple[Fired, ...] = ()
    raised: tuple[Raised, ...] = ()
    cold: tuple[Cold, ...] = ()
    stood_down: tuple[str, ...] = ()
    """The scopes a raise stood down this step, each named once."""

    @property
    def refusal(self) -> Fired | None:
        """The first row that refuses this step's entries, or None when none does."""
        return next(
            (fired for fired in self.fired if refuses_entries(fired.row, shadowed=fired.shadowed)),
            None,
        )

    @property
    def refusal_reason(self) -> str | None:
        """Why this step's entries are refused, in the words its rows use, or None."""
        if (fired := self.refusal) is not None:
            return f"halt slot: {fired.row.code} answers {fired.answer.verb.value}"
        down = sorted(ENTRY_SCOPES & set(self.stood_down))
        if down:
            return f"halt slot: {' and '.join(down)} stood down after link_fault"
        return None


class Runner:
    """The rows one unit runs, the instance made for each, and the scopes a raise stood down.

    ``instances`` is the unit's own live mapping, keyed by ``ControlRow.key``, so a host or a test
    that swaps one row's instance reaches the runner through the one table that holds it.
    """

    def __init__(self, rows: Sequence[ControlRow], instances: Mapping[str, Instance]) -> None:
        self._rows = tuple(rows)
        self._instances = instances
        self._down: set[str] = set()
        self._down_scopes: set[str] = set()
        self._cold: set[str] = set()

    def run(self, facts: Mapping[str, object]) -> ControlRun:
        """Run every row that is not stood down, feeding each the facts it declares."""
        fired: list[Fired] = []
        raised: list[Raised] = []
        cold: list[Cold] = []
        down: list[str] = []
        for row in self._rows:
            if row.key in self._down or not gate_open(row, facts):
                continue
            missing = tuple(read for read in row.reads if read not in facts)
            if missing and row.until_n is ColdRule.WARN:
                if row.key not in self._cold:
                    self._cold.add(row.key)
                    cold.append(Cold(row, missing))
                continue
            evidence: dict[str, object] = {
                read.partition(".")[2]: facts[read] for read in row.reads if read in facts
            }
            try:
                raw = self._instances[row.key].update(evidence)
            except Exception:  # a row's raise is link_fault, and its scope stands down
                self._down.add(row.key)
                raised.append(Raised(row, LINK_FAULT))
                if row.scope not in self._down_scopes:
                    self._down_scopes.add(row.scope)
                    down.append(row.scope)
                continue
            if not isinstance(raw, Halt):
                continue
            shadowed = row.shadow or (bool(missing) and row.until_n is ColdRule.SHADOW)
            fired.append(Fired(row, Answer(row.verb, None, raw.reason, row.code), shadowed))
        return ControlRun(tuple(fired), tuple(raised), tuple(cold), tuple(down))


def own_facts(trades: Sequence[ClosedTrade], instant: Instant) -> dict[str, object]:
    """The unit's own statistics from its journal, in the units their blocks read.

    ``session_loss_r`` and ``session_fills`` count the trades closed in the instant's session,
    which is the UTC calendar day until sessions compile. ``loss_streak`` counts the losing trades
    at the end of the journal, and ``losing_day_streak`` the losing days before it.
    """
    rows = sorted(trades, key=lambda trade: (trade.closed_at.value_ns, trade.trade_id))
    today = _day(instant)
    session = [trade for trade in rows if _day(trade.closed_at) == today]
    loss_streak = 0
    for trade in reversed(rows):
        if trade.r_after_costs >= 0:
            break
        loss_streak += 1
    days: dict[int, Decimal] = {}
    for trade in rows:
        day = _day(trade.closed_at)
        days[day] = days.get(day, Decimal(0)) + trade.r_after_costs
    losing_days = 0
    for day in sorted(days, reverse=True):
        if days[day] >= 0:
            break
        losing_days += 1
    return {
        "own.session_loss_r": sum((trade.r_after_costs for trade in session), Decimal(0)),
        "own.session_fills": len(session),
        "own.loss_streak": loss_streak,
        "own.losing_day_streak": losing_days,
    }


def _day(instant: Instant) -> int:
    """The UTC day number of one instant, the session key until sessions compile."""
    return instant.value_ns // _NS_PER_DAY
