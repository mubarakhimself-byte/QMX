"""Public typed and durable checks for the private Book protection-plan lineage."""

from pathlib import Path
from typing import TypeVar

from qmf.core import (
    ExactRational,
    Instant,
    Instrument,
    Price,
    PriceDelta,
    Result,
    UnitKind,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.data import JournalReader, JournalWriter
from qmf.data.store import EvidenceStore
from qmn.ledger.protection_plan import (
    create_protection_admission_plan,
    find_protection_admission_plan,
    persist_protection_admission_plan,
    read_protection_admission_plan,
)

T = TypeVar("T")


def _value(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fixture(tmp_path: Path):
    venue = _value(VenueId.try_create("venue-plan-fixture"))
    instrument = _value(Instrument.try_create(venue, "EURUSD"))
    reference = _value(Price.try_create(110_000, instrument, 3))
    risk = _value(PriceDelta.try_create(1_000, instrument, 3))
    offset = _value(PriceDelta.try_create(0, instrument, 3))
    trigger = _value(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE))
    minimum = _value(ExactRational.try_create(0, 1, UnitKind.R_MULTIPLE))
    command_fp = _value(fingerprint({"fixture": "entry-command"}))
    binding = _value(fingerprint({"fixture": "ct28-binding"}))
    policy_fp = _value(fingerprint({"fixture": "book-definition"}))
    policy_source = {
        "class": "qmn-book-ratchet-registry-binding",
        "format_version": 1,
        "book_definition_fp1": policy_fp.value,
        "family_id": "family-plan-fixture",
        "registry_values": {
            "breakeven_ratchet_trigger": trigger.fp1_identity(),
            "breakeven_ratchet_offset": offset.fp1_identity(),
            "amend_min_improvement": minimum.fp1_identity(),
        },
    }
    plan = create_protection_admission_plan(
        command_fp1=command_fp,
        binding_epoch=binding,
        bot_id="bot-plan-fixture",
        family_id="family-plan-fixture",
        direction="long",
        reference_price=reference,
        original_risk_distance=risk,
        trigger=trigger,
        offset=offset,
        amend_min_improvement=minimum,
        policy_source_identity=policy_source,
    )
    store = EvidenceStore(tmp_path / "evidence")
    journal = _value(store.for_world(World.LIVE)).journal
    writer_id = _value(WriterId.try_create("fixture", "node", "protection", "epoch-a"))
    writer = _value(JournalWriter.resume(journal, writer_id, stream_name="protection"))
    at = _value(Instant.try_create(1_724_000_000_000_000_000))
    return plan, store, journal, writer, at


def test_explicit_book_plan_persists_and_reopens_exact_ct13_row(tmp_path: Path) -> None:
    plan_result, store, journal, writer, at = _fixture(tmp_path)
    plan = _value(plan_result)
    receipt = _value(
        persist_protection_admission_plan(
            plan, writer=writer, journal=journal, stream_name="protection", at=at
        )
    )
    assert receipt.plan == plan
    assert receipt.event.sequence == 0
    assert receipt.event.payload["plan_fp1"] == receipt.plan_fp1.value
    checked = _value(JournalReader(journal).read_checked("protection", for_world=World.LIVE))
    assert len(checked) == 1
    assert checked[0].to_row() == receipt.event.to_row()
    world_store = _value(store.for_world(World.LIVE))
    assert receipt.physical_receipt.sequence is not None
    raw_rows = _value(world_store.journal.read_stream("protection", for_world=World.LIVE))
    assert raw_rows[receipt.physical_receipt.sequence] == receipt.event.to_row()
    writer_after_restart = _value(
        JournalWriter.resume(journal, writer.writer, stream_name="protection")
    )
    assert writer_after_restart.next_sequence == 1
    reopened = _value(
        read_protection_admission_plan(
            journal=journal, stream_name="protection", plan_fp1=receipt.plan_fp1
        )
    )
    assert reopened.plan == plan
    assert reopened.event.to_row() == receipt.event.to_row()
    resolved = _value(
        find_protection_admission_plan(
            journal=journal,
            stream_name="protection",
            command_fp1=plan.command_fp1,
            binding_epoch=plan.binding_epoch,
        )
    )
    assert resolved.plan_fp1 == receipt.plan_fp1


def test_missing_or_wrong_unit_ratchet_values_refuse_before_ct13_write(tmp_path: Path) -> None:
    plan_result, _store, journal, writer, _at = _fixture(tmp_path)
    plan = _value(plan_result)
    assert is_refusal(
        create_protection_admission_plan(
            command_fp1=plan.command_fp1,
            binding_epoch=plan.binding_epoch,
            bot_id=plan.bot_id,
            family_id=plan.family_id,
            direction=plan.direction,
            reference_price=plan.reference_price,
            original_risk_distance=plan.original_risk_distance,
            trigger=None,
            offset=plan.policy.offset,
            amend_min_improvement=plan.policy.amend_min_improvement,
            policy_source_identity=plan.policy.source_identity,
        )
    )
    wrong_unit = _value(ExactRational.try_create(1, 2, UnitKind.RATE))
    assert is_refusal(
        create_protection_admission_plan(
            command_fp1=plan.command_fp1,
            binding_epoch=plan.binding_epoch,
            bot_id=plan.bot_id,
            family_id=plan.family_id,
            direction=plan.direction,
            reference_price=plan.reference_price,
            original_risk_distance=plan.original_risk_distance,
            trigger=wrong_unit,
            offset=plan.policy.offset,
            amend_min_improvement=plan.policy.amend_min_improvement,
            policy_source_identity=plan.policy.source_identity,
        )
    )
    assert writer.next_sequence == 0
    assert _value(JournalReader(journal).read_checked("protection", for_world=World.LIVE)) == []


def test_plan_refuses_foreign_instrument_offset_without_writing(tmp_path: Path) -> None:
    plan_result, _store, journal, writer, _at = _fixture(tmp_path)
    plan = _value(plan_result)
    foreign = _value(VenueId.try_create("other-venue"))
    other_instrument = _value(Instrument.try_create(foreign, "EURUSD"))
    other_offset = _value(PriceDelta.try_create(0, other_instrument, 3))
    assert is_refusal(
        create_protection_admission_plan(
            command_fp1=plan.command_fp1,
            binding_epoch=plan.binding_epoch,
            bot_id=plan.bot_id,
            family_id=plan.family_id,
            direction=plan.direction,
            reference_price=plan.reference_price,
            original_risk_distance=plan.original_risk_distance,
            trigger=plan.policy.trigger,
            offset=other_offset,
            amend_min_improvement=plan.policy.amend_min_improvement,
            policy_source_identity=plan.policy.source_identity,
        )
    )
    assert writer.next_sequence == 0
    assert _value(JournalReader(journal).read_checked("protection", for_world=World.LIVE)) == []
