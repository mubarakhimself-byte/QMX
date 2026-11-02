"""Fills, sizes, costs, carry, margin and holes behave like a real market (B10).

A stand-in unit answers scripted entries and exits, and the shared unit handler trades them over
hand-written bars through ``replay_windowed`` with QMB's own ports (``BarExecution`` and
``ReplayCash``), each built from an instrument record the way the unit runner builds them. The
hole test runs the QMB app's backtest job over a run folder with a three-day hole. The bars are
made up to the tick, not evidence.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

import pyarrow.parquet as pq
import pytest
from qmb.data.generate import build_generation_grid, resolve_generator_config
from qmb.execution.cost import CostProfile
from qmb.execution.fill import BarExecution, FillKind
from qmb.execution.financing import (
    CashKind,
    ReplayCash,
    carry_schedule,
    read_funding_rates,
)
from qmb.execution.risk import MarginRule, margin_rule
from qmb.host.replay import BarWindow, VenueDay, replay_windowed
from qmb.host.unit_handler import JournalPort, ListJournal, UnitSliceHandler
from qmb.host.unit_runner import LoadedUnit, load_unit_folder
from qmb.results.journal import RunJournal
from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal
from qmf.risk.unit_intent import UnitIntent
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import OHLC, QuoteBar, UnitStep, accept_unit_intents
from test_run_journal import _backtest_job, _text
from test_unit_runner import make_run_folder

_REPO = Path(__file__).resolve().parents[2]
_RECORDS = _REPO / "qml" / "tests" / "fixtures" / "records"
_APP = _REPO / "qmx-agents" / "apps" / "qmb"
_MINE = Fingerprint("fp1:sha256:" + "a" * 64)
_OWN = "aaaaaaaaaaaa-1"
_M15 = 900_000_000_000
_FX, _GOLD, _PERP = "fx.eurusd", "metal.xauusd", "perp.btc"


def _ns(text: str) -> int:
    """A UTC wall time as epoch ns."""
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp()) * 1_000_000_000


def _bar(opened: str, bid: tuple[str, str, str, str], spread: str) -> QuoteBar:
    """An M15 bar opening at ``opened``, stamped at its close, its ask the bid plus ``spread``."""
    sides = [Decimal(v) for v in bid]
    ask = [v + Decimal(spread) for v in sides]
    return QuoteBar(Instant(_ns(opened) + _M15), OHLC(*sides), OHLC(*ask))


def _flat(start: str, end: str, bid: str, spread: str) -> list[QuoteBar]:
    """Unchanging bars every 15 minutes from ``start`` up to ``end``."""
    at, stop, bars = datetime.fromisoformat(start), datetime.fromisoformat(end), []
    while at < stop:
        bars.append(_bar(at.isoformat(), (bid, bid, bid, bid), spread))
        at += timedelta(minutes=15)
    return bars


def _close_of(opened: str) -> int:
    return _ns(opened) + _M15


def _entry(market: str, symbol: str, quantity: str, stop: str, row: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "entry",
        "unit": {"unit_id": "u", "version_ref": _MINE.value, "compiled_fingerprint": _MINE.value},
        "instrument": {"venue": "icmarkets-ctrader", "symbol": symbol},
        "market_id": market,
        "direction": "long",
        "reason_code": {"code": "test", "book_family": "unit"},
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
        "order": {"type": "market"},
        "quantity": quantity,
        "sizer_receipt": {"inputs_used": ["equity"], "rounding_residue_r": "0/1"},
        "protection": {"stop": stop, "targets": []},
        "not_before": 0,
        "placeholder_labels": [],
        "decision_row_id": row,
    }


def _exit(symbol: str) -> dict[str, object]:
    return {
        "contract_format_version": 3,
        "intent_family": "exit",
        "kind": "close_full",
        "position_ref": {
            "position_id": _OWN,
            "instrument": {"venue": "icmarkets-ctrader", "symbol": symbol},
            "opened_by": _MINE.value,
        },
        "reason_code": {"code": "time-exit", "book_family": "unit"},
        "decision_row_id": "row-exit",
    }


class _Scripted:
    """A unit that answers each scripted instant with its intents."""

    def __init__(self, script: Mapping[int, Sequence[Mapping[str, object]]]) -> None:
        self._steps: dict[int, tuple[UnitIntent, ...]] = {}
        for at, wires in script.items():
            intents = accept_unit_intents(wires)
            assert not isinstance(intents, TypedRefusal), intents
            self._steps[at] = intents.value

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        return Ok(UnitStep(instant, self._steps.get(instant.value_ns, ()), (), (), ()))


def _fixture_record(name: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads((_RECORDS / name).read_text("utf-8")))


_PERP_TERMS: dict[str, object] = {
    "venue": "hyperliquid",
    "symbol": "BTC/USDC:USDC",
    "market_id": "btc",
    "class": "perp",
    "currency": "USDC",
    "digits": 2,
    "tick_size": "0.01",
    "contract_size": "1",
    "value_per_point": "1",
    "lot_step": "0.001",
    "min_lot": "0.001",
    "calendar_ref": "crypto-24x7@1",
    "zone": "UTC",
    "day_boundary": "00:00",
    "data_levels": {"levels": [0, 1, 5]},
    "leverage": {"version": 1, "tiers": [{"leverage": "10"}]},
    "margin": {"intraday": "0.1", "overnight": "0.1"},
    "funding_interval": "PT8H",
    "record_version": 1,
    "status": "specified",
}


def _drive(
    terms: Mapping[str, Mapping[str, object]],
    bars: Mapping[str, Sequence[QuoteBar]],
    script: Mapping[int, Sequence[Mapping[str, object]]],
    *,
    journal: JournalPort | None = None,
    rates: Mapping[str, Sequence[str]] | None = None,
) -> UnitSliceHandler:
    """Trade ``script`` over ``bars`` with the ports the unit runner builds from each record."""
    records: dict[str, InstrumentRecord] = {}
    margins: dict[str, MarginRule] = {}
    carry = {}
    for market, raw in terms.items():
        record = parse_record(dict(raw))
        assert not isinstance(record, TypedRefusal), record
        records[market] = record.value
        day = VenueDay.try_create(record.value.zone, record.value.day_boundary)
        assert not isinstance(day, TypedRefusal), day
        recorded = None
        if rates is not None and market in rates:
            read = read_funding_rates(rates[market])
            assert not isinstance(read, TypedRefusal), read
            recorded = read.value
        schedule = carry_schedule(
            market,
            raw,
            value_per_point=record.value.value_per_point,
            day=day.value,
            bar_ns=_M15,
            rates=recorded,
        )
        assert not isinstance(schedule, TypedRefusal), schedule
        carry[market] = schedule.value
        rule = margin_rule(record.value, raw.get("liquidation_rule"))
        assert not isinstance(rule, TypedRefusal), rule
        if rule.value is not None:
            margins[market] = rule.value
    windows = {market: BarWindow(64) for market in bars}
    costs: dict[str, CostProfile] = {}
    started = UnitSliceHandler.start(
        lambda _surfaces: Ok(_Scripted(script)),
        stream="m15",
        records=records,
        bars=windows,
        opened_by=_MINE,
        equity=Decimal("10000.00"),
        execution=BarExecution(_M15, costs, margins),
        journal=journal or ListJournal(),
        cash=ReplayCash(carry, costs, _M15),
    )
    assert not isinstance(started, TypedRefusal), started
    driven = replay_windowed(started.value, {m: iter(b) for m, b in bars.items()}, windows)
    assert not isinstance(driven, TypedRefusal), driven
    return started.value


def _trade(handler: UnitSliceHandler) -> tuple[object, ...]:
    (trade,) = handler.trades
    return (trade.exit_kind, trade.exit_price, trade.money, trade.r, trade.gap_through_stop)


def _cash(handler: UnitSliceHandler) -> list[tuple[CashKind, int, Decimal, str]]:
    return [(c.kind, c.instant.value_ns, c.money, c.detail) for c in handler.cash_events]


@pytest.fixture(scope="module")
def loaded(tmp_path_factory: pytest.TempPathFactory) -> LoadedUnit:
    found = load_unit_folder(make_run_folder(tmp_path_factory.mktemp("b10")))
    assert not isinstance(found, TypedRefusal), found
    return found.value


def _journal(loaded: LoadedUnit, out: Path) -> RunJournal:
    opened = RunJournal.open(out, loaded.compiled, run_id="run-b10", machine="pc", build="test")
    assert not isinstance(opened, TypedRefusal), opened
    return opened.value


def _rows(journal: RunJournal) -> dict[str, list[dict[str, object]]]:
    """Every row body the closed journal wrote, by kind."""
    closed = journal.close()
    assert not isinstance(closed, TypedRefusal), closed
    rows: dict[str, list[dict[str, object]]] = {}
    for part in closed.value.parts:
        rows.setdefault(part.kind, []).extend(
            json.loads(r["record"])["body"] for r in pq.read_table(part.path).to_pylist()
        )
    return rows


def test_a_weekend_gap_through_the_stop_fills_at_the_gap_and_records_minus_1_7_r(
    loaded: LoadedUnit, tmp_path: Path
) -> None:
    friday = [
        _bar("2025-01-10T21:15", ("1.08500",) * 4, "0.00010"),
        _bar("2025-01-10T21:30", ("1.08500", "1.08520", "1.08490", "1.08500"), "0.00010"),
        _bar("2025-01-10T21:45", ("1.08500", "1.08510", "1.08490", "1.08500"), "0.00010"),
    ]
    sunday = _bar("2025-01-12T22:00", ("1.07643", "1.07700", "1.07600", "1.07650"), "0.00010")
    journal = _journal(loaded, tmp_path)
    handler = _drive(
        {_FX: _fixture_record("eurusd.json")},
        {_FX: [*friday, sunday]},
        {_close_of("2025-01-10T21:15"): [_entry(_FX, "EURUSD", "0.10", "1.08000", "row-1")]},
        journal=journal,
    )

    assert _trade(handler) == (
        FillKind.STOP,
        Decimal("1.07643"),
        Decimal("-86.70"),
        Decimal("-1.7000"),
        True,
    )
    (row,) = _rows(journal)["trade"]
    assert (row["r"], row["exit_price"], row["gap_through_stop"]) == ("-1.7000", "1.07643", True)


def test_a_stop_the_bar_reaches_inside_it_still_fills_at_the_stop_for_minus_1_r() -> None:
    bars = [
        _bar("2025-01-07T10:00", ("1.08500",) * 4, "0.00010"),
        _bar("2025-01-07T10:15", ("1.08500",) * 4, "0.00010"),
        _bar("2025-01-07T10:30", ("1.08400", "1.08450", "1.07900", "1.07950"), "0.00010"),
    ]

    handler = _drive(
        {_FX: _fixture_record("eurusd.json")},
        {_FX: bars},
        {_close_of("2025-01-07T10:00"): [_entry(_FX, "EURUSD", "0.10", "1.08000", "row-1")]},
    )

    assert _trade(handler) == (
        FillKind.STOP,
        Decimal("1.08000"),
        Decimal("-51.00"),
        Decimal("-1.0000"),
        False,
    )


def test_0_037_lots_trades_0_03_with_the_residue_journaled_and_0_004_skips(
    loaded: LoadedUnit, tmp_path: Path
) -> None:
    journal = _journal(loaded, tmp_path)
    handler = _drive(
        {_FX: _fixture_record("eurusd.json"), _GOLD: _fixture_record("xauusd.json")},
        {
            _FX: _flat("2025-01-07T10:00", "2025-01-07T10:45", "1.08500", "0.00010"),
            _GOLD: _flat("2025-01-07T10:00", "2025-01-07T10:45", "2650.00", "0.30"),
        },
        {
            _close_of("2025-01-07T10:00"): [
                _entry(_FX, "EURUSD", "0.037", "1.08000", "row-fx"),
                _entry(_GOLD, "XAUUSD", "0.004", "2600.00", "row-gold"),
            ]
        },
        journal=journal,
    )
    rows = _rows(journal)

    assert [(f.market_id, f.quantity, f.residue_r) for f in handler.fills] == [
        (_FX, Decimal("0.03"), Decimal("0.1892"))
    ]
    assert [(f["quantity"], f["receipt_quantity"], f["residue_r"]) for f in rows["fill"]] == [
        ("0.03", "0.037", "0.1892")
    ]
    assert [(g["decision_row_id"], g["reason"], g["residue_r"]) for g in rows["guard"]] == [
        ("row-gold", "below_min_lot", "1")
    ]


def test_a_wednesday_rollover_carries_three_nights_of_swap() -> None:
    eurusd = _fixture_record("eurusd.json") | {
        "swap": {"long": "-6.5", "short": "1.2", "triple_day": "wednesday"}
    }

    handler = _drive(
        {_FX: eurusd},
        {_FX: _flat("2025-01-07T09:30", "2025-01-09T10:30", "1.08500", "0.00010")},
        {
            _close_of("2025-01-07T09:30"): [_entry(_FX, "EURUSD", "0.10", "1.00000", "row-1")],
            _close_of("2025-01-09T09:30"): [_exit("EURUSD")],
        },
    )

    assert _cash(handler) == [
        (CashKind.SWAP, _ns("2025-01-07T22:00"), Decimal("-0.65"), "1 night at -6.5"),
        (CashKind.SWAP, _ns("2025-01-08T22:00"), Decimal("-1.95"), "3 nights at -6.5"),
    ]
    assert handler.trades[0].money == Decimal("-1.00")


def test_a_perp_held_24_hours_pays_three_fundings_at_the_venues_times() -> None:
    rates = [
        "timestamp,rate",
        *(
            f"{_ns(at) // 1_000_000},{rate}"
            for at, rate in (
                ("2025-01-07T00:00", "0.0003"),
                ("2025-01-07T08:00", "0.0001"),
                ("2025-01-07T16:00", "0.0002"),
                ("2025-01-08T00:00", "-0.0001"),
                ("2025-01-08T08:00", "0.0003"),
            )
        ),
    ]

    handler = _drive(
        {_PERP: _PERP_TERMS},
        {_PERP: _flat("2025-01-07T00:00", "2025-01-08T01:00", "100.00", "0.02")},
        {
            _close_of("2025-01-07T00:00"): [_entry(_PERP, "BTC", "2", "90.00", "row-1")],
            _close_of("2025-01-08T00:00"): [_exit("BTC")],
        },
        rates={_PERP: rates},
    )

    assert [(kind, at, money) for kind, at, money, _ in _cash(handler)] == [
        (CashKind.FUNDING, _ns("2025-01-07T08:00"), Decimal("-0.02")),
        (CashKind.FUNDING, _ns("2025-01-07T16:00"), Decimal("-0.04")),
        (CashKind.FUNDING, _ns("2025-01-08T00:00"), Decimal("0.02")),
    ]


def test_index_financing_and_a_dividend_land_as_cash_on_the_venue_day() -> None:
    us500 = {
        **_fixture_record("eurusd.json"),
        "symbol": "US500",
        "market_id": "sp500",
        "class": "index_cfd",
        "digits": 2,
        "tick_size": "0.01",
        "contract_size": "1",
        "value_per_point": "1",
        "pip": {"size": "1", "source": "test"},
        "financing": {"long": "-0.0730", "short": "0.0365", "days_per_year": "365"},
        "events": [{"kind": "dividend", "at": "2025-01-09", "amount_per_lot": "1.42"}],
    }

    handler = _drive(
        {"index.sp500": us500},
        {"index.sp500": _flat("2025-01-08T12:00", "2025-01-09T12:00", "5000.00", "0.50")},
        {
            _close_of("2025-01-08T12:00"): [_entry("index.sp500", "US500", "2", "4900.00", "r")],
            _close_of("2025-01-09T11:30"): [_exit("US500")],
        },
    )

    assert _cash(handler) == [
        (CashKind.FINANCING, _ns("2025-01-08T22:00"), Decimal("-2.00"), "1 night at -0.0730"),
        (CashKind.DIVIDEND, _ns("2025-01-08T22:00"), Decimal("2.84"), "1.42 per lot"),
    ]


def test_a_perp_past_its_maintenance_margin_is_liquidated_at_the_records_level() -> None:
    perp = _PERP_TERMS | {"liquidation_rule": "maintenance:0.05"}
    bars = [
        _bar("2025-01-07T10:00", ("100.00",) * 4, "0.02"),
        _bar("2025-01-07T10:15", ("100.00",) * 4, "0.02"),
        _bar("2025-01-07T10:30", ("99.00", "99.10", "94.00", "94.50"), "0.02"),
    ]

    handler = _drive(
        {_PERP: perp},
        {_PERP: bars},
        {_close_of("2025-01-07T10:00"): [_entry(_PERP, "BTC", "1", "90.00", "row-1")]},
        rates={_PERP: ["timestamp,rate"]},
    )

    assert _trade(handler) == (
        FillKind.LIQUIDATION,
        Decimal("94.76"),
        Decimal("-5.26"),
        Decimal("-0.5250"),
        False,
    )


def _write_247(folder: Path, hole: tuple[str, str]) -> None:
    """Both markets' bars every 15 minutes through March 2025, 24/7, EURUSD missing ``hole``."""
    skip = (_ns(hole[0]), _ns(hole[1]))
    # market: start price in points, decimals, one bar's move in points, spread in points
    for market, (start, decimals, move, spread) in {
        _FX: (108_000, 5, 10, 2),
        _GOLD: (2_900_000, 3, 500, 250),
    }.items():
        record = folder / "records" / f"{market}.json"
        record.write_text(
            json.dumps(json.loads(record.read_text("utf-8")) | {"calendar_ref": "crypto-24x7@1"}),
            "utf-8",
        )
        rows: dict[str, list[str]] = {"bid": [], "ask": []}
        for n, at in enumerate(range(_ns("2025-03-01T00:00"), _ns("2025-04-01T00:00"), _M15)):
            if market == _FX and skip[0] <= at < skip[1]:
                continue
            level = start + abs(n % 192 - 96) * move
            for side, offset in (("bid", 0), ("ask", spread)):
                cells = [_text(level + offset, decimals)] * 4
                rows[side].append(",".join([str(at // 1_000_000), *cells, "0"]))
        for side, lines in rows.items():
            (folder / "bars" / market / f"{side}.csv").write_text(
                "timestamp,open,high,low,close,volume\n" + "\n".join(lines) + "\n", "utf-8"
            )


@pytest.fixture
def hole_job(tmp_path: Path) -> Path:
    folder = tmp_path / "qmbr-pc-01JC0000000000000000000000"
    folder.mkdir()
    make_run_folder(folder)
    (folder / "run").rename(folder / "in")
    _write_247(folder / "in", ("2025-03-10T00:00", "2025-03-13T00:00"))
    found = load_unit_folder(folder / "in")
    assert not isinstance(found, TypedRefusal), found
    request = {
        "compiled_fp": found.value.compiled.compiled_fingerprint.value,
        "equity": "10000.00",
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
    }
    (folder / "in" / "request.json").write_text(json.dumps(request), "utf-8")
    return folder


def test_a_three_day_hole_lands_failed_unless_the_study_allows_gaps(hole_job: Path) -> None:
    run = _backtest_job()
    inputs = {"run_id": hole_job.name, "run_folder": str(hole_job)}

    refused = cast("dict[str, object]", run(inputs)["data"])
    asked = json.loads((hole_job / "in" / "request.json").read_text("utf-8"))
    (hole_job / "in" / "request.json").write_text(json.dumps(asked | {"allow_gaps": True}), "utf-8")
    allowed = cast("dict[str, object]", run(inputs)["data"])
    report = json.loads((hole_job / "out" / "report.json").read_text("utf-8"))

    assert refused["status"] == "failed"
    assert str(refused["reason"]).startswith(
        "data: fx.eurusd misses 288 bars in open time after the bar opening 2025-03-09 23:45 UTC"
    )
    assert allowed["status"] == "finished"
    assert report["holes"] == [
        {
            "market_id": "fx.eurusd",
            "after": _ns("2025-03-09T23:45"),
            "before": _ns("2025-03-13T00:00"),
            "bars_missing": 288,
        }
    ]
    assert cast("dict[str, object]", allowed["labels"])["costs_uncalibrated"] is True


def test_a_crypto_request_gets_the_crypto_generator_on_always_open_hours() -> None:
    saturday = {
        "process": "gbm",
        "venue": "hyperliquid",
        "symbol": "BTC",
        "scale": 2,
        "tick_size": 1,
        "resolution": "H1",
        "bar_step_ns": 3_600_000_000_000,
        "start_ns": _ns("2025-01-11T00:00"),
        "end_ns": _ns("2025-01-12T00:00"),
        "seed_price": 9_500_000,
        "volatility": "0.01",
        "seed": 7,
    }

    perp = resolve_generator_config(saturday | {"asset_class": "perp"})
    fx = resolve_generator_config(saturday | {"asset_class": "fx"})
    assert not isinstance(perp, TypedRefusal), perp
    assert not isinstance(fx, TypedRefusal), fx
    perp_grid = build_generation_grid(perp.value)
    fx_grid = build_generation_grid(fx.value)

    assert (perp.value.generator, perp.value.calendar_rule_set) == ("crypto", "always-open")
    assert fx.value.generator == "forex-cfd"
    assert not isinstance(perp_grid, TypedRefusal), perp_grid
    assert len(perp_grid.value) == 24
    assert isinstance(fx_grid, TypedRefusal)
    assert fx_grid.context["field"] == "window"


def test_the_qmb_app_runs_below_normal_priority() -> None:
    probe = f"""
import os, runpy, sys, types
mcp = types.ModuleType("fastmcp")
class FastMCP:
    def __init__(self, *args, **kwargs): pass
    def tool(self): return lambda function: function
mcp.FastMCP = FastMCP
sys.modules["fastmcp"] = mcp
sys.path.insert(0, {str(_APP)!r})
runpy.run_path({str(_APP / "server.py")!r}, run_name="qmb_server")
if sys.platform == "win32":
    import ctypes
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
    print(kernel.GetPriorityClass(kernel.GetCurrentProcess()))
else:
    print(os.nice(0))
"""
    shown = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True, timeout=120
    )

    below_normal = "16384" if sys.platform == "win32" else "10"
    assert shown.stdout.strip() == below_normal, shown.stderr
