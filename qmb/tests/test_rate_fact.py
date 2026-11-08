"""The rate into the account's currency, read from QMB's own bars (AD-10 "Currency").

Four seams: the fact is the conversion bar's mid as an exact ``Fraction``, a replay with no
conversion bars skips by ``rate_absent`` and says so on its run stamp, the G check sizes a
JPY-quoting unit, and a stale rate never stops an exit. The literals are the section's
Verify, unit block: 500 USD at the stop from equity 100000 at fraction 0.005.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import csv
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import TypeVar, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION
from qml.blocks.api import EntryFace, parse_entry
from qml.check.layer_g import layer_g
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    OHLC,
    Account,
    DecisionRow,
    HostedUnit,
    Proposal,
    QuoteBar,
    RatePort,
    TraceLevel,
    construct_unit,
)
from qml.unit.model import Side
from qmb.execution.fill import BarExecution
from qmb.host.facts import RATE_ABSENT, ReplayRates, SliceRates, provided, rate_fact
from qmb.host.replay import BarWindow, window_size
from qmb.host.unit_handler import (
    FillKind,
    ListJournal,
    UnitSliceHandler,
    UnitTrade,
)
from qmb.host.unit_runner import (
    LoadedUnit,
    UnitRunRequest,
    load_unit_folder,
    parse_unit_run_request,
    run_loaded,
)
from qmb.runloop import DeclaredStream, SliceObservation, StreamSet, run_slice

REPO = Path(__file__).resolve().parents[2]
STDLIB = REPO / "qml" / "src" / "qml" / "blocks" / "stdlib"
TEMPLATE = REPO / "qml" / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
RECORDS = REPO / "qml" / "tests" / "fixtures" / "records"
SLICES = REPO / "qml" / "tests" / "fixtures" / "slices"

ACCOUNT_CURRENCY = "USD"
EQUITY = Decimal("100000")
FRACTION = Decimal("0.005")
BAR_NS = 900 * 1_000_000_000
START_NS = 1_740_952_800_000_000_000
QUOTES = "icmarkets-ctrader"

Prices = tuple[tuple[str, str, str, str], tuple[str, str, str, str]]
_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert isinstance(result, Ok), result.context
    return result.value


def _instant(step: int) -> Instant:
    return Instant(START_NS + step * BAR_NS)


def _fixture(symbol: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads((RECORDS / f"{symbol}.json").read_text("utf-8")))


def _record(document: dict[str, object]) -> InstrumentRecord:
    parsed = parse_record(document)
    assert isinstance(parsed, Ok), parsed
    return parsed.value


def _jpy_record(symbol: str, market_id: str) -> dict[str, object]:
    """A JPY-quoting record whose USD rate is the USDJPY market's own mid, inverted."""
    return _fixture("usdjpy") | {
        "symbol": symbol,
        "market_id": market_id,
        "conversions": {ACCOUNT_CURRENCY: {"market_id": "usdjpy", "invert": True}},
    }


def _write_side(path: Path, opens: Sequence[int], cells: Sequence[OHLC]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["timestamp,open,high,low,close"]
    for ms, bar in zip(opens, cells, strict=True):
        lines.append(f"{ms},{bar.open},{bar.high},{bar.low},{bar.close}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bars(folder: Path, market: str, bars: Sequence[Prices]) -> None:
    opens = [
        (START_NS + step * BAR_NS) // 1_000_000 - BAR_NS // 1_000_000
        for step in range(len(bars))
    ]
    for side, index in (("bid", 0), ("ask", 1)):
        cells = [OHLC(*(Decimal(cell) for cell in bar[index])) for bar in bars]
        _write_side(folder / "bars" / market / f"{side}.csv", opens, cells)


def _slice_series(symbol: str) -> tuple[list[int], list[OHLC], list[OHLC]]:
    def side(name: str) -> dict[int, OHLC]:
        path = SLICES / f"synthetic-{symbol}-m15-{name}-2025-03-01-2025-04-01.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            return {
                int(row["timestamp"]): OHLC(
                    Decimal(row["open"]),
                    Decimal(row["high"]),
                    Decimal(row["low"]),
                    Decimal(row["close"]),
                )
                for row in csv.DictReader(handle)
            }

    bid, ask = side("bid"), side("ask")
    opens = sorted(bid.keys() & ask.keys())
    return opens, [bid[ms] for ms in opens], [ask[ms] for ms in opens]


def _folder(
    root: Path,
    *,
    markets: Sequence[tuple[str, str]],
    records: Mapping[str, dict[str, object]],
    bars: Mapping[str, Sequence[Prices]],
    numbers: Mapping[str, str] | None = None,
) -> Path:
    """A run folder as the node link stages one: the unit, every pinned block, records, bars."""
    folder = root / "run"
    (folder / "records").mkdir(parents=True)
    document = cast("dict[str, object]", json.loads(TEMPLATE.read_text("utf-8")))
    document["markets"] = [
        {"market_id": market, "instrument_ref": {"venue": QUOTES, "symbol": symbol}}
        for market, symbol in markets
    ]
    for name, default in (numbers or {}).items():
        numbers_in_force = cast("dict[str, dict[str, object]]", document["numbers"])
        numbers_in_force[name]["default"] = default
    pins: list[dict[str, object]] = []
    for entry_path in sorted(STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry_path.read_bytes())
        assert isinstance(face, EntryFace), face
        pins.append(
            {"entry_id": face.entry_id, "version": face.version, "fingerprint": face.fingerprint}
        )
        target = folder / "blocks" / face.pin
        target.mkdir(parents=True, exist_ok=True)
        for name in ("block.py", "entry.json"):
            shutil.copyfile(entry_path.with_name(name), target / name)
    document["pins"] = pins
    (folder / "unit.json").write_text(json.dumps(document), "utf-8")
    for market, record in records.items():
        (folder / "records" / f"{market}.json").write_text(json.dumps(record), "utf-8")
    for market, series in bars.items():
        _write_bars(folder, market, series)
    return folder


def _four_markets() -> tuple[list[tuple[str, str]], dict[str, dict[str, object]]]:
    markets = [
        ("fx.eurusd", "EURUSD"),
        ("metal.xauusd", "XAUUSD"),
        ("fx.usdjpy", "USDJPY"),
        ("fx.eurjpy", "EURJPY"),
    ]
    records = {
        "fx.eurusd": _fixture("eurusd"),
        "metal.xauusd": _fixture("xauusd"),
        "fx.usdjpy": _jpy_record("USDJPY", "usdjpy"),
        "fx.eurjpy": _jpy_record("EURJPY", "eurjpy"),
    }
    return markets, records


def _flat(bid: str, ask: str, count: int = 3) -> list[Prices]:
    """``count`` bars whose four quotes sit at ``bid`` on the bid side and ``ask`` on the ask."""
    return [((bid,) * 4, (ask,) * 4) for _ in range(count)]


def _target() -> ExecutionTarget:
    return _ok(ExecutionTarget.try_create(AccountRole.DEMO, VenueId(QUOTES), "rc-07"))


def _proposal(
    compiled: CompiledUnit,
    record: InstrumentRecord,
    *,
    market: str,
    instant: Instant,
    entry: str,
    stop: str,
    row: str,
) -> Proposal:
    """One entry as the unit's own ``enter`` spells it, before the host adds the size."""
    target = _target()
    wire: dict[str, object] = {
        "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
        "intent_family": "entry",
        "unit": {
            "unit_id": compiled.unit.unit_id,
            "version_ref": compiled.document_fingerprint.value,
            "compiled_fingerprint": compiled.compiled_fingerprint.value,
        },
        "instrument": {"venue": record.venue, "symbol": record.symbol},
        "market_id": market,
        "direction": Side.LONG.value,
        "reason_code": {"code": compiled.unit.family_id, "book_family": "unit"},
        "execution_target": {
            "role": target.role.value,
            "venue_id": target.venue_id.value,
            "account_id": target.account_id,
        },
        "order": {"type": "market"},
        "protection": {"stop": stop, "targets": [], "time_exit_bars": 1},
        "not_before": instant.value_ns,
        "placeholder_labels": list(compiled.placeholders),
        "decision_row_id": row,
    }
    return Proposal(
        wire=wire,
        row=DecisionRow(
            row_id=row,
            instant=instant,
            market_id=market,
            side=Side.LONG,
            outcome="taken",
            slot_trail=(),
            numbers_in_force={"risk_fraction": FRACTION},
            reason="all slots hold",
        ),
        market_id=market,
        side=Side.LONG,
        entry_price=Decimal(entry),
        stop=Decimal(stop),
        params={"fraction": FRACTION},
        record=record,
    )


class _Scripted:
    """A unit whose signal half stands in: every size and every exit is the real one."""

    def __init__(self, real: HostedUnit, queued: Mapping[int, tuple[Proposal, ...]]) -> None:
        self._real = real
        self._queued = dict(queued)

    def on_instant(self, instant: object, /) -> Result[object]:
        assert isinstance(instant, Instant)
        step = self._real.on_instant(instant)
        if is_refusal(step):
            return step
        extra = self._queued.get(instant.value_ns, ())
        return Ok(replace(step.value, proposals=extra)) if extra else step

    def price(self, proposal: Proposal, facts: Account) -> object:
        return self._real.price(proposal, facts)


def _host(compiled: CompiledUnit, surfaces: Mapping[str, object]) -> HostedUnit:
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=cast("Mapping[str, object]", surfaces),
            scope_id="rc-07",
            execution_target=_target(),
            trace_level=TraceLevel.EVENTS,
        )
    )


class _Rig:
    """One host driving the shared handler: its windows, its journal and its unit."""

    def __init__(
        self,
        loaded: LoadedUnit,
        *,
        rates: RatePort,
        queued: Mapping[int, tuple[Proposal, ...]],
    ) -> None:
        self.journal = ListJournal()
        self.windows = {market: BarWindow(window_size(loaded.compiled)) for market in loaded.feeds}
        self.handler = _ok(
            UnitSliceHandler.start(
                lambda surfaces: Ok(_Scripted(_host(loaded.compiled, surfaces), queued)),
                stream=loaded.compiled.plan.stream,
                records=loaded.records,
                bars=self.windows,
                opened_by=loaded.compiled.compiled_fingerprint,
                equity=EQUITY,
                execution=BarExecution(loaded.bar_ns, loaded.costs, loaded.margins),
                journal=self.journal,
                rates=rates,
            )
        )


def _run_folder(
    folder: Path, *, rates: RatePort, queued: Mapping[int, tuple[Proposal, ...]]
) -> _Rig:
    return _Rig(_ok(load_unit_folder(folder)), rates=rates, queued=queued)


def _drive(rig: _Rig, series: Mapping[str, Sequence[QuoteBar]]) -> None:
    """Each instant's slice through ``run_slice``, the production driver."""
    streams = _ok(StreamSet.try_create([DeclaredStream(market, market) for market in series]))
    by_instant: dict[int, list[tuple[str, QuoteBar]]] = {}
    for market, bars in series.items():
        for bar in bars:
            by_instant.setdefault(bar.knowable_at.value_ns, []).append((market, bar))
    frontier: Instant | None = None
    resting: object = ()
    for ns in sorted(by_instant):
        closed = by_instant[ns]
        for market, bar in closed:
            rig.windows[market].push(bar)
        outcome = _ok(
            run_slice(
                [SliceObservation(market, Instant(ns)) for market, _ in closed],
                stream_set=streams,
                current_frontier=frontier,
                clock=None,
                handler=rig.handler,
                resting=resting,
            )
        )
        frontier, resting = outcome.frontier, outcome.resting


def _request(compiled: CompiledUnit) -> UnitRunRequest:
    target = _target()
    return _ok(
        parse_unit_run_request(
            {
                "run_id": "rc-07",
                "compiled_fingerprint": compiled.compiled_fingerprint.value,
                "equity": str(EQUITY),
                "execution_target": {
                    "role": target.role.value,
                    "venue_id": target.venue_id.value,
                    "account_id": target.account_id,
                },
            }
        )
    )


def test_the_rate_is_the_conversion_bars_mid_as_an_exact_fraction() -> None:
    bar = QuoteBar(
        _instant(0),
        OHLC(*(Decimal("149.99"),) * 4),
        OHLC(*(Decimal("150.01"),) * 4),
    )

    inverted = rate_fact(bar, invert=True, source="qmb:replay")
    direct = rate_fact(bar, invert=False, source="qmb:replay")

    assert inverted.value == Fraction(1, 150)
    assert inverted.ts == bar.knowable_at
    assert direct.value == Fraction(150)
    records = (_record(_jpy_record("USDJPY", "usdjpy")), _record(_fixture("eurusd")))
    assert provided(records, ACCOUNT_CURRENCY) == ("market.rate:JPY",)


def test_a_replay_missing_the_conversion_bars_skips_by_name_on_its_run_stamp(
    tmp_path: Path,
) -> None:
    folder = _folder(
        tmp_path,
        markets=[("fx.eurusd", "EURUSD"), ("fx.eurjpy", "EURJPY")],
        records={"fx.eurusd": _fixture("eurusd"), "fx.eurjpy": _jpy_record("EURJPY", "eurjpy")},
        bars={
            "fx.eurusd": _flat("1.1000", "1.1002"),
            "fx.eurjpy": _flat("160.00", "160.02"),
        },
    )
    loaded = _ok(load_unit_folder(folder))
    result = _ok(run_loaded(loaded, _request(loaded.compiled)))

    assert loaded.missing_rates == ("usdjpy",)
    assert RATE_ABSENT in result.labels

    proposal = _proposal(
        loaded.compiled,
        loaded.records["fx.eurjpy"],
        market="fx.eurjpy",
        instant=_instant(0),
        entry="160.00",
        stop="159.50",
        row="row-eurjpy-absent",
    )
    rig = _run_folder(
        folder,
        rates=ReplayRates(ACCOUNT_CURRENCY, loaded.conversions, loaded.rate_feeds),
        queued={_instant(0).value_ns: (proposal,)},
    )
    minted = _ok(rig.handler.mint_intents("fx.eurjpy", _instant(0)))

    assert minted == ()
    rows = [record for record in rig.journal.records if isinstance(record, DecisionRow)]
    assert (rows[-1].outcome, rows[-1].reason) == ("skipped", "sizer: rate_absent")


def test_the_g_check_sizes_a_jpy_unit(tmp_path: Path) -> None:
    opens, bid, ask = _slice_series("EURUSD")
    folder = _folder(
        tmp_path,
        markets=[("fx.eurusd", "EURUSD")],
        records={
            "fx.eurusd": _fixture("eurusd")
            | {
                "currency": "JPY",
                "conversions": {ACCOUNT_CURRENCY: {"market_id": "usdjpy", "invert": True}},
            },
            "usdjpy": _fixture("usdjpy"),
        },
        bars={},
    )
    for side, cells in (("bid", bid), ("ask", ask)):
        _write_side(folder / "bars" / "fx.eurusd" / f"{side}.csv", opens, cells)
    flat = [OHLC(*(Decimal("150.00"),) * 4) for _ in opens]
    for side in ("bid", "ask"):
        _write_side(folder / "bars" / "usdjpy" / f"{side}.csv", opens, flat)
    loaded = _ok(load_unit_folder(folder))
    series = _ok(loaded.bars())
    conversion = {market: tuple(feed()) for market, feed in loaded.rate_feeds.items()}

    sized = layer_g(
        loaded.compiled,
        loaded.sources,
        series,
        execution_target=_target(),
        equity=EQUITY,
        loaded_in_isolation=False,
        rates=SliceRates(ACCOUNT_CURRENCY, loaded.conversions, conversion),
    )
    unsized = layer_g(
        loaded.compiled,
        loaded.sources,
        series,
        execution_target=_target(),
        equity=EQUITY,
        loaded_in_isolation=False,
    )

    assert cast("int", sized.report["trades"]) > 0
    assert unsized.report["trades"] == 0


def test_a_stale_rate_never_stops_an_exit(tmp_path: Path) -> None:
    folder = _folder(
        tmp_path,
        markets=[("fx.eurusd", "EURUSD"), ("fx.eurjpy", "EURJPY")],
        records={
            "fx.eurusd": _fixture("eurusd"),
            "fx.eurjpy": _jpy_record("EURJPY", "eurjpy"),
            "usdjpy": _fixture("usdjpy"),
        },
        bars={
            "fx.eurusd": _flat("1.1000", "1.1002", count=4),
            "fx.eurjpy": _flat("160.00", "160.02", count=4),
            "usdjpy": _flat("150.00", "150.00", count=1),
        },
        numbers={"time_out_bars": "1"},
    )
    loaded = _ok(load_unit_folder(folder))
    entry = _proposal(
        loaded.compiled,
        loaded.records["fx.eurusd"],
        market="fx.eurusd",
        instant=_instant(0),
        entry="1.1000",
        stop="1.0950",
        row="row-eurusd-entry",
    )
    stale = _proposal(
        loaded.compiled,
        loaded.records["fx.eurjpy"],
        market="fx.eurjpy",
        instant=_instant(1),
        entry="160.00",
        stop="159.50",
        row="row-eurjpy-stale",
    )
    rig = _run_folder(
        folder,
        rates=ReplayRates(ACCOUNT_CURRENCY, loaded.conversions, loaded.rate_feeds),
        queued={_instant(0).value_ns: (entry,), _instant(1).value_ns: (stale,)},
    )
    _drive(
        rig,
        {
            "fx.eurusd": [
                QuoteBar(
                    _instant(step),
                    OHLC(*(Decimal("1.1000"),) * 4),
                    OHLC(*(Decimal("1.1002"),) * 4),
                )
                for step in range(4)
            ]
        },
    )

    rows = [record for record in rig.journal.records if isinstance(record, DecisionRow)]
    assert ("skipped", "sizer: rate_stale") in [(row.outcome, row.reason) for row in rows]
    trades = [record for record in rig.journal.records if isinstance(record, UnitTrade)]
    assert [(t.exit_kind, t.quantity) for t in trades] == [(FillKind.CLOSE, Decimal("1.00"))]
    assert trades[0].rate == Fraction(1)


def test_a_replay_with_the_conversion_bars_says_nothing_about_the_rate(tmp_path: Path) -> None:
    markets, records = _four_markets()
    folder = _folder(
        tmp_path,
        markets=markets,
        records=records,
        bars={
            "fx.eurusd": _flat("1.1000", "1.1002"),
            "metal.xauusd": _flat("2000.00", "2000.20"),
            "fx.usdjpy": _flat("149.99", "150.01"),
            "fx.eurjpy": _flat("159.90", "160.10"),
        },
    )
    loaded = _ok(load_unit_folder(folder))
    rates = ReplayRates(ACCOUNT_CURRENCY, loaded.conversions, loaded.rate_feeds)
    result = _ok(run_loaded(loaded, _request(loaded.compiled)))

    assert loaded.missing_rates == ()
    assert RATE_ABSENT not in result.labels
    fact = rates.rate(loaded.records["fx.usdjpy"], _instant(2))
    assert fact is not None and fact.value == Fraction(1, 150)
    assert rates.rate(loaded.records["fx.eurusd"], _instant(2)) is None
