"""The per-decision diff of a live day against its replay (QB-23, Level 0 AD-5).

A live unit and its replay through QMB write the same `signal` rows, one per decision, because
both drive the one unit handler. Row ids carry each run's own scope, so a decision is keyed by
what it decided about: its instant, market and side, and its occurrence among that day's rows of
the same instant, market and side, so two rows of one key pair up in order and never overwrite
each other. Each key of the day is ``matched`` when both sides wrote the same outcome and
reason, ``differs`` when they wrote other ones, ``live_only`` or ``replay_only`` when one side
has no row. A day that matches lists no decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

__all__ = ["DecisionDiff", "decision_diff"]

Key: TypeAlias = tuple[int, str, str, int]


@dataclass(frozen=True, slots=True)
class DecisionDiff:
    matched: int
    decisions: tuple[Mapping[str, object], ...]
    """Every decision that is not matched, in the day's order."""

    def fields(self) -> dict[str, object]:
        return {
            "matched": self.matched,
            "differs": len(self.decisions),
            "decisions": [dict(d) for d in self.decisions],
        }


def _keyed(
    rows: Sequence[Mapping[str, object]], start: int, end: int
) -> dict[Key, Mapping[str, object]]:
    found: dict[Key, Mapping[str, object]] = {}
    seen: dict[tuple[int, str, str], int] = {}
    for row in rows:
        instant = row.get("instant")
        if type(instant) is int and start <= instant < end:
            about = (instant, str(row.get("market_id")), str(row.get("side")))
            seen[about] = seen.get(about, -1) + 1
            found[(*about, seen[about])] = row
    return found


def decision_diff(
    live: Sequence[Mapping[str, object]],
    replay: Sequence[Mapping[str, object]],
    *,
    start_ns: int,
    end_ns: int,
) -> DecisionDiff:
    """The decisions of ``[start_ns, end_ns)`` that live and replay did not decide alike."""
    lived, replayed = _keyed(live, start_ns, end_ns), _keyed(replay, start_ns, end_ns)
    matched = 0
    decisions: list[Mapping[str, object]] = []
    for key in sorted(lived.keys() | replayed.keys()):
        instant, market, side, occurrence = key
        here, there = lived.get(key), replayed.get(key)
        said = {
            "instant": instant,
            "market_id": market,
            "side": side,
            "occurrence": occurrence,
            "live": None if here is None else _said(here),
            "replay": None if there is None else _said(there),
        }
        if here is None or there is None:
            decisions.append(said | {"diff": "replay_only" if here is None else "live_only"})
        elif _said(here) != _said(there):
            decisions.append(said | {"diff": "differs"})
        else:
            matched += 1
    return DecisionDiff(matched, tuple(decisions))


def _said(row: Mapping[str, object]) -> dict[str, object]:
    return {"outcome": row.get("outcome"), "reason": cast("object", row.get("reason"))}
