"""The judge's paper scoring: a paper lane's fresh trades, scored by script (Part B judge.md).

A market that became a candidate needs fresh trades after it became one before it reaches his
card. A paper lane starts when its unit and market go to paper; only trades closed after that
count. The lane is scored two ways, both by script:

- its record in R after costs, the sum of the fresh trades' R;
- a sequential score: the average, over a fixed set of bets, of the wealth a bettor would hold
  after staking that fraction on each trade's R in turn. It starts at 1, and reaching
  `sequential_pass` (20) is the pass, so a lane can be judged after any trade without the
  repeated looks inflating its chance.

The lane is "fresh enough" once it holds the later of `fresh_trades` trades and `fresh_days`
days, and "ready for his card" once it holds the later of `card_trades` and `card_days` with its
sequential score not below its start. A trade whose initial risk is unknown has no R; it is
counted as `r_missing` and never scored.

`paper_run` names the `paper-run` item (version 2) by the lane and builds its fields. Stdlib and
qmf-core only; the host's records job reads the trades and lands the item.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Final, cast

from qmf.core import fingerprint, is_refusal

__all__ = [
    "PAPER_RUN_KIND",
    "PaperLane",
    "PaperRule",
    "PaperScore",
    "PaperTrade",
    "ended_run",
    "paper_run",
    "score",
    "sequential_score",
]

PAPER_RUN_KIND: Final = "paper-run"
SCORER_VERSION: Final = "1"
NS_PER_DAY: Final = 86_400 * 1_000_000_000
SIX_PLACES: Final = Decimal("0.000001")


@dataclass(frozen=True, slots=True)
class PaperRule:
    """`[judge]`'s paper settings, each with its starting default (judge.md section 6)."""

    fresh_trades: int = 30
    fresh_days: int = 14
    card_trades: int = 30
    card_days: int = 28
    sequential_pass: Decimal = Decimal(20)
    bets: tuple[Decimal, ...] = (Decimal("0.025"), Decimal("0.05"), Decimal("0.1"), Decimal("0.2"))

    @classmethod
    def of(cls, judge: Mapping[str, object]) -> PaperRule:
        """The rule `[judge]` describes; a key that is missing or not usable keeps its default."""
        base = cls()

        def whole(name: str, default: int) -> int:
            value = judge.get(name, default)
            return (
                value
                if isinstance(value, int) and not isinstance(value, bool) and value > 0
                else default
            )

        bets = judge.get("sequential_bets")
        listed = cast("list[object]", bets) if isinstance(bets, list) else []
        parsed = tuple(found for item in listed if (found := _exact(item)) is not None)
        return cls(
            fresh_trades=whole("fresh_trades", base.fresh_trades),
            fresh_days=whole("fresh_days", base.fresh_days),
            card_trades=whole("paper_card_trades", base.card_trades),
            card_days=whole("paper_card_days", base.card_days),
            sequential_pass=_exact(judge.get("sequential_pass")) or base.sequential_pass,
            bets=parsed or base.bets,
        )


def _exact(value: object) -> Decimal | None:
    """A setting's number as an exact decimal: decimal text or a whole number, never a float."""
    if isinstance(value, bool) or not isinstance(value, str | int):
        return None
    try:
        found = Decimal(str(value))
    except InvalidOperation:
        return None
    return found if found.is_finite() and found > 0 else None


DEFAULT_RULE: Final = PaperRule()


@dataclass(frozen=True, slots=True)
class PaperLane:
    """One paper lane: a unit on a market, on one account, on one node, since it began."""

    unit: str
    market: str
    account: str
    node: str
    started_at_ns: int

    @property
    def item(self) -> str:
        """Named by the lane and its start, never by when it was scored."""
        named = fingerprint(
            {
                "unit": self.unit,
                "market": self.market,
                "account": self.account,
                "node": self.node,
                "started_at_ns": self.started_at_ns,
            }
        )
        if is_refusal(named):
            raise ValueError(f"a paper lane does not fingerprint: {named}")
        return f"{PAPER_RUN_KIND}-{named.value.digest[:24]}"


@dataclass(frozen=True, slots=True)
class PaperTrade:
    """A closed paper trade as the scoring reads it: when it closed and its R after costs."""

    closed_at_ns: int
    r: Decimal | None


def sequential_score(rs: Sequence[Decimal], bets: Sequence[Decimal]) -> Decimal:
    """The average wealth, over ``bets``, of staking each bet on every trade's R in turn.

    It starts at 1. A bet whose stake would lose more than everything holds nothing from then on.
    """
    if not bets:
        return Decimal(1)
    total = Decimal(0)
    for bet in bets:
        wealth = Decimal(1)
        for r in rs:
            wealth = max(Decimal(0), wealth * (Decimal(1) + bet * r))
        total += wealth
    return (total / len(bets)).quantize(SIX_PLACES)


@dataclass(frozen=True, slots=True)
class PaperScore:
    trades: int
    r_missing: int
    record_r: Decimal
    sequential: Decimal
    fresh_enough: bool
    ready_for_card: bool
    passed: bool


def score(
    lane: PaperLane, trades: Sequence[PaperTrade], *, now_ns: int, rule: PaperRule = DEFAULT_RULE
) -> PaperScore:
    """Score a lane's trades closed after it began, in the order they closed."""
    fresh = sorted(
        (trade for trade in trades if trade.closed_at_ns >= lane.started_at_ns),
        key=lambda trade: trade.closed_at_ns,
    )
    rs = [trade.r for trade in fresh if trade.r is not None]
    sequential = sequential_score(rs, rule.bets)
    span = now_ns - lane.started_at_ns
    return PaperScore(
        trades=len(fresh),
        r_missing=len(fresh) - len(rs),
        record_r=sum(rs, Decimal(0)),
        sequential=sequential,
        fresh_enough=len(rs) >= rule.fresh_trades and span >= rule.fresh_days * NS_PER_DAY,
        ready_for_card=len(rs) >= rule.card_trades
        and span >= rule.card_days * NS_PER_DAY
        and sequential >= Decimal(1),
        passed=sequential >= rule.sequential_pass,
    )


def _iso(ns: int) -> str:
    return datetime.fromtimestamp(ns // 1_000_000_000, tz=UTC).isoformat().replace("+00:00", "Z")


def ended_run(fields: Mapping[str, object], *, status: str, ended_at_ns: int) -> dict[str, object]:
    """A lane's last `paper-run` fields once it left paper, its score as last landed."""
    return {**fields, "status": status, "ended_at": _iso(ended_at_ns)}


def paper_run(
    lane: PaperLane,
    trades: Sequence[PaperTrade],
    *,
    now_ns: int,
    status: str = "running",
    ended_at_ns: int | None = None,
    journal: Sequence[str] = (),
    rule: PaperRule = DEFAULT_RULE,
) -> tuple[str, dict[str, object]]:
    """The lane's `paper-run` item and its version 2 fields."""
    scored = score(lane, trades, now_ns=now_ns, rule=rule)
    fields: dict[str, object] = {
        "unit": lane.unit,
        "market": lane.market,
        "account": lane.account,
        "node": lane.node,
        "started_at": _iso(lane.started_at_ns),
        "status": status,
        "record_r": str(scored.record_r),
        "sequential_score": str(scored.sequential),
        "trades": scored.trades,
        "r_missing": scored.r_missing,
        "fresh_enough": scored.fresh_enough,
        "ready_for_card": scored.ready_for_card,
        "sequential_passed": scored.passed,
        "journal": sorted(journal),
        "scorer_version": SCORER_VERSION,
    }
    if ended_at_ns is not None:
        fields["ended_at"] = _iso(ended_at_ns)
    return lane.item, fields
