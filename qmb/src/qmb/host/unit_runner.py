"""QMB's runner for a compiled unit over a run folder (Part B slice B5b, R1-L0-02, CA-03).

A run folder holds what the core gathered for one run:

- ``unit.json``: the unit document, its pins included;
- ``blocks/<entry_id>@<version>/block.py`` and ``entry.json``: every pinned block;
- ``records/<market_id>.json``: the instrument record of each of the unit's markets;
- ``bars/<market_id>/bid.csv`` and ``ask.csv``: the market's closed bars on the unit's stream,
  one row per bar (``timestamp`` is the bar's open in epoch milliseconds, then ``open``,
  ``high``, ``low``, ``close``), the test and hand-saved route;
- or ``data/<market_id>/``: the market's months copied from the market store, ticks or a pair of
  ``bar-m1`` series, beside a ``card.json`` naming their files, scale and window, which clip them;
- ``request.json``, optional: its ``markets`` names the markets a run trades, of the unit's;
- ``costs/<market_id>.json``, optional: the market's ``qmx.qmb.cost-profile/1``;
- ``funding/<market_id>.csv``: a market that pays funding, its recorded rates
  (``timestamp,rate``).

The runner compiles the document through QML's compiler, whose one block loader checks every
pin's fingerprint, refuses a compiled fingerprint other than the request's before the first
bar, hosts the unit with ``construct_unit``, and drives the shared unit handler through
``run_slice`` one bar instant at a time. The bars stream from the files through the windowed
reader (B7): each market keeps the unit's derived warm-up in memory, never the run behind it,
and its bars close in the venue's day. The result carries every trade in money and R, every
fill against its sizer receipt, and the ``zero_trades`` label when nothing closed. Given a
``RunJournal``, every row the run makes is written to the unit journal on disk, with each
slice's instant and every hole in a market's bars (B9).

Every market rule reads the instrument record (B10): fills, gaps and liquidation through
``BarExecution``, swaps, financing, funding and dividends through the record's
``CarrySchedule``, commission and slippage through the cost profile. Before the first bar a
preflight counts each market's holes in open time; one longer than the request's
``gap_bars_refuse`` fails the run unless the request sets ``allow_gaps``, and then the result
lists it. A request that names its window also has the open bars missing at each end counted, and
the result says ``data_short``. They fail the run past the same limit, where the market's calendar
holds closures from before the window, so a shut day there would not read as missing. A run whose
costs come from no calibrated profile says ``costs_uncalibrated``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from functools import partial
from itertools import islice
from pathlib import Path
from typing import Any, Final, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.numbers import ConversionRef, InstrumentRecord, parse_record
from qml.protocol.unit import (
    ACCOUNT_CURRENCY,
    MotionSwitch,
    OwnPosition,
    QuoteBar,
    TraceLevel,
    construct_unit,
)

from qmb._refuse import invalid, policy
from qmb.data.gap_check import (
    DATA_SHORT,
    GAP_BARS_REFUSE,
    HOLES_UNCHECKED,
    Hole,
    ShortEnds,
    find_holes,
    open_time,
    short_ends,
)
from qmb.execution.cost import (
    CALIBRATED_MIN_FILLS,
    COSTS_UNCALIBRATED,
    CostProfile,
    parse_cost_profile,
)
from qmb.execution.fill import BarExecution
from qmb.execution.financing import (
    CarrySchedule,
    CashEvent,
    ReplayCash,
    carry_schedule,
    read_funding_rates,
)
from qmb.execution.risk import MarginRule, margin_rule
from qmb.host.facts import RATE_ABSENT, ReplayRates, conversions
from qmb.host.replay import (
    BarWindow,
    DataCard,
    Fidelity,
    Row,
    VenueDay,
    read_bar_pair_csv,
    read_bar_pair_parquet,
    read_tick_parquet,
    replay_feed,
    replay_windowed,
    window_size,
)
from qmb.host.unit_handler import (
    ExecutionPort,
    Fill,
    JournalRecord,
    UnitSliceHandler,
    UnitTrade,
)
from qmb.results.journal import RunJournal
from qmb.runloop.bars import BarBuilder

__all__ = [
    "ZERO_TRADES",
    "BarFeed",
    "LoadedUnit",
    "UnitRunRequest",
    "UnitRunResult",
    "load_unit_folder",
    "parse_unit_run_request",
    "run_loaded",
    "run_unit",
]

ZERO_TRADES: Final[str] = "zero_trades"
_NS_PER_SEC: Final[int] = 1_000_000_000
_CENT: Final[Decimal] = Decimal("0.01")
_NS_PER_MS: Final[int] = 1_000_000
_EPOCH: Final[datetime] = datetime(1970, 1, 1, tzinfo=UTC)
_QUOTES: Final[DataCard] = DataCard(Fidelity.QUOTES)

BarFeed = Callable[[], Iterator[QuoteBar | TypedRefusal]]
"""Opens one market's closed bars afresh, read from its files as the run asks for them."""


@dataclass(frozen=True, slots=True)
class UnitRunRequest:
    """What the core asks of one unit run, parsed from its JSON body."""

    run_id: str
    compiled_fingerprint: str
    equity: Decimal
    execution_target: ExecutionTarget
    motion: MotionSwitch = MotionSwitch.ON
    trace: TraceLevel = TraceLevel.EVENTS
    allow_gaps: bool = False
    """The study runs over holes in its data; the unit sees each one as a gap row."""
    gap_bars_refuse: int = GAP_BARS_REFUSE
    calibrated_min_fills: int = CALIBRATED_MIN_FILLS
    window_ns: tuple[int, int] | None = None
    """The half-open window the bars should fill, when the caller names one."""


@dataclass(frozen=True, slots=True)
class LoadedUnit:
    """A run folder's unit compiled, its block sources, and a bar feed per market id.

    A feed opens the market's files each time it is called, so one load serves every run of it
    (``motion = both`` runs the unit twice). Beside each market's record sit what the record's
    rules read: its carry, its margin rule when it states one, and its cost profile when the
    folder holds one.

    ``conversions`` is each quote currency's conversion market, by the account currency it
    converts into, and ``rate_feeds`` holds that market's bars beside the unit's own. A market
    the folder cannot read is named in ``missing_rates``: the run sizes those entries by the
    named skip and says so on its labels.
    """

    compiled: CompiledUnit
    sources: Mapping[str, bytes]
    records: Mapping[str, InstrumentRecord]
    feeds: Mapping[str, BarFeed]
    bar_ns: int
    carry: Mapping[str, CarrySchedule]
    margins: Mapping[str, MarginRule]
    costs: Mapping[str, CostProfile]
    conversions: Mapping[str, ConversionRef] = field(default_factory=dict[str, ConversionRef])
    rate_feeds: Mapping[str, BarFeed] = field(default_factory=dict[str, BarFeed])
    missing_rates: tuple[str, ...] = ()

    def bars(self, limit: int | None = None) -> Result[dict[str, tuple[QuoteBar, ...]]]:
        """Each market's first ``limit`` bars held whole, or all of them, for a short recorded
        slice; a run streams them."""
        held: dict[str, tuple[QuoteBar, ...]] = {}
        for market, feed in self.feeds.items():
            bars: list[QuoteBar] = []
            for item in islice(feed(), limit):
                if isinstance(item, TypedRefusal):
                    return item
                bars.append(item)
            held[market] = tuple(bars)
        return Ok(held)


@dataclass(frozen=True, slots=True)
class UnitRunResult:
    run_id: str
    compiled_fingerprint: str
    trades: tuple[UnitTrade, ...]
    fills: tuple[Fill, ...]
    open_positions: Mapping[str, OwnPosition]
    net_money: Decimal
    """The account's own move over the run, in its currency and in cents: every trade's money and
    every cash event's, each converted from its market's quote. A figure no rate converts is left
    out, and the labels name ``rate_absent``."""
    total_r: Decimal
    labels: tuple[str, ...]
    cash_events: tuple[CashEvent, ...] = ()
    holes: tuple[Hole, ...] = ()
    """Holes in open time the run went over because the request allowed gaps."""
    unchecked: tuple[str, ...] = ()
    """Markets whose calendar QMB cannot read yet, so their holes were not counted."""
    short: tuple[ShortEnds, ...] = ()
    """Markets whose bars stop short of the window, with the open bars missing at each end."""
    max_drawdown_r: Decimal = Decimal(0)
    """The deepest fall of the running total of the trades' R from its high."""


def _window_ns(given: object) -> Result[tuple[int, int] | None]:
    """A request's ``{start, end}`` dates as a half-open window in ns, or None for no window."""
    if given is None:
        return Ok(None)
    named = cast("Mapping[str, object]", given if isinstance(given, Mapping) else {})
    start, end = _day_ms(named.get("start")), _day_ms(named.get("end"))
    if start is None or end is None:
        return invalid("window", "a run's window is {start, end} as dates", window=str(named))
    return Ok((start * _NS_PER_MS, end * _NS_PER_MS))


def parse_unit_run_request(body: object) -> Result[UnitRunRequest]:
    """The request from its JSON body; every field is text so no amount passes as a float."""
    if not isinstance(body, Mapping):
        return invalid("request", "a unit run request is a JSON object")
    fields = cast("Mapping[str, object]", body)
    run_id, fp, equity = (
        fields.get("run_id"),
        fields.get("compiled_fingerprint"),
        fields.get("equity"),
    )
    target = fields.get("execution_target")
    if not isinstance(run_id, str) or not run_id.strip():
        return invalid("run_id", "a unit run names its core run id")
    if not isinstance(fp, str) or not fp.startswith("fp1:"):
        return invalid("compiled_fingerprint", "a unit run pins the compiled fingerprint")
    if not isinstance(equity, str):
        return invalid("equity", "equity is decimal text", given=repr(equity))
    try:
        amount = Decimal(equity)
    except InvalidOperation:
        return invalid("equity", "equity is decimal text", given=equity)
    if not amount.is_finite() or amount <= 0:
        return invalid("equity", "equity is a positive amount", given=equity)
    if not isinstance(target, Mapping):
        return invalid("execution_target", "a unit run names its execution target")
    t = cast("Mapping[str, object]", target)
    try:
        role = AccountRole(str(t.get("role")))
    except ValueError:
        return invalid("execution_target", "the target's role is an account role")
    made = ExecutionTarget.try_create(role, VenueId(str(t.get("venue_id"))), t.get("account_id"))
    if is_refusal(made):
        return made
    try:
        motion = MotionSwitch(str(fields.get("motion", "on")))
    except ValueError:
        return invalid("motion", "motion is on or off", given=repr(fields.get("motion")))
    try:
        trace = TraceLevel(str(fields.get("trace", "events")))
    except ValueError:
        return invalid("trace", "trace is events or every_bar", given=repr(fields.get("trace")))
    allow_gaps = fields.get("allow_gaps") or False
    if not isinstance(allow_gaps, bool):
        return invalid("allow_gaps", "allow_gaps is true or false", given=repr(allow_gaps))
    counts: dict[str, int] = {}
    for name, default in (
        ("gap_bars_refuse", GAP_BARS_REFUSE),
        ("calibrated_min_fills", CALIBRATED_MIN_FILLS),
    ):
        given = fields.get(name)
        value = default if given is None else given
        if type(value) is not int or value < 0:
            return invalid(name, f"{name} is a whole number of zero or more", given=repr(value))
        counts[name] = value
    window = _window_ns(fields.get("window"))
    if is_refusal(window):
        return window
    return Ok(
        UnitRunRequest(
            run_id,
            fp,
            amount,
            made.value,
            motion,
            trace,
            allow_gaps,
            counts["gap_bars_refuse"],
            counts["calibrated_min_fills"],
            window.value,
        )
    )


def _bar_seconds(stream: str) -> int | None:
    unit, count = stream[:1], stream[1:]
    if not count.isdigit() or int(count) == 0:
        return None
    match unit:
        case "m":
            return int(count) * 60
        case "h":
            return int(count) * 3600
        case "d":
            return int(count) * 86_400
        case _:
            return None


@dataclass(frozen=True, slots=True)
class _BarFiles:
    """One market's bid and ask files of the unit's stream, built into bars in the venue's day."""

    bid: Path
    ask: Path
    seconds: int
    day: VenueDay

    def __call__(self) -> Iterator[QuoteBar | TypedRefusal]:
        rows = read_bar_pair_csv(self.bid, self.ask, self.seconds)
        return replay_feed(_QUOTES, rows, BarBuilder(self.day.span, self.seconds))


@dataclass(frozen=True, slots=True)
class _StoreFiles:
    """One market's months copied from the market store, built into bars in the venue's day.

    Ticks end where they start, so the window's end closes the last bar."""

    rows: Callable[[], Iterator[Row | TypedRefusal]]
    seconds: int
    day: VenueDay
    until_ns: int

    def __call__(self) -> Iterator[QuoteBar | TypedRefusal]:
        builder = BarBuilder(self.day.span, self.seconds)
        return replay_feed(_QUOTES, self.rows(), builder, until_ns=self.until_ns)


def _bar_files(folder: Path, market: str, day: VenueDay, seconds: int) -> Result[_BarFiles]:
    bid, ask = folder / "bars" / market / "bid.csv", folder / "bars" / market / "ask.csv"
    for path in (bid, ask):
        if not path.is_file():
            return invalid("bars", "a market's bars are a bid and an ask file", missing=str(path))
    builder = BarBuilder.try_create(day.span, seconds)
    if is_refusal(builder):
        return builder
    return Ok(_BarFiles(bid, ask, seconds, day))


def _day_ms(text: object) -> int | None:
    try:
        moment = datetime.fromisoformat(str(text)).replace(tzinfo=UTC)
    except ValueError:
        return None
    return (moment - _EPOCH) // timedelta(milliseconds=1)


def _store_files(data: Path, day: VenueDay, seconds: int) -> Result[_StoreFiles]:
    """The feed a market's ``card.json`` describes: its ticks, or its bid and ask ``bar-m1``."""
    try:
        found: object = json.loads((data / "card.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return invalid("data", "a market's store months sit beside their card", error=str(error))
    card = cast("Mapping[str, Any]", found)
    series = card.get("series")
    scale = card.get("scale")
    if type(scale) is not int:
        return invalid("data", f"{(series or ['this series'])[0]} states no price scale")
    window = cast("Mapping[str, object]", card.get("window") or {})
    start, end = _day_ms(window.get("start")), _day_ms(window.get("end"))
    if start is None or end is None:
        return invalid("data", "a market's card names its window as dates", window=str(window))
    files = {
        side: [data / name for name in names]
        for side, names in cast("Mapping[str, list[str]]", card.get("files") or {}).items()
    }
    rows: Callable[[], Iterator[Row | TypedRefusal]]
    match card.get("kind"), files:
        case "ticks", {"ticks": ticks}:
            rows = partial(read_tick_parquet, ticks, scale, start, end)
        case "bar-m1", {"bid": bid, "ask": ask}:
            rows = partial(read_bar_pair_parquet, bid, ask, scale, start, end)
        case _:
            return invalid("data", "a market's card names ticks or a bar-m1 pair", series=series)
    return Ok(_StoreFiles(rows, seconds, day, end * _NS_PER_MS))


def _market_feed(folder: Path, market: str, day: VenueDay, seconds: int) -> Result[BarFeed]:
    data = folder / "data" / market
    if data.is_dir():
        return _store_files(data, day, seconds)
    return _bar_files(folder, market, day, seconds)


def _asked_markets(folder: Path) -> Result[frozenset[str] | None]:
    """The markets the core's request names, or None for a folder whose request names none."""
    path = folder / "request.json"
    if not path.is_file():
        return Ok(None)
    try:
        asked: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return invalid("request", "the run's request is a JSON object", error=str(error))
    named = cast("Mapping[str, object]", asked).get("markets") if isinstance(asked, dict) else None
    return Ok(None if named is None else frozenset(cast("list[str]", named)))


@dataclass(frozen=True, slots=True)
class _MarketRules:
    carry: CarrySchedule
    margin: MarginRule | None
    costs: CostProfile | None


def _market_rules(
    folder: Path,
    market: str,
    record: InstrumentRecord,
    terms: Mapping[str, object],
    day: VenueDay,
    bar_ns: int,
) -> Result[_MarketRules]:
    """What the market's record and the folder's profile say beyond the price."""
    rates: Mapping[int, Decimal] | None = None
    funding = folder / "funding" / f"{market}.csv"
    if funding.is_file():
        read = read_funding_rates(funding.read_text(encoding="utf-8").splitlines())
        if is_refusal(read):
            return read
        rates = read.value
    carry = carry_schedule(
        market, terms, value_per_point=record.value_per_point, day=day, bar_ns=bar_ns, rates=rates
    )
    if is_refusal(carry):
        return carry
    margin = margin_rule(record, terms.get("liquidation_rule"))
    if is_refusal(margin):
        return margin
    profile = folder / "costs" / f"{market}.json"
    if not profile.is_file():
        return Ok(_MarketRules(carry.value, margin.value, None))
    costs = parse_cost_profile(json.loads(profile.read_text(encoding="utf-8")))
    if is_refusal(costs):
        return costs
    return Ok(_MarketRules(carry.value, margin.value, costs.value))


def _conversion_feed(folder: Path, market: str, seconds: int) -> BarFeed | None:
    """The conversion market's own bar feed, or None when this folder holds none it can read."""
    try:
        document: object = json.loads((folder / "records" / f"{market}.json").read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    parsed = parse_record(document)
    if is_refusal(parsed):
        return None
    day = VenueDay.try_create(parsed.value.zone, parsed.value.day_boundary)
    if is_refusal(day):
        return None
    feed = _market_feed(folder, market, day.value, seconds)
    return None if is_refusal(feed) else feed.value


def _rate_book(
    folder: Path,
    records: Mapping[str, InstrumentRecord],
    loaded: Mapping[str, BarFeed],
    seconds: int,
) -> tuple[dict[str, ConversionRef], dict[str, BarFeed], tuple[str, ...]]:
    """The conversion markets' bars beside the unit's own, and the ones this folder cannot read.

    A conversion market the unit itself trades is already loaded, so its feed is shared and no
    bar is read twice. One it does not trade is read from its own record and bars in the folder,
    which is all QMB needs: it keys bars by market id and never by symbol.
    """
    refs: dict[str, ConversionRef] = {}
    feeds: dict[str, BarFeed] = {}
    missing: list[str] = []
    by_record = {record.market_id: market for market, record in records.items()}
    for quote, ref in conversions(records.values(), ACCOUNT_CURRENCY).items():
        refs[quote] = ref
        traded = by_record.get(ref.market_id)
        if traded is not None and traded in loaded:
            feeds[ref.market_id] = loaded[traded]
            continue
        if ref.market_id in feeds or ref.market_id in missing:
            continue
        found = _conversion_feed(folder, ref.market_id, seconds)
        if found is None:
            missing.append(ref.market_id)
        else:
            feeds[ref.market_id] = found
    return refs, feeds, tuple(missing)


def load_unit_folder(folder: Path) -> Result[LoadedUnit]:
    """Compile the folder's unit from its pinned blocks and open a bar feed per market."""
    try:
        document: object = json.loads((folder / "unit.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return invalid(
            "unit", "a run folder holds its unit document as unit.json", error=str(error)
        )
    sources: dict[str, bytes] = {}
    entries: dict[str, bytes] = {}
    blocks = folder / "blocks"
    for pin in sorted(p for p in blocks.iterdir() if p.is_dir()) if blocks.is_dir() else ():
        sources[pin.name] = (pin / "block.py").read_bytes()
        entries[pin.name] = (pin / "entry.json").read_bytes()
    records: dict[str, InstrumentRecord] = {}
    terms: dict[str, Mapping[str, object]] = {}
    for path in sorted((folder / "records").glob("*.json")):
        raw: object = json.loads(path.read_text(encoding="utf-8"))
        parsed = parse_record(raw)
        if is_refusal(parsed):
            return parsed
        records[path.stem] = parsed.value
        terms[path.stem] = cast("Mapping[str, object]", raw)
    compiled = compile_unit(
        document,
        CompileContext(
            sources=sources,
            entries=entries,
            records=records,
            # QMB replays against its own execution, which fills each intent whole and keeps
            # every position apart, so a backtest runs the same two-position document the node
            # runs on a hedging account (AD-25).
            nets_positions=False,
        ),
    )
    if not isinstance(compiled, CompiledUnit):
        return invalid(
            "unit",
            compiled[0].message if compiled else "the unit does not compile",
            problems=tuple(f"{p.layer}:{p.kind}:{p.where}: {p.message}" for p in compiled),
        )
    seconds = _bar_seconds(compiled.plan.stream)
    if seconds is None:
        return invalid(
            "stream", "QMB replays minute, hour or day bars", stream=compiled.plan.stream
        )
    asked = _asked_markets(folder)
    if is_refusal(asked):
        return asked
    feeds: dict[str, BarFeed] = {}
    rules: dict[str, _MarketRules] = {}
    for market, record in compiled.plan.markets:
        if asked.value is not None and market.market_id not in asked.value:
            continue
        day = VenueDay.try_create(record.zone, record.day_boundary)
        if is_refusal(day):
            return day
        files = _market_feed(folder, market.market_id, day.value, seconds)
        if is_refusal(files):
            return files
        feeds[market.market_id] = files.value
        found = _market_rules(
            folder,
            market.market_id,
            record,
            terms.get(market.market_id, {}),
            day.value,
            seconds * _NS_PER_SEC,
        )
        if is_refusal(found):
            return found
        rules[market.market_id] = found.value
    unit_records = {m.market_id: record for m, record in compiled.plan.markets}
    refs, rate_feeds, missing = _rate_book(folder, unit_records, feeds, seconds)
    return Ok(
        LoadedUnit(
            compiled,
            sources,
            unit_records,
            feeds,
            seconds * _NS_PER_SEC,
            {m: r.carry for m, r in rules.items()},
            {m: r.margin for m, r in rules.items() if r.margin is not None},
            {m: r.costs for m, r in rules.items() if r.costs is not None},
            refs,
            rate_feeds,
            missing,
        )
    )


def run_unit(
    folder: Path,
    request: UnitRunRequest,
    *,
    execution: ExecutionPort | None = None,
    seeded: Mapping[str, OwnPosition] | None = None,
) -> Result[UnitRunResult]:
    """Trade the folder's unit over its bars through the shared unit handler."""
    loaded = load_unit_folder(folder)
    if is_refusal(loaded):
        return loaded
    return run_loaded(loaded.value, request, execution=execution, seeded=seeded)


def run_loaded(
    loaded: LoadedUnit,
    request: UnitRunRequest,
    *,
    execution: ExecutionPort | None = None,
    seeded: Mapping[str, OwnPosition] | None = None,
    journal: RunJournal | None = None,
) -> Result[UnitRunResult]:
    """Trade a loaded unit; ``journal`` receives every row and is left open."""
    compiled = loaded.compiled
    if compiled.compiled_fingerprint.value != request.compiled_fingerprint:
        return policy(
            "compiled_fingerprint",
            "the unit compiled to another fingerprint than the run pinned, so it does not start",
            pinned=request.compiled_fingerprint,
            compiled=compiled.compiled_fingerprint.value,
        )
    seconds = _bar_seconds(compiled.plan.stream)
    if seconds is None:
        return invalid(
            "stream", "QMB replays minute, hour or day bars", stream=compiled.plan.stream
        )
    checked = _preflight(loaded, request)
    if is_refusal(checked):
        return checked
    holes, unchecked, short = checked.value
    windows = {market: BarWindow(window_size(compiled)) for market in loaded.feeds}
    rates = (
        None
        if not loaded.conversions
        else ReplayRates(ACCOUNT_CURRENCY, loaded.conversions, loaded.rate_feeds)
    )
    handler = UnitSliceHandler.start(
        lambda surfaces: construct_unit(
            compiled,
            read_surfaces=surfaces,
            scope_id=request.run_id,
            execution_target=request.execution_target,
            motion=request.motion,
            trace_level=request.trace,
        ),
        stream=compiled.plan.stream,
        records=loaded.records,
        bars=windows,
        opened_by=compiled.compiled_fingerprint,
        equity=request.equity,
        execution=execution
        if execution is not None
        else BarExecution(loaded.bar_ns, loaded.costs, loaded.margins),
        journal=_Unkept() if journal is None else journal,
        seeded=seeded,
        cash=ReplayCash(loaded.carry, loaded.costs, loaded.bar_ns),
        rates=rates,
    )
    if is_refusal(handler):
        return handler
    driven = replay_windowed(
        handler.value,
        {market: feed() for market, feed in loaded.feeds.items()},
        windows,
        on_slice=None if journal is None else _JournalSlices(journal, seconds * _NS_PER_SEC),
    )
    if is_refusal(driven):
        return driven
    if rates is not None and rates.refused is not None:
        return rates.refused
    trades, cash = handler.value.trades, handler.value.cash_events
    account = handler.value.latest_account()
    uncalibrated = any(
        market not in loaded.costs
        or not loaded.costs[market].calibrated(request.calibrated_min_fills)
        for market in loaded.feeds
    )
    labels = (
        *(() if trades else (ZERO_TRADES,)),
        *((COSTS_UNCALIBRATED,) if uncalibrated else ()),
        *((HOLES_UNCHECKED,) if unchecked else ()),
        *((DATA_SHORT,) if short else ()),
        *((RATE_ABSENT,) if loaded.missing_rates or account.unpriced else ()),
    )
    return Ok(
        UnitRunResult(
            run_id=request.run_id,
            compiled_fingerprint=compiled.compiled_fingerprint.value,
            trades=trades,
            fills=handler.value.fills,
            open_positions=handler.value.open_positions,
            net_money=(account.equity - request.equity).quantize(_CENT, rounding=ROUND_HALF_EVEN),
            total_r=sum((t.r for t in trades), Decimal(0)),
            labels=labels,
            cash_events=cash,
            holes=holes,
            unchecked=unchecked,
            short=short,
            max_drawdown_r=handler.value.max_drawdown_r,
        )
    )


@dataclass
class _Opens:
    """One market's bar opens as its feed gives them, holding only the first and last, so a scan
    of any run length stays flat, and the refusal that stopped the feed, if one did."""

    feed: Iterable[QuoteBar | TypedRefusal]
    bar_ns: int
    ends: tuple[int, ...] = ()
    refused: TypedRefusal | None = None

    def __iter__(self) -> Iterator[int]:
        for item in self.feed:
            if isinstance(item, TypedRefusal):
                self.refused = item
                return
            at = item.knowable_at.value_ns - self.bar_ns
            self.ends = (self.ends[0] if self.ends else at, at)
            yield at


def _preflight(
    loaded: LoadedUnit, request: UnitRunRequest
) -> Result[tuple[tuple[Hole, ...], tuple[str, ...], tuple[ShortEnds, ...]]]:
    """Each market's holes in open time and its short ends, refused past the request's limit unless
    it allows gaps. A short end refuses only on a calendar holding closures from before the window,
    because elsewhere a shut day would read as missing."""
    holes: list[Hole] = []
    unchecked: list[str] = []
    short: list[ShortEnds] = []
    too_short: list[ShortEnds] = []
    for market, feed in loaded.feeds.items():
        hours = open_time(loaded.records[market].calendar_ref)
        if hours is None:
            unchecked.append(market)
            continue
        opens = _Opens(feed(), loaded.bar_ns)
        holes += find_holes(
            market, opens, bar_ns=loaded.bar_ns, hours=hours, refuse_bars=request.gap_bars_refuse
        )
        if opens.refused is not None:
            return opens.refused
        if request.window_ns is None:
            continue
        start_ns, end_ns = request.window_ns
        ends = short_ends(
            market, opens.ends, bar_ns=loaded.bar_ns, hours=hours, start_ns=start_ns, end_ns=end_ns
        )
        if ends.before_first or ends.after_last:
            short.append(ends)
            if max(
                ends.before_first, ends.after_last
            ) > request.gap_bars_refuse and hours.closures_before(start_ns):
                too_short.append(ends)
    if holes and not request.allow_gaps:
        first = holes[0]
        after = _EPOCH + timedelta(microseconds=first.after_ns // 1_000)
        return policy(
            "data",
            f"{first.market_id} misses {first.bars_missing} bars in open time after the bar "
            f"opening {after:%Y-%m-%d %H:%M} UTC, more than the {request.gap_bars_refuse} a "
            "run allows unless its study allows gaps",
            holes=[(h.market_id, h.after_ns, h.before_ns, h.bars_missing) for h in holes],
        )
    if too_short and not request.allow_gaps:
        first = too_short[0]
        return policy(
            "data",
            f"{first.market_id} stops short of its window: {first.before_first} bars in open time "
            f"are missing before its first bar and {first.after_last} after its last, more than "
            f"the {request.gap_bars_refuse} a run allows unless its study allows gaps",
            short=[(s.market_id, s.before_first, s.after_last) for s in too_short],
        )
    return Ok((tuple(holes), tuple(unchecked), tuple(short)))


class _Unkept:
    """The journal port of a run with no journal: its rows are not kept."""

    def append(self, record: JournalRecord, /) -> None:
        del record


@dataclass
class _JournalSlices:
    """Sets each slice's instant on the journal and writes a gap row where a market's bars skip."""

    journal: RunJournal
    bar_ns: int
    last: dict[str, int] = field(default_factory=dict[str, int])

    def __call__(self, instant: Instant, markets: Sequence[str]) -> None:
        self.journal.at(instant)
        ns = instant.value_ns
        for market in markets:
            before = self.last.get(market, ns)
            if (missing := (ns - before) // self.bar_ns - 1) > 0:
                self.journal.data_gap(market, Instant(before), instant, missing)
            self.last[market] = ns
