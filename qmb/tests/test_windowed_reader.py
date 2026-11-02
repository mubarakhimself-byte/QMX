"""The windowed reader's memory stays flat in run length (B7, QB-01, CC-07).

A run keeps each market's derived warm-up plus its declared lookback, never the history
behind it, and nothing caps its steps. Peak memory is traced over the whole read, from the
rows streaming in to the bars landing in the window, at 10,000 and at 200,000 one-minute steps.
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Iterator, MutableMapping
from decimal import Decimal
from pathlib import Path

from qmb.host.replay import (
    WINDOW_MEMORY_TOLERANCE,
    Bar,
    BarWindow,
    DataCard,
    Tick,
    VenueDay,
    replay_feed,
    window_size,
)
from qmb.host.unit_runner import load_unit_folder
from qmb.runloop.bars import BarBuilder
from qmf.core.refusal import TypedRefusal
from qml.protocol.unit import OHLC, QuoteBar
from test_unit_runner import make_run_folder

_START_MS = 1_577_836_800_000
"""2020-01-01T00:00Z."""


def _minutes(count: int) -> Iterator[Bar]:
    """``count`` one-minute bid bars of a deterministic zig-zag, built as they are read."""
    for step in range(count):
        level = Decimal(108_000 + (step * 7) % 61 - 30).scaleb(-5)
        tick = Decimal("0.00001")
        yield Bar(_START_MS + step * 60_000, OHLC(level, level + tick, level - tick, level))


def _read(steps: int, window: MutableMapping[int, QuoteBar] | BarWindow) -> tuple[int, int]:
    """Steps read and the peak bytes traced while reading them into ``window``."""
    day = VenueDay.try_create("America/New_York", "17:00")
    assert not isinstance(day, TypedRefusal), day
    builder = BarBuilder.try_create(day.value.span, 60)
    assert not isinstance(builder, TypedRefusal), builder
    card = DataCard.try_create("bars", Decimal("0.00002"))
    assert not isinstance(card, TypedRefusal), card
    until_ns = (_START_MS + steps * 60_000) * 1_000_000
    tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    read = 0
    for bar in replay_feed(card.value, _minutes(steps), builder.value, until_ns=until_ns):
        assert not isinstance(bar, TypedRefusal), bar
        if isinstance(window, BarWindow):
            window.push(bar)
        else:
            window[bar.knowable_at.value_ns] = bar
        read += 1
    peak = tracemalloc.get_traced_memory()[1] - base
    tracemalloc.stop()
    return read, peak


def test_the_dummys_window_is_its_derived_warm_up(tmp_path: Path) -> None:
    loaded = load_unit_folder(make_run_folder(tmp_path))
    assert not isinstance(loaded, TypedRefusal), loaded

    assert window_size(loaded.value.compiled) == 921
    assert window_size(loaded.value.compiled, lookback=79) == 1000


def test_peak_memory_at_200000_steps_stays_within_the_tolerance_of_10000() -> None:
    small_window, large_window = BarWindow(921), BarWindow(921)

    small_steps, small_peak = _read(10_000, small_window)
    large_steps, large_peak = _read(200_000, large_window)

    assert (small_steps, large_steps) == (10_000, 200_000)
    assert (len(small_window), len(large_window)) == (921, 921)
    assert list(large_window)[-1] == 1_589_836_800_000_000_000  # 2020-05-18T21:20Z
    assert large_peak <= small_peak * (1 + WINDOW_MEMORY_TOLERANCE)


def test_the_probe_sees_a_reader_that_keeps_every_bar_grow_past_the_tolerance() -> None:
    _, kept_10000 = _read(10_000, {})
    _, kept_20000 = _read(20_000, {})

    assert kept_20000 > kept_10000 * (1 + WINDOW_MEMORY_TOLERANCE)


def test_a_card_refuses_a_row_of_another_kind_and_the_feed_stops_there() -> None:
    day = VenueDay.try_create("America/New_York", "17:00")
    assert not isinstance(day, TypedRefusal), day
    builder = BarBuilder.try_create(day.value.span, 60)
    assert not isinstance(builder, TypedRefusal), builder
    card = DataCard.try_create("bars", Decimal("0.00002"))
    assert not isinstance(card, TypedRefusal), card
    rows = [*_minutes(2), Tick(_START_MS + 180_000, Decimal("1.08"), Decimal("1.08002"))]

    fed = list(replay_feed(card.value, rows, builder.value, until_ns=0))

    assert [type(item).__name__ for item in fed] == ["QuoteBar", "TypedRefusal"]
    refusal = fed[-1]
    assert isinstance(refusal, TypedRefusal)
    assert refusal.context == {
        "field": "rows",
        "reason": "a row is the kind of data its card declares",
        "fidelity": "bars",
        "row": "Tick",
    }
    unspread = DataCard.try_create("bars")
    assert isinstance(unspread, TypedRefusal)
    assert unspread.context["field"] == "spread"
