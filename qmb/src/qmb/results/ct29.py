"""Read durable CT-29 close evidence into CT-32 trade measures.

This adapter treats CT-13 as the authority for which closes belong to a replay.
It never derives a close from fill callbacks: the journal event names a persisted
CT-29 record, and long/short attribution must be supplied from the opening-position
ledger explicitly.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from qmf.core import Fingerprint, Money, Ok, Result, WriterId, is_refusal
from qmf.data.journal import JournalEventType
from qmf.data.journal_producer import JournalReader
from qmf.risk.exit_record import ExitRecord, ExitResultLabel

from qmb._refuse import invalid, policy
from qmb.results.measures import ClosedTrade, TradeSide

__all__ = ["EXIT_RECORD_REF_KEY", "CT29ClosedTrade", "read_ct29_closed_trades"]

EXIT_RECORD_REF_KEY: Final[str] = "exit_record_ref"
_BINDING_EPOCH_KEY: Final[str] = "binding_epoch"


@dataclass(frozen=True, slots=True)
class CT29ClosedTrade:
    """A CT-32 trade paired with the exact CT-29 and CT-13 evidence identities."""

    record: ExitRecord
    record_fingerprint: Fingerprint
    journal_event_fingerprint: Fingerprint
    closed_trade: ClosedTrade


def read_ct29_closed_trades(
    *,
    journal_reader: JournalReader,
    stream_name: str,
    writer: WriterId,
    record_resolver: Mapping[str, ExitRecord],
    position_sides: Mapping[str, TradeSide],
    binding_epoch: Fingerprint,
    result_label: ExitResultLabel,
) -> Result[tuple[CT29ClosedTrade, ...]]:
    """Resolve journaled close refs and construct exact CT-32 closed trades.

    Each matching CT-13 ``risk transition`` event must contain ``exit_record_ref``
    (the full CT-29 fingerprint) and ``binding_epoch``. The resolver represents the
    caller's persisted CT-29 record room; keys must equal each record's recomputed
    fingerprint. A side is required by the CT-29 virtual-position fingerprint and
    comes from opening-position attribution, because CT-29 itself has no side field.
    The event must carry the same result label world and the CT-29 epoch/label must
    match the requested replay. The returned objects retain both evidence refs; a
    caller should consume these values directly instead of supplying arbitrary
    ``ClosedTrade`` instances.
    """
    if not stream_name.strip():
        return invalid("stream_name", "a CT-13 writer stream name is explicit")
    events = journal_reader.read_checked(stream_name, for_world=result_label.world)
    if is_refusal(events):
        return events
    closes: list[CT29ClosedTrade] = []
    seen_records: set[str] = set()
    for event in events.value:
        if event.writer != writer:
            return policy(
                "writer",
                "a CT-13 stream ref must resolve only events from its declared WriterId",
                stream=stream_name,
                sequence=event.sequence,
            )
        if event.event_type is not JournalEventType.RISK_TRANSITION:
            continue
        raw_ref = event.payload.get(EXIT_RECORD_REF_KEY)
        raw_epoch = event.payload.get(_BINDING_EPOCH_KEY)
        # Ordinary risk transitions may carry their epoch while having no close
        # reference. Only the explicit CT-29 reference selects a close for this fold.
        if raw_ref is None:
            continue
        if not isinstance(raw_ref, str) or not isinstance(raw_epoch, str):
            return invalid(
                "journal_payload",
                "a CT-29 close transition carries fingerprint strings for record and epoch",
                sequence=event.sequence,
            )
        parsed_ref = Fingerprint.try_create(raw_ref)
        if is_refusal(parsed_ref):
            return parsed_ref
        parsed_epoch = Fingerprint.try_create(raw_epoch)
        if is_refusal(parsed_epoch):
            return parsed_epoch
        if parsed_epoch.value != binding_epoch:
            return policy(
                "binding_epoch",
                "a CT-29 close is bound to the requested replay epoch",
                sequence=event.sequence,
            )
        record = record_resolver.get(parsed_ref.value.value)
        if not isinstance(record, ExitRecord):
            return invalid(
                "exit_record_ref",
                "the journal reference resolves to a persisted typed CT-29 ExitRecord",
                sequence=event.sequence,
                reference=parsed_ref.value.value,
            )
        record_fp = record.fingerprint()
        if is_refusal(record_fp):
            return record_fp
        if record_fp.value != parsed_ref.value:
            return policy(
                "exit_record_ref",
                "the resolved CT-29 record fingerprint must match the durable journal ref",
                sequence=event.sequence,
            )
        if record_fp.value.value in seen_records:
            return invalid(
                "exit_record_ref",
                "one CT-29 record is consumed once per stream projection",
                reference=record_fp.value.value,
            )
        if record.binding_epoch != binding_epoch:
            return policy("binding_epoch", "the CT-29 record belongs to another epoch")
        if record.result_label != result_label or event.world is not result_label.world:
            return policy(
                "result_label",
                "journal event and CT-29 record match the requested replay result label",
                sequence=event.sequence,
            )
        if event.instant != record.recorded_at:
            return policy(
                "recorded_at",
                "the CT-13 transition instant matches the immutable CT-29 close instant",
                sequence=event.sequence,
            )
        raw_side = position_sides.get(record.virtual_position_ref.value)
        if not isinstance(raw_side, TradeSide):
            return invalid(
                "position_side",
                "the opening-position ledger supplies an explicit long/short side for each close",
                virtual_position_ref=record.virtual_position_ref.value,
            )
        net = record.net_realized_pnl()
        if is_refusal(net):
            return net
        fees = _sum_costs(record)
        if is_refusal(fees):
            return fees
        trade = ClosedTrade.try_create(net.value, fees.value, raw_side, record.recorded_at)
        if is_refusal(trade):
            return trade
        closes.append(
            CT29ClosedTrade(
                record=record,
                record_fingerprint=record_fp.value,
                journal_event_fingerprint=event.fingerprint,
                closed_trade=trade.value,
            )
        )
        seen_records.add(record_fp.value.value)
    return _ok(tuple(closes))


def _sum_costs(record: ExitRecord) -> Result[Money]:
    """Sum the exact CT-29 cost components without currency conversion."""
    total = Money.try_create(
        0, record.realized_pnl.currency, record.realized_pnl.scale
    )
    if is_refusal(total):
        return total
    for component in record.cost_components:
        added = total.value.add(component.amount)
        if is_refusal(added):
            return added
        total = added
    return total


def _ok(value: tuple[CT29ClosedTrade, ...]) -> Result[tuple[CT29ClosedTrade, ...]]:
    return Ok(value)
