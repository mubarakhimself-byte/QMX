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
from qmf.data.store import EvidenceStore, StoreReceipt
from qmf.data.store.rooms import RoomRole

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.shakedown import ShakedownSignaturePage
from qmn.mis.catalog import SqsBaselineArtifact
from qmn.mis.signal_snapshot import SqsBaselineKey, sqs_baseline_key

__all__ = [
    "ADMISSION_ARTIFACT_FORMAT_VERSION",
    "AdmissionArtifactRef",
    "PersistedSqsBaseline",
    "persist_shakedown_signature_page",
    "persist_sqs_baseline",
    "read_admission_artifact",
]

ADMISSION_ARTIFACT_FORMAT_VERSION: Final[int] = 1
_ARTIFACT_ROW_CLASS: Final[str] = "qmn-admission-artifact-row-v1"
_ARTIFACT_CLASSES: Final[frozenset[str]] = frozenset(
    {"shakedown-signature-page", "sqs-baseline-artifact"}
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
    """Reopened typed SQS input plus verified source-observation lineage."""

    artifact: SqsBaselineArtifact
    reference: AdmissionArtifactRef


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
        return invalid("source_archive_fp1s", "baseline lineage is a sequence of CT-10 archive refs")
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
    body = {
        "class": "qmn-sqs-baseline-envelope-v1",
        "format_version": ADMISSION_ARTIFACT_FORMAT_VERSION,
        "artifact": artifact.fp1_identity(),
        "artifact_fp1": _artifact_fingerprint(artifact.fp1_identity()).value.value,
        "source_archive_fp1s": [ref.value for ref in refs],
        "calendar_identity": rebuilt_calendar.value.fp1_identity(),
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


def read_admission_artifact(
    store: object,
    reference: object,
) -> Result[Mapping[str, object]]:
    """Reopen and verify the exact immutable CT-11 row and its inner body."""
    if type(reference) is not AdmissionArtifactRef:
        return invalid("reference", "artifact reader consumes its typed CT-11 receipt")
    if reference.artifact_class not in _ARTIFACT_CLASSES:
        return invalid("artifact_class", "private admission artifact kind is registered")
    world_store = _live_world_store(store)
    if is_refusal(world_store):
        return world_store
    rows = world_store.value.append_store.read_raw(reference.archive_fp1, for_world=World.LIVE)
    if is_refusal(rows):
        return rows
    if len(rows.value) != 1 or not isinstance(rows.value[0], Mapping):
        return policy("artifact_row", "admission artifact reopens as one canonical row")
    row = cast(Mapping[str, object], rows.value[0])
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
    return Ok(row_body)


def read_sqs_baseline(
    store: object,
    reference: object,
) -> Result[PersistedSqsBaseline]:
    """Reopen a typed SQS baseline and recheck every cited LIVE CT-10 source."""
    if type(reference) is not AdmissionArtifactRef or reference.artifact_class != "sqs-baseline-artifact":
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
    return Ok(PersistedSqsBaseline(artifact=artifact.value, reference=reference))


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


def _decode_row(
    row: Mapping[str, object],
) -> Result[tuple[Mapping[str, object], str, Fingerprint, tuple[Fingerprint, ...], Mapping[str, object] | None]]:
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
    for raw_ref in raw_refs:
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
                "baseline lineage contains actual LIVE CT-10 bid/ask facts for its venue and instrument",
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
        return invalid("conditioning", "session, statistic, and refit-series declarations are nonblank")
    refit = _coerce_fp(payload.get("refit_policy_fp"), "refit_policy_fp")
    if is_refusal(refit):
        return refit
    return Ok(
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


def _live_world_store(store: object) -> Result[object]:
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
        and type(receipt.outcome) is WriteOutcome
    )


def _artifact_fingerprint(body: Mapping[str, object]) -> Result[Fingerprint]:
    return fingerprint(dict(body))


def _coerce_fp(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value.value if type(value) is Fingerprint else value)
    if is_refusal(parsed):
        return invalid(field, "identity reference is a canonical fp1 fingerprint")
    return parsed
