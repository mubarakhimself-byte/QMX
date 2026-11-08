"""Private CT-11 storage for AD-32 work and SQS input artifacts.

These helpers persist existing typed evidence as content-addressed immutable
raw artifacts. They do not add CT-13 event fields: signed promotion cards
remain the existing citation mechanism. LIVE SQS artifacts are accepted only
with checked LIVE CT-10 quote observations in their lineage envelope.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qmf.core import (
    CalendarIdentity,
    Fingerprint,
    Instrument,
    Ok,
    PriceDelta,
    Result,
    VenueId,
    World,
    WriteOutcome,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore, StoreReceipt, WorldStore
from qmf.data.store.rooms import RoomRole
from qmf.readings.catalog import SqsBaselineArtifact
from qmf.readings.signal_snapshot import SqsBaselineKey, sqs_baseline_key

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.shakedown import ShakedownEvidence, ShakedownSignaturePage

__all__ = [
    "ADMISSION_ARTIFACT_FORMAT_VERSION",
    "AdmissionArtifactRef",
    "PersistedSqsBaseline",
    "SqsBaselineDerivationReceipt",
    "persist_shakedown_signature_page",
    "persist_sqs_baseline",
    "persist_sqs_baseline_derivation",
    "read_admission_artifact",
    "read_sqs_baseline_derivation_receipt",
]

ADMISSION_ARTIFACT_FORMAT_VERSION: Final[int] = 1
_ARTIFACT_ROW_CLASS: Final[str] = "qmn-admission-artifact-row-v1"
_ARTIFACT_CLASSES: Final[frozenset[str]] = frozenset(
    {"shakedown-signature-page", "sqs-baseline-artifact", "sqs-baseline-derivation"}
)


@dataclass(frozen=True, slots=True)
class AdmissionArtifactRef:
    """The checked CT-11 location and inner identity of one private artifact."""

    artifact_class: str
    artifact_fp1: Fingerprint
    archive_fp1: Fingerprint
    source_archive_fp1s: tuple[Fingerprint, ...]
    calendar_identity: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class PersistedSqsBaseline:
    """Reopened SQS value and checked source lineage, without a fit attestation."""

    artifact: SqsBaselineArtifact
    reference: AdmissionArtifactRef
    derivation_verified: bool = False


@dataclass(frozen=True, slots=True)
class SqsBaselineDerivationReceipt:
    """Durable fit recipe and provenance; this type alone is not fit verification."""

    reference: AdmissionArtifactRef
    baseline_reference: AdmissionArtifactRef
    average_spread: PriceDelta
    sample_count: int
    session_id: str
    statistic: str
    rounding_policy: str
    refit_series_id: str
    refit_policy_fp: Fingerprint
    session_occurrence_fp1s: tuple[Fingerprint, ...]
    calendar_registration_fp1: Fingerprint


def persist_shakedown_signature_page(
    store: object,
    page: object,
) -> Result[AdmissionArtifactRef]:
    """Persist a complete existing signature page; refuse incomplete AD-32 joins.

    Current ``ShakedownEvidence`` does not carry a typed resolved BMS identity or
    capability-satisfaction record. The helper therefore refuses the present
    page rather than converting its binding token or booleans into those proofs.
    """
    if type(page) is not ShakedownSignaturePage:
        return invalid("page", "AD-32 evidence is a typed ShakedownSignaturePage")
    shakedown = page.shakedown
    if type(shakedown) is not ShakedownEvidence:
        return invalid("page.shakedown", "signature page carries the exact shakedown evidence type")
    if not isinstance(getattr(shakedown, "bms_fingerprint", None), Fingerprint):
        return unavailable(
            "bms_fingerprint",
            "the signature page requires the resolved CT-27 fingerprint from its CT-28 binding",
            failure_id="configured_runtime.admission_page_bms_missing",
        )
    if getattr(shakedown, "capability_satisfaction", None) is None:
        return unavailable(
            "capability_satisfaction",
            "the signature page requires the checked CT-28 capability-satisfaction result",
            failure_id="configured_runtime.admission_page_capabilities_missing",
        )
    body = page.as_mapping()
    return _persist_body(store, "shakedown-signature-page", body, (), None)


def persist_sqs_baseline(
    store: object,
    artifact: object,
    *,
    source_archive_fp1s: object,
    calendar_identity: object,
) -> Result[AdmissionArtifactRef]:
    """Persist a typed LIVE baseline with checked CT-10 quote-source lineage.

    This boundary validates the SQS artifact and its cited LIVE source rows; it
    does not fit or refit the baseline. The operator-declared statistic,
    conditioning, and refit policy remain the artifact's identity.
    """
    if type(artifact) is not SqsBaselineArtifact:
        return invalid("artifact", "SQS baseline input is a typed SqsBaselineArtifact")
    checked_artifact = _revalidate_sqs_baseline(artifact)
    if is_refusal(checked_artifact):
        return checked_artifact
    artifact = checked_artifact.value
    if type(calendar_identity) is not CalendarIdentity:
        return invalid(
            "calendar_identity",
            "SQS conditioning pins the official market-hours CalendarIdentity",
        )
    rebuilt_calendar = CalendarIdentity.try_create(
        calendar_identity.rule_set,
        calendar_identity.rule_set_version,
        calendar_identity.tzdata_version,
    )
    if is_refusal(rebuilt_calendar):
        return rebuilt_calendar
    if rebuilt_calendar.value != calendar_identity:
        return invalid("calendar_identity", "calendar identity revalidates canonically")
    if artifact.key.environment != "live":
        return policy("environment", "a LIVE SQS baseline is conditioned by live observations")
    if not isinstance(source_archive_fp1s, Sequence) or isinstance(
        source_archive_fp1s, (str, bytes)
    ):
        return invalid(
            "source_archive_fp1s",
            "baseline lineage is a sequence of CT-10 archive refs",
        )
    refs: list[Fingerprint] = []
    for raw_ref in cast(Sequence[object], source_archive_fp1s):
        parsed = _coerce_fp(raw_ref, "source_archive_fp1s")
        if is_refusal(parsed):
            return parsed
        refs.append(parsed.value)
    if len(refs) < 2 or len({ref.value for ref in refs}) != len(refs):
        return invalid(
            "source_archive_fp1s",
            "baseline lineage cites at least two unique quote observations",
        )
    observations = _read_quote_sources(store, refs, artifact.key)
    if is_refusal(observations):
        return observations
    artifact_fp = _artifact_fingerprint(artifact.fp1_identity())
    if is_refusal(artifact_fp):
        return artifact_fp
    body = {
        "class": "qmn-sqs-baseline-envelope-v1",
        "format_version": ADMISSION_ARTIFACT_FORMAT_VERSION,
        "artifact": artifact.fp1_identity(),
        "artifact_fp1": artifact_fp.value.value,
        "source_archive_fp1s": [ref.value for ref in refs],
        "calendar_identity": rebuilt_calendar.value.fp1_identity(),
        "derivation_status": "unverified-input-artifact",
        "conditioning": {
            "session_window_id": artifact.session_window_id,
            "statistic": artifact.statistic,
            "refit_series_id": artifact.refit_series_id,
            "refit_policy_fp1": artifact.refit_policy_fp.value,
        },
    }
    return _persist_body(
        store,
        "sqs-baseline-artifact",
        body,
        tuple(refs),
        MappingProxyType(rebuilt_calendar.value.fp1_identity()),
    )


def persist_sqs_baseline_derivation(
    store: object,
    *,
    baseline_reference: object,
    average_spread: object,
    sample_count: object,
    session_id: object,
    statistic: object,
    rounding_policy: object,
    refit_series_id: object,
    refit_policy_fp: object,
    session_occurrence_fp1s: object,
    calendar_registration_fp1: object,
) -> Result[AdmissionArtifactRef]:
    """Persist a private recipe/readback witness beside an unverified SQS input.

    The witness is data, not authority to mark a baseline derived. Its checked
    reader validates every field and a caller must recompute from reopened CT-10
    facts and the pinned calendar before treating the fit as derived.
    """
    checked_reference = _revalidate_reference(baseline_reference)
    if is_refusal(checked_reference):
        return checked_reference
    baseline_ref = checked_reference.value
    if baseline_ref.artifact_class != "sqs-baseline-artifact":
        return invalid("baseline_reference", "fit receipt cites an SQS input artifact")
    baseline = read_sqs_baseline(store, baseline_ref)
    if is_refusal(baseline):
        return baseline
    if type(average_spread) is not PriceDelta:
        return invalid("average_spread", "fit receipt carries an exact PriceDelta")
    checked_average = PriceDelta.try_create(
        average_spread.value, average_spread.instrument, average_spread.scale
    )
    if is_refusal(checked_average):
        return checked_average
    if checked_average.value.instrument != baseline.value.artifact.key.instrument:
        return policy("average_spread", "fit quantity uses the input baseline instrument")
    if checked_average.value.as_fraction() != baseline.value.artifact.average_spread.as_fraction():
        return policy("average_spread", "fit quantity equals the persisted baseline quantity")
    if type(sample_count) is not int or sample_count <= 0:
        return invalid("sample_count", "fit recipe records a positive exact sample count")
    tokens: dict[str, str] = {}
    for name, raw in (
        ("session_id", session_id),
        ("statistic", statistic),
        ("rounding_policy", rounding_policy),
        ("refit_series_id", refit_series_id),
    ):
        if type(raw) is not str or not raw.strip():
            return invalid(name, "fit recipe uses explicit nonblank text")
        tokens[name] = raw
    if tokens["statistic"] not in {"mean", "median"}:
        return unavailable("statistic", "fit receipt supports only the implemented mean/median")
    if tokens["rounding_policy"] != "exact-decimal-no-rounding-v1":
        return unavailable("rounding_policy", "fit receipt supports the implemented exact policy")
    if baseline.value.artifact.statistic != (f"{tokens['statistic']}/{tokens['rounding_policy']}"):
        return policy("statistic", "fit recipe matches the input artifact's declared statistic")
    if baseline.value.artifact.refit_series_id != tokens["refit_series_id"]:
        return policy("refit_series_id", "fit recipe matches the input artifact's refit series")
    if type(refit_policy_fp) is not Fingerprint:
        return invalid("refit_policy_fp", "fit recipe carries an official policy fingerprint")
    checked_refit_fp = _coerce_fp(refit_policy_fp, "refit_policy_fp")
    if is_refusal(checked_refit_fp):
        return checked_refit_fp
    if checked_refit_fp.value != baseline.value.artifact.refit_policy_fp:
        return policy("refit_policy_fp", "fit recipe matches the input artifact's refit policy")
    checked_calendar_fp = _coerce_fp(calendar_registration_fp1, "calendar_registration_fp1")
    if is_refusal(checked_calendar_fp):
        return checked_calendar_fp
    if not isinstance(session_occurrence_fp1s, Sequence) or isinstance(
        session_occurrence_fp1s, (str, bytes)
    ):
        return invalid("session_occurrence_fp1s", "fit receipt cites official window occurrences")
    occurrences: list[Fingerprint] = []
    for raw in cast(Sequence[object], session_occurrence_fp1s):
        parsed = _coerce_fp(raw, "session_occurrence_fp1s")
        if is_refusal(parsed):
            return parsed
        occurrences.append(parsed.value)
    if not occurrences or len({item.value for item in occurrences}) != len(occurrences):
        return invalid("session_occurrence_fp1s", "fit receipt has unique checked occurrences")
    calendar_identity = baseline_ref.calendar_identity
    if calendar_identity is None:
        return invalid("baseline_reference", "fit receipt input cites its CT-02 identity")
    body = {
        "class": "qmn-sqs-derived-fit-v1",
        "format_version": ADMISSION_ARTIFACT_FORMAT_VERSION,
        "baseline_reference": _reference_body(baseline_ref),
        "average_spread": checked_average.value.fp1_identity(),
        "sample_count": sample_count,
        "session_id": tokens["session_id"],
        "statistic": tokens["statistic"],
        "rounding_policy": tokens["rounding_policy"],
        "refit_series_id": tokens["refit_series_id"],
        "refit_policy_fp1": checked_refit_fp.value.value,
        "session_occurrence_fp1s": [item.value for item in occurrences],
        "calendar_registration_fp1": checked_calendar_fp.value.value,
    }
    return _persist_body(
        store,
        "sqs-baseline-derivation",
        body,
        baseline_ref.source_archive_fp1s,
        calendar_identity,
    )


def read_admission_artifact(
    store: object,
    reference: object,
) -> Result[Mapping[str, object]]:
    """Reopen and verify the exact immutable CT-11 row and its inner body."""
    checked_reference = _revalidate_reference(reference)
    if is_refusal(checked_reference):
        return checked_reference
    reference = checked_reference.value
    if reference.artifact_class not in _ARTIFACT_CLASSES:
        return invalid("artifact_class", "private admission artifact kind is registered")
    world_store = _live_world_store(store)
    if is_refusal(world_store):
        return world_store
    rows = world_store.value.append_store.read_raw(reference.archive_fp1, for_world=World.LIVE)
    if is_refusal(rows):
        return rows
    reopened_row: object = rows.value[0] if len(rows.value) == 1 else None
    if not isinstance(reopened_row, Mapping):
        return policy("artifact_row", "admission artifact reopens as one canonical row")
    row = cast(Mapping[str, object], reopened_row)
    decoded = _decode_row(row)
    if is_refusal(decoded):
        return decoded
    row_body, row_kind, row_artifact_fp, row_sources, row_calendar = decoded.value
    if (
        row_kind != reference.artifact_class
        or row_artifact_fp != reference.artifact_fp1
        or row_sources != reference.source_archive_fp1s
        or row_calendar != reference.calendar_identity
    ):
        return policy("artifact_reference", "reopened row matches its complete typed receipt")
    body_fp = fingerprint(dict(row_body))
    if is_refusal(body_fp):
        return body_fp
    if body_fp.value != reference.artifact_fp1:
        return policy("artifact_fp1", "reopened body recomputes the cited inner identity")
    if reference.artifact_class == "sqs-baseline-artifact":
        baseline = _decode_sqs_baseline(row_body)
        if is_refusal(baseline):
            return baseline
        if baseline.value.fp1_identity() != row_body.get("artifact"):
            return policy("artifact", "typed SQS baseline matches its persisted identity body")
        nested_fp = _coerce_fp(row_body.get("artifact_fp1"), "artifact_fp1")
        if is_refusal(nested_fp):
            return nested_fp
        typed_fp = fingerprint(baseline.value.fp1_identity())
        if is_refusal(typed_fp):
            return typed_fp
        nested_sources = row_body.get("source_archive_fp1s")
        if not isinstance(nested_sources, list):
            return invalid("source_archive_fp1s", "SQS envelope cites its checked CT-10 inputs")
        parsed_sources: list[Fingerprint] = []
        for item in cast(list[object], nested_sources):
            parsed = _coerce_fp(item, "source_archive_fp1s")
            if is_refusal(parsed):
                return parsed
            parsed_sources.append(parsed.value)
        nested_calendar = row_body.get("calendar_identity")
        if (
            nested_fp.value != typed_fp.value
            or tuple(parsed_sources) != reference.source_archive_fp1s
            or nested_calendar != reference.calendar_identity
            or row_body.get("derivation_status") != "unverified-input-artifact"
            or row_body.get("conditioning")
            != {
                "session_window_id": baseline.value.session_window_id,
                "statistic": baseline.value.statistic,
                "refit_series_id": baseline.value.refit_series_id,
                "refit_policy_fp1": baseline.value.refit_policy_fp.value,
            }
        ):
            return policy(
                "sqs_lineage",
                "SQS body binds the typed baseline, calendar, source refs, "
                "and declared conditioning",
            )
    elif reference.artifact_class == "sqs-baseline-derivation":
        receipt = _decode_sqs_baseline_derivation(store, row_body, reference)
        if is_refusal(receipt):
            return receipt
        if (
            receipt.value.baseline_reference.source_archive_fp1s != reference.source_archive_fp1s
            or receipt.value.baseline_reference.calendar_identity != reference.calendar_identity
        ):
            return policy(
                "derivation_lineage", "fit receipt repeats exact source and calendar refs"
            )
    return Ok(row_body)


def read_sqs_baseline(
    store: object,
    reference: object,
) -> Result[PersistedSqsBaseline]:
    """Reopen a typed SQS baseline and recheck every cited LIVE CT-10 source."""
    checked_reference = _revalidate_reference(reference)
    if is_refusal(checked_reference):
        return checked_reference
    reference = checked_reference.value
    if reference.artifact_class != "sqs-baseline-artifact":
        return invalid("reference", "SQS reader receives a typed SQS baseline reference")
    body = read_admission_artifact(store, reference)
    if is_refusal(body):
        return body
    artifact = _decode_sqs_baseline(body.value)
    if is_refusal(artifact):
        return artifact
    lineage = _read_quote_sources(store, list(reference.source_archive_fp1s), artifact.value.key)
    if is_refusal(lineage):
        return lineage
    return Ok(
        PersistedSqsBaseline(
            artifact=artifact.value,
            reference=reference,
            derivation_verified=False,
        )
    )


def read_sqs_baseline_derivation_receipt(
    store: object,
    reference: object,
) -> Result[SqsBaselineDerivationReceipt]:
    """Reopen the durable fit recipe while leaving physical-fit proof to its verifier."""
    checked_reference = _revalidate_reference(reference)
    if is_refusal(checked_reference):
        return checked_reference
    if checked_reference.value.artifact_class != "sqs-baseline-derivation":
        return invalid("reference", "fit reader receives a durable derivation receipt")
    body = read_admission_artifact(store, checked_reference.value)
    if is_refusal(body):
        return body
    return _decode_sqs_baseline_derivation(store, body.value, checked_reference.value)


def _decode_sqs_baseline_derivation(
    store: object,
    body: Mapping[str, object],
    reference: AdmissionArtifactRef,
) -> Result[SqsBaselineDerivationReceipt]:
    required = {
        "class",
        "format_version",
        "baseline_reference",
        "average_spread",
        "sample_count",
        "session_id",
        "statistic",
        "rounding_policy",
        "refit_series_id",
        "refit_policy_fp1",
        "session_occurrence_fp1s",
        "calendar_registration_fp1",
    }
    if (
        set(body) != required
        or body.get("class") != "qmn-sqs-derived-fit-v1"
        or type(body.get("format_version")) is not int
        or body.get("format_version") != ADMISSION_ARTIFACT_FORMAT_VERSION
    ):
        return invalid("derivation", "private SQS fit receipt has its exact versioned fields")
    baseline_ref = _decode_reference_body(body.get("baseline_reference"))
    if is_refusal(baseline_ref):
        return baseline_ref
    if baseline_ref.value.artifact_class != "sqs-baseline-artifact":
        return invalid("baseline_reference", "derived-fit receipt cites its input baseline")
    baseline = read_sqs_baseline(store, baseline_ref.value)
    if is_refusal(baseline):
        return baseline
    if (
        reference.artifact_class != "sqs-baseline-derivation"
        or reference.source_archive_fp1s != baseline_ref.value.source_archive_fp1s
        or reference.calendar_identity != baseline_ref.value.calendar_identity
    ):
        return policy("derivation_lineage", "receipt reference matches nested input lineage")
    raw_count = body.get("sample_count")
    if type(raw_count) is not int or raw_count <= 0:
        return invalid("sample_count", "fit receipt has a positive exact sample count")
    tokens: dict[str, str] = {}
    for name in ("session_id", "statistic", "rounding_policy", "refit_series_id"):
        raw = body.get(name)
        if type(raw) is not str or not raw.strip():
            return invalid(name, "fit receipt carries an explicit nonblank token")
        tokens[name] = raw
    if tokens["statistic"] not in {"mean", "median"}:
        return unavailable("statistic", "fit receipt statistic is not implemented")
    if tokens["rounding_policy"] != "exact-decimal-no-rounding-v1":
        return unavailable("rounding_policy", "fit receipt rounding policy is not implemented")
    artifact = baseline.value.artifact
    if artifact.statistic != f"{tokens['statistic']}/{tokens['rounding_policy']}":
        return policy("statistic", "fit receipt matches the input's declared statistic")
    if artifact.refit_series_id != tokens["refit_series_id"]:
        return policy("refit_series_id", "fit receipt matches the input's refit-series identity")
    refit_fp = _coerce_fp(body.get("refit_policy_fp1"), "refit_policy_fp1")
    if is_refusal(refit_fp):
        return refit_fp
    if refit_fp.value != artifact.refit_policy_fp:
        return policy("refit_policy_fp1", "fit receipt matches the input refit policy")
    registration_fp = _coerce_fp(body.get("calendar_registration_fp1"), "calendar_registration_fp1")
    if is_refusal(registration_fp):
        return registration_fp
    occurrence_raw = body.get("session_occurrence_fp1s")
    if not isinstance(occurrence_raw, list):
        return invalid("session_occurrence_fp1s", "fit receipt has occurrence fingerprints")
    occurrences: list[Fingerprint] = []
    for raw in cast(list[object], occurrence_raw):
        parsed = _coerce_fp(raw, "session_occurrence_fp1s")
        if is_refusal(parsed):
            return parsed
        occurrences.append(parsed.value)
    if not occurrences or len({item.value for item in occurrences}) != len(occurrences):
        return invalid("session_occurrence_fp1s", "fit receipt occurrences are unique and nonempty")
    if [item.value for item in occurrences] != sorted(item.value for item in occurrences):
        return invalid("session_occurrence_fp1s", "fit receipt occurrences have canonical order")
    expected_session_identity = canonical_bytes(
        {
            "class": "qmn-sqs-session-conditioning-v1",
            "session_id": tokens["session_id"],
            "calendar_registration_fp1": registration_fp.value.value,
        }
    )
    if is_refusal(expected_session_identity):
        return expected_session_identity
    if artifact.session_window_id != expected_session_identity.value.decode("utf-8"):
        return policy("session_id", "fit receipt matches the input's stable session conditioning")
    average_body = body.get("average_spread")
    if not isinstance(average_body, Mapping):
        return invalid("average_spread", "fit receipt carries exact PriceDelta identity content")
    average_map = cast(Mapping[str, object], average_body)
    average = _decode_price_delta(average_map, artifact.key.instrument)
    if is_refusal(average):
        return average
    if dict(average.value.fp1_identity()) != dict(average_map):
        return invalid("average_spread", "fit receipt carries canonical PriceDelta content")
    if average.value.as_fraction() != artifact.average_spread.as_fraction():
        return policy("average_spread", "fit receipt and input preserve the same exact quantity")
    return Ok(
        SqsBaselineDerivationReceipt(
            reference=reference,
            baseline_reference=baseline_ref.value,
            average_spread=average.value,
            sample_count=raw_count,
            session_id=tokens["session_id"],
            statistic=tokens["statistic"],
            rounding_policy=tokens["rounding_policy"],
            refit_series_id=tokens["refit_series_id"],
            refit_policy_fp=refit_fp.value,
            session_occurrence_fp1s=tuple(occurrences),
            calendar_registration_fp1=registration_fp.value,
        )
    )


def _decode_reference_body(value: object) -> Result[AdmissionArtifactRef]:
    required = {
        "artifact_class",
        "artifact_fp1",
        "archive_fp1",
        "source_archive_fp1s",
        "calendar_identity",
    }
    if not isinstance(value, Mapping):
        return invalid("baseline_reference", "nested CT-11 reference has exact typed fields")
    raw_body = cast(Mapping[object, object], value)
    if set(raw_body) != required:
        return invalid("baseline_reference", "nested CT-11 reference has exact typed fields")
    body = cast(Mapping[str, object], value)
    kind = body.get("artifact_class")
    if type(kind) is not str:
        return invalid("artifact_class", "nested reference class is text")
    artifact_fp = _coerce_fp(body.get("artifact_fp1"), "artifact_fp1")
    archive_fp = _coerce_fp(body.get("archive_fp1"), "archive_fp1")
    if is_refusal(artifact_fp):
        return artifact_fp
    if is_refusal(archive_fp):
        return archive_fp
    raw_sources = body.get("source_archive_fp1s")
    if not isinstance(raw_sources, list):
        return invalid("source_archive_fp1s", "nested reference has stored source refs")
    sources: list[Fingerprint] = []
    for raw in cast(list[object], raw_sources):
        parsed = _coerce_fp(raw, "source_archive_fp1s")
        if is_refusal(parsed):
            return parsed
        sources.append(parsed.value)
    calendar = body.get("calendar_identity")
    if not isinstance(calendar, Mapping):
        return invalid("calendar_identity", "nested baseline reference pins CT-02 identity")
    checked_calendar = _revalidate_calendar(cast(Mapping[str, object], calendar))
    if is_refusal(checked_calendar):
        return checked_calendar
    return _revalidate_reference(
        AdmissionArtifactRef(
            artifact_class=kind,
            artifact_fp1=artifact_fp.value,
            archive_fp1=archive_fp.value,
            source_archive_fp1s=tuple(sources),
            calendar_identity=checked_calendar.value,
        )
    )


def _reference_body(reference: AdmissionArtifactRef) -> Mapping[str, object]:
    return {
        "artifact_class": reference.artifact_class,
        "artifact_fp1": reference.artifact_fp1.value,
        "archive_fp1": reference.archive_fp1.value,
        "source_archive_fp1s": [item.value for item in reference.source_archive_fp1s],
        "calendar_identity": dict(reference.calendar_identity or {}),
    }


def _persist_body(
    store: object,
    kind: str,
    body: Mapping[str, object],
    source_refs: tuple[Fingerprint, ...],
    calendar: Mapping[str, object] | None,
) -> Result[AdmissionArtifactRef]:
    if kind not in _ARTIFACT_CLASSES:
        return invalid("kind", "admission artifact kind is registered")
    world_store = _live_world_store(store)
    if is_refusal(world_store):
        return world_store
    body_fp = fingerprint(dict(body))
    if is_refusal(body_fp):
        return body_fp
    encoded = canonical_bytes(dict(body))
    if is_refusal(encoded):
        return encoded
    row: dict[str, object] = {
        "class": _ARTIFACT_ROW_CLASS,
        "format_version": ADMISSION_ARTIFACT_FORMAT_VERSION,
        "artifact_class": kind,
        "artifact_fp1": body_fp.value.value,
        "body_json": encoded.value.decode("utf-8"),
        "source_archive_fp1s": [ref.value for ref in source_refs],
    }
    if calendar is not None:
        calendar_bytes = canonical_bytes(dict(calendar))
        if is_refusal(calendar_bytes):
            return calendar_bytes
        row["calendar_identity_json"] = calendar_bytes.value.decode("utf-8")
    written = world_store.value.append_store.append_raw([row])
    if is_refusal(written):
        return written
    receipt = written.value
    expected_row_fp = fingerprint([row])
    if is_refusal(expected_row_fp):
        return expected_row_fp
    if not _valid_store_receipt(receipt, expected_row_fp.value):
        return policy("store_receipt", "CT-11 receipt identifies the retained LIVE raw artifact")
    reopened = world_store.value.append_store.read_raw(receipt.fingerprint, for_world=World.LIVE)
    if is_refusal(reopened):
        return reopened
    if len(reopened.value) != 1:
        return policy("artifact_readback", "one CT-11 row reopens before success")
    readback = _decode_row(cast(Mapping[str, object], reopened.value[0]))
    if is_refusal(readback):
        return readback
    rb_body, rb_kind, rb_fp, rb_sources, rb_calendar = readback.value
    expected_sources = source_refs
    expected_calendar = MappingProxyType(dict(calendar)) if calendar is not None else None
    if (
        rb_kind != kind
        or rb_body != body
        or rb_fp != body_fp.value
        or rb_sources != expected_sources
        or rb_calendar != expected_calendar
    ):
        return policy("artifact_readback", "reopened CT-11 body and lineage match the write")
    return Ok(
        AdmissionArtifactRef(
            artifact_class=kind,
            artifact_fp1=body_fp.value,
            archive_fp1=receipt.fingerprint,
            source_archive_fp1s=source_refs,
            calendar_identity=expected_calendar,
        )
    )


_DecodedRow = tuple[
    Mapping[str, object],
    str,
    Fingerprint,
    tuple[Fingerprint, ...],
    Mapping[str, object] | None,
]


def _decode_row(row: Mapping[str, object]) -> Result[_DecodedRow]:
    required = {
        "class",
        "format_version",
        "artifact_class",
        "artifact_fp1",
        "body_json",
        "source_archive_fp1s",
    }
    optional = {"calendar_identity_json"}
    if set(row) - required - optional or required - set(row):
        return invalid("artifact_row", "private CT-11 row has its exact versioned fields")
    if (
        row.get("class") != _ARTIFACT_ROW_CLASS
        or type(row.get("format_version")) is not int
        or row.get("format_version") != ADMISSION_ARTIFACT_FORMAT_VERSION
    ):
        return invalid("artifact_row", "private CT-11 row class and format version are recognized")
    kind = row.get("artifact_class")
    if not isinstance(kind, str) or kind not in _ARTIFACT_CLASSES:
        return invalid("artifact_class", "private artifact type is recognized")
    raw_json = row.get("body_json")
    if not isinstance(raw_json, str):
        return invalid("body_json", "private artifact body is canonical JSON text")
    try:
        value = json.loads(raw_json)
    except (json.JSONDecodeError, UnicodeError):
        return invalid("body_json", "private artifact body parses as JSON")
    if not isinstance(value, Mapping):
        return invalid("body_json", "private artifact body is an object")
    body = cast(Mapping[str, object], value)
    canonical = canonical_bytes(dict(body))
    parsed_fp = _coerce_fp(row.get("artifact_fp1"), "artifact_fp1")
    if is_refusal(canonical):
        return canonical
    if is_refusal(parsed_fp):
        return parsed_fp
    if canonical.value.decode("utf-8") != raw_json:
        return invalid("body_json", "private artifact body uses exact canonical JSON")
    computed = fingerprint(dict(body))
    if is_refusal(computed):
        return computed
    if computed.value != parsed_fp.value:
        return policy("artifact_fp1", "row's presented artifact identity matches its body")
    raw_refs = row.get("source_archive_fp1s")
    if not isinstance(raw_refs, list):
        return invalid("source_archive_fp1s", "CT-10 lineage refs are a persisted sequence")
    refs: list[Fingerprint] = []
    for raw_ref in cast(list[object], raw_refs):
        parsed = _coerce_fp(raw_ref, "source_archive_fp1s")
        if is_refusal(parsed):
            return parsed
        refs.append(parsed.value)
    calendar: Mapping[str, object] | None = None
    if "calendar_identity_json" in row:
        raw_calendar = row.get("calendar_identity_json")
        if not isinstance(raw_calendar, str):
            return invalid("calendar_identity_json", "calendar identity is canonical JSON")
        try:
            parsed_calendar = json.loads(raw_calendar)
        except (json.JSONDecodeError, UnicodeError):
            return invalid("calendar_identity_json", "calendar identity JSON parses")
        if not isinstance(parsed_calendar, Mapping):
            return invalid("calendar_identity_json", "calendar identity is an object")
        calendar = MappingProxyType(cast(Mapping[str, object], parsed_calendar))
    return Ok((MappingProxyType(dict(body)), kind, parsed_fp.value, tuple(refs), calendar))


def _read_quote_sources(
    store: object,
    refs: Sequence[Fingerprint],
    key: SqsBaselineKey,
) -> Result[tuple[SourceObservation, ...]]:
    world_store = _live_world_store(store)
    if is_refusal(world_store):
        return world_store
    boundary = SourceObservationBoundary(cast(EvidenceStore, store))
    observations: list[SourceObservation] = []
    for ref in refs:
        observation = boundary.read(ref, in_world=World.LIVE, for_world=World.LIVE)
        if is_refusal(observation):
            return observation
        source = observation.value
        context = source.market_data
        if (
            type(source) is not SourceObservation
            or source.world is not World.LIVE
            or source.foreign_money is None
            or context is None
            or context.side not in {"bid", "ask"}
            or context.venue != key.venue.value
            or context.symbol != key.instrument.symbol
            or key.instrument.venue != key.venue
        ):
            return policy(
                "source_observation",
                "baseline lineage contains actual LIVE CT-10 bid/ask facts for "
                "its venue and instrument",
            )
        observations.append(source)
    sides = {item.market_data.side for item in observations if item.market_data is not None}
    if sides != {"bid", "ask"}:
        return invalid("source_archive_fp1s", "baseline lineage contains both actual quote sides")
    return Ok(tuple(observations))


def _decode_sqs_baseline(body: Mapping[str, object]) -> Result[SqsBaselineArtifact]:
    if (
        body.get("class") != "qmn-sqs-baseline-envelope-v1"
        or type(body.get("format_version")) is not int
        or body.get("format_version") != ADMISSION_ARTIFACT_FORMAT_VERSION
        or set(body)
        != {
            "class",
            "format_version",
            "artifact",
            "artifact_fp1",
            "source_archive_fp1s",
            "calendar_identity",
            "derivation_status",
            "conditioning",
        }
    ):
        return invalid("artifact", "SQS private envelope has its exact class and format version")
    raw_artifact = body.get("artifact")
    if not isinstance(raw_artifact, Mapping):
        return invalid("artifact", "SQS envelope carries typed artifact identity content")
    payload = cast(Mapping[str, object], raw_artifact)
    required = {
        "class",
        "key",
        "average_spread",
        "session_window_id",
        "statistic",
        "refit_series_id",
        "refit_policy_fp",
    }
    if set(payload) - (required | {"dispersion"}) or required - set(payload):
        return invalid("artifact", "SQS baseline identity has exact contract fields")
    if payload.get("class") != "sqs-baseline-artifact":
        return invalid("artifact.class", "typed baseline identity is recognized")
    key_body = payload.get("key")
    if not isinstance(key_body, Mapping):
        return invalid("key", "SQS baseline carries its official key identity")
    key_map = cast(Mapping[str, object], key_body)
    instrument_body = key_map.get("instrument")
    if not isinstance(instrument_body, Mapping):
        return invalid("key.instrument", "SQS key carries an instrument identity")
    instrument_map = cast(Mapping[str, object], instrument_body)
    venue = VenueId.try_create(key_map.get("venue"))
    instrument_venue = VenueId.try_create(instrument_map.get("venue"))
    if is_refusal(venue):
        return venue
    if is_refusal(instrument_venue):
        return instrument_venue
    if instrument_venue.value != venue.value:
        return policy("key.instrument", "baseline key instrument and venue identities agree")
    instrument = Instrument.try_create(venue.value, instrument_map.get("symbol"))
    if is_refusal(instrument):
        return instrument
    key = sqs_baseline_key(venue.value, key_map.get("environment"), instrument.value)
    if is_refusal(key):
        return key
    average = _decode_price_delta(payload.get("average_spread"), instrument.value)
    if is_refusal(average):
        return average
    dispersion: PriceDelta | None = None
    if "dispersion" in payload:
        parsed_dispersion = _decode_price_delta(payload.get("dispersion"), instrument.value)
        if is_refusal(parsed_dispersion):
            return parsed_dispersion
        dispersion = parsed_dispersion.value
    session = payload.get("session_window_id")
    statistic = payload.get("statistic")
    series = payload.get("refit_series_id")
    if any(not isinstance(item, str) or not item.strip() for item in (session, statistic, series)):
        return invalid(
            "conditioning",
            "session, statistic, and refit-series declarations are nonblank",
        )
    refit = _coerce_fp(payload.get("refit_policy_fp"), "refit_policy_fp")
    if is_refusal(refit):
        return refit
    return _revalidate_sqs_baseline(
        SqsBaselineArtifact(
            key=key.value,
            average_spread=average.value,
            session_window_id=cast(str, session),
            statistic=cast(str, statistic),
            refit_series_id=cast(str, series),
            refit_policy_fp=refit.value,
            dispersion=dispersion,
        )
    )


def _decode_price_delta(value: object, instrument: Instrument) -> Result[PriceDelta]:
    if not isinstance(value, Mapping):
        return invalid("price_delta", "SQS spread value carries a typed price-delta identity")
    body = cast(Mapping[str, object], value)
    numerator, denominator = body.get("num"), body.get("den")
    if (
        body.get("class") != "price-delta"
        or type(numerator) is not int
        or type(denominator) is not int
        or denominator <= 0
    ):
        return invalid("price_delta", "price-delta identity carries exact rational integers")
    for scale in range(73):
        scaled = numerator * (10**scale)
        if scaled % denominator == 0:
            return PriceDelta.try_create(scaled // denominator, instrument, scale)
    return invalid("price_delta", "price-delta magnitude has a representable exact decimal scale")


def _live_world_store(store: object) -> Result[WorldStore]:
    if type(store) is not EvidenceStore:
        return invalid("store", "admission artifacts use the exact QMF EvidenceStore")
    world_store = store.for_world(World.LIVE)
    if is_refusal(world_store):
        return world_store
    if world_store.value.world is not World.LIVE:
        return policy("world", "admission artifacts persist in the LIVE QMF namespace")
    return world_store


def _valid_store_receipt(receipt: object, expected_fp: Fingerprint) -> bool:
    return (
        type(receipt) is StoreReceipt
        and receipt.fingerprint == expected_fp
        and receipt.world is World.LIVE
        and receipt.room_role is RoomRole.IMMUTABLE_RAW_ARCHIVE
        and receipt.engine == "parquet"
        and receipt.is_evidence_bearing is True
        and receipt.retained_forever is True
        and type(receipt.format_version) is int
        and receipt.format_version == 1
        and type(receipt.outcome) is WriteOutcome
        and receipt.sequence is None
        and receipt.engine_major is None
        and receipt.rebuild_calendar_identity is None
        and receipt.rebuild_tzdata_version is None
    )


def _artifact_fingerprint(body: Mapping[str, object]) -> Result[Fingerprint]:
    return fingerprint(dict(body))


def _revalidate_reference(value: object) -> Result[AdmissionArtifactRef]:
    if type(value) is not AdmissionArtifactRef:
        return invalid("reference", "artifact reader consumes its typed CT-11 receipt")
    ref = value
    if type(ref.artifact_class) is not str or ref.artifact_class not in _ARTIFACT_CLASSES:
        return invalid("artifact_class", "private admission artifact kind is registered")
    artifact_fp = _coerce_fp(ref.artifact_fp1, "artifact_fp1")
    archive_fp = _coerce_fp(ref.archive_fp1, "archive_fp1")
    if is_refusal(artifact_fp):
        return artifact_fp
    if is_refusal(archive_fp):
        return archive_fp
    if type(ref.source_archive_fp1s) is not tuple:
        return invalid("source_archive_fp1s", "receipt lineage is an immutable tuple")
    source_refs: list[Fingerprint] = []
    for raw_ref in cast(tuple[object, ...], ref.source_archive_fp1s):
        parsed = _coerce_fp(raw_ref, "source_archive_fp1s")
        if is_refusal(parsed):
            return parsed
        source_refs.append(parsed.value)
    if len({item.value for item in source_refs}) != len(source_refs):
        return invalid("source_archive_fp1s", "receipt lineage refs are unique")
    calendar: Mapping[str, object] | None = None
    if ref.calendar_identity is not None:
        checked_calendar = _revalidate_calendar(ref.calendar_identity)
        if is_refusal(checked_calendar):
            return checked_calendar
        calendar = checked_calendar.value
    if ref.artifact_class in {"sqs-baseline-artifact", "sqs-baseline-derivation"}:
        if not source_refs or calendar is None:
            return invalid("reference", "SQS receipt carries quote-source and calendar lineage")
    elif source_refs or calendar is not None:
        return invalid("reference", "signature-page receipt has no unbound SQS lineage")
    return Ok(
        AdmissionArtifactRef(
            artifact_class=ref.artifact_class,
            artifact_fp1=artifact_fp.value,
            archive_fp1=archive_fp.value,
            source_archive_fp1s=tuple(source_refs),
            calendar_identity=calendar,
        )
    )


def _revalidate_sqs_baseline(value: object) -> Result[SqsBaselineArtifact]:
    if type(value) is not SqsBaselineArtifact:
        return invalid("artifact", "SQS baseline input is the exact typed artifact")
    artifact = value
    if type(artifact.key) is not SqsBaselineKey:
        return invalid("key", "SQS artifact carries the exact typed SqsBaselineKey")
    key = artifact.key
    if (
        type(key.venue) is not VenueId
        or type(key.instrument) is not Instrument
        or type(key.instrument.venue) is not VenueId
    ):
        return invalid("key", "SQS key identities are official VenueId and Instrument values")
    venue = VenueId.try_create(key.venue.value)
    instrument_venue = VenueId.try_create(key.instrument.venue.value)
    if is_refusal(venue):
        return venue
    if is_refusal(instrument_venue):
        return instrument_venue
    if venue.value != instrument_venue.value:
        return policy("key", "SQS key instrument and venue identities match")
    instrument = Instrument.try_create(venue.value, key.instrument.symbol)
    if is_refusal(instrument):
        return instrument
    checked_key = sqs_baseline_key(venue.value, key.environment, instrument.value)
    if is_refusal(checked_key):
        return checked_key
    if key.environment != "live":
        return policy("environment", "LIVE baseline uses the live conditioning key")
    if type(artifact.average_spread) is not PriceDelta:
        return invalid("average_spread", "SQS average is a typed PriceDelta")
    average_instrument = _revalidate_instrument(artifact.average_spread.instrument)
    if is_refusal(average_instrument):
        return average_instrument
    if average_instrument.value != instrument.value:
        return policy("average_spread", "average spread is tagged by the baseline instrument")
    average = PriceDelta.try_create(
        artifact.average_spread.value,
        instrument.value,
        artifact.average_spread.scale,
    )
    if is_refusal(average):
        return average
    dispersion: PriceDelta | None = None
    if artifact.dispersion is not None:
        if type(artifact.dispersion) is not PriceDelta:
            return invalid("dispersion", "SQS dispersion is absent or a typed PriceDelta")
        dispersion_instrument = _revalidate_instrument(artifact.dispersion.instrument)
        if is_refusal(dispersion_instrument):
            return dispersion_instrument
        if dispersion_instrument.value != instrument.value:
            return policy("dispersion", "dispersion is tagged by the baseline instrument")
        checked_dispersion = PriceDelta.try_create(
            artifact.dispersion.value,
            instrument.value,
            artifact.dispersion.scale,
        )
        if is_refusal(checked_dispersion):
            return checked_dispersion
        dispersion = checked_dispersion.value
    for field, token in (
        ("session_window_id", artifact.session_window_id),
        ("statistic", artifact.statistic),
        ("refit_series_id", artifact.refit_series_id),
    ):
        if type(token) is not str or not token.strip():
            return invalid(field, "SQS conditioning declaration is a nonblank string")
    if type(artifact.refit_policy_fp) is not Fingerprint:
        return invalid("refit_policy_fp", "SQS refit policy is a typed fingerprint")
    refit_fp = _coerce_fp(artifact.refit_policy_fp, "refit_policy_fp")
    if is_refusal(refit_fp):
        return refit_fp
    return Ok(
        SqsBaselineArtifact(
            key=checked_key.value,
            average_spread=average.value,
            session_window_id=artifact.session_window_id,
            statistic=artifact.statistic,
            refit_series_id=artifact.refit_series_id,
            refit_policy_fp=refit_fp.value,
            dispersion=dispersion,
        )
    )


def _revalidate_calendar(value: object) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid("calendar_identity", "receipt calendar is a canonical identity mapping")
    raw_calendar = cast(Mapping[str, object], value)
    checked_calendar = CalendarIdentity.try_create(
        raw_calendar.get("rule_set"),
        raw_calendar.get("rule_set_version"),
        raw_calendar.get("tzdata_version"),
    )
    if is_refusal(checked_calendar):
        return checked_calendar
    identity = checked_calendar.value.fp1_identity()
    if dict(raw_calendar) != identity:
        return invalid("calendar_identity", "receipt cites the official CalendarIdentity body")
    return Ok(MappingProxyType(identity))


def _revalidate_instrument(value: object) -> Result[Instrument]:
    if type(value) is not Instrument or type(value.venue) is not VenueId:
        return invalid("instrument", "price data carries an official Instrument identity")
    venue = VenueId.try_create(value.venue.value)
    if is_refusal(venue):
        return venue
    return Instrument.try_create(venue.value, value.symbol)


def _coerce_fp(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value.value if type(value) is Fingerprint else value)
    if is_refusal(parsed):
        return invalid(field, "identity reference is a canonical fp1 fingerprint")
    return parsed
