"""A unit reads two streams, and no bar it reads is knowable after the instant it reads it.

K9 17's unit seams for RC-31. One minute feed: a 1-minute, a 5-minute and a 15-minute unit
trade from it, each stepping on its own bar. A two-stream unit steps on its primary (the 1-minute
bar) and reads the 5-minute stream at its last closed bar, so at minute 7 it reads the bar that
closed at minute 5, and one minute later the same bar is still the one it reads.

The seam is the unit door: ``compile_unit`` then ``construct_unit`` over the host's own read
surfaces. At the parent a unit with two streams refuses at compile, which is the red these tests
start from.
"""
# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path

from qmf.core.chrono import Instant
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompiledUnit, compile_unit
from qml.feed import roll_up
from qml.protocol.unit import Account, HostedUnit, OHLC, QuoteBar, Surface, UnitStep, construct_unit
from test_compile_dummy import _At, _context, _drive, _entries, _ok, _target

MINUTE_NS = 60_000_000_000
START = 1_742_500_800_000_000_000
"""2025-03-20 19:46:40 UTC, a whole fifteen-minute bucket's start, as RC-30's roll-up test uses."""
BARS = 1_400
"""Fourteen and a half hours of one-minute bars: 280 five-minute bars and 93 fifteen-minute ones."""
SECONDS = {"m1": 60, "m5": 300, "m15": 900}
_WAVE = tuple(abs((index % 40) - 20) for index in range(40))
"""A forty-minute V: a trough every forty bars, so every stream finds a swing low."""
_STDLIB = Path(__file__).resolve().parents[1] / "src" / "qml" / "blocks" / "stdlib"


def _minute_feed(count: int = BARS) -> list[QuoteBar]:
    """One deterministic one-minute feed: the wave on the bid side, with a two-pip spread."""
    spread = Decimal("0.00002")
    bars: list[QuoteBar] = []
    for index in range(count):
        value = Decimal("1.10000") + Decimal(_WAVE[index % len(_WAVE)]) * Decimal("0.0001")
        low, high = value - spread, value + spread
        bid = OHLC(value, high, low, value)
        ask = OHLC(value + spread, high + spread, low + spread, value + spread)
        bars.append(QuoteBar(Instant(START + (index + 1) * MINUTE_NS), bid, ask))
    return bars


def _rolled(feed: Sequence[QuoteBar], seconds: int) -> list[QuoteBar]:
    """The feed rolled up to one stream, whole buckets only, through the repo's own function."""
    factor = seconds * 1_000_000_000 // MINUTE_NS
    out: list[QuoteBar] = []
    for start in range(0, len(feed) - factor + 1, factor):
        rolled = roll_up(feed[start : start + factor], seconds)
        if rolled is not None:
            out.append(rolled)
    return out


def _pins() -> list[dict[str, object]]:
    pins: list[dict[str, object]] = []
    for entry in sorted(_STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
    return pins


def _stream(name: str) -> dict[str, object]:
    return {
        "name": name,
        "market": "*",
        "bar": {"kind": "time", "size": str(SECONDS[name])},
        "input": "closed_bars",
        "price": "bid_ask",
    }


def _above(name: str, stream: str) -> dict[str, object]:
    return {
        "name": name,
        "block": "value-above@1",
        "params": {"level": {"value": "0"}, "below": {"value": "0"}},
        "inputs": {"series": f"{stream}.close"},
    }


def _document(*streams: str) -> dict[str, object]:
    """The smallest unit that trades: both slots hold, the entry is at the next open.

    ``streams`` is the document's stream list, primary first. The slots read the slowest stream,
    so a two-stream unit's first stream only drives the step and the exits.
    """
    slow = streams[-1]
    return {
        "schema": "qmx.unit/1",
        "unit_id": "+".join(streams),
        "family_id": "second-stream",
        "claim_card": {
            "idea": "hold whenever the slow stream is above zero",
            "sources": [{"source_ref": "qmx:test", "locator": "rc-31", "dated": "2026-11-09"}],
            "written_at": "2026-11-09T00:00:00Z",
        },
        "markets": [
            {
                "market_id": "fx.eurusd",
                "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "EURUSD"},
            }
        ],
        "streams": [_stream(name) for name in streams],
        "direction": "long",
        "logic": {
            "long": {
                "slots": {
                    "context": {
                        "role": "context",
                        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
                        "bindings": [_above("slow", slow)],
                    },
                    "trigger": {
                        "role": "trigger",
                        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
                        "bindings": [_above("hold", slow)],
                    },
                    "entry_order": {
                        "role": "entry_order",
                        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
                        "bindings": [
                            {
                                "name": "next_open",
                                "block": "market-next-open@1",
                                "params": {},
                                "inputs": {},
                            }
                        ],
                    },
                }
            }
        },
        "exit_set": [
            {
                "name": "swing_stop",
                "scope": "position",
                "block": "swing-stop-buffer@1",
                "params": {"buffer": {"value": "0.0002"}},
                "inputs": {"series": streams[0]},
            },
            {
                "name": "target_2r",
                "scope": "position",
                "block": "target-r-multiple@1",
                "params": {"multiple": {"value": "2"}},
                "inputs": {},
            },
            {
                "name": "time_out",
                "scope": "position",
                "block": "time-exit-bars@1",
                "params": {"bars": {"value": "100"}},
                "inputs": {},
            },
        ],
        "sizer": {
            "name": "fixed_fraction",
            "block": "fixed-fraction-at-stop@2",
            "params": {"fraction": {"value": "0.005"}},
            "inputs": {},
        },
        "halts": {"position": [], "unit": [], "account": []},
        "reads": [],
        "numbers": {},
        "pins": _pins(),
    }


def _compiled(*streams: str) -> CompiledUnit:
    compiled = compile_unit(_document(*streams), _context())
    assert isinstance(compiled, CompiledUnit), compiled
    return compiled


class _Latest:
    """A bar surface: the latest closed bar of one stream knowable at the instant."""

    def __init__(self, series: Sequence[QuoteBar]) -> None:
        self._series = series
        self._stamps = [bar.knowable_at.value_ns for bar in series]

    def at(self, instant: Instant, /) -> object:
        low, high = 0, len(self._stamps)
        while low < high:
            middle = (low + high) // 2
            if instant.value_ns < self._stamps[middle]:
                high = middle
            else:
                low = middle + 1
        return self._series[low - 1] if low else None


def _surfaces(series: Mapping[str, Sequence[QuoteBar]]) -> dict[str, Surface]:
    out: dict[str, Surface] = {
        "account": _At(lambda _i: Account(Decimal("10000.00"))),
        "own_journal": _At(lambda _i: ()),
        "own_position:fx.eurusd": _At(lambda _i: ()),
    }
    for name, bars in series.items():
        out[f"bars:{name}:fx.eurusd"] = _Latest(bars)
    return out


def _host(compiled: CompiledUnit, series: Mapping[str, Sequence[QuoteBar]]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces(series),
            scope_id="run-rc-31",
            execution_target=_target(),
        )
    )


def _instants(series: Sequence[QuoteBar]) -> list[Instant]:
    return [bar.knowable_at for bar in series]


def _step_at(steps: Sequence[UnitStep], instant: Instant) -> UnitStep:
    return next(step for step in steps if step.instant == instant)


def _trail(step: UnitStep, binding: str) -> str | None:
    return next(
        (
            output.output
            for row in step.decisions
            for output in row.slot_trail
            if output.binding == binding
        ),
        None,
    )


def _decisions(step: UnitStep) -> list[tuple[str, str, list[tuple[str, str, str | None]]]]:
    return [
        (row.outcome, row.reason, [(out.slot, out.binding, out.output) for out in row.slot_trail])
        for row in step.decisions
    ]


def test_k9_17_one_feed() -> None:
    feed = _minute_feed()
    counts: dict[str, int] = {}
    for stream in ("m1", "m5", "m15"):
        series = _rolled(feed, SECONDS[stream])
        compiled = _compiled(stream)
        unit = _host(compiled, {stream: series})
        steps = _drive(unit, _instants(series))
        counts[stream] = len(steps)
        assert compiled.plan.streams == (stream,)
        assert _entries(steps), f"the {stream} unit trades from the one-minute feed"
    assert counts == {"m1": BARS, "m5": 280, "m15": 93}, "each unit steps on its own bar size"

    one = _rolled(feed, 60)
    five = _rolled(feed, 300)
    both = _compiled("m1", "m5")
    steps = _drive(_host(both, {"m1": one, "m5": five}), _instants(one)[:100])

    assert both.plan.streams == ("m1", "m5"), "the fastest stream is the primary"
    assert both.plan.stream == "m1", "the single-stream name still answers the primary"
    at_seven = _step_at(steps, Instant(START + 7 * MINUTE_NS))
    assert _trail(at_seven, "slow") == str(feed[4].bid.close), (
        "at minute 7 the unit reads the five-minute bar whose close is minute 5's"
    )
    closed_at_five = next(bar for bar in five if bar.knowable_at == Instant(START + 5 * MINUTE_NS))
    assert str(closed_at_five.bid.close) == str(feed[4].bid.close)
    assert _entries(steps), "the two-stream unit trades, on its 1-minute step and its 5-minute read"


def test_a_slower_bar_is_never_seen_early() -> None:
    feed = _minute_feed()
    five = _rolled(feed, 300)
    compiled = _compiled("m1", "m5")
    steps = _drive(_host(compiled, {"m1": feed, "m5": five}), _instants(feed)[:9])

    at_nine = _step_at(steps, Instant(START + 9 * MINUTE_NS))
    visible = next(bar for bar in five if bar.knowable_at.value_ns <= at_nine.instant.value_ns)
    assert visible.knowable_at == Instant(START + 5 * MINUTE_NS), (
        "at minute 9 the five-minute bar the unit can see closed at minute 5"
    )

    expected = [None] * 4 + [str(feed[4].bid.close)] * 5
    assert [_trail(step, "slow") for step in steps] == expected, (
        "no step reads a five-minute close before its bucket closed"
    )

    eight = _step_at(steps, Instant(START + 8 * MINUTE_NS))
    assert _decisions(eight) == _decisions(at_nine), (
        "moving the evidence one minute forward changes no decision"
    )
