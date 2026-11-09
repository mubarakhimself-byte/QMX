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

A taken decision is written when it is decided, before any order it names can leave, and it is
never rewritten. One the host would not fill (a position already open, a size below the minimum
lot) lands a second ``signal`` row with outcome ``blocked``, linked to it by
``decision_row_id`` and carrying the reason code and the guard's words, beside the ``guard`` row
that said no. A block that raised lands one ``risk_event`` row per root-cause key, which is the
card's record.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_kinds.unit import BLOCK_CODE, BLOCK_REASON_FAMILY
from qmf.data.journal_writer import AppendOutcome, JournalWriter, WriterScope
from qmf.risk.journal import UNIT_FAULT, RiskEvent
from qml.compile import CompiledUnit
from qml.protocol.unit import CalibrationRow, DecisionRow, StateEvent
from qml.receipt import stored_row

from qmb._refuse import invalid
from qmb.execution.financing import CashEvent
from qmb.host.unit_handler import ControlFire, Fill, JournalRecord, Skip, UnitTrade, WouldHave

__all__ = [
    "BLOCK_REASON_FAMILY",
    "BRAKE_REASON_HEADS",
    "JournalPart",
    "JournalReport",
    "RunJournal",
]

WRITER_ROLE: Final[str] = "qmb"

BRAKE_REASON_HEADS: Final[tuple[str, ...]] = (
    "R this session, at or past the",
    "losing days in a row, at or past the limit of",
    "fills this session, above the limit of",
    "the account is down ",
    " drawdown limit",
)
"""The words each shipped halt answers with, as the head or tail that survives its numbers. A brake
publishes its own words, so a new one needs a code here or the row files as ``unlisted``."""

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
    ("kill switch", "kill_switch"),
    ("paused at", "kill_switch"),
    ("withdrawn", "kill_switch"),
    ("venue not ready", "health_stop"),
    ("cannot prove", "health_stop"),
    ("node journal", "health_stop"),
    ("venue refused", "health_stop"),
    ("venue answer unknown", "health_stop"),
    ("venue cannot", "health_stop"),
    ("widens the stop", "stop_wrong_side"),
    ("does not favour", "not_favoured"),
    ("cross-unit hook", "cross_unit_hook"),
    ("could not be built", "health_stop"),
    ("no unit holds", "health_stop"),
    ("does not hold this order's stop", "health_stop"),
    # A brake's own words: the row a live one suppresses names the slot, and each shipped halt's
    # words name the slot too, because which brake it was rides the row's code.
    ("halt slot: ", "halt_slot"),
    *((head, "halt_slot") for head in BRAKE_REASON_HEADS),
)
"""The reason code of each reason text QML's hosted unit, the handler and the trading node's
order path write, first match wins."""

UNLISTED_REASON: Final[str] = "unlisted"
"""A live journal's code for a text the table has none for. The row's ``detail`` keeps the words."""

_OUTCOME_CODES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "no_signal": "no_signal",
        "suppressed_warming": "warming_up",
        "suppressed_limit": "max_positions",
    }
)

_BLOCK_WORD: Final[re.Pattern[str]] = re.compile(
    f"{re.escape(BLOCK_REASON_FAMILY)}[a-z0-9][a-z0-9._-]*"
)


def _family_code(text: str) -> str | None:
    """A user block's own code, where its words carry one in the family it owns."""
    found = _BLOCK_WORD.search(text)
    if found is None:
        return None
    code = found.group(0)
    return code if BLOCK_CODE.match(code) is not None else None


def _fire_body(code: str, root: str, incident: str | None = None) -> dict[str, object]:
    """A risk event's body: what fired, the incident it belongs to, and the alert he reads.

    ``root`` is the root-cause key the one card is filed under, so two rows of one broken block
    make one card. ``event_id`` names the incident and not the row, so the same brake firing again
    after a restart files under one incident; a brake passes its own row, because two brakes can run
    one block. ``actionable`` is true because only his hand resumes a brake, and a row carries no
    deadline because nothing about it expires.
    """
    return {
        "code": code,
        "root": root,
        "event_id": f"{code}:{root if incident is None else incident}",
        "action": (
            "look at the block, then resume the unit when it is fixed"
            if code == UNIT_FAULT
            else "look at the brake, then resume it when its cause is gone"
        ),
        "actionable": True,
    }


def _reason_code(outcome: str, text: str) -> str | None:
    """The closed-list code for a decision's reason text, or None when the list has none. A block
    that names its own code in ``BLOCK_REASON_FAMILY`` answers here without a table row."""
    return (
        next((code for words, code in _REASON_WORDS if words in text), None)
        or _family_code(text)
        or _OUTCOME_CODES.get(outcome)
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
class _ReplayClock:
    """The writer's clock in a replay: the slice instant, so rows partition by bar month."""

    now: int = 0

    def __call__(self) -> int:
        return self.now


class RunJournal:
    """The journal port of one run: the handler appends, the runner sets the slice instant."""

    def __init__(
        self,
        writer: JournalWriter,
        clock: _ReplayClock,
        compiled: CompiledUnit,
        run_id: str,
        account: str | None = None,
    ) -> None:
        self._writer = writer
        self._clock = clock
        self._compiled = compiled
        self._run_id = run_id
        self._account = account
        self._live = account is not None
        self._venues = {m.market_id: r.venue for m, r in compiled.plan.markets}
        self._pins = {
            (side.side.value, binding.name): binding.pin
            for side in compiled.plan.sides
            for slot in side.slots
            for binding in slot.bindings
        }
        self._ordinal = 0
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

    @classmethod
    def open_live(
        cls,
        root: Path,
        compiled: CompiledUnit,
        *,
        scope_id: str,
        world: JournalWorld,
        machine: str,
        role: str,
        build: str,
        boot_epoch_id: str,
        account: str,
    ) -> Result[RunJournal]:
        """A trading host's unit journal: one fsynced line under ``root`` per row, as it is
        made, in the host's own world (the trading node, Part C slice C-12a). ``scope_id`` is
        the deployment id; the rows keep the shapes a QMB run writes and name ``account``. A
        text with no code costs a label, never the journal, and a row the writer refuses
        leaves the later rows still tried, with ``write_failure`` set."""
        scope = WriterScope(JournalStream.UNIT, compiled.unit.unit_id, world, machine, role, build)
        clock = _ReplayClock()
        writer = JournalWriter.open(root, scope, clock=clock, boot_epoch_id=boot_epoch_id)
        if is_refusal(writer):
            return writer
        return Ok(cls(writer.value, clock, compiled, scope_id, account))

    @property
    def write_failure(self) -> TypedRefusal | None:
        """The last row the writer refused, or None while every row has landed."""
        return self._refused

    def at(self, instant: Instant) -> None:
        """The replay instant every row until the next call is written at."""
        self._clock.now = instant.value_ns
        self._ordinal = 0

    def append(self, record: JournalRecord, /) -> None:
        match record:
            case DecisionRow():
                self._decision(replace(record, written_before_send=True))
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
            case RiskEvent():
                self._risk_event(record)
            case ControlFire():
                self._control_fire(record)
            case WouldHave():
                self._would_have(record)

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
        """Finish the partition files, or the refusal a row met on the way."""
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
            account=self._account,
            run_id=self._run_id,
        )

    def _write(self, kind: str, body: Mapping[str, object], facts: RowFacts) -> None:
        if self._refused is not None and not self._live:
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
        """One decision row, written once, here, before any order it names can leave.

        AD-9's "One row": both chains append to one trail, and the row is journalled after the
        last link and before any order leaves, with every input stored so it replays alone. The
        row therefore lands now and not at its fill: a send that raises must leave the row that
        would have explained the size, and the ``fill`` row that follows is what says what the
        venue took.
        """
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
            "detail": row.reason,
            "readings_used": readings,
            **stored_row(row),
        }
        code = _reason_code(row.outcome, row.reason)
        if code is None and row.outcome == "skipped":
            code = self._unlisted(row.row_id, row.reason)
            if code is None:
                return
        if code is not None:
            body["reason"] = code
        self._write("signal", body, self._facts(row.market_id))

    def _unlisted(self, row_id: str, text: str) -> str | None:
        """The code of a text the table has none for. A live journal answers ``unlisted``. A
        QMB run answers None and fails at ``close()``, because that protects evidence."""
        if self._live:
            return UNLISTED_REASON
        if self._refused is None:
            self._refused = invalid(
                "reason",
                "a decision's reason has no code in the journal's closed list",
                row_id=row_id,
                text=text,
            )
        return None

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
        """The guard row that says why a decided entry never filled. The decision's own row is
        already written and stays as the unit decided it; this row is what refused it."""
        code = _reason_code("blocked", skip.reason) or self._unlisted(
            skip.decision_row_id, skip.reason
        )
        if code is None:
            return
        key = f"guard:{skip.decision_row_id}"
        if key in self._once:
            self._repeats += 1
            return
        self._once.add(key)
        blocked: dict[str, object] = {
            "row_id": f"{skip.decision_row_id}/blocked",
            "instant": skip.instant.value_ns,
            "market_id": skip.market_id,
            "outcome": "blocked",
            "reason": code,
            "detail": skip.reason,
            "decision_row_id": skip.decision_row_id,
            "residue_r": str(skip.residue_r),
        }
        self._write("signal", blocked, self._facts(skip.market_id))
        guard: dict[str, object] = {
            "decision_row_id": skip.decision_row_id,
            "instant": skip.instant.value_ns,
            "verdict": "blocked",
            "reason": code,
            "detail": skip.reason,
            "residue_r": str(skip.residue_r),
        }
        self._write("guard", guard, self._facts(skip.market_id))

    def _risk_event(self, event: RiskEvent) -> None:
        """The code that fired and the root cause its one card is filed under (AD-23).

        The alert fields are derived here rather than carried, so every producer of the kind files
        the same shape: a fault's row and a brake's row both say what happened, what he does about
        it, and that it is his to act on. A fault names no deadline, because nothing expires.
        """
        self._write("risk_event", _fire_body(event.code, event.root), self._facts(None))

    def _control_fire(self, fire: ControlFire) -> None:
        """A brake that fired for real: which row, which block, what it ran and why (AD-12)."""
        body = _fire_body(fire.code, fire.root, fire.row)
        body |= {"row": fire.row, "pin": fire.pin, "verb": fire.verb, "detail": fire.reason}
        self._write("risk_event", body, self._facts(None))

    def _would_have(self, row: WouldHave) -> None:
        """The entry a brake would have refused, or did, with the share of them recorded (R1)."""
        code = _reason_code("blocked", row.reason) or self._unlisted(
            row.decision_row_id, row.reason
        )
        if code is None:
            return
        body: dict[str, object] = {
            "row": row.row,
            "decision_row_id": row.decision_row_id,
            "code": row.code,
            "reason": code,
            "propensity": f"{row.propensity.numerator}/{row.propensity.denominator}",
            "verb": row.verb,
            "detail": row.reason,
        }
        if row.market_id is not None:
            body["market_id"] = row.market_id
        if row.side is not None:
            body["side"] = row.side
        self._write("would_have", body, self._facts(row.market_id))

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
        # The two stamps RC-07 put on the close: the account-currency rate this row's money
        # converts by, exact as ``n/d``, and how old that read was in seconds. Labelled, so a
        # reader converts money without reading a rate. A position adopted after a restart
        # carries no rate, and the row omits the key rather than claim one.
        if trade.rate is not None:
            body["rate"] = f"{trade.rate.numerator}/{trade.rate.denominator}"
        body["rate_age_s"] = f"{trade.rate_age_s:f}"
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
