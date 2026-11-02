"""QMB's runner for a compiled unit over a run folder (Part B slice B5b, R1-L0-02, CA-03).

A run folder holds what the core gathered for one run:

- ``unit.json``: the unit document, its pins included;
- ``blocks/<entry_id>@<version>/block.py`` and ``entry.json``: every pinned block;
- ``records/<market_id>.json``: the instrument record of each of the unit's markets;
- ``bars/<market_id>/bid.csv`` and ``ask.csv``: the market's closed bars on the unit's stream,
  one row per bar (``timestamp`` is the bar's open in epoch milliseconds, then ``open``,
  ``high``, ``low``, ``close``), as the Dukascopy download template saves them.

The runner compiles the document through QML's compiler, whose one block loader checks every
pin's fingerprint, refuses a compiled fingerprint other than the request's before the first
bar, hosts the unit with ``construct_unit``, and drives the shared unit handler through
``run_slice`` one bar instant at a time. The bars stream from the files through the windowed
reader (B7): each market keeps the unit's derived warm-up in memory, never the run behind it,
and its bars close in the venue's day. The result carries every trade in money and R, every
fill against its sizer receipt, and the ``zero_trades`` label when nothing closed. Given a
``RunJournal``, every row the run makes is written to the unit journal on disk, with each
slice's instant and every hole in a market's bars (B9).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.risk.paper import ExecutionTarget
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import MotionSwitch, OwnPosition, QuoteBar, TraceLevel, construct_unit

from qmb._refuse import invalid, policy
from qmb.host.replay import (
    BarWindow,
    DataCard,
    Fidelity,
    VenueDay,
    read_bar_pair_csv,
    replay_feed,
    replay_windowed,
    window_size,
)
from qmb.host.unit_handler import (
    ExecutionPort,
    Fill,
    JournalRecord,
    NextOpenExecution,
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


@dataclass(frozen=True, slots=True)
class LoadedUnit:
    """A run folder's unit compiled, its block sources, and a bar feed per market id.

    A feed opens the market's files each time it is called, so one load serves every run of it
    (``motion = both`` runs the unit twice).
    """

    compiled: CompiledUnit
    sources: Mapping[str, bytes]
    records: Mapping[str, InstrumentRecord]
    feeds: Mapping[str, BarFeed]

    def bars(self) -> Result[dict[str, tuple[QuoteBar, ...]]]:
        """Every market's bars held whole, for a short recorded slice; a run streams them."""
        held: dict[str, tuple[QuoteBar, ...]] = {}
        for market, feed in self.feeds.items():
            bars: list[QuoteBar] = []
            for item in feed():
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
    total_r: Decimal
    labels: tuple[str, ...]


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
    return Ok(UnitRunRequest(run_id, fp, amount, made.value, motion, trace))


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


def _bar_files(
    folder: Path, market: str, record: InstrumentRecord, seconds: int
) -> Result[_BarFiles]:
    bid, ask = folder / "bars" / market / "bid.csv", folder / "bars" / market / "ask.csv"
    for path in (bid, ask):
        if not path.is_file():
            return invalid("bars", "a market's bars are a bid and an ask file", missing=str(path))
    day = VenueDay.try_create(record.zone, record.day_boundary)
    if is_refusal(day):
        return day
    builder = BarBuilder.try_create(day.value.span, seconds)
    if is_refusal(builder):
        return builder
    return Ok(_BarFiles(bid, ask, seconds, day.value))


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
    for path in sorted((folder / "records").glob("*.json")):
        parsed = parse_record(json.loads(path.read_text(encoding="utf-8")))
        if is_refusal(parsed):
            return parsed
        records[path.stem] = parsed.value
    compiled = compile_unit(
        document, CompileContext(sources=sources, entries=entries, records=records)
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
    feeds: dict[str, BarFeed] = {}
    for market, record in compiled.plan.markets:
        files = _bar_files(folder, market.market_id, record, seconds)
        if is_refusal(files):
            return files
        feeds[market.market_id] = files.value
    unit_records = {m.market_id: record for m, record in compiled.plan.markets}
    return Ok(LoadedUnit(compiled, sources, unit_records, feeds))


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
    windows = {market: BarWindow(window_size(compiled)) for market in loaded.feeds}
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
        execution=execution if execution is not None else NextOpenExecution(),
        journal=_Unkept() if journal is None else journal,
        seeded=seeded,
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
    trades = handler.value.trades
    return Ok(
        UnitRunResult(
            run_id=request.run_id,
            compiled_fingerprint=compiled.compiled_fingerprint.value,
            trades=trades,
            fills=handler.value.fills,
            open_positions=handler.value.open_positions,
            net_money=sum((t.money for t in trades), Decimal(0)),
            total_r=sum((t.r for t in trades), Decimal(0)),
            labels=() if trades else (ZERO_TRADES,),
        )
    )


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
