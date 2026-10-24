"""The split gap and the seal's move: both are fingerprinted, journaled, and his alone."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from typing import Any

from qmf.core import CalendarIdentity, World, WriterId, is_ok, is_refusal
from qmf.data.seal import SEAL_CONTROL_STREAM, SEAL_MOVE_SUBTYPE, HoldoutSeal, OperatorClick
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore

DAY = 86_400 * 1_000_000_000


def _value(result: Any) -> Any:
    assert is_ok(result)
    return result.value


def _at(year: int, month: int, day: int = 1) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp()) * 1_000_000_000


JAN = _at(2026, 1, 1)
TRAIN_END = _at(2026, 1, 10)
VALIDATION_END = _at(2026, 1, 20)
FEB = _at(2026, 2, 1)


def _calendar() -> CalendarIdentity:
    built = CalendarIdentity.try_create("forex-17NY", "v1", "2025a")
    assert is_ok(built)
    return built.value


def _manifest(gap_ns: int = DAY) -> SplitManifest:
    segments = SplitManifest.default_split_segments([TRAIN_END, VALIDATION_END, FEB])
    assert is_ok(segments)
    built = SplitManifest.try_create(
        calendar_identity=_calendar(),
        segments=segments.value,
        seal_boundary=_value(SplitBoundary.try_create(FEB)),
        purge_width=0,
        embargo_width=0,
        gap=gap_ns,
        world=World.REPLAY,
    )
    assert is_ok(built)
    return built.value


def _seal() -> HoldoutSeal:
    built = HoldoutSeal.try_create(
        seal_boundary=_value(SplitBoundary.try_create(FEB)),
        calendar_identity=_calendar(),
        world=World.REPLAY,
        holdout_months=12,
    )
    assert is_ok(built)
    return built.value


def _journal(tmp_path: Path) -> JournalStore:
    bundle = EvidenceStore(tmp_path / "store").for_world(World.REPLAY)
    assert is_ok(bundle)
    return bundle.value.journal


def _writer() -> WriterId:
    built = WriterId.try_create("workstation", "qmf-data", SEAL_CONTROL_STREAM, "boot-1")
    assert is_ok(built)
    return built.value


def test_the_gap_is_part_of_the_split_fingerprint() -> None:
    wide = _manifest(DAY)
    none = _manifest(0)
    assert wide.gap.value_ns == DAY
    assert wide.split_id != none.split_id
    assert wide.split_id == _manifest(DAY).split_id


def test_a_train_window_stops_a_gap_before_the_next_segment() -> None:
    manifest = _manifest(DAY)
    clipped = manifest.apply_gap(SegmentRole.TRAIN, JAN, FEB)
    assert is_ok(clipped)
    assert _value(clipped) == (JAN, TRAIN_END - DAY)
    validation = manifest.apply_gap(SegmentRole.VALIDATION, JAN, FEB)
    assert is_ok(validation)
    assert _value(validation) == (TRAIN_END, VALIDATION_END - DAY)


def test_the_seal_moves_only_on_his_click(tmp_path: Path) -> None:
    seal = _seal()
    journal = _journal(tmp_path)
    moved_without = seal.move(journal, _writer(), at=JAN, click="a run asked", boundary=JAN)
    assert is_refusal(moved_without)
    assert "click" in str(moved_without.context)
    click = OperatorClick.try_create(JAN)
    assert is_ok(click)
    refused_agent = OperatorClick.try_create(JAN, principal="agent:s1")
    assert is_refusal(refused_agent)
    moved = seal.move(journal, _writer(), at=JAN, click=click.value, boundary=JAN)
    assert is_ok(moved)
    events = journal.read_stream(SEAL_CONTROL_STREAM, for_world=World.REPLAY)
    assert is_ok(events)
    assert [event["control_action_subtype"] for event in events.value] == [SEAL_MOVE_SUBTYPE]
    assert events.value[0]["sealed_boundary"] == _value(SplitBoundary.try_create(JAN)).label()


def test_the_sealed_span_outgrows_its_setting() -> None:
    seal = _seal()
    outgrown = seal.outgrown(13)
    assert is_ok(outgrown)
    assert _value(outgrown) is True
    within = seal.outgrown(12)
    assert is_ok(within)
    assert _value(within) is False
    task = seal.overdue_task(13, at=JAN)
    assert is_ok(task)
    assert _value(task) is not None
    assert _value(task)["reason"] == "seal:span-outgrown"
    assert _value(task)["sealed_months"] == 13
    assert _value(seal.overdue_task(12, at=JAN)) is None
