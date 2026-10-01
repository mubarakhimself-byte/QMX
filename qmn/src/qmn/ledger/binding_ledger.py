"""Per-binding append-only exact-integer virtual ledger (TN-25; Story 26.4).

Each Book binding carries its own virtual-ledger record stream written by the
risk-domain writer ``(machine, risk role, binding)`` in the exact scaled-integer
domain at the account money exponent. Fills attributed through command identity
append here and fold the binding's virtual positions. Venue positions remain a
separate observation-derived fold (DEC-0210; FR-077). No float participates on
the money path.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Final, cast

from qmf.core import (
    Fingerprint,
    Instant,
    JournalSink,
    Money,
    Ok,
    Quantity,
    Result,
    is_refusal,
)
from qmf.risk.r_faces import RFaces

from qmn.ledger._refuse import clean_token, invalid, policy
from qmn.ledger.virtual import (
    AttributedFill,
    VirtualPosition,
    VirtualPositionStatus,
    guard_no_scale_in,
    mint_virtual_position,
    rebase_partial_entry,
)
from qmn.venue import SubmissionOutcome, SubmissionResult

__all__ = [
    "LEDGER_RECORD_KINDS",
    "BindingVirtualLedger",
    "EntryReservationEvent",
    "EntryReservationRecovery",
    "FoldFillResult",
    "LedgerRecord",
    "LedgerRecordKind",
    "refuse_float_money",
    "seed_binding_ledger",
    "sum_virtual_quantities",
]


class LedgerRecordKind(StrEnum):
    """Append-only virtual-ledger record kinds (TN-25)."""

    SEED = "seed"
    FILL = "fill"
    REALIZED = "realized"
    BOUNDARY = "boundary"
    MARK = "mark"


LEDGER_RECORD_KINDS: Final[tuple[LedgerRecordKind, ...]] = tuple(LedgerRecordKind)


@dataclass(frozen=True, slots=True)
class LedgerRecord:
    """One append-only exact scaled-integer ledger row."""

    kind: LedgerRecordKind
    binding_epoch: Fingerprint
    sequence: int
    recorded_at: Instant
    cash_delta: Money | None
    position_ref: Fingerprint | None
    command_identity: Fingerprint | None
    money_scale: int
    note: str | None = None

    def as_mapping(self) -> Mapping[str, object]:
        body: dict[str, object] = {
            "binding_epoch": self.binding_epoch.value,
            "kind": self.kind.value,
            "money_scale": self.money_scale,
            "recorded_at": self.recorded_at.fp1_identity(),
            "sequence": self.sequence,
        }
        if self.cash_delta is not None:
            body["cash_delta"] = self.cash_delta.fp1_identity()
        if self.position_ref is not None:
            body["position_ref"] = self.position_ref.value
        if self.command_identity is not None:
            body["command_identity"] = self.command_identity.value
        if self.note is not None:
            body["note"] = self.note
        return MappingProxyType(body)


@dataclass(frozen=True, slots=True)
class FoldFillResult:
    """Outcome of folding one attributed fill into the binding ledger."""

    record: LedgerRecord
    position: VirtualPosition
    created: bool
    scale_in_refused: bool = False


@dataclass(frozen=True, slots=True)
class EntryReservationEvent:
    """One committed entry reservation transition for restart recovery."""

    binding_epoch: Fingerprint
    sequence: int
    instrument: str
    command_identity: Fingerprint
    event: str
    outcome: str | None = None

    @classmethod
    def from_mapping(cls, payload: object) -> Result[EntryReservationEvent]:
        if not isinstance(payload, Mapping):
            return invalid("reservation_event", "persisted event is a mapping")
        source = cast("Mapping[object, object]", payload)
        if source.get("class") != "qmn-entry-reservation-event":
            return invalid(
                "reservation_event", "persisted event has the reservation event class"
            )
        binding = Fingerprint.try_create(source.get("binding_epoch"))
        identity = Fingerprint.try_create(source.get("command_identity"))
        if is_refusal(binding):
            return binding
        if is_refusal(identity):
            return identity
        sequence = source.get("sequence")
        instrument = clean_token(source.get("instrument"))
        event = clean_token(source.get("event"))
        outcome = source.get("outcome")
        format_version = source.get("format_version")
        if type(format_version) is not int or format_version != 1:
            return invalid("reservation_event", "persisted event format version 1 is required")
        if type(sequence) is not int or sequence < 1 or instrument is None or event is None:
            return invalid(
                "reservation_event", "persisted event has sequence, instrument, and kind"
            )
        if outcome is not None and not isinstance(outcome, str):
            return invalid("reservation_event", "optional outcome is a string")
        return Ok(
            cls(
                binding_epoch=binding.value,
                sequence=sequence,
                instrument=instrument,
                command_identity=identity.value,
                event=event,
                outcome=outcome,
            )
        )

    def as_mapping(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "binding_epoch": self.binding_epoch.value,
            "class": "qmn-entry-reservation-event",
            "command_identity": self.command_identity.value,
            "event": self.event,
            "instrument": self.instrument,
            "sequence": self.sequence,
            "format_version": 1,
        }
        if self.outcome is not None:
            payload["outcome"] = self.outcome
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class EntryReservationRecovery:
    """Complete committed prefix supplied by the journal's recovery reader.

    The composition adapter sets ``complete`` only when the underlying journal
    confirms no earlier/later segment is missing and its committed high-water
    equals the event count. This record does not itself discover journal state.
    """

    binding_epoch: Fingerprint
    events: tuple[EntryReservationEvent, ...]
    committed_high_water: int
    complete: bool


@dataclass
class BindingVirtualLedger:
    """Binding-scoped exact-integer virtual ledger plus virtual-position fold.

    Venue positions are never stored here. Money arithmetic uses :class:`Money`
    scaled integers at the declared account money exponent.
    """

    binding_epoch: Fingerprint
    currency: str
    money_scale: int
    seed: Money
    realized_cash: Money
    _records: list[LedgerRecord] = field(default_factory=list[LedgerRecord])
    _positions: dict[str, VirtualPosition] = field(default_factory=dict[str, VirtualPosition])
    _by_ref: dict[str, VirtualPosition] = field(default_factory=dict[str, VirtualPosition])
    _pending_entries: dict[str, Fingerprint] = field(default_factory=dict[str, Fingerprint])
    _reservation_journal: JournalSink[object] | None = None
    _reservation_sequence: int = 0
    _reservation_recovered: bool = False
    _reservation_uncertain: bool = False
    _sequence: int = 0

    @property
    def records(self) -> tuple[LedgerRecord, ...]:
        return tuple(self._records)

    @property
    def open_positions(self) -> tuple[VirtualPosition, ...]:
        return tuple(p for p in self._positions.values() if p.status is VirtualPositionStatus.OPEN)

    def position_snapshots(self) -> Mapping[str, tuple[str, Mapping[str, object]]]:
        """Public position identity snapshot for boundary-act invariants."""
        return MappingProxyType(
            {
                key: (pos.position_ref.value, MappingProxyType(pos.faces.fp1_identity()))
                for key, pos in self._positions.items()
            }
        )

    def has_open_virtual(self, instrument: object) -> bool:
        token = clean_token(instrument)
        if token is None:
            return False
        pos = self._positions.get(token)
        return pos is not None and pos.status is VirtualPositionStatus.OPEN

    def position_for(self, instrument: object) -> VirtualPosition | None:
        token = clean_token(instrument)
        if token is None:
            return None
        return self._positions.get(token)

    def position_by_ref(self, position_ref: object) -> VirtualPosition | None:
        if not isinstance(position_ref, Fingerprint):
            return None
        return self._by_ref.get(position_ref.value)

    def has_pending_entry(self, instrument: object) -> bool:
        token = clean_token(instrument)
        return token is not None and token in self._pending_entries

    def pending_entry_identity(self, instrument: object) -> Fingerprint | None:
        token = clean_token(instrument)
        return None if token is None else self._pending_entries.get(token)

    @property
    def reservation_admission_ready(self) -> bool:
        """True only after complete recovery with a clean durable append path."""
        return (
            self._reservation_journal is not None
            and self._reservation_recovered
            and not self._reservation_uncertain
        )

    def recover_entry_reservations(self, recovery: object) -> Result[None]:
        """Rebuild pending occupancy from a complete ordered journal projection."""
        if not isinstance(recovery, EntryReservationRecovery):
            return invalid(
                "reservation_recovery",
                "recovery requires the typed committed journal prefix from the composition adapter",
            )
        if (
            recovery.binding_epoch != self.binding_epoch
            or not recovery.complete
            or recovery.committed_high_water != len(recovery.events)
            or recovery.committed_high_water < self._reservation_sequence
        ):
            return policy(
                "reservation_recovery",
                "recovery is complete through the exact committed high-water for this binding",
            )
        pending: dict[str, Fingerprint] = {}
        last_sequence = 0
        for event in recovery.events:
            if event.binding_epoch != self.binding_epoch or event.sequence != last_sequence + 1:
                return policy(
                    "reservation_events",
                    "recovery events are contiguous and belong to this exact binding epoch",
                    sequence=event.sequence,
                )
            if event.event == "reserved":
                if event.instrument in pending:
                    return policy(
                        "reservation_events", "recovery cannot reserve an occupied instrument"
                    )
                pending[event.instrument] = event.command_identity
            elif event.event in {"accepted", "unknown"}:
                if pending.get(event.instrument) != event.command_identity:
                    return policy(
                        "reservation_events",
                        "submission outcome matches a pending reservation",
                    )
            elif event.event in {"released", "filled"}:
                if pending.get(event.instrument) != event.command_identity:
                    return policy(
                        "reservation_events", "terminal event matches a pending reservation"
                    )
                del pending[event.instrument]
            else:
                return invalid(
                    "reservation_events",
                    "event kind is reserved, accepted, unknown, released, or filled",
                )
            last_sequence = event.sequence
        self._pending_entries = pending
        self._reservation_sequence = last_sequence
        self._reservation_recovered = True
        self._reservation_uncertain = False
        return Ok(None)

    def _append_reservation_event(
        self,
        instrument: str,
        command_identity: Fingerprint,
        event: str,
        *,
        outcome: str | None = None,
    ) -> Result[None]:
        sink = self._reservation_journal
        if sink is None or not self._reservation_recovered or self._reservation_uncertain:
            return policy(
                "reservation_journal",
                "hosted reservations require complete recovery and a clean durable journal",
            )
        next_sequence = self._reservation_sequence + 1
        record = EntryReservationEvent(
            binding_epoch=self.binding_epoch,
            sequence=next_sequence,
            instrument=instrument,
            command_identity=command_identity,
            event=event,
            outcome=outcome,
        )
        appended = sink.append(record.as_mapping())
        if is_refusal(appended):
            self._reservation_uncertain = True
            return appended
        if appended.value.detail.get("complete") is False:
            self._reservation_uncertain = True
            return policy(
                "reservation_journal",
                "reservation journal did not confirm a complete durable append",
            )
        self._reservation_sequence = next_sequence
        return Ok(None)

    def reserve_entry(self, instrument: object, command_identity: object) -> Result[None]:
        """Reserve one entry until its fill or a definitive no-fill terminal."""
        token = clean_token(instrument)
        if token is None or not isinstance(command_identity, Fingerprint):
            return invalid(
                "entry_reservation", "reservation requires instrument and command identity"
            )
        if self.has_open_virtual(token) or token in self._pending_entries:
            return policy(
                "entry_reservation",
                "an open position or unresolved entry already occupies this binding/instrument",
                instrument=token,
            )
        appended = self._append_reservation_event(token, command_identity, "reserved")
        if is_refusal(appended):
            return appended
        self._pending_entries[token] = command_identity
        return Ok(None)

    def reserve_entries(self, entries: object) -> Result[None]:
        """Reserve a fully built batch after validating it without side effects."""
        if isinstance(entries, (str, bytes)) or not isinstance(entries, Sequence):
            return invalid("entries", "batch reservations are an ordered sequence")
        parsed: list[tuple[str, Fingerprint]] = []
        seen: set[str] = set()
        for raw in cast("Sequence[object]", entries):
            pair = cast("tuple[object, ...]", raw) if isinstance(raw, tuple) else ()
            if (
                len(pair) != 2
                or not isinstance(pair[1], Fingerprint)
            ):
                return invalid(
                    "entries", "each reservation is an instrument and command fingerprint"
                )
            token = clean_token(pair[0])
            identity = pair[1]
            if (
                token is None
                or token in seen
                or self.has_open_virtual(token)
                or token in self._pending_entries
            ):
                return policy(
                    "entries",
                    "the binding ledger admits at most one open or pending entry per instrument",
                    instrument=token,
                )
            parsed.append((token, identity))
            seen.add(token)
        for token, identity in parsed:
            appended = self._append_reservation_event(token, identity, "reserved")
            if is_refusal(appended):
                return appended
            self._pending_entries[token] = identity
        return Ok(None)

    def observe_submission_outcome(
        self, instrument: object, command_identity: object, submission: object
    ) -> Result[None]:
        """Apply only typed four-outcome semantics to an entry reservation.

        UNKNOWN and accepted remain reserved. A definitive venue rejection or
        local denial releases; fills release through ``fold_fill`` instead.
        """
        if not isinstance(submission, SubmissionResult):
            return invalid(
                "submission_outcome",
                "entry reservation consumes a typed SubmissionResult",
            )
        if submission.command_fp1 != command_identity:
            return policy(
                "entry_reservation",
                "submission result identity must match the reserved command",
            )
        if submission.outcome not in {
            SubmissionOutcome.ACCEPTED_BY_VENUE,
            SubmissionOutcome.REJECTED_BY_VENUE,
            SubmissionOutcome.DENIED_LOCALLY,
            SubmissionOutcome.UNKNOWN,
        }:
            return invalid(
                "submission_outcome",
                "entry reservation consumes the single-command four-outcome law",
            )
        if submission.outcome in {
            SubmissionOutcome.REJECTED_BY_VENUE,
            SubmissionOutcome.DENIED_LOCALLY,
        }:
            return self._release_entry(instrument, command_identity, terminal=True)
        token = clean_token(instrument)
        if (
            token is None
            or not isinstance(command_identity, Fingerprint)
            or self._pending_entries.get(token) != command_identity
        ):
            return policy("entry_reservation", "submission outcome must match the pending command")
        event_kind = (
            "accepted"
            if submission.outcome is SubmissionOutcome.ACCEPTED_BY_VENUE
            else "unknown"
        )
        appended = self._append_reservation_event(
            token,
            command_identity,
            event_kind,
            outcome=submission.outcome.value,
        )
        if is_refusal(appended):
            return appended
        return Ok(None)

    def _release_entry(
        self, instrument: object, command_identity: object, *, terminal: bool
    ) -> Result[None]:
        token = clean_token(instrument)
        if token is None or not isinstance(command_identity, Fingerprint):
            return invalid(
                "entry_reservation", "release requires instrument and command identity"
            )
        if self._pending_entries.get(token) != command_identity:
            return policy(
                "entry_reservation",
                "outcome does not match the pending command",
                terminal=terminal,
            )
        appended = self._append_reservation_event(
            token,
            command_identity,
            "released",
            outcome="unsubmitted" if not terminal else "definitive-no-fill",
        )
        if is_refusal(appended):
            return appended
        del self._pending_entries[token]
        return Ok(None)

    def book_capital(self) -> Money:
        """Period-open capital excluding unrealized P&L — sizing input only."""
        return self.realized_cash

    def virtual_quantity(self, instrument: object) -> Quantity | None:
        pos = self.position_for(instrument)
        if pos is None or pos.status is not VirtualPositionStatus.OPEN:
            return None
        return pos.filled_quantity

    def refuse_entry_if_open(self, instrument: object) -> Result[None]:
        """No-scale-in guard over virtual positions (TN-25 / TN-6)."""
        return guard_no_scale_in(has_open_virtual_position=self.has_open_virtual(instrument))

    def fold_fill(
        self,
        *,
        fill: object,
        bot_id: object,
        admission_identity: object,
        faces: object,
        admitted_quantity: object,
        entry_terminal: object = False,
    ) -> Result[FoldFillResult]:
        """Append one attributed fill and fold the virtual position (Story 26.4).

        Preserves admission identity and frozen R faces. An entry on an
        instrument that already holds an open virtual position refuses as
        no-scale-in. A partial ENTRY at first terminal state re-bases
        ``original_risk_amount`` exactly once.
        """
        if not isinstance(fill, AttributedFill):
            return invalid(
                "fill",
                "the risk-domain writer folds an AttributedFill joined by command identity",
                given=repr(fill),
            )
        pending = self._pending_entries.get(fill.instrument)
        if pending is not None and pending != fill.command_identity:
            return policy(
                "entry_reservation",
                "attributed fill must match the unresolved entry command identity",
                instrument=fill.instrument,
            )
        if fill.realized_cash is not None:
            refused = refuse_float_money(fill.realized_cash)
            if is_refusal(refused):
                return refused
            if fill.realized_cash.currency != self.currency:
                return invalid(
                    "realized_cash",
                    "fill cash must match the binding ledger currency",
                    ledger=self.currency,
                    fill=fill.realized_cash.currency,
                )
            if fill.realized_cash.scale != self.money_scale:
                return invalid(
                    "realized_cash",
                    "fill cash must use the declared account money scale",
                    ledger_scale=self.money_scale,
                    fill_scale=fill.realized_cash.scale,
                )

        existing = self._positions.get(fill.instrument)
        created = False
        position: VirtualPosition

        if existing is None or existing.status is VirtualPositionStatus.CLOSED:
            if not isinstance(faces, RFaces):
                return invalid("faces", "admission carries frozen RFaces", given=repr(faces))
            minted = mint_virtual_position(
                binding_epoch=self.binding_epoch,
                instrument=fill.instrument,
                bot_id=bot_id,
                admission_identity=admission_identity,
                command_identity=fill.command_identity,
                faces=faces,
                admitted_quantity=admitted_quantity,
                filled_quantity=fill.quantity,
                status=VirtualPositionStatus.OPEN,
            )
            if is_refusal(minted):
                return minted
            position = minted.value
            created = True
        else:
            # Open virtual position on this instrument → no scale-in.
            blocked = guard_no_scale_in(has_open_virtual_position=True)
            if is_refusal(blocked):
                return blocked
            position = existing

        if entry_terminal is True and not position.rebased:
            admitted_frac = position.admitted_quantity.as_fraction()
            filled_frac = fill.quantity.as_fraction()
            if 0 < filled_frac < admitted_frac:
                rebased = rebase_partial_entry(
                    position, filled_quantity=fill.quantity, terminal=True
                )
                if is_refusal(rebased):
                    return rebased
                position = rebased.value[0]

        if fill.realized_cash is not None:
            updated_cash = self.realized_cash.add(fill.realized_cash)
            if is_refusal(updated_cash):
                return updated_cash
            self.realized_cash = updated_cash.value

        self._sequence += 1
        record = LedgerRecord(
            kind=LedgerRecordKind.FILL,
            binding_epoch=self.binding_epoch,
            sequence=self._sequence,
            recorded_at=fill.recorded_at,
            cash_delta=fill.realized_cash,
            position_ref=position.position_ref,
            command_identity=fill.command_identity,
            money_scale=self.money_scale,
        )
        self._records.append(record)
        self._positions[position.instrument] = position
        self._by_ref[position.position_ref.value] = position
        if pending == fill.command_identity:
            appended = self._append_reservation_event(
                fill.instrument, fill.command_identity, "filled", outcome="attributed-fill"
            )
            if is_refusal(appended):
                return appended
            self._pending_entries.pop(fill.instrument, None)
        return Ok(
            FoldFillResult(
                record=record,
                position=position,
                created=created,
            )
        )

    def close_position(
        self,
        *,
        instrument: object,
        realized_cash: object,
        recorded_at: object,
        command_identity: object,
    ) -> Result[LedgerRecord]:
        """Close an open virtual position and append a realized cash row."""
        pos = self.position_for(instrument)
        if pos is None or pos.status is not VirtualPositionStatus.OPEN:
            return invalid(
                "instrument",
                "close requires an open virtual position on the instrument",
                given=repr(instrument),
            )
        if not isinstance(realized_cash, Money):
            return invalid(
                "realized_cash",
                "realized cash is Money at the account scale",
                given=repr(realized_cash),
            )
        refused = refuse_float_money(realized_cash)
        if is_refusal(refused):
            return refused
        if realized_cash.currency != self.currency or realized_cash.scale != self.money_scale:
            return invalid(
                "realized_cash",
                "realized cash must match ledger currency and money scale",
            )
        if not isinstance(recorded_at, Instant):
            return invalid("recorded_at", "close carries an Instant", given=repr(recorded_at))
        if not isinstance(command_identity, Fingerprint):
            return invalid(
                "command_identity",
                "close joins by declared command identity",
                given=repr(command_identity),
            )
        updated_cash = self.realized_cash.add(realized_cash)
        if is_refusal(updated_cash):
            return updated_cash
        self.realized_cash = updated_cash.value
        closed = VirtualPosition(
            position_ref=pos.position_ref,
            binding_epoch=pos.binding_epoch,
            instrument=pos.instrument,
            bot_id=pos.bot_id,
            admission_identity=pos.admission_identity,
            command_identity=pos.command_identity,
            faces=pos.faces,
            admission_faces=pos.admission_faces,
            admitted_quantity=pos.admitted_quantity,
            filled_quantity=pos.filled_quantity,
            status=VirtualPositionStatus.CLOSED,
            rebased=pos.rebased,
            admission_plan_edge=pos.admission_plan_edge,
            execution_quality=pos.execution_quality,
        )
        self._positions[closed.instrument] = closed
        self._by_ref[closed.position_ref.value] = closed
        self._sequence += 1
        record = LedgerRecord(
            kind=LedgerRecordKind.REALIZED,
            binding_epoch=self.binding_epoch,
            sequence=self._sequence,
            recorded_at=recorded_at,
            cash_delta=realized_cash,
            position_ref=closed.position_ref,
            command_identity=command_identity,
            money_scale=self.money_scale,
        )
        self._records.append(record)
        return Ok(record)

    def append_boundary(
        self,
        *,
        cash_delta: object,
        recorded_at: object,
        note: object,
    ) -> Result[LedgerRecord]:
        """Append a treasury-boundary cash row — never touches positions."""
        if not isinstance(cash_delta, Money):
            return invalid("cash_delta", "boundary cash is Money", given=repr(cash_delta))
        refused = refuse_float_money(cash_delta)
        if is_refusal(refused):
            return refused
        if cash_delta.currency != self.currency or cash_delta.scale != self.money_scale:
            return invalid(
                "cash_delta",
                "boundary cash must match ledger currency and money scale",
            )
        if not isinstance(recorded_at, Instant):
            return invalid(
                "recorded_at",
                "boundary act carries an Instant",
                given=repr(recorded_at),
            )
        note_token = clean_token(note)
        if note_token is None:
            return invalid("note", "boundary act names its kind", given=repr(note))
        # Snapshot open positions — boundary must leave them untouched.
        before = {k: v.position_ref.value for k, v in self._positions.items()}
        updated = self.realized_cash.add(cash_delta)
        if is_refusal(updated):
            return updated
        self.realized_cash = updated.value
        after = {k: v.position_ref.value for k, v in self._positions.items()}
        if before != after:
            return policy(
                "positions",
                "a treasury boundary act never touches positions",
            )
        self._sequence += 1
        record = LedgerRecord(
            kind=LedgerRecordKind.BOUNDARY,
            binding_epoch=self.binding_epoch,
            sequence=self._sequence,
            recorded_at=recorded_at,
            cash_delta=cash_delta,
            position_ref=None,
            command_identity=None,
            money_scale=self.money_scale,
            note=note_token,
        )
        self._records.append(record)
        return Ok(record)


def refuse_float_money(value: object) -> Result[None]:
    """Refuse a binary float on the money path (FM-1 / DEC-0225)."""
    if isinstance(value, float):
        return invalid(
            "value",
            "no float on the money path; money is an exact scaled integer with a declared scale",
            given=repr(value),
        )
    if isinstance(value, Money):
        return Ok(None)
    if isinstance(value, int) and not isinstance(value, bool):
        return Ok(None)
    return Ok(None)


def seed_binding_ledger(
    *,
    binding_epoch: object,
    seed: object,
    recorded_at: object,
    currency: object = "USD",
    money_scale: object | None = None,
    reservation_journal: object = None,
    reservation_recovery: object = None,
) -> Result[BindingVirtualLedger]:
    """Open a binding virtual ledger at an exact scaled-integer seed (TN-25)."""
    if not isinstance(binding_epoch, Fingerprint):
        return invalid(
            "binding_epoch",
            "the virtual ledger is scoped to the CT-28 binding epoch",
            given=repr(binding_epoch),
        )
    if isinstance(seed, float):
        return invalid(
            "seed",
            "no float on the money path; seed is Money at the account money scale",
            given=repr(seed),
        )
    if not isinstance(seed, Money):
        return invalid("seed", "ledger seed is Money", given=repr(seed))
    cur = clean_token(currency)
    if cur is None:
        return invalid("currency", "ledger currency is a non-blank tag", given=repr(currency))
    if seed.currency != cur:
        return invalid(
            "seed",
            "seed currency must match the ledger currency",
            seed=seed.currency,
            ledger=cur,
        )
    scale: int
    if money_scale is None:
        scale = seed.scale
    elif isinstance(money_scale, bool) or not isinstance(money_scale, int) or money_scale < 0:
        return invalid(
            "money_scale",
            "account money scale is a non-negative integer exponent",
            given=repr(money_scale),
        )
    else:
        scale = money_scale
    if seed.scale != scale:
        return invalid(
            "seed",
            "seed must use the declared account money scale",
            seed_scale=seed.scale,
            money_scale=scale,
        )
    if not isinstance(recorded_at, Instant):
        return invalid("recorded_at", "seed carries an Instant", given=repr(recorded_at))
    if seed.as_fraction() < 0:
        return invalid("seed", "ledger seed is non-negative", given=str(seed.as_fraction()))

    seed_record = LedgerRecord(
        kind=LedgerRecordKind.SEED,
        binding_epoch=binding_epoch,
        sequence=1,
        recorded_at=recorded_at,
        cash_delta=seed,
        position_ref=None,
        command_identity=None,
        money_scale=scale,
        note="seed",
    )
    journal: JournalSink[object] | None
    if reservation_journal is None:
        journal = None
    elif isinstance(reservation_journal, JournalSink):
        journal = cast("JournalSink[object]", reservation_journal)
    else:
        return invalid(
            "reservation_journal",
            "entry reservations append through the injected JournalSink",
            given=type(reservation_journal).__name__,
        )
    ledger = BindingVirtualLedger(
            binding_epoch=binding_epoch,
            currency=cur,
            money_scale=scale,
            seed=seed,
            realized_cash=seed,
            _records=[seed_record],
            _reservation_journal=journal,
            _sequence=1,
        )
    if reservation_recovery is not None:
        recovered = ledger.recover_entry_reservations(reservation_recovery)
        if is_refusal(recovered):
            return recovered
    elif journal is not None:
        return invalid(
            "reservation_recovery",
            "a durable reservation journal opens only with its complete committed prefix",
        )
    return Ok(ledger)


def sum_virtual_quantities(
    ledgers: Sequence[BindingVirtualLedger],
    *,
    instrument: object,
) -> Result[Quantity | None]:
    """Sum open virtual quantities for one instrument across bindings."""
    inst = clean_token(instrument)
    if inst is None:
        return invalid("instrument", "instrument is a non-blank token", given=repr(instrument))
    total: Quantity | None = None
    for ledger in ledgers:
        qty = ledger.virtual_quantity(inst)
        if qty is None:
            continue
        if total is None:
            total = qty
            continue
        added = total.add(qty)
        if is_refusal(added):
            return added
        total = added.value
    return Ok(total)
