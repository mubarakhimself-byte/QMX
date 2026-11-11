"""K9 test 15 on the node: a sizing number and an exit number move, the next entry uses them, and a
position already open keeps the numbers it opened with (AD-14 steps 5 and 6).

The node is the real :class:`~qmn.app.runtime.Runtime` over the conformance account, the node's own
fake venue: it keeps every ticket it receives, holds each stop and fires it on its bars. The unit
is the shipped dummy with ``risk_fraction`` and ``target_r`` bound to ``own-r-step@1``, which moves
each one step toward its cautious side after 20 losing trades. The dummy's long side is held open
and its swing stop answers a fixed level, so every trade is scripted. EURUSD enters once at 1.10000
with its stop at 1.09500 and is held. Gold enters at 2000.00 with its stop at 1990.00, and every
gold bar's low takes the stop, so each gold bar closes one losing trade and opens the next.

A restart is a real one: the node is stopped and opened again on the same data folder, over the
same venue, which still holds what it held.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import cast

import pytest
import test_app_runtime as base
from qmb.host.unit_handler import HeldPosition, UnitSliceHandler
from qmf.core import Account, AccountRole, VenueId
from qmf.core.chrono import Instant
from qmf.core.refusal import is_refusal
from qmf.data.journal_writer import JournalWriter
from qmf.venue.commands import CommandKind
from qml.blocks.api import EntryOrder, Signal
from qml.compile import CompiledUnit
from qml.protocol.unit import OHLC, HostedUnit, QuoteBar
from qmn.app.feed_keeper import Bar, FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.runtime import (
    ConformanceAccount,
    Deployment,
    NodeUnit,
    Runtime,
    Venue,
    compile_staged,
    parse_deployment,
    staging_folder,
)
from qmn.app.server import Node, open_node
from qmn.app.store import Json

EURUSD = "fx.eurusd"
GOLD = "metal.xauusd"
BAR = 900_000_000_000
EQUITY = Decimal("100000")
"""The section's equity: 0.5 % of it at a 0.0050 stop is 1.00 lot of EURUSD."""
EUR_STOP = Decimal("1.09500")
GOLD_STOP = Decimal("1990.00")
LOSERS = 20
RESTART_AT = 13
"""The trade the restart comes after, part way through the count of 20."""


def document() -> dict[str, object]:
    """The dummy with both risk numbers moved by ``own-r-step@1`` every 20 closed trades, and a
    time exit long enough that it never closes a scripted position."""
    unit = cast("dict[str, object]", json.loads(json.dumps(base.dummy_document())))
    numbers = cast("dict[str, dict[str, object]]", unit["numbers"])
    for name in ("risk_fraction", "target_r"):
        numbers[name]["kind"] = "calibrated"
        numbers[name]["motion"] = {
            "mode": "shrink_from_own_trades",
            "source": "own_record",
            "cadence": {"every_closed_trades": LOSERS},
            "min_count": LOSERS,
            "shrink_k": 100,
            "step_limit": 1,
            "rule": "own-r-step@1",
            "rule_params": {"cautious": "-1"},
        }
    numbers["time_out_bars"]["default"] = "1000"
    return unit


class _Answering:
    """A block bound to one answer, so the scripted bars decide every trade."""

    def __init__(self, answer: object) -> None:
        self._answer = answer

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        return self._answer

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


@dataclass
class Rig:
    root: Path
    account: ConformanceAccount
    feed: FeedKeeper
    source: RecordedSource
    now: list[int]
    trading: tuple[str, ...]
    """The markets whose long side is held open; every other side stays quiet."""
    node: Node | None = None

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def runtime(self) -> Runtime:
        assert self.node is not None and self.node.runtime is not None
        return self.node.runtime

    def call(self, op: str, args: Mapping[str, Json]) -> dict[str, Json]:
        assert self.node is not None
        return self.node.call(op, dict(args))


def rig(root: Path, trading: tuple[str, ...] = (EURUSD, GOLD)) -> Rig:
    """One conformance account and its feed, which outlive a node restart."""
    now = [base.LIVE_FROM - base.DAY]
    source = RecordedSource([])
    opened = ConformanceAccount.open(
        Account(base.ACCOUNT, VenueId("icmarkets-ctrader"), AccountRole.DEMO), EQUITY
    )
    assert not is_refusal(opened), opened
    feed = FeedKeeper(
        "ctrader", "demo", source, tuple(base.MARKETS), lambda: now[0], Recording(None)
    )
    feed.listen(opened.value.on_bar)
    for at, market, bar in base.month().bars:
        if at < base.LIVE_FROM:
            feed.recording.keep(market, bar)
    return Rig(root, opened.value, feed, source, now, trading)


@cache
def compiled_for(data: Path) -> CompiledUnit:
    """The unit as the node compiles it from the staged files, compiled once per folder."""
    made = compile_staged(
        parse_deployment(cast("Mapping[str, object]", staged(data))),
        staging_folder(data, "dep-1"),
        nets_positions=False,
    )
    assert isinstance(made, CompiledUnit), made
    return made


def staged(data: Path) -> dict[str, Json]:
    deployment = base.deployment(data)
    deployment["unit_document"] = cast("Json", document())
    return deployment


def open_on(rig: Rig) -> None:
    """Open the node on the rig's data folder: its first start, or a process restart."""

    def venues(journal: JournalWriter, epoch: str) -> Mapping[str, Venue]:
        del journal, epoch
        return {base.ACCOUNT: Venue(rig.account, rig.feed)}

    def sleep(seconds: float) -> None:
        rig.now[0] += int(seconds * 1e9)

    rig.node = open_node(
        rig.data,
        here="fp-pc-1",
        machine="pc",
        clock_ns=lambda: rig.now[0],
        sleep=sleep,
        random_bytes=lambda size: b"\x07" * size,
        venues=venues,
    )

    def compile_once(deployment: Deployment, folder: Path, **_: object) -> CompiledUnit:
        del deployment, folder
        return compiled_for(rig.data)

    rig.runtime.compile = compile_once


def deploy(rig: Rig) -> None:
    rig.now[0] = base.LIVE_FROM - base.DAY
    deployment = staged(rig.data)
    fingerprint = compiled_for(rig.data).compiled_fingerprint.value
    deployment["compiled_fingerprint"] = fingerprint
    cast("dict[str, Json]", deployment["g_record"])["compiled_fingerprint"] = fingerprint
    open_on(rig)
    deployed = rig.call("deploy", {"op_id": "op-deploy-1", "deployment": deployment})
    assert deployed["ok"] is True, deployed
    trading(rig)


def trading(rig: Rig) -> None:
    """Tick until the unit trades, then script its long side."""
    for _ in range(3000):
        rig.runtime.tick()
        hosted = rig.runtime.hosted.get("dep-1")
        if hosted is not None and hosted.phase.value == "trading":
            break
    else:
        hosted = rig.runtime.hosted.get("dep-1")
        pytest.fail(f"the unit never traded: {hosted and (hosted.phase, hosted.detail)}")
    script(unit_of(rig), rig.trading)


def node_unit(rig: Rig) -> NodeUnit:
    return cast("NodeUnit", rig.runtime.hosted["dep-1"].unit)


def unit_of(rig: Rig) -> HostedUnit:
    hosted = node_unit(rig).hosted_unit
    assert hosted is not None
    return hosted


def handler_of(rig: Rig) -> UnitSliceHandler:
    handler = node_unit(rig).handler
    assert handler is not None
    return handler


def script(unit: HostedUnit, trading: tuple[str, ...]) -> None:
    """Hold the long side of each trading market open on every bar and fix each market's stop."""
    held = _Answering(Signal(state=True, value=Decimal(1)))
    quiet = _Answering(Signal(state=False, value=Decimal(0)))
    for market in unit._core.markets:
        stop = EUR_STOP if market.market_id == EURUSD else GOLD_STOP
        for key in list(market.instances):
            if key.endswith(("trend", "strength", "rsi_cross")):
                opened = key.startswith("long.") and market.market_id in trading
                market.instances[key] = held if opened else quiet
            elif key.endswith("next_open"):
                market.instances[key] = _Answering(EntryOrder(kind="market", at="next_open"))
            elif key.endswith("swing_stop"):
                market.instances[key] = _Answering(stop)


def quote_bar(at: int, bid: tuple[str, str, str, str], spread: str) -> QuoteBar:
    o, h, lo, c = (Decimal(one) for one in bid)
    gap = Decimal(spread)
    return QuoteBar(Instant(at), OHLC(o, h, lo, c), OHLC(o + gap, h + gap, lo + gap, c + gap))


def eur_bar(at: int, high: str = "1.09995") -> QuoteBar:
    """A EURUSD bar whose ask closes at 1.10000. Its bid high reaches a target only when asked."""
    return quote_bar(at, ("1.09990", high, "1.09980", "1.09990"), "0.00010")


def gold_bar(at: int, low: str = "1985.00") -> QuoteBar:
    """A gold bar whose ask closes at 2000.00 and whose bid low takes a 1990.00 stop."""
    return quote_bar(at, ("1999.90", "2000.00", low, "1999.90"), "0.10")


def play(rig: Rig, at: int, bars: Sequence[tuple[str, QuoteBar]]) -> None:
    rig.now[0] = at
    rig.source.play(
        [
            *(Bar(market, bar) for market, bar in bars),
            *(Quote(market, at, bar.bid.close, bar.ask.close, "both") for market, bar in bars),
        ]
    )
    rig.runtime.tick()


def rows(rig: Rig, kind: str) -> list[dict[str, Json]]:
    answer = rig.call("journal_tail", {"streams": ["unit"]})
    assert answer["ok"] is True, answer
    listed = cast("list[dict[str, Json]]", cast("dict[str, Json]", answer["value"])["rows"])
    return [cast("dict[str, Json]", row["body"]) for row in listed if row["kind"] == kind]


def eur_held(rig: Rig) -> list[HeldPosition]:
    return [held for _, held in handler_of(rig).held_in(EURUSD)]


def gold_trades(rig: Rig) -> int:
    return sum(1 for row in rows(rig, "trade") if row["exit_kind"] == "stop")


@dataclass(frozen=True)
class Run:
    moved_at_trade: int
    """How many losing trades had closed when the calibration rows landed."""
    calibrations: tuple[tuple[str, str, str, str], ...]
    """Each move as (number, old, new, calibration row id)."""
    eur_target_after_move: Decimal | None
    amends: int
    """Tickets that amended an open position's protection at the venue."""


RISK_NUMBERS = ("risk_fraction", "target_r")
"""The two numbers this test moves. The dummy's own logic number moves on the same trades too."""


def calibrations(rig: Rig) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(
        (str(row["number"]), str(row["old"]), str(row["new"]), str(row["row_id"]))
        for row in rows(rig, "calibration")
        if row["number"] in RISK_NUMBERS
    )


def drive(rig: Rig, *, restart_at: int | None = None) -> tuple[Run, int]:
    """EURUSD opens and is held while gold loses 20 trades; the run's moves and the next bar."""
    at = base.LIVE_FROM
    play(rig, at, [(EURUSD, eur_bar(at)), (GOLD, gold_bar(at, "1995.00"))])
    at += BAR
    moved_at = 0
    while not calibrations(rig) and at < base.LIVE_FROM + 60 * BAR:
        play(rig, at, [(EURUSD, eur_bar(at)), (GOLD, gold_bar(at))])
        at += BAR
        if restart_at is not None and gold_trades(rig) == restart_at:
            rig.runtime.stop()
            open_on(rig)
            trading(rig)
            restart_at = None
        if calibrations(rig) and not moved_at:
            moved_at = gold_trades(rig)
    held = eur_held(rig)
    amends = sum(
        1
        for ticket in rig.account.received
        if ticket.command.kind is CommandKind.AMEND_PROTECTION
    )
    return (
        Run(
            moved_at,
            calibrations(rig),
            held[0].target if held else None,
            amends,
        ),
        at,
    )


@pytest.fixture
def started(tmp_path: Path) -> Iterator[Rig]:
    made = rig(tmp_path)
    deploy(made)
    yield made
    if made.node is not None and made.node.runtime is not None:
        made.node.runtime.stop()


def test_k9_15_self_configuration(started: Rig) -> None:
    run, at = drive(started)

    play(started, at, [(EURUSD, eur_bar(at, high="1.10960")), (GOLD, gold_bar(at, "1995.00"))])
    past_the_moved_target = len(eur_held(started))
    at += BAR
    play(started, at, [(EURUSD, eur_bar(at, high="1.11000")), (GOLD, gold_bar(at, "1995.00"))])
    at += BAR
    play(started, at, [(EURUSD, eur_bar(at)), (GOLD, gold_bar(at, "1995.00"))])
    closed = [row for row in rows(started, "trade") if row["exit_kind"] != "stop"]
    entries = [
        t.quantity
        for t in started.account.received
        if t.market_id == EURUSD and t.command.kind is CommandKind.PLACE_ORDER
    ]
    held = eur_held(started)
    sized = [
        row
        for row in rows(started, "signal")
        if row.get("market_id") == EURUSD and row.get("outcome") == "taken" and row.get("binding")
    ][-1]
    inputs = cast("dict[str, dict[str, Json]]", sized["inputs"])
    in_force = cast("dict[str, Json]", sized["numbers_in_force"])

    assert run.moved_at_trade == LOSERS, "the move lands on trade 20, with EURUSD held"
    assert sorted((n, old, new) for n, old, new, _ in run.calibrations) == [
        ("risk_fraction", "0.005", "0.0049"),
        ("target_r", "2", "1.9"),
    ]
    assert run.eur_target_after_move == Decimal("1.11000"), "the open trade keeps its target"
    assert run.amends == 0, "a moved number amends no open position at the venue"
    assert past_the_moved_target == 1, "a bar past 1.1095 but short of 1.1100 leaves it open"
    assert [(row["exit_kind"], row["exit_price"], row["reason_code"]) for row in closed] == [
        ("target", "1.09990", "target")
    ]
    stamped = cast("dict[str, Json]", closed[0]["numbers_at_entry"])
    assert (stamped["number:target_r"], stamped["number:risk_fraction"]) == ("2", "0.005")
    assert (in_force["risk_fraction"], in_force["target_r"]) == ("0.0049", "1.9")
    assert inputs["account.realised_since"]["value"] == "-9450", "20 gold losses since the start"
    assert entries == [Decimal("1.00"), Decimal("0.88")], "0.0049 of 90550 at 500 a lot"
    assert [h.target for h in held] == [Decimal("1.10950")]
    assert dict(held[0].entry_stamps)["number:target_r"] == Decimal("1.9")


def test_a_restart_at_trade_13_ends_in_the_same_move(tmp_path: Path) -> None:
    """Gold alone, so the count is all that differs: the node restarted after its 13th losing
    trade moves both numbers on trade 20, to the same values with the same row ids."""
    straight = rig(tmp_path / "straight", (GOLD,))
    deploy(straight)
    once, _ = drive(straight)
    straight.runtime.stop()

    restarted = rig(tmp_path / "restarted", (GOLD,))
    deploy(restarted)
    again, _ = drive(restarted, restart_at=RESTART_AT)
    restarted.runtime.stop()

    assert once.moved_at_trade == LOSERS
    assert again.moved_at_trade == LOSERS, "the count survives the restart at trade 13"
    assert again.calibrations == once.calibrations
