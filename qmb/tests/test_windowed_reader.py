"""A run's memory stays flat in its length (B7, QB-01, CC-07).

A run keeps each market's derived warm-up plus its declared lookback, never the history
behind it, and nothing caps its steps. Peak memory is traced at 10,000 and at 200,000 steps, over
the read from the rows streaming in to the bars landing in the window, and over a real run.
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Iterator, MutableMapping
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmb.host.behaviour import check_behaviour
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
from qmb.host.unit_runner import load_unit_folder, run_loaded
from qmb.runloop.bars import BarBuilder
from qmf.core.refusal import TypedRefusal
from qml.protocol.unit import OHLC, QuoteBar
from test_unit_runner import dummy_document, make_run_folder, request

_START_MS = 1_577_836_800_000
"""2020-01-01T00:00Z."""
_LONG_RUN = 200_000


def _minutes(count: int) -> Iterator[Bar]:
    """``count`` one-minute bid bars of a deterministic zig-zag, built as they are read."""
    for step in range(count):
        level = Decimal(108_000 + (step * 7) % 61 - 30).scaleb(-5)
        tick = Decimal("0.00001")
        yield Bar(_START_MS + step * 60_000, 60, OHLC(level, level + tick, level - tick, level))


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


def _one_side_on_one_market() -> dict[str, object]:
    """The dummy trading one side of one market, the cheapest real run to repeat 200,000 times."""
    document = dummy_document()
    logic = cast("dict[str, object]", document["logic"])
    del logic["short"]
    del cast("dict[str, object]", document["numbers"])["rsi_high"]
    document["direction"] = "long"
    document["markets"] = cast("list[object]", document["markets"])[:1]
    return document


def _peak_of_a_real_run(root: Path, steps: int) -> tuple[int, int]:
    """Bars of ``steps`` closes that zig-zag without a trade, because a run keeps every trade it
    makes by design. Answers the trades made and the peak bytes traced over ``run_loaded``."""
    root.mkdir()
    folder = make_run_folder(root, _one_side_on_one_market())
    for side, spread in (("bid", 0), ("ask", 2)):
        with (folder / "bars" / "fx.eurusd" / f"{side}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as bars:
            bars.write("timestamp,open,high,low,close,volume\n")
            for step in range(steps):
                level = 108_000 + abs(step % 192 - 96) * 10 + spread
                text = f"{level // 100_000}.{level % 100_000:05d}"
                bars.write(f"{_START_MS + step * 900_000},{text},{text},{text},{text},0\n")
    loaded = load_unit_folder(folder)
    assert not isinstance(loaded, TypedRefusal), loaded
    asked = request(folder)
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    ran = run_loaded(loaded.value, asked)
    peak = tracemalloc.get_traced_memory()[1] - base
    tracemalloc.stop()
    assert not isinstance(ran, TypedRefusal), ran
    return len(ran.value.trades), peak


def test_a_real_backtest_of_200000_steps_stays_flat(tmp_path: Path) -> None:
    small_trades, small_peak = _peak_of_a_real_run(tmp_path / "small", 10_000)
    large_trades, large_peak = _peak_of_a_real_run(tmp_path / "large", _LONG_RUN)

    assert (small_trades, large_trades) == (0, 0)
    assert large_peak <= small_peak * (1 + WINDOW_MEMORY_TOLERANCE)


def test_the_behaviour_check_reads_no_more_than_its_slice(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)

    whole = check_behaviour(folder, request(folder), loaded_in_isolation=False)
    cut = check_behaviour(folder, request(folder), slice_bars=1200, loaded_in_isolation=False)
    floor = check_behaviour(folder, request(folder), slice_bars=1, loaded_in_isolation=False)

    assert not isinstance(whole, TypedRefusal), whole
    assert not isinstance(cut, TypedRefusal), cut
    assert not isinstance(floor, TypedRefusal), floor
    ends = [cast("dict[str, object]", c.value.report["slice"])["to"] for c in (whole, cut, floor)]
    assert ends == [1743199200000000000, 1742378400000000000, 1742293800000000000]


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
