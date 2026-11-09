"""The rate on the node's feed and in QMB's replay, and the same size from both (AD-10).

The node reads its rate from the feed's own record of the conversion market and QMB from the
run folder's bars; both hand the one converter the same exact ``Fraction``, so the four markets
of RC-05 lose 500 USD at the stop from equity 100000 at fraction 0.005, and the two hosts'
quantities are equal. K9 test 16.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import TypeVar, cast

from qmb.execution.fill import BarExecution
from qmb.host.facts import ReplayRates
from qmb.host.replay import BarWindow, window_size
from qmb.host.unit_handler import ListJournal, UnitSliceHandler
from qmb.host.unit_runner import LoadedUnit, load_unit_folder
from qmb.runloop import RestingIntent
from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompiledUnit
from qml.numbers import InstrumentRecord
from qml.protocol.unit import (
    OHLC,
    Account,
    DecisionRow,
    HostedUnit,
    Priced,
    Proposal,
    QuoteBar,
    RatePort,
    Surface,
    TraceLevel,
    UnitStep,
    construct_unit,
)
from qml.unit.model import Side
from qmn.app.facts import FeedRates, provided, refs
from qmn.app.feed_keeper import (
    Bar,
    BookState,
    FeedKeeper,
    RecordedSource,
    Recording,
)

REPO = Path(__file__).resolve().parents[2]
STDLIB = REPO / "qml" / "src" / "qml" / "blocks" / "stdlib"
TEMPLATE = REPO / "qml" / "src" / "qml" / "unit" / "templates" / "dummy-trend-pullback.json"
RECORDS = REPO / "qml" / "tests" / "fixtures" / "records"

CURRENCY = "USD"
EQUITY = Decimal("100000")
FRACTION = Decimal("0.005")
BAR_NS = 900 * 1_000_000_000
START_NS = 1_740_952_800_000_000_000
QUOTES = "icmarkets-ctrader"
MARKETS = (
    ("fx.eurusd", "EURUSD"),
    ("metal.xauusd", "XAUUSD"),
    ("fx.usdjpy", "USDJPY"),
    ("fx.eurjpy", "EURJPY"),
)
CASES = (
    ("fx.eurusd", "1.1000", "1.0950", "1.00", Fraction(1)),
    ("metal.xauusd", "2000.00", "1995.00", "1.00", Fraction(1)),
    ("fx.usdjpy", "150.00", "149.50", "1.50", Fraction(1, 150)),
    ("fx.eurjpy", "160.00", "159.50", "1.50", Fraction(1, 150)),
)

Prices = tuple[tuple[str, str, str, str], tuple[str, str, str, str]]
_T = TypeVar("_T")


def _ok(result: Result[_T]) -> _T:
    assert isinstance(result, Ok), result.context
    return result.value


def _instant(step: int) -> Instant:
    return Instant(START_NS + step * BAR_NS)


def _fixture(symbol: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads((RECORDS / f"{symbol}.json").read_text("utf-8")))


def _jpy_record(symbol: str, market_id: str) -> dict[str, object]:
    return _fixture("usdjpy") | {
        "symbol": symbol,
        "market_id": market_id,
        "conversions": {CURRENCY: {"market_id": "usdjpy", "invert": True}},
    }


def _write_side(path: Path, opens: Sequence[int], cells: Sequence[OHLC]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["timestamp,open,high,low,close"]
    for ms, bar in zip(opens, cells, strict=True):
        lines.append(f"{ms},{bar.open},{bar.high},{bar.low},{bar.close}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bars(folder: Path, market: str, bars: Sequence[Prices]) -> None:
    opens = [
        (START_NS + step * BAR_NS) // 1_000_000 - BAR_NS // 1_000_000 for step in range(len(bars))
    ]
    for side, index in (("bid", 0), ("ask", 1)):
        cells = [OHLC(*(Decimal(cell) for cell in bar[index])) for bar in bars]
        _write_side(folder / "bars" / market / f"{side}.csv", opens, cells)


def _flat(bid: str, ask: str, count: int = 3) -> list[Prices]:
    return [((bid, bid, bid, bid), (ask, ask, ask, ask)) for _ in range(count)]


def _folder(root: Path) -> Path:
    """A run folder over the four markets, their records and three bars each."""
    folder = root / "run"
    (folder / "records").mkdir(parents=True)
    document = cast("dict[str, object]", json.loads(TEMPLATE.read_text("utf-8")))
    document["markets"] = [
        {"market_id": market, "instrument_ref": {"venue": QUOTES, "symbol": symbol}}
        for market, symbol in MARKETS
    ]
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
    records = {
        "fx.eurusd": _fixture("eurusd"),
        "metal.xauusd": _fixture("xauusd"),
        "fx.usdjpy": _jpy_record("USDJPY", "usdjpy"),
        "fx.eurjpy": _jpy_record("EURJPY", "eurjpy"),
    }
    for market, record in records.items():
        (folder / "records" / f"{market}.json").write_text(json.dumps(record), "utf-8")
    for market, (bid, ask) in (
        ("fx.eurusd", ("1.1000", "1.1002")),
        ("metal.xauusd", ("2000.00", "2000.20")),
        ("fx.usdjpy", ("149.99", "150.01")),
        ("fx.eurjpy", ("159.90", "160.10")),
    ):
        _write_bars(folder, market, _flat(bid, ask))
    return folder


def _target() -> ExecutionTarget:
    return _ok(ExecutionTarget.try_create(AccountRole.DEMO, VenueId(QUOTES), "rc-07"))


def _proposal(
    compiled: CompiledUnit, record: InstrumentRecord, market: str, entry: str, stop: str
) -> Proposal:
    instant = _instant(2)
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
        "decision_row_id": f"row-{market}",
    }
    return Proposal(
        wire=wire,
        row=DecisionRow(
            row_id=f"row-{market}",
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


class _Standing:
    """The unit's signal half stands in; every size is the real ``HostedUnit.price``."""

    def __init__(self, real: HostedUnit, proposals: Sequence[Proposal]) -> None:
        self._real = real
        self._proposals = tuple(proposals)
        self._at = proposals[0].row.instant.value_ns

    def on_instant(self, instant: object, /) -> Result[UnitStep]:
        assert isinstance(instant, Instant)
        step = self._real.on_instant(instant)
        if is_refusal(step) or instant.value_ns != self._at:
            return step
        return Ok(replace(step.value, proposals=self._proposals))

    def price(self, proposal: Proposal, facts: Account) -> Priced:
        return self._real.price(proposal, facts)


def _hosted(loaded: LoadedUnit, rates: RatePort, proposals: Sequence[Proposal]) -> UnitSliceHandler:
    def host(surfaces: Mapping[str, Surface]) -> Result[_Standing]:
        real = _ok(
            construct_unit(
                loaded.compiled,
                read_surfaces=surfaces,
                scope_id="rc-07",
                execution_target=_target(),
                trace_level=TraceLevel.EVENTS,
            )
        )
        return Ok(_Standing(real, proposals))

    return _ok(
        UnitSliceHandler.start(
            host,
            stream=loaded.compiled.plan.stream,
            records=loaded.records,
            bars={market: BarWindow(window_size(loaded.compiled)) for market in loaded.feeds},
            opened_by=loaded.compiled.compiled_fingerprint,
            equity=EQUITY,
            execution=BarExecution(loaded.bar_ns, loaded.costs, loaded.margins),
            journal=ListJournal(),
            rates=rates,
        )
    )


def _sizes(
    loaded: LoadedUnit, rates: RatePort, proposals: Sequence[Proposal]
) -> tuple[dict[str, str], Account]:
    """Each market's committed quantity, and the account facts the host supplied to size them."""
    handler = _hosted(loaded, rates, proposals)
    quantities: dict[str, str] = {}
    for proposal in proposals:
        minted = cast(
            "tuple[RestingIntent, ...]",
            _ok(handler.mint_intents(proposal.market_id, proposal.row.instant)),
        )
        assert len(minted) == 1, (proposal.market_id, minted)
        wire = cast("Mapping[str, object]", minted[0].order)
        quantities[proposal.market_id] = cast("str", wire["quantity"])
    account = cast("Account", handler.read_surfaces()["account"].at(_instant(2)))
    return quantities, account


def _rate_of(account: Account, record: InstrumentRecord) -> Fraction:
    if record.currency == account.currency:
        return Fraction(1)
    fact = account.rates[record.currency]
    assert fact.value is not None, record.currency
    return Fraction(fact.value)


def test_k9_16_currency(tmp_path: Path) -> None:
    loaded = _ok(load_unit_folder(_folder(tmp_path)))
    proposals = [
        _proposal(loaded.compiled, loaded.records[market], market, entry, stop)
        for market, entry, stop, _, _ in CASES
    ]

    qmb_sizes, qmb_account = _sizes(
        loaded, ReplayRates(CURRENCY, loaded.conversions, loaded.rate_feeds), proposals
    )
    recorded = Recording(None)
    for bar in cast("Sequence[QuoteBar]", tuple(loaded.rate_feeds["usdjpy"]())):
        recorded.keep("fx.usdjpy", bar)
    node_rates = FeedRates(recorded, refs(loaded.records, CURRENCY), CURRENCY)
    node_sizes, node_account = _sizes(loaded, node_rates, proposals)

    assert provided(tuple(loaded.records.values()), CURRENCY) == ("market.rate:JPY",)
    assert qmb_sizes == node_sizes
    assert qmb_sizes == {market: expected for market, _, _, expected, _ in CASES}

    for market, entry, stop, _, rate in CASES:
        record = loaded.records[market]
        assert _rate_of(node_account, record) == rate
        assert _rate_of(qmb_account, record) == rate
        loss = (
            Fraction(Decimal(qmb_sizes[market]))
            * Fraction(abs(Decimal(entry) - Decimal(stop)))
            * Fraction(record.value_per_point)
            * rate
        )
        assert loss == 500, market


def test_the_feed_keeps_a_conversion_market_beside_the_traded_ones() -> None:
    source = RecordedSource(
        [
            (
                Bar(
                    "fx.eurusd",
                    QuoteBar(
                        _instant(0),
                        OHLC(*(Decimal("1.1000"),) * 4),
                        OHLC(*(Decimal("1.1002"),) * 4),
                    ),
                ),
            )
        ]
    )
    feed = FeedKeeper("ctrader", "demo", source, ("fx.eurusd",), lambda: 0, Recording(None))

    assert feed.widen(("fx.usdjpy",)) is True
    assert feed.markets == ("fx.eurusd", "fx.usdjpy")
    assert feed.book("fx.usdjpy").book_state is BookState.REBUILDING
    assert feed.widen(("fx.eurusd", "fx.usdjpy")) is False

    feed.drop("a deployment added a conversion market")
    feed.pump()

    assert source.subscribed == ("fx.eurusd", "fx.usdjpy")
