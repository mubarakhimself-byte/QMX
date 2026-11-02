"""A QMB run's unit journal, written through the journal writer's bundle mode (Part B slice B9).

Every record the run's unit and its handler make becomes one typed row of the unit journal
(Level 0 AD-27): each decision is one ``signal`` row with the value, source and version of
every reading the unit computed (MIS-10, JR-04), and the run adds its ``calibration``,
``state``, ``guard``, ``fill``, ``trade``, ``cash`` and ``data_event`` rows. A trade that a gap
took past its stop carries ``gap_through_stop`` (RS-13), and each swap, financing, funding,
dividend or commission line is one ``cash`` row (B10). The rows land as partition
files under the run's output folder, and the job hands them to the core as the result's
``journal/*`` blobs, so a run's journal is one Library record.

A row's record id is its own decision row id wherever the writer has one (R1-B-10): a
``signal`` or ``calibration`` row is the unit's ``row_id``, a ``fill`` its decision row id and
fill kind, a ``trade`` the fill that closed it. So a slice written again repeats every id, and
the writer drops the repeat. ``guard`` and ``data_event`` rows carry sequence ids, so this
journal keeps one per decision row id and one per gap.

A taken decision waits for its fill: a filled one is written ``taken``, and one the host
would not fill (a position already open, a size below the minimum lot) is written
``blocked`` with its reason code, beside the ``guard`` row that said no.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import AppendOutcome, JournalWriter, WriterScope
from qml.compile import CompiledUnit
from qml.protocol.unit import CalibrationRow, DecisionRow, StateEvent

from qmb._refuse import invalid
from qmb.execution.financing import CashEvent
from qmb.host.unit_handler import Fill, JournalRecord, Skip, UnitTrade

__all__ = ["JournalPart", "JournalReport", "RunJournal"]

WRITER_ROLE: Final[str] = "qmb"

_REASON_WORDS: Final[tuple[tuple[str, str], ...]] = (
    ("minimum lot", "below_min_lot"),
    ("largest order", "above_max_lot"),
    ("a position is open", "max_positions"),
    ("warming up", "warming_up"),
    ("not on the loss side", "stop_wrong_side"),
    ("no market entry order", "no_entry_order"),
    ("has no level yet", "reading_absent"),
    ("no account facts", "reading_absent"),
    ("the sizer answered nothing", "reading_absent"),
    ("sizer: ", "sizer_skip"),
)
"""The reason code of each reason text QML's hosted unit and the handler write, first match wins."""

_OUTCOME_CODES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "no_signal": "no_signal",
        "suppressed_warming": "warming_up",
        "suppressed_limit": "max_positions",
    }
)


def _reason_code(outcome: str, text: str) -> str | None:
    """The closed-list code for a decision's reason text, or None when the list has none."""
    return next((code for words, code in _REASON_WORDS if words in text), None) or (
        _OUTCOME_CODES.get(outcome)
    )


@dataclass(frozen=True, slots=True)
class JournalPart:
    """One partition file the writer finished: one kind's rows for one month."""

    kind: str
    month: str
    path: Path
    rows: int


@dataclass(frozen=True, slots=True)
class JournalReport:
    parts: tuple[JournalPart, ...]
    rows: Mapping[str, int]
    """Rows written, by kind."""
    repeats: int
    """Rows offered again under an id already written, so not written twice."""
    warnings: tuple[Mapping[str, object], ...]
    """``determinism_break``: an id offered again with another body, kept out."""


@dataclass
class _Pending:
    body: dict[str, object]
    facts: RowFacts


@dataclass
class _ReplayClock:
    """The writer's clock in a replay: the slice instant, so rows partition by bar month."""

    now: int = 0

    def __call__(self) -> int:
        return self.now


class RunJournal:
    """The journal port of one run: the handler appends, the runner sets the slice instant."""

    def __init__(
        self, writer: JournalWriter, clock: _ReplayClock, compiled: CompiledUnit, run_id: str
    ) -> None:
        self._writer = writer
        self._clock = clock
        self._compiled = compiled
        self._run_id = run_id
        self._venues = {m.market_id: r.venue for m, r in compiled.plan.markets}
        self._pins = {
            (side.side.value, binding.name): binding.pin
            for side in compiled.plan.sides
            for slot in side.slots
            for binding in slot.bindings
        }
        self._ordinal = 0
        self._pending: dict[str, _Pending] = {}
        self._deals: dict[tuple[str, int, str], str] = {}
        self._once: set[str] = set()
        self._rows: dict[str, int] = {}
        self._repeats = 0
        self._warnings: list[Mapping[str, object]] = []
        self._refused: TypedRefusal | None = None

    @classmethod
    def open(
        cls, out_dir: Path, compiled: CompiledUnit, *, run_id: str, machine: str, build: str
    ) -> Result[RunJournal]:
        """A run's journal whose partition files land under ``out_dir`` when it closes."""
        scope = WriterScope(
            JournalStream.UNIT,
            compiled.unit.unit_id,
            JournalWorld.BACKTEST,
            machine,
            WRITER_ROLE,
            build,
        )
        clock = _ReplayClock()
        writer = JournalWriter.open_bundle(out_dir, scope, clock=clock)
        if is_refusal(writer):
            return writer
        return Ok(cls(writer.value, clock, compiled, run_id))

    def at(self, instant: Instant) -> None:
        """The replay instant every row until the next call is written at."""
        self._clock.now = instant.value_ns
        self._ordinal = 0

    def append(self, record: JournalRecord, /) -> None:
        match record:
            case DecisionRow():
                self._decision(record)
            case CalibrationRow():
                self._calibration(record)
            case StateEvent():
                self._state(record)
            case Fill():
                self._fill(record)
            case Skip():
                self._skip(record)
            case UnitTrade():
                self._trade(record)
            case CashEvent():
                self._cash(record)

    def data_gap(self, market_id: str, after: Instant, before: Instant, bars_missing: int) -> None:
        """Bars the unit's stream did not hold between two bars it did (QB-18)."""
        key = f"gap:{market_id}:{after.value_ns}"
        if key in self._once:
            self._repeats += 1
            return
        self._once.add(key)
        body: dict[str, object] = {
            "event": "gap",
            "market_id": market_id,
            "after": after.value_ns,
            "before": before.value_ns,
            "bars_missing": bars_missing,
        }
        self._write("data_event", body, self._facts(market_id))

    def close(self) -> Result[JournalReport]:
        """Write decisions still waiting for a fill as taken, then finish the partition files."""
        for row_id in list(self._pending):
            pending = self._pending.pop(row_id)
            self._write("signal", pending.body, pending.facts)
        files = self._writer.close()
        if self._refused is not None:
            return self._refused
        if is_refusal(files):
            return files
        parts = tuple(
            JournalPart(f.key.split("/")[2], f.key.rsplit("/", 1)[1], f.path, f.rows)
            for f in files.value
        )
        return Ok(JournalReport(parts, dict(self._rows), self._repeats, tuple(self._warnings)))

    def _facts(self, market_id: str | None) -> RowFacts:
        return RowFacts(
            ts_recv=self._clock.now,
            clock_ok=True,
            unit_id=self._compiled.unit.unit_id,
            unit_version=self._compiled.document_fingerprint.value,
            market_id=market_id,
            venue=None if market_id is None else self._venues.get(market_id),
            run_id=self._run_id,
        )

    def _write(self, kind: str, body: Mapping[str, object], facts: RowFacts) -> None:
        if self._refused is not None:
            return
        receipt = self._writer.append(kind, body, facts)
        if is_refusal(receipt):
            self._refused = receipt
            return
        match receipt.value.outcome:
            case AppendOutcome.APPENDED:
                self._rows[kind] = self._rows.get(kind, 0) + 1
            case AppendOutcome.REPEAT:
                self._repeats += 1
            case AppendOutcome.DETERMINISM_BREAK:
                self._warnings.append(receipt.value.warning or {})

    def _decision(self, row: DecisionRow) -> None:
        side = row.side.value
        readings: list[object] = [r for r in row.readings_used if isinstance(r, Mapping)]
        for out in row.slot_trail:
            pin = self._pins.get((side, out.binding))
            if pin is None or out.output is None:
                continue
            block, _, version = pin.rpartition("@")
            readings.append(
                {
                    "reading": f"{out.slot}.{out.binding}",
                    "block": block,
                    "version": version,
                    "value": out.output,
                    "source": "unit",
                    "knowable_at": row.instant.value_ns,
                }
            )
        body: dict[str, object] = {
            "row_id": row.row_id,
            "instant": row.instant.value_ns,
            "market_id": row.market_id,
            "side": side,
            "outcome": row.outcome,
            "detail": row.reason,
            "readings_used": readings,
            "numbers_in_force": {name: str(v) for name, v in row.numbers_in_force.items()},
        }
        code = _reason_code(row.outcome, row.reason)
        if code is not None:
            body["reason"] = code
        elif row.outcome == "skipped":
            self._refuse(row.row_id, row.reason)
            return
        facts = self._facts(row.market_id)
        if row.outcome == "taken":
            self._pending[row.row_id] = _Pending(body, facts)
            return
        self._write("signal", body, facts)

    def _refuse(self, row_id: str, text: str) -> None:
        if self._refused is None:
            self._refused = invalid(
                "reason",
                "a decision's reason has no code in the journal's closed list",
                row_id=row_id,
                text=text,
            )

    def _calibration(self, row: CalibrationRow) -> None:
        body: dict[str, object] = {
            "row_id": row.row_id,
            "number": row.number,
            "old": str(row.old),
            "new": str(row.new),
            "rule": row.rule,
            "read_trades": {
                "from_trade_id": row.from_trade_id,
                "to_trade_id": row.to_trade_id,
                "count": row.count,
            },
            "statistic": dict(row.statistic),
            "watermark": row.watermark.value_ns,
        }
        self._write("calibration", body, self._facts(None))

    def _state(self, event: StateEvent) -> None:
        body: dict[str, object] = {
            "event": event.kind,
            "scope_id": self._run_id,
            "instant": self._clock.now,
            "ordinal": self._ordinal,
            "market_id": event.market_id,
        }
        if event.reason:
            body["reason"] = event.reason
        self._ordinal += 1
        self._write("state", body, self._facts(event.market_id))

    def _fill(self, fill: Fill) -> None:
        pending = self._pending.pop(fill.decision_row_id, None)
        if pending is not None:
            self._write("signal", pending.body, pending.facts)
        deal = f"{fill.decision_row_id}.{fill.kind.value}"
        self._deals[(fill.position_id, fill.instant.value_ns, fill.kind.value)] = deal
        body: dict[str, object] = {
            "deal_id": deal,
            "decision_row_id": fill.decision_row_id,
            "instant": fill.instant.value_ns,
            "position_id": fill.position_id,
            "kind": fill.kind.value,
            "side": fill.side.value,
            "price": str(fill.price),
            "quantity": str(fill.quantity),
            "residue_r": str(fill.residue_r),
        }
        if fill.receipt_quantity is not None:
            body["receipt_quantity"] = str(fill.receipt_quantity)
        self._write("fill", body, self._facts(fill.market_id))

    def _skip(self, skip: Skip) -> None:
        code = _reason_code("blocked", skip.reason)
        if code is None:
            self._refuse(skip.decision_row_id, skip.reason)
            return
        pending = self._pending.pop(skip.decision_row_id, None)
        if pending is not None:
            body = pending.body | {"outcome": "blocked", "reason": code, "detail": skip.reason}
            self._write("signal", body, pending.facts)
        key = f"guard:{skip.decision_row_id}"
        if key in self._once:
            self._repeats += 1
            return
        self._once.add(key)
        guard: dict[str, object] = {
            "decision_row_id": skip.decision_row_id,
            "instant": skip.instant.value_ns,
            "verdict": "blocked",
            "reason": code,
            "detail": skip.reason,
            "residue_r": str(skip.residue_r),
        }
        self._write("guard", guard, self._facts(skip.market_id))

    def _trade(self, trade: UnitTrade) -> None:
        deal = self._deals.get(
            (trade.trade_id, trade.closed_at.value_ns, trade.exit_kind.value),
            f"{trade.trade_id}.{trade.exit_kind.value}.{trade.closed_at.value_ns}",
        )
        body: dict[str, object] = {
            "closing_deal_id": deal,
            "trade_id": trade.trade_id,
            "side": trade.side.value,
            "opened_at": trade.opened_at.value_ns,
            "closed_at": trade.closed_at.value_ns,
            "entry_price": str(trade.entry_price),
            "exit_price": str(trade.exit_price),
            "stop": str(trade.stop),
            "quantity": str(trade.quantity),
            "exit_kind": trade.exit_kind.value,
            "money": str(trade.money),
            "r": str(trade.r),
        }
        if trade.gap_through_stop:
            body["gap_through_stop"] = True
        self._write("trade", body, self._facts(trade.market_id))

    def _cash(self, event: CashEvent) -> None:
        body: dict[str, object] = {
            "deal_id": f"{event.position_id}.{event.line}",
            "position_id": event.position_id,
            "instant": event.instant.value_ns,
            "kind": event.kind.value,
            "money": str(event.money),
            "detail": event.detail,
        }
        self._write("cash", body, self._facts(event.market_id))
