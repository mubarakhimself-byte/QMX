"""The dummy replays quotes, trades and bars as each data card declares (B7, QB-02, QB-21).

The data is QML's synthetic EURUSD and XAUUSD month (``qml/tests/fixtures/slices``), whose
ask is the bid plus a fixed spread. So the same month written as bid and ask bars (quotes),
as prints with their aggressor side (trades), and as bid bars with the declared spread (bars)
must trade the one golden list below, which is also the list the shipped runner trades over
the same files.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from decimal import Decimal
from pathlib import Path

from qmb.host.replay import (
    Aggressor,
    Bar,
    BarWindow,
    DataCard,
    Fidelity,
    Print,
    Row,
    Tick,
    read_bar_csv,
    read_bar_pair_csv,
    replay_feed,
    replay_windowed,
    window_size,
)
from qmb.host.unit_handler import ListJournal, NextOpenExecution, UnitSliceHandler
from qmb.host.unit_runner import load_unit_folder
from qmb.runloop.bars import BarBuilder, VenueDay
from qmf.core.refusal import TypedRefusal
from qml.protocol.unit import QuoteBar, construct_unit
from test_unit_runner import make_run_folder, request

_UNTIL_NS = 1_743_465_600_000_000_000
"""2025-04-01T00:00Z, where the month's files end."""
_SPREADS = {"fx.eurusd": Decimal("0.00002"), "metal.xauusd": Decimal("0.250")}

_GOLDEN = [
    ("fx.eurusd", "short", 1742508900, 1742510700, "1.06858", "1.06887", "-49.88"),
    ("fx.eurusd", "short", 1742513400, 1742526900, "1.06866", "1.06912", "-49.68"),
    ("fx.eurusd", "short", 1742532300, 1742575500, "1.06884", "1.06856", "21.00"),
    ("fx.eurusd", "short", 1742769900, 1742813100, "1.06840", "1.06823", "15.47"),
    ("fx.eurusd", "short", 1742834700, 1742838300, "1.06794", "1.06825", "-49.60"),
    ("fx.eurusd", "short", 1742843700, 1742850900, "1.06796", "1.06889", "-49.29"),
    ("metal.xauusd", "long", 1742966100, 1742983200, "3245.944", "3240.57", "-48.37"),
    ("metal.xauusd", "long", 1743092100, 1743120000, "3234.202", "3242.15", "95.38"),
]
"""Market, side, opened and closed (UTC seconds), entry, exit and money of every trade."""


def _as_prints(rows: Iterable[Bar | TypedRefusal], spread: Decimal) -> Iterator[Row]:
    """Each bid bar as four prints inside its 15 minutes: sells at the bid, buys at the ask."""
    for row in rows:
        assert not isinstance(row, TypedRefusal), row
        bar = row.price
        yield Print(row.open_ms, bar.open, Aggressor.SELL)
        yield Print(row.open_ms + 60_000, bar.high + spread, Aggressor.BUY)
        yield Print(row.open_ms + 120_000, bar.low, Aggressor.SELL)
        yield Print(row.open_ms + 840_000, bar.close + spread, Aggressor.BUY)


def _rows(fidelity: Fidelity, files: Path, spread: Decimal) -> Iterable[Row | TypedRefusal]:
    match fidelity:
        case Fidelity.QUOTES:
            return read_bar_pair_csv(files / "bid.csv", files / "ask.csv")
        case Fidelity.TRADES:
            return _as_prints(read_bar_csv(files / "bid.csv"), spread)
        case Fidelity.BARS:
            return read_bar_csv(files / "bid.csv")


def _trade_list(tmp_path: Path, fidelity: Fidelity) -> list[tuple[object, ...]]:
    folder = make_run_folder(tmp_path)
    loaded = load_unit_folder(folder)
    assert not isinstance(loaded, TypedRefusal), loaded
    compiled = loaded.value.compiled
    asked = request(folder)
    size = window_size(compiled)
    windows = {market: BarWindow(size) for market in loaded.value.records}
    feeds: dict[str, Iterator[QuoteBar | TypedRefusal]] = {}
    for market, record in loaded.value.records.items():
        day = VenueDay.try_create(record.zone, record.day_boundary)
        assert not isinstance(day, TypedRefusal), day
        builder = BarBuilder.try_create(day.value, 900)
        assert not isinstance(builder, TypedRefusal), builder
        files = folder / "bars" / market
        spread = None if fidelity is Fidelity.QUOTES else _SPREADS[market]
        card = DataCard.try_create(fidelity.value, spread)
        assert not isinstance(card, TypedRefusal), card
        rows = _rows(fidelity, files, _SPREADS[market])
        feeds[market] = replay_feed(card.value, rows, builder.value, until_ns=_UNTIL_NS)
    handler = UnitSliceHandler.start(
        lambda surfaces: construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id=asked.run_id,
            execution_target=asked.execution_target,
            motion=asked.motion,
        ),
        stream=compiled.plan.stream,
        records=loaded.value.records,
        bars=windows,
        opened_by=compiled.compiled_fingerprint,
        equity=asked.equity,
        execution=NextOpenExecution(),
        journal=ListJournal(),
    )
    assert not isinstance(handler, TypedRefusal), handler
    steps = replay_windowed(handler.value, feeds, windows)
    assert not isinstance(steps, TypedRefusal), steps
    assert steps.value == 1920
    return [
        (
            t.market_id,
            t.side.value,
            t.opened_at.value_ns // 1_000_000_000,
            t.closed_at.value_ns // 1_000_000_000,
            str(t.entry_price),
            str(t.exit_price),
            str(t.money),
        )
        for t in handler.value.trades
    ]


def test_quotes_replay_the_bid_and_ask_bars_into_the_golden_trades(tmp_path: Path) -> None:
    assert _trade_list(tmp_path, Fidelity.QUOTES) == _GOLDEN


def test_trades_replay_prints_with_the_declared_spread_into_the_golden_trades(
    tmp_path: Path,
) -> None:
    assert _trade_list(tmp_path, Fidelity.TRADES) == _GOLDEN


def test_bars_replay_one_side_with_the_declared_spread_into_the_golden_trades(
    tmp_path: Path,
) -> None:
    assert _trade_list(tmp_path, Fidelity.BARS) == _GOLDEN


def _daily_closes(zone: str, boundary: str, ticks: Iterable[Tick]) -> list[int]:
    day = VenueDay.try_create(zone, boundary)
    assert not isinstance(day, TypedRefusal), day
    builder = BarBuilder.try_create(day.value, 86_400)
    assert not isinstance(builder, TypedRefusal), builder
    card = DataCard.try_create("quotes")
    assert not isinstance(card, TypedRefusal), card
    closes: list[int] = []
    for bar in replay_feed(card.value, ticks, builder.value, until_ns=_WEEK_END_NS):
        assert not isinstance(bar, TypedRefusal), bar
        closes.append(bar.knowable_at.value_ns // 1_000_000_000)
    return closes


_WEEK_START_MS = 1_741_219_200_000
"""2025-03-06T00:00Z, a Thursday; New York moves to daylight time on Sunday 9 March."""
_WEEK_END_NS = 1_741_737_600_000_000_000
"""2025-03-12T00:00Z."""


def _fx_week_ticks() -> Iterator[Tick]:
    """A tick every 15 minutes while FX trades: shut from Friday 17:00 to Sunday 17:00 NY."""
    friday_close, sunday_open = 1_741_384_800_000, 1_741_554_000_000
    ms = _WEEK_START_MS
    while ms < _WEEK_END_NS // 1_000_000:
        if not friday_close <= ms < sunday_open:
            yield Tick(ms, Decimal("1.08000"), Decimal("1.08002"))
        ms += 900_000


def test_a_week_of_ticks_closes_its_daily_bars_at_the_venues_day_boundary() -> None:
    closes = _daily_closes("America/New_York", "17:00", _fx_week_ticks())

    assert closes == [
        1741298400,  # Thu 6 Mar 22:00Z, 17:00 New York standard time
        1741384800,  # Fri 7 Mar 22:00Z
        1741640400,  # Mon 10 Mar 21:00Z, 17:00 New York daylight time
        1741726800,  # Tue 11 Mar 21:00Z
    ]
    assert _daily_closes("UTC", "00:00", _fx_week_ticks()) == [
        1741305600,
        1741392000,
        1741564800,
        1741651200,
        1741737600,
    ]
