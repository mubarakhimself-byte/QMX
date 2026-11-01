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
``run_slice`` one bar instant at a time. The result carries every trade in money and R, every
fill against its sizer receipt, and the ``zero_trades`` label when nothing closed. Given a
``RunJournal``, every row the run makes is also written to the unit journal, with each slice's
instant and every hole in a market's bars (B9).
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, cast

from qmf.core.chrono import Instant
from qmf.core.identity import AccountRole, VenueId
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.risk.paper import ExecutionTarget
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import (
    OHLC,
    MotionSwitch,
    OwnPosition,
    QuoteBar,
    TraceLevel,
    construct_unit,
)

from qmb._refuse import invalid, policy
from qmb.host.unit_handler import (
    ExecutionPort,
    Fill,
    JournalRecord,
    ListJournal,
    NextOpenExecution,
    UnitSliceHandler,
    UnitTrade,
)
from qmb.results.journal import RunJournal
from qmb.runloop.loop import DeclaredStream, RestingIntent, SliceObservation, StreamSet, run_slice

__all__ = [
    "ZERO_TRADES",
    "LoadedUnit",
    "UnitRunRequest",
    "UnitRunResult",
    "load_unit_folder",
    "parse_unit_run_request",
    "run_loaded",
    "run_unit",
]

ZERO_TRADES: Final[str] = "zero_trades"
_NS_PER_MS: Final[int] = 1_000_000


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
    """A run folder's unit compiled, its block sources and its bars by market id."""

    compiled: CompiledUnit
    sources: Mapping[str, bytes]
    records: Mapping[str, InstrumentRecord]
    bars: Mapping[str, tuple[QuoteBar, ...]]


@dataclass(frozen=True, slots=True)
class UnitRunResult:
    run_id: str
    compiled_fingerprint: str
    trades: tuple[UnitTrade, ...]
    fills: tuple[Fill, ...]
    journal: tuple[JournalRecord, ...]
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


def _side(path: Path) -> Result[dict[int, OHLC]]:
    if not path.is_file():
        return invalid("bars", "a market's bars are a bid and an ask file", missing=str(path))
    rows: dict[int, OHLC] = {}
    try:
        for row in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))):
            rows[int(row["timestamp"])] = OHLC(
                Decimal(row["open"]),
                Decimal(row["high"]),
                Decimal(row["low"]),
                Decimal(row["close"]),
            )
    except (KeyError, ValueError, InvalidOperation) as error:
        return invalid(
            "bars",
            "a bar row is timestamp, open, high, low, close",
            file=str(path),
            error=str(error),
        )
    return Ok(rows)


def _bars(folder: Path, market: str, seconds: int) -> Result[tuple[QuoteBar, ...]]:
    bid = _side(folder / "bars" / market / "bid.csv")
    if is_refusal(bid):
        return bid
    ask = _side(folder / "bars" / market / "ask.csv")
    if is_refusal(ask):
        return ask
    length_ns = seconds * 1_000_000_000
    return Ok(
        tuple(
            QuoteBar(Instant(ms * _NS_PER_MS + length_ns), bid.value[ms], ask.value[ms])
            for ms in sorted(bid.value.keys() & ask.value.keys())
        )
    )


def load_unit_folder(folder: Path) -> Result[LoadedUnit]:
    """Compile the folder's unit from its pinned blocks and read its markets' bars."""
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
    bars: dict[str, tuple[QuoteBar, ...]] = {}
    for market, _ in compiled.plan.markets:
        read = _bars(folder, market.market_id, seconds)
        if is_refusal(read):
            return read
        bars[market.market_id] = read.value
    unit_records = {m.market_id: record for m, record in compiled.plan.markets}
    return Ok(LoadedUnit(compiled, sources, unit_records, bars))


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
    """Trade a loaded unit; ``journal`` also receives every row, and is left open."""
    compiled = loaded.compiled
    if compiled.compiled_fingerprint.value != request.compiled_fingerprint:
        return policy(
            "compiled_fingerprint",
            "the unit compiled to another fingerprint than the run pinned, so it does not start",
            pinned=request.compiled_fingerprint,
            compiled=compiled.compiled_fingerprint.value,
        )
    kept = ListJournal()
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
        bars={m: {b.knowable_at.value_ns: b for b in s} for m, s in loaded.bars.items()},
        opened_by=compiled.compiled_fingerprint,
        equity=request.equity,
        execution=execution if execution is not None else NextOpenExecution(),
        journal=kept if journal is None else _Both(kept, journal),
        seeded=seeded,
    )
    if is_refusal(handler):
        return handler
    seconds = _bar_seconds(compiled.plan.stream)
    if seconds is None:
        return invalid(
            "stream", "QMB replays minute, hour or day bars", stream=compiled.plan.stream
        )
    driven = _drive(handler.value, loaded.bars, seconds * 1_000_000_000, journal)
    if is_refusal(driven):
        return driven
    trades = handler.value.trades
    return Ok(
        UnitRunResult(
            run_id=request.run_id,
            compiled_fingerprint=compiled.compiled_fingerprint.value,
            trades=trades,
            fills=handler.value.fills,
            journal=tuple(kept.records),
            open_positions=handler.value.open_positions,
            net_money=sum((t.money for t in trades), Decimal(0)),
            total_r=sum((t.r for t in trades), Decimal(0)),
            labels=() if trades else (ZERO_TRADES,),
        )
    )


@dataclass(frozen=True, slots=True)
class _Both:
    kept: ListJournal
    run: RunJournal

    def append(self, record: JournalRecord, /) -> None:
        self.kept.append(record)
        self.run.append(record)


def _drive(
    handler: UnitSliceHandler,
    bars: Mapping[str, Sequence[QuoteBar]],
    bar_ns: int,
    journal: RunJournal | None,
) -> Result[None]:
    streams = StreamSet.try_create([DeclaredStream(market, market) for market in bars])
    if is_refusal(streams):
        return streams
    at: dict[int, list[str]] = {}
    for market, series in bars.items():
        for bar in series:
            at.setdefault(bar.knowable_at.value_ns, []).append(market)
    frontier: Instant | None = None
    resting: tuple[RestingIntent, ...] = ()
    last: dict[str, int] = {}
    for ns in sorted(at):
        if journal is not None:
            journal.at(Instant(ns))
            for market in at[ns]:
                before = last.get(market, ns)
                if (missing := (ns - before) // bar_ns - 1) > 0:
                    journal.data_gap(market, Instant(before), Instant(ns), missing)
                last[market] = ns
        observed = [SliceObservation(market, Instant(ns)) for market in at[ns]]
        outcome = run_slice(
            observed,
            stream_set=streams.value,
            current_frontier=frontier,
            handler=handler,
            resting=resting,
        )
        if is_refusal(outcome):
            return outcome
        frontier, resting = outcome.value.frontier, outcome.value.resting
    return Ok(None)
