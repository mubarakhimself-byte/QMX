"""Futures replay contract by contract, with the roll as an event and no back-adjusted price (B11).

A two-contract fixture: ESH5 trades near 5000 and ESM5 near 5050 across the 14 March 2025 roll.
Before the roll the unit sees ESH5's own bars; from the roll on, ESM5's own bars, with a window
of ESM5's bars from before the roll. The 50-point gap between the two is never taken out of
either contract's prices.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from qmb.host.replay import (
    Bar,
    BarWindow,
    DataCard,
    FuturesChain,
    Roll,
    VenueDay,
    futures_feed,
    replay_windowed,
)
from qmb.host.unit_handler import UnitSliceHandler
from qmb.runloop.bars import BarBuilder
from qmb.runloop.loop import RestingIntent, SliceObservation
from qmb.runloop.stream import emit_stream_control, record_stream_subscription
from qmf.core.chrono import Instant
from qmf.core.refusal import Ok, Result, TypedRefusal, is_ok, is_refusal
from qml.protocol.unit import OHLC, OwnPosition

ROLL_AT = "2025-03-14T00:00:00Z"
ROLL_NS = 1_741_910_400_000_000_000
START_MS = 1_741_910_100_000
"""2025-03-13T23:55Z, five minutes before the roll."""
CARD: dict[str, object] = {
    "stitching": {"method": "contract-by-contract", "adjusted": False},
    "rolls": [{"at": ROLL_AT, "from": "ESH5", "to": "ESM5"}],
}


def minutes(level: str) -> list[Bar]:
    """Ten one-minute bars from 23:55, each closing a quarter point above the last."""
    bars: list[Bar] = []
    for step in range(10):
        close = Decimal(level) + Decimal("0.25") * step
        bars.append(Bar(START_MS + step * 60_000, 60, OHLC(close, close, close, close)))
    return bars


class Watcher:
    """A stand-in unit that records the last close and the oldest close its window holds."""

    def __init__(self, windows: Mapping[str, BarWindow], rest_at_ns: int | None = None) -> None:
        self.windows = windows
        self.rest_at_ns = rest_at_ns
        self.seen: list[tuple[str, Decimal, Decimal]] = []

    def open_on(self, market: str) -> tuple[OwnPosition, ...]:
        """This stand-in holds nothing on any market, so only a resting order refuses a roll."""
        return ()

    def update_stream(
        self, stream_id: str, observation: SliceObservation | None, frontier: Instant
    ) -> Result[None]:
        return Ok(None)

    def scheduled_position_event(self, stream_id: str, frontier: Instant) -> Result[None]:
        return Ok(None)

    def execute_resting(
        self, intent: RestingIntent, observation: SliceObservation | None, frontier: Instant
    ) -> Result[bool]:
        return Ok(False)

    def update_closed_data(
        self, stream_id: str, observation: SliceObservation, frontier: Instant
    ) -> Result[None]:
        return Ok(None)

    def mint_intents(self, stream_id: str, frontier: Instant) -> Result[object]:
        window = self.windows[stream_id]
        held = list(window.values())
        at = datetime.fromtimestamp(frontier.value_ns // 1_000_000_000, tz=UTC)
        self.seen.append((f"{at:%H:%M}", held[-1].bid.close, held[0].bid.close))
        if frontier.value_ns == self.rest_at_ns:
            return Ok((RestingIntent("entry-1", stream_id),))
        return Ok(())


def replay(rest_at_ns: int | None = None) -> tuple[Watcher, list[tuple[str, Roll]], Result[int]]:
    chain = FuturesChain.try_create(CARD)
    assert is_ok(chain), chain
    card = DataCard.try_create("bars", Decimal("0.25"))
    assert is_ok(card), card
    day = VenueDay.try_create("America/Chicago", "17:00")
    assert is_ok(day), day

    def builder() -> BarBuilder:
        built = BarBuilder.try_create(day.value.span, 60)
        assert is_ok(built), built
        return built.value

    def rows(level: str) -> Iterator[Bar]:
        yield from minutes(level)

    windows = {"ES": BarWindow(3)}
    watcher = Watcher(windows, rest_at_ns)
    rolls: list[tuple[str, Roll]] = []
    feed = futures_feed(
        chain.value,
        card.value,
        {"ESH5": lambda: rows("5000.00"), "ESM5": lambda: rows("5050.00")},
        builder,
        window=3,
    )
    steps = replay_windowed(
        cast("UnitSliceHandler", watcher),
        {"ES": feed},
        windows,
        on_roll=lambda market, roll: rolls.append((market, roll)),
    )
    return watcher, rolls, steps


def test_the_two_contract_fixture_shows_one_roll_and_each_contract_at_its_own_prices() -> None:
    watcher, rolls, steps = replay()

    assert is_ok(steps) and steps.value == 10
    assert [(market, roll.as_record()) for market, roll in rolls] == [
        (
            "ES",
            {
                "event_kind": "roll",
                "at_ns": ROLL_NS,
                "contract": "ESH5",
                "next_contract": "ESM5",
            },
        )
    ]
    assert [bar.bid.close for bar in rolls[0][1].warm] == [
        Decimal("5050.25"),
        Decimal("5050.50"),
        Decimal("5050.75"),
    ]
    assert watcher.seen == [
        ("23:56", Decimal("5000.00"), Decimal("5000.00")),
        ("23:57", Decimal("5000.25"), Decimal("5000.00")),
        ("23:58", Decimal("5000.50"), Decimal("5000.00")),
        ("23:59", Decimal("5000.75"), Decimal("5000.25")),
        ("00:00", Decimal("5051.00"), Decimal("5050.50")),
        ("00:01", Decimal("5051.25"), Decimal("5050.75")),
        ("00:02", Decimal("5051.50"), Decimal("5051.00")),
        ("00:03", Decimal("5051.75"), Decimal("5051.25")),
        ("00:04", Decimal("5052.00"), Decimal("5051.50")),
        ("00:05", Decimal("5052.25"), Decimal("5051.75")),
    ]


def test_a_back_adjusted_card_is_refused_by_name() -> None:
    adjusted = {**CARD, "stitching": {"method": "back-adjusted", "adjusted": True}}

    refused = FuturesChain.try_create(adjusted)

    assert is_refusal(refused)
    assert refused.context["reason"] == (
        "QMB replays futures contract by contract and never a back-adjusted price"
    )


def test_a_roll_reached_with_a_resting_order_refuses_the_run() -> None:
    _, rolls, steps = replay(rest_at_ns=ROLL_NS - 60_000_000_000)

    assert rolls == []
    assert isinstance(steps, TypedRefusal)
    assert {k: steps.context[k] for k in ("market", "contract", "next_contract", "at_ns")} == {
        "market": "ES",
        "contract": "ESH5",
        "next_contract": "ESM5",
        "at_ns": ROLL_NS,
    }


def test_a_live_feed_carries_the_roll_as_a_control_event_naming_both_contracts() -> None:
    now = 1_741_910_400_000_000_000
    lease = {
        "consumer_id": "consumer:a",
        "expires_at": now + 60_000_000_000,
        "lease_id": "lease:a",
        "renewed_at": now,
    }
    subscription = record_stream_subscription(
        {
            "backpressure_policy": "block",
            "buffer_bound": 10000,
            "channel": "ticks",
            "cursor": {"epoch": 1, "sequence": 10},
            "cursor_durable": True,
            "cutover_watermark": {"epoch": 1, "sequence": 10},
            "epoch": 1,
            "leases": [lease],
            "phase": "replay",
            "sequence_domain": "provider-channel",
            "shared": False,
            "source_id": "cme",
            "sub_id": "sub:ticks-es",
            "venue_id": "cme-broker",
        },
        as_of=now,
    )
    assert is_ok(subscription), subscription

    roll = emit_stream_control(
        subscription.value,
        event_kind="roll",
        detected_at=now,
        contract="ESH5",
        next_contract="ESM5",
    )
    gap = emit_stream_control(
        subscription.value, event_kind="gap", detected_at=now, contract="ESH5"
    )

    assert is_ok(roll)
    assert roll.value.as_record() == {
        "detected_at": now,
        "epoch": 1,
        "event_kind": "roll",
        "sub_id": "sub:ticks-es",
        "contract": "ESH5",
        "next_contract": "ESM5",
    }
    assert is_refusal(gap)
    assert gap.context["field"] == "contract"
