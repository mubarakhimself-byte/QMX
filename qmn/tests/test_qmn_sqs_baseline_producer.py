"""Exact SQS baseline fitting from physical LIVE CT-10 and official CT-02 rows."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from qmf.calendar_forex import (
    CalendarBinding,
    ForexCalendarRegistration,
    register_forex_17ny,
)
from qmf.core import (
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
    read_admission_artifact,
    read_sqs_baseline,
    read_sqs_baseline_derivation_receipt,
)
from qmn.host.sqs_baseline_producer import (
    SqsBaselineProduction,
    SqsBaselineStatistic,
    SqsRoundingPolicy,
    produce_sqs_baseline,
    read_sqs_baseline_derivation,
)
from qmf.readings.signal_snapshot import SqsBaselineKey, sqs_baseline_key

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instant(value: str) -> Instant:
    timestamp = datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp()
    return _ok(Instant.try_create(int(timestamp * 1_000_000_000)))


def _fixture(
    root: Path,
    *,
    sample_times: tuple[str, str] = (
        "2025-01-07T15:00:00+00:00",
        "2025-01-08T15:00:00+00:00",
    ),
    spreads: tuple[int, int] = (10, 20),
) -> tuple[EvidenceStore, SqsBaselineKey, ForexCalendarRegistration, tuple[Fingerprint, ...]]:
    store = EvidenceStore(root)
    venue = _ok(VenueId.try_create("ctrader-fixture"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    key = _ok(sqs_baseline_key(venue, "live", instrument))
    registration = _ok(register_forex_17ny(binding=CalendarBinding(venue_ids=(venue.value,))))
    writer = _ok(WriterId.try_create("qmn-test", "sensor", "quotes", "boot-fit"))
    boundary = SourceObservationBoundary(store)
    references: list[Fingerprint] = []
    samples = tuple(
        (time_text, bid, ask)
        for time_text, base, spread in zip(
            sample_times,
            (100_000, 200_000),
            spreads,
            strict=True,
        )
        for bid, ask in ((base, base + spread),)
    )
    sequence = 0
    for pair_index, (time_text, bid, ask) in enumerate(samples):
        instant = _instant(time_text)
        for side, amount in (("bid", bid), ("ask", ask)):
            observation = _ok(
                SourceObservation.try_create(
                    event_time=instant,
                    known_at=instant,
                    source="explicit-local-ct10-conformance-double",
                    source_native_id=f"quote-{pair_index}",
                    revision="1",
                    receive_wall_time=instant,
                    writer=writer,
                    sequence=sequence,
                    world=World.LIVE,
                    foreign_money=_ok(ForeignMoney.try_create(amount, 5)),
                    market_data=_ok(
                        MarketDataContext.try_create(
                            venue=venue.value,
                            symbol=instrument.symbol,
                            resolution="tick",
                            side=side,
                            license_tag="fixture-license",
                            provenance={"origin": "explicit-local-conformance-double"},
                        )
                    ),
                )
            )
            receipt = _ok(boundary.admit(observation))
            references.append(receipt.archive.fingerprint)
            sequence += 1
    return store, key, registration, tuple(references)


def _produce(
    store: EvidenceStore,
    key: SqsBaselineKey,
    registration: ForexCalendarRegistration,
    refs: tuple[Fingerprint, ...],
    *,
    statistic: SqsBaselineStatistic = SqsBaselineStatistic.MEAN,
) -> Result[SqsBaselineProduction]:
    identity = registration.calendar_identity
    return produce_sqs_baseline(
        store,
        key=key,
        source_archive_fp1s=refs,
        calendar=registration,
        calendar_identity=identity,
        session_id="declared-forex-core-session",
        statistic=statistic,
        rounding_policy=SqsRoundingPolicy.EXACT_DECIMAL_NO_ROUNDING,
        refit_series_id="declared-series-v1",
        refit_policy_fp=_ok(fingerprint({"class": "explicit-refit-policy-v1"})),
    )


def test_sqs_baseline_is_derived_reopened_and_recomputed_from_live_ct10(
    tmp_path: Path,
) -> None:
    store, key, registration, refs = _fixture(tmp_path / "evidence")

    result = _ok(_produce(store, key, registration, refs))

    assert result.persisted.derivation_verified is False
    assert result.derivation_reference.artifact_class == "sqs-baseline-derivation"
    assert result.sample_count == 2
    assert result.statistic == "mean"
    assert result.session_id == "declared-forex-core-session"
    assert result.rounding_policy == SqsRoundingPolicy.EXACT_DECIMAL_NO_ROUNDING.value
    assert result.persisted.artifact.average_spread == _ok(
        PriceDelta.try_create(15, key.instrument, 5)
    )
    assert len(result.session_occurrence_fp1s) == 2
    assert result.calendar_registration_fp1 == _ok(registration.artifact_fingerprint())
    # Reopen with a fresh store facade and independently recompute from the
    # persisted fit recipe and physical CT-10 facts.
    reopened_store = EvidenceStore(store.root)
    reopened_baseline = _ok(read_sqs_baseline(reopened_store, result.reference))
    assert reopened_baseline.derivation_verified is False
    spreads: list[int] = []
    boundary = SourceObservationBoundary(reopened_store)
    observations = [
        _ok(boundary.read(ref, in_world=World.LIVE, for_world=World.LIVE)) for ref in refs
    ]
    for pair in range(0, len(observations), 2):
        sides = {
            observation.market_data.side: observation.foreign_money.verbatim
            for observation in observations[pair : pair + 2]
            if observation.market_data is not None and observation.foreign_money is not None
        }
        spreads.append(sides["ask"] - sides["bid"])
    assert sum(spreads) // len(spreads) == reopened_baseline.artifact.average_spread.value
    assert reopened_baseline.artifact.statistic == "mean/exact-decimal-no-rounding-v1"
    assert reopened_baseline.reference.source_archive_fp1s == refs
    assert (
        reopened_baseline.reference.calendar_identity
        == registration.calendar_identity.fp1_identity()
    )
    expected_session_id = _ok(
        canonical_bytes(
            {
                "class": "qmn-sqs-session-conditioning-v1",
                "session_id": "declared-forex-core-session",
                "calendar_registration_fp1": result.calendar_registration_fp1.value,
            }
        )
    ).decode("utf-8")
    assert reopened_baseline.artifact.session_window_id == expected_session_id
    envelope = _ok(read_admission_artifact(reopened_store, result.reference))
    assert envelope["derivation_status"] == "unverified-input-artifact"
    assert envelope["conditioning"] == {
        "session_window_id": expected_session_id,
        "statistic": "mean/exact-decimal-no-rounding-v1",
        "refit_series_id": "declared-series-v1",
        "refit_policy_fp1": _ok(fingerprint({"class": "explicit-refit-policy-v1"})).value,
    }
    assert reopened_baseline.artifact.refit_series_id == "declared-series-v1"
    assert reopened_baseline.artifact.refit_policy_fp == _ok(
        fingerprint({"class": "explicit-refit-policy-v1"})
    )
    durable_recipe = _ok(
        read_sqs_baseline_derivation_receipt(reopened_store, result.derivation_reference)
    )
    assert durable_recipe.sample_count == 2
    assert durable_recipe.session_occurrence_fp1s == result.session_occurrence_fp1s
    independently_checked = _ok(
        read_sqs_baseline_derivation(
            reopened_store,
            result.derivation_reference,
            calendar=registration,
        )
    )
    assert independently_checked.persisted.derivation_verified is False
    assert (
        independently_checked.persisted.artifact.fp1_identity()
        == result.persisted.artifact.fp1_identity()
    )


def test_sqs_fractional_mean_normalizes_across_price_delta_scales(tmp_path: Path) -> None:
    store, key, registration, refs = _fixture(tmp_path / "fractional", spreads=(20, 40))

    result = _ok(_produce(store, key, registration, refs))

    average = result.persisted.artifact.average_spread
    assert (average.value, average.scale) == (3, 4)
    assert average.as_fraction().numerator == 3
    assert average.as_fraction().denominator == 10_000
    assert result.derivation_reference.artifact_class == "sqs-baseline-derivation"


def test_sqs_baseline_refuses_demo_quotes_and_undeclared_statistic_without_write(
    tmp_path: Path,
) -> None:
    store, key, registration, refs = _fixture(tmp_path / "evidence")
    archive_root = store.root / "live" / "immutable-raw-archive"
    before = {path.relative_to(archive_root) for path in archive_root.rglob("*") if path.is_file()}
    demo_key = _ok(sqs_baseline_key(key.venue, "demo", key.instrument))
    demo = produce_sqs_baseline(
        store,
        key=demo_key,
        source_archive_fp1s=refs,
        calendar=registration,
        calendar_identity=registration.calendar_identity,
        session_id="declared-forex-core-session",
        statistic=SqsBaselineStatistic.MEAN,
        rounding_policy=SqsRoundingPolicy.EXACT_DECIMAL_NO_ROUNDING,
        refit_series_id="declared-series-v1",
        refit_policy_fp=_ok(fingerprint({"class": "explicit-refit-policy-v1"})),
    )
    unsupported = produce_sqs_baseline(
        store,
        key=key,
        source_archive_fp1s=refs,
        calendar=registration,
        calendar_identity=registration.calendar_identity,
        session_id="declared-forex-core-session",
        statistic="quantile-0.9",
        rounding_policy=SqsRoundingPolicy.EXACT_DECIMAL_NO_ROUNDING,
        refit_series_id="declared-series-v1",
        refit_policy_fp=_ok(fingerprint({"class": "explicit-refit-policy-v1"})),
    )

    assert is_refusal(demo)
    assert is_refusal(unsupported)
    # Both refusals happen before an admission artifact is appended.
    after = {path.relative_to(archive_root) for path in archive_root.rglob("*") if path.is_file()}
    assert after == before


def test_sqs_baseline_refuses_foreign_instrument_and_closed_calendar_window(
    tmp_path: Path,
) -> None:
    store, key, registration, refs = _fixture(tmp_path / "evidence")
    archive_root = store.root / "live" / "immutable-raw-archive"
    before = {path.relative_to(archive_root) for path in archive_root.rglob("*") if path.is_file()}
    foreign_instrument = _ok(Instrument.try_create(key.venue, "GBPUSD"))
    foreign_key = _ok(sqs_baseline_key(key.venue, "live", foreign_instrument))
    foreign_source = _produce(store, foreign_key, registration, refs)

    closed_store, closed_key, closed_registration, closed_refs = _fixture(
        tmp_path / "closed-evidence",
        sample_times=(
            "2025-01-12T15:00:00+00:00",
            "2025-01-12T15:01:00+00:00",
        ),
    )
    closed_archive_root = closed_store.root / "live" / "immutable-raw-archive"
    closed_before = {
        path.relative_to(closed_archive_root)
        for path in closed_archive_root.rglob("*")
        if path.is_file()
    }
    closed_window = _produce(closed_store, closed_key, closed_registration, closed_refs)

    assert is_refusal(foreign_source)
    assert is_refusal(closed_window)
    after = {path.relative_to(archive_root) for path in archive_root.rglob("*") if path.is_file()}
    closed_after = {
        path.relative_to(closed_archive_root)
        for path in closed_archive_root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert closed_after == closed_before
