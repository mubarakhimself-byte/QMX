"""Durable CT-11 admission artifact and LIVE SQS source-lineage controls."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, TypeVar, cast

from qmf.core import (
    CalendarIdentity,
    Fingerprint,
    Instant,
    Instrument,
    PriceDelta,
    VenueId,
    World,
    canonical_bytes,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.core.refusal import Result
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore
from qmn.host.admission_artifacts import (
    AdmissionArtifactRef,
    persist_shakedown_signature_page,
    persist_sqs_baseline,
    read_admission_artifact,
    read_sqs_baseline,
)
from qmn.host.shakedown import ShakedownEvidence, ShakedownSignaturePage
from qmf.readings.catalog import SqsBaselineArtifact
from qmf.readings.signal_snapshot import sqs_baseline_key

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fixture(
    store_root: Path,
) -> tuple[EvidenceStore, SqsBaselineArtifact, tuple[Fingerprint, ...], CalendarIdentity]:
    store = EvidenceStore(store_root)
    venue = _ok(VenueId.try_create("ctrader-fixture"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    instant = _ok(Instant.try_create(1_800_000_000_000_000_000))
    writer = _ok(WriterId.try_create("qmn-test", "sensor", "quotes", "boot-a"))
    boundary = SourceObservationBoundary(store)
    refs: list[Fingerprint] = []
    for sequence, (side, value) in enumerate((("bid", 100_000), ("ask", 100_010))):
        observation = _ok(
            SourceObservation.try_create(
                event_time=instant,
                known_at=instant,
                source="local-live-quote-fixture",
                source_native_id="quote-1",
                revision="1",
                receive_wall_time=instant,
                writer=writer,
                sequence=sequence,
                world=World.LIVE,
                foreign_money=_ok(ForeignMoney.try_create(value, 5)),
                market_data=_ok(
                    MarketDataContext.try_create(
                        venue=venue.value,
                        symbol=instrument.symbol,
                        resolution="tick",
                        side=side,
                        license_tag="fixture-license",
                        provenance={"origin": "explicit-conformance-double"},
                    )
                ),
            )
        )
        admitted = _ok(boundary.admit(observation))
        refs.append(admitted.archive.fingerprint)
    key = _ok(sqs_baseline_key(venue, "live", instrument))
    baseline = SqsBaselineArtifact(
        key=key,
        average_spread=_ok(PriceDelta.try_create(10, instrument, 5)),
        session_window_id="fixture-session",
        statistic="mean",
        refit_series_id="fixture-refit-series",
        refit_policy_fp=_ok(fingerprint({"class": "fixture-refit-policy"})),
    )
    calendar = _ok(CalendarIdentity.try_create("fixture-market-hours", "v1", "tz-fixture"))
    return store, baseline, tuple(refs), calendar


def test_sqs_baseline_persists_and_reopens_exact_typed_input_and_live_ct10_refs(
    tmp_path: Path,
) -> None:
    store, baseline, refs, calendar = _fixture(tmp_path / "evidence")

    reference = _ok(
        persist_sqs_baseline(
            store,
            baseline,
            source_archive_fp1s=refs,
            calendar_identity=calendar,
        )
    )
    # A fresh EvidenceStore instance proves the result comes from durable CT-11
    # rows and CT-10 archive reads rather than the writer object's state.
    reopened_store = EvidenceStore(tmp_path / "evidence")
    reopened = _ok(read_sqs_baseline(reopened_store, reference))

    assert reopened.artifact.fp1_identity() == baseline.fp1_identity()
    assert reopened.reference.source_archive_fp1s == refs
    assert reopened.reference.calendar_identity == calendar.fp1_identity()
    assert reopened.derivation_verified is False
    generic = _ok(read_admission_artifact(reopened_store, reference))
    assert generic["derivation_status"] == "unverified-input-artifact"


def test_sqs_writer_refuses_wrong_key_and_non_live_baseline_before_artifact_write(
    tmp_path: Path,
) -> None:
    store, baseline, refs, calendar = _fixture(tmp_path / "evidence")
    other_instrument = _ok(Instrument.try_create(baseline.key.venue, "GBPUSD"))
    wrong_key = replace(
        baseline,
        key=_ok(sqs_baseline_key(baseline.key.venue, "live", other_instrument)),
    )

    refused_key = persist_sqs_baseline(
        store,
        wrong_key,
        source_archive_fp1s=refs,
        calendar_identity=calendar,
    )
    demo = replace(
        baseline,
        key=_ok(sqs_baseline_key(baseline.key.venue, "demo", baseline.key.instrument)),
    )
    refused_world = persist_sqs_baseline(
        store,
        demo,
        source_archive_fp1s=refs,
        calendar_identity=calendar,
    )

    assert is_refusal(refused_key)
    assert is_refusal(refused_world)


def test_sqs_reader_refuses_changed_inner_identity_and_missing_source_refs(tmp_path: Path) -> None:
    store, baseline, refs, calendar = _fixture(tmp_path / "evidence")
    reference = _ok(
        persist_sqs_baseline(
            store,
            baseline,
            source_archive_fp1s=refs,
            calendar_identity=calendar,
        )
    )
    changed = replace(
        reference,
        artifact_fp1=_ok(fingerprint({"class": "foreign-artifact"})),
    )
    missing = persist_sqs_baseline(
        store,
        baseline,
        source_archive_fp1s=(),
        calendar_identity=calendar,
    )

    assert is_refusal(read_sqs_baseline(store, changed))
    assert is_refusal(missing)


def test_sqs_reader_refuses_correctly_fingerprinted_demo_key_row(tmp_path: Path) -> None:
    store, live_baseline, refs, calendar = _fixture(tmp_path / "evidence")
    demo_key = _ok(
        sqs_baseline_key(live_baseline.key.venue, "demo", live_baseline.key.instrument)
    )
    demo_baseline = replace(live_baseline, key=demo_key)
    artifact_identity = demo_baseline.fp1_identity()
    artifact_fp = _ok(fingerprint(artifact_identity))
    body = {
        "class": "qmn-sqs-baseline-envelope-v1",
        "format_version": 1,
        "artifact": artifact_identity,
        "artifact_fp1": artifact_fp.value,
        "source_archive_fp1s": [ref.value for ref in refs],
        "calendar_identity": calendar.fp1_identity(),
        "derivation_status": "unverified-input-artifact",
        "conditioning": {
            "session_window_id": demo_baseline.session_window_id,
            "statistic": demo_baseline.statistic,
            "refit_series_id": demo_baseline.refit_series_id,
            "refit_policy_fp1": demo_baseline.refit_policy_fp.value,
        },
    }
    encoded = _ok(canonical_bytes(body))
    envelope_fp = _ok(fingerprint(body))
    row = {
        "class": "qmn-admission-artifact-row-v1",
        "format_version": 1,
        "artifact_class": "sqs-baseline-artifact",
        "artifact_fp1": envelope_fp.value,
        "body_json": encoded.decode("utf-8"),
        "source_archive_fp1s": [ref.value for ref in refs],
        "calendar_identity_json": _ok(canonical_bytes(calendar.fp1_identity())).decode("utf-8"),
    }
    world_store = _ok(store.for_world(World.LIVE))
    archive_receipt = _ok(world_store.append_store.append_raw([row]))
    reference = AdmissionArtifactRef(
        artifact_class="sqs-baseline-artifact",
        artifact_fp1=envelope_fp,
        archive_fp1=archive_receipt.fingerprint,
        source_archive_fp1s=refs,
        calendar_identity=calendar.fp1_identity(),
    )

    assert is_refusal(read_admission_artifact(store, reference))
    assert is_refusal(read_sqs_baseline(store, reference))


def test_signature_page_is_not_persisted_without_typed_ct27_and_ct28_joins(
    tmp_path: Path,
) -> None:
    store = EvidenceStore(tmp_path / "evidence")
    # The current public evidence type has neither a resolved CT-27 identity
    # nor CT-28 capability receipt. Even a nominal page cannot stand in for
    # those missing authority joins.
    evidence = ShakedownEvidence(
        binding_identity="fixture-binding",
        shakedown_role=cast(Any, object()),
        exercises_run=(),
        layer2=cast(Any, object()),
        window_settings=cast(Any, object()),
        effect_matrix=cast(Any, object()),
        paper_ledger=cast(Any, object()),
        kill_line_breached=False,
        reconciliation=cast(Any, object()),
        sqs_baseline=cast(Any, object()),
        sqs_live_conditioned=False,
        containment=cast(Any, object()),
        command_path_submitted_live=False,
        venue_client_kind="fixture",
    )
    page = ShakedownSignaturePage(layer1_checks_run=(), shakedown=evidence)

    refused = persist_shakedown_signature_page(store, page)

    assert is_refusal(refused)
