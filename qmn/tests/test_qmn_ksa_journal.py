"""The guarded root folds CT-30 KSA only from checked CT-13 records."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmf.core import Instant, Result, VenueId, World, WriterId, fingerprint, is_ok, is_refusal
from qmf.data import JournalReader, JournalWriter
from qmf.data.store import EvidenceStore
from qmn.protection.ksa import (
    KsaEnforcementScope,
    KsaLevel,
    KsaTriggerClass,
    mint_level_epoch,
)
from qmn.protection.ksa_journal import (
    KSA_EPOCH_CLASS,
    KSA_ESCALATION_CLASS,
    KsaJournalProjection,
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instant(ns: int = 1_700_000_000_000_000_000) -> Instant:
    result = Instant.try_create(ns)
    assert is_ok(result), result
    return result.value


def _projection(
    tmp_path: Path,
    *,
    include_epochs: bool = True,
    authorize_writer: bool = True,
) -> KsaJournalProjection:
    evidence = EvidenceStore(tmp_path / "evidence")
    world_store = _ok(evidence.for_world(World.LIVE))
    writer_id = _ok(WriterId.try_create("node-test", "risk", "ksa-state", "boot-1"))
    writer = _ok(JournalWriter.resume(world_store.journal, writer_id, stream_name="ksa-state"))
    global_scope = KsaEnforcementScope.global_scope()
    stream_scope = _ok(KsaEnforcementScope.stream(_venue_id(), "acct-1"))
    global_epoch = _ok(
        mint_level_epoch(epoch_id="global-1", scope=global_scope, opened_at=_instant())
    )
    stream_epoch = _ok(
        mint_level_epoch(epoch_id="stream-1", scope=stream_scope, opened_at=_instant())
    )
    epochs = (global_epoch, stream_epoch) if include_epochs else (global_epoch,)
    for epoch in epochs:
        epoch_fp = _ok(fingerprint(epoch.fp1_identity()))
        _ok(
            writer.record_control_action(
                "ksa-level-epoch",
                instant=_instant(),
                payload={
                    "class": KSA_EPOCH_CLASS,
                    "epoch_fp1": epoch_fp.value,
                    "epoch_id": epoch.epoch_id,
                    "scope": epoch.scope.token(),
                },
            )
        )
    _ok(
        writer.record_control_action(
            "ksa-escalation",
            instant=_instant(1_700_000_000_100_000_000),
            payload={
                "class": KSA_ESCALATION_CLASS,
                "level": KsaLevel.RED.value,
                "trigger_class": KsaTriggerClass.CONNECTIVITY.value,
                "scope": stream_scope.token(),
                "level_epoch_id": stream_epoch.epoch_id,
                "arbitration_rank": 1,
                "quiet_elapsed_ns": 0,
            },
        )
    )
    accepted_writer = writer_id
    if not authorize_writer:
        accepted_writer = _ok(WriterId.try_create("untrusted", "risk", "ksa-state", "boot-1"))
    projection = _ok(
        KsaJournalProjection.try_create(
            reader=JournalReader(world_store.journal),
            world=World.LIVE,
            stream_name="ksa-state",
            global_epoch=global_epoch,
            stream_epoch=stream_epoch,
            authorized_writers=frozenset({accepted_writer}),
        )
    )
    # Retain the store through the projection's reader; EvidenceStore owns no
    # separate process resource after the checked journal has been opened.
    return projection


def _venue_id() -> VenueId:
    result = VenueId.try_create("venue-test")
    assert is_ok(result), result
    return result.value


def test_checked_ct30_projection_folds_scoped_severity_and_evidence(tmp_path: Path) -> None:
    projection = _projection(tmp_path)
    scope = _ok(KsaEnforcementScope.stream(_venue_id(), "acct-1"))

    folded = projection.levels(expected_stream_scope=scope)

    assert is_ok(folded), folded
    assert folded.value.global_level is KsaLevel.GREEN
    assert folded.value.stream_level is KsaLevel.RED
    assert len(folded.value.epoch_fingerprints) == 2
    assert len(folded.value.event_fingerprints) == 3


def test_missing_epoch_witness_fails_closed_instead_of_defaulting_green(tmp_path: Path) -> None:
    projection = _projection(tmp_path, include_epochs=False)
    scope = _ok(KsaEnforcementScope.stream(_venue_id(), "acct-1"))

    folded = projection.levels(expected_stream_scope=scope)

    assert is_refusal(folded)
    assert folded.context["field"] == "ksa_epoch_witness"


def test_unconfigured_ct30_writer_cannot_supply_even_epoch_witness(tmp_path: Path) -> None:
    projection = _projection(tmp_path, authorize_writer=False)
    scope = _ok(KsaEnforcementScope.stream(_venue_id(), "acct-1"))

    folded = projection.levels(expected_stream_scope=scope)

    assert is_refusal(folded)
    assert folded.context["field"] == "ksa_writer"


def test_other_binding_scope_cannot_supply_stream_ksa_state(tmp_path: Path) -> None:
    projection = _projection(tmp_path)
    other_scope = _ok(KsaEnforcementScope.stream(_venue_id(), "other-account"))

    folded = projection.levels(expected_stream_scope=other_scope)

    assert is_refusal(folded)
    assert folded.context["field"] == "ksa_scope"
