"""Derive a LIVE SQS baseline from checked CT-10 quote facts.

The calendar is supplied by the application root and must be the official pinned
CT-02 provider whose identity is recorded on the artifact. This module does not
infer market sessions from civil dates or timestamps. It only accepts observations
for which that provider returns the containing ``SessionWindow``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, cast

from qmf.core import (
    CalendarIdentity,
    Fingerprint,
    Instrument,
    Ok,
    PriceDelta,
    Result,
    SessionWindow,
    VenueId,
    World,
    canonical_bytes,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import Instant
from qmf.data.observation import SourceObservation
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.store import EvidenceStore
from qmf.readings.catalog import SqsBaselineArtifact
from qmf.readings.signal_snapshot import SqsBaselineKey

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.admission_artifacts import (
    AdmissionArtifactRef,
    PersistedSqsBaseline,
    persist_sqs_baseline,
    persist_sqs_baseline_derivation,
    read_sqs_baseline,
    read_sqs_baseline_derivation_receipt,
)

__all__ = [
    "MarketHoursCalendar",
    "SqsBaselineProduction",
    "SqsBaselineStatistic",
    "produce_sqs_baseline",
    "read_sqs_baseline_derivation",
]

_MAX_PRICE_SCALE = 18
_STATISTIC_LABEL: dict[str, str] = {
    "mean": "mean",
    "median": "median",
}


class MarketHoursCalendar(Protocol):
    """The existing CT-02 market-hours provider surface."""

    identity: CalendarIdentity

    def session_window(self, instant: object) -> Result[SessionWindow | None]: ...


class MarketHoursCalendarRegistration(Protocol):
    """The explicit CT-02 composition registration and its venue binding."""

    provider: MarketHoursCalendar
    calendar_identity: CalendarIdentity
    binding: object

    def artifact_fingerprint(self) -> Result[Fingerprint]: ...


class SqsBaselineStatistic(StrEnum):
    """Explicit supported exact statistics; no implicit choice or quantile shape."""

    MEAN = "mean"
    MEDIAN = "median"


class SqsRoundingPolicy(StrEnum):
    """Exact arithmetic contract carried in the statistic identity."""

    EXACT_DECIMAL_NO_ROUNDING = "exact-decimal-no-rounding-v1"


@dataclass(frozen=True, slots=True)
class SqsBaselineProduction:
    """A fit whose durable private recipe passed fresh-store source recomputation."""

    persisted: PersistedSqsBaseline
    reference: AdmissionArtifactRef
    derivation_reference: AdmissionArtifactRef
    sample_count: int
    statistic: str
    session_id: str
    rounding_policy: str
    session_occurrence_fp1s: tuple[Fingerprint, ...]
    calendar_registration_fp1: Fingerprint


@dataclass(frozen=True, slots=True)
class _Quote:
    observation: SourceObservation
    value: int
    scale: int
    side: str


def produce_sqs_baseline(
    store: object,
    *,
    key: object,
    source_archive_fp1s: object,
    calendar: object,
    calendar_identity: object,
    session_id: object,
    statistic: object,
    rounding_policy: object,
    refit_series_id: object,
    refit_policy_fp: object,
) -> Result[SqsBaselineProduction]:
    """Derive, persist, reopen, and recompute an exact LIVE SQS baseline.

    The declared statistic is ``mean`` or ``median``. The arithmetic is exact
    decimal only: the result is represented at the source quote scale or an
    increased decimal scale up to qmf-core's supported limit. If it cannot be
    represented exactly, this method refuses; it never rounds. Quantiles remain
    unsupported because the governing declaration does not specify their shape.
    """
    checked = _validate_inputs(
        store,
        key=key,
        source_archive_fp1s=source_archive_fp1s,
        calendar=calendar,
        calendar_identity=calendar_identity,
        session_id=session_id,
        statistic=statistic,
        rounding_policy=rounding_policy,
        refit_series_id=refit_series_id,
        refit_policy_fp=refit_policy_fp,
    )
    if not is_ok(checked):
        return checked
    (
        evidence_store,
        baseline_key,
        refs,
        provider,
        calendar_registration_fp,
        calendar_id,
        session_token,
        statistic_token,
        rounding_token,
        series_token,
        refit_fp,
    ) = checked.value
    quotes = _read_quotes(evidence_store, refs, baseline_key)
    if is_refusal(quotes):
        return quotes
    grouped = _group_quote_samples(quotes.value)
    if is_refusal(grouped):
        return grouped
    samples, source_scale = grouped.value
    occurrences = _resolve_session_occurrences(
        provider,
        calendar_id,
        calendar_registration_fp,
        [quote.observation for quote in quotes.value],
    )
    if not is_ok(occurrences):
        return occurrences
    session_identity = _conditioned_session_id(session_token, calendar_registration_fp)
    if is_refusal(session_identity):
        return session_identity
    average = _derive_statistic(
        [spread for spread, _ in samples],
        instrument=baseline_key.instrument,
        scale=source_scale,
        statistic=statistic_token,
    )
    if is_refusal(average):
        return average
    artifact = SqsBaselineArtifact(
        key=baseline_key,
        average_spread=average.value,
        session_window_id=session_identity.value,
        statistic=f"{statistic_token}/{rounding_token}",
        refit_series_id=series_token,
        refit_policy_fp=refit_fp,
    )
    persisted_ref = persist_sqs_baseline(
        evidence_store,
        artifact,
        source_archive_fp1s=refs,
        calendar_identity=calendar_id,
    )
    if is_refusal(persisted_ref):
        return persisted_ref
    fit_ref = persist_sqs_baseline_derivation(
        evidence_store,
        baseline_reference=persisted_ref.value,
        average_spread=average.value,
        sample_count=len(samples),
        session_id=session_token,
        statistic=statistic_token,
        rounding_policy=rounding_token,
        refit_series_id=series_token,
        refit_policy_fp=refit_fp,
        session_occurrence_fp1s=occurrences.value,
        calendar_registration_fp1=calendar_registration_fp,
    )
    if is_refusal(fit_ref):
        return fit_ref
    # The checked fit read path uses a new store facade, reopens both CT-11
    # receipts and all cited CT-10 rows, then recomputes from the durable recipe.
    return read_sqs_baseline_derivation(
        EvidenceStore(evidence_store.root), fit_ref.value, calendar=calendar
    )


def read_sqs_baseline_derivation(
    store: object,
    reference: object,
    *,
    calendar: object,
) -> Result[SqsBaselineProduction]:
    """Reopen a private fit recipe and prove its statistic from current CT-10 reads.

    ``PersistedSqsBaseline.derivation_verified`` remains false by design. This
    richer result is available only after a fresh physical-source recomputation.
    """
    if type(store) is not EvidenceStore:
        return invalid("store", "SQS derivation readback uses the official EvidenceStore")
    receipt = read_sqs_baseline_derivation_receipt(store, reference)
    if is_refusal(receipt):
        return receipt
    baseline = read_sqs_baseline(store, receipt.value.baseline_reference)
    if is_refusal(baseline):
        return baseline
    calendar_body = receipt.value.baseline_reference.calendar_identity
    if calendar_body is None:
        return invalid("calendar_identity", "fit input pins an official CT-02 identity")
    calendar_id = CalendarIdentity.try_create(
        calendar_body.get("rule_set"),
        calendar_body.get("rule_set_version"),
        calendar_body.get("tzdata_version"),
    )
    if not is_ok(calendar_id):
        return calendar_id
    checked = _validate_inputs(
        store,
        key=baseline.value.artifact.key,
        source_archive_fp1s=receipt.value.baseline_reference.source_archive_fp1s,
        calendar=calendar,
        calendar_identity=calendar_id.value,
        session_id=receipt.value.session_id,
        statistic=receipt.value.statistic,
        rounding_policy=receipt.value.rounding_policy,
        refit_series_id=receipt.value.refit_series_id,
        refit_policy_fp=receipt.value.refit_policy_fp,
    )
    if not is_ok(checked):
        return checked
    (
        evidence_store,
        key,
        refs,
        provider,
        calendar_registration_fp,
        checked_calendar_id,
        session_id,
        statistic,
        rounding_policy,
        _refit_series_id,
        _refit_policy_fp,
    ) = checked.value
    if calendar_registration_fp != receipt.value.calendar_registration_fp1:
        return policy(
            "calendar_registration", "fit receipt binds the reopened official CT-02 registration"
        )
    quotes = _read_quotes(evidence_store, refs, key)
    if is_refusal(quotes):
        return quotes
    grouped = _group_quote_samples(quotes.value)
    if is_refusal(grouped):
        return grouped
    samples, source_scale = grouped.value
    occurrences = _resolve_session_occurrences(
        provider,
        checked_calendar_id,
        calendar_registration_fp,
        [quote.observation for quote in quotes.value],
    )
    if not is_ok(occurrences):
        return occurrences
    if (
        len(samples) != receipt.value.sample_count
        or occurrences.value != receipt.value.session_occurrence_fp1s
    ):
        return policy(
            "derivation_inputs", "stored sample and official-window lineage recomputes exactly"
        )
    conditioned_session = _conditioned_session_id(session_id, calendar_registration_fp)
    if not is_ok(conditioned_session):
        return conditioned_session
    if baseline.value.artifact.session_window_id != conditioned_session.value:
        return policy(
            "session_id", "persisted baseline and fit recipe share stable session conditioning"
        )
    recomputed = _derive_statistic(
        [spread for spread, _ in samples],
        instrument=key.instrument,
        scale=source_scale,
        statistic=statistic,
    )
    if is_refusal(recomputed):
        return recomputed
    if (
        recomputed.value.as_fraction() != baseline.value.artifact.average_spread.as_fraction()
        or recomputed.value.as_fraction() != receipt.value.average_spread.as_fraction()
    ):
        return policy(
            "baseline_recompute", "physical CT-10 quotes reproduce the exact persisted quantity"
        )
    return Ok(
        SqsBaselineProduction(
            persisted=baseline.value,
            reference=receipt.value.baseline_reference,
            derivation_reference=receipt.value.reference,
            sample_count=len(samples),
            statistic=statistic,
            session_id=session_id,
            rounding_policy=rounding_policy,
            session_occurrence_fp1s=occurrences.value,
            calendar_registration_fp1=calendar_registration_fp,
        )
    )


def _validate_inputs(
    store: object,
    *,
    key: object,
    source_archive_fp1s: object,
    calendar: object,
    calendar_identity: object,
    session_id: object,
    statistic: object,
    rounding_policy: object,
    refit_series_id: object,
    refit_policy_fp: object,
) -> Result[
    tuple[
        EvidenceStore,
        SqsBaselineKey,
        tuple[Fingerprint, ...],
        MarketHoursCalendar,
        Fingerprint,
        CalendarIdentity,
        str,
        str,
        str,
        str,
        Fingerprint,
    ]
]:
    if type(store) is not EvidenceStore:
        return invalid("store", "baseline producer requires the official EvidenceStore")
    if type(key) is not SqsBaselineKey:
        return invalid("key", "baseline producer requires a typed SqsBaselineKey")
    baseline_key = key
    if baseline_key.environment != "live":
        return policy("environment", "SQS baseline production is explicitly LIVE")
    if type(baseline_key.venue) is not VenueId or type(baseline_key.instrument) is not Instrument:
        return invalid("key", "baseline key carries official venue and instrument identities")
    if not isinstance(source_archive_fp1s, Sequence) or isinstance(
        source_archive_fp1s, (str, bytes)
    ):
        return invalid("source_archive_fp1s", "source refs are an explicit sequence")
    refs: list[Fingerprint] = []
    for raw in cast(Sequence[object], source_archive_fp1s):
        parsed = Fingerprint.try_create(raw.value if type(raw) is Fingerprint else raw)
        if is_refusal(parsed):
            return parsed
        refs.append(parsed.value)
    if len(refs) < 2 or len({ref.value for ref in refs}) != len(refs):
        return invalid(
            "source_archive_fp1s", "baseline cites at least two unique quote observations"
        )
    provider_object = getattr(calendar, "provider", None)
    if not callable(getattr(provider_object, "session_window", None)):
        return invalid("calendar", "calendar is an explicit registration with official provider")
    if type(calendar_identity) is not CalendarIdentity:
        return invalid("calendar_identity", "conditioning carries an official CalendarIdentity")
    checked_id = CalendarIdentity.try_create(
        calendar_identity.rule_set,
        calendar_identity.rule_set_version,
        calendar_identity.tzdata_version,
    )
    if not is_ok(checked_id):
        return checked_id
    registration = cast(MarketHoursCalendarRegistration, calendar)
    provider = registration.provider
    if type(registration.calendar_identity) is not CalendarIdentity:
        return invalid("calendar.calendar_identity", "registration has official CalendarIdentity")
    if (
        registration.calendar_identity != checked_id.value
        or provider.identity != checked_id.value
        or provider.identity != calendar_identity
    ):
        return policy("calendar_identity", "registered provider and configured identity match")
    binding = getattr(registration, "binding", None)
    venue_ids_raw: object = getattr(binding, "venue_ids", None)
    if not isinstance(venue_ids_raw, tuple):
        return policy("calendar_binding", "official registration explicitly binds the SQS venue")
    venue_ids = cast(tuple[object, ...], venue_ids_raw)
    if any(type(venue_id) is not str for venue_id in venue_ids):
        return invalid("calendar_binding", "calendar venue identifiers are exact strings")
    if baseline_key.venue.value not in venue_ids:
        return policy("calendar_binding", "official registration explicitly binds the SQS venue")
    if not callable(getattr(calendar, "artifact_fingerprint", None)):
        return invalid("calendar", "registration exposes official extension artifact identity")
    calendar_artifact_fp = registration.artifact_fingerprint()
    if not is_ok(calendar_artifact_fp):
        return calendar_artifact_fp
    session_token = _token(session_id, "session_id")
    statistic_token = _token(statistic, "statistic")
    rounding_token = _token(rounding_policy, "rounding_policy")
    series_token = _token(refit_series_id, "refit_series_id")
    if not is_ok(session_token):
        return session_token
    if not is_ok(statistic_token):
        return statistic_token
    if not is_ok(rounding_token):
        return rounding_token
    if not is_ok(series_token):
        return series_token
    if statistic_token.value not in _STATISTIC_LABEL:
        return unavailable("statistic", "only explicitly declared mean and median are implemented")
    if rounding_token.value != SqsRoundingPolicy.EXACT_DECIMAL_NO_ROUNDING.value:
        return unavailable(
            "rounding_policy", "only exact decimal arithmetic without rounding is implemented"
        )
    if type(refit_policy_fp) is not Fingerprint:
        return invalid("refit_policy_fp", "refit policy identity is an official Fingerprint")
    refit = Fingerprint.try_create(refit_policy_fp.value)
    if not is_ok(refit):
        return refit
    return Ok(
        (
            store,
            baseline_key,
            tuple(refs),
            provider,
            calendar_artifact_fp.value,
            checked_id.value,
            session_token.value,
            statistic_token.value,
            rounding_token.value,
            series_token.value,
            refit.value,
        )
    )


def _read_quotes(
    store: EvidenceStore,
    refs: tuple[Fingerprint, ...],
    key: SqsBaselineKey,
) -> Result[tuple[_Quote, ...]]:
    boundary = SourceObservationBoundary(store)
    quotes: list[_Quote] = []
    for ref in refs:
        result = boundary.read(ref, in_world=World.LIVE, for_world=World.LIVE)
        if is_refusal(result):
            return result
        observation = result.value
        context = observation.market_data
        amount = observation.foreign_money
        if (
            type(observation) is not SourceObservation
            or observation.world is not World.LIVE
            or observation.is_correction
            or context is None
            or amount is None
            or context.side not in ("bid", "ask")
            or context.venue != key.venue.value
            or context.symbol != key.instrument.symbol
            or key.instrument.venue != key.venue
        ):
            return policy("quote", "source row is a LIVE quote for the configured key")
        if type(amount.verbatim) is not int or type(amount.scale) is not int:
            return invalid(
                "quote.price", "CT-10 quote is an exact integer at a declared decimal scale"
            )
        if amount.scale < 0 or amount.scale > _MAX_PRICE_SCALE:
            return invalid("quote.scale", "quote price scale is in the supported exact range")
        quotes.append(_Quote(observation, amount.verbatim, amount.scale, context.side))
    return Ok(tuple(quotes))


def _group_quote_samples(
    quotes: tuple[_Quote, ...],
) -> Result[tuple[tuple[tuple[int, tuple[int, int, str, str, str, str, str]], ...], int]]:
    if not quotes:
        return invalid("quotes", "baseline requires persisted quote observations")
    scales = {quote.scale for quote in quotes}
    if len(scales) != 1:
        return policy("quote.scale", "all quotes use one declared instrument price scale")
    grouped: dict[tuple[int, int, str, str, str, str, str], dict[str, _Quote]] = {}
    for quote in quotes:
        context = quote.observation.market_data
        if context is None:
            return invalid("quote", "a paired spread is sourced from checked market-data context")
        key = (
            quote.observation.event_time.value_ns,
            quote.observation.known_at.value_ns,
            context.resolution,
            quote.observation.source,
            quote.observation.source_native_id,
            quote.observation.revision,
            context.license_tag,
        )
        side_map = grouped.setdefault(key, {})
        if quote.side in side_map:
            return invalid("quotes", "one bid and one ask exist for each exact source frontier")
        side_map[quote.side] = quote
    samples: list[tuple[int, tuple[int, int, str, str, str, str, str]]] = []
    for sample_key, sides in grouped.items():
        if set(sides) != {"bid", "ask"}:
            return invalid("quotes", "each quote frontier contains both bid and ask")
        bid, ask = sides["bid"], sides["ask"]
        if ask.value < bid.value:
            return policy("quotes", "recorded ask is not below the recorded bid")
        samples.append((ask.value - bid.value, sample_key))
    samples.sort(key=lambda sample: sample[1])
    return Ok((tuple(samples), next(iter(scales))))


def _resolve_session_occurrences(
    calendar: MarketHoursCalendar,
    identity: CalendarIdentity,
    registration_fp: Fingerprint,
    observations: Sequence[SourceObservation],
) -> Result[tuple[Fingerprint, ...]]:
    occurrences: dict[str, Fingerprint] = {}
    for item in observations:
        observation = item
        if type(observation.event_time) is not Instant:
            return invalid("event_time", "calendar lookup uses the checked CT-10 event Instant")
        window = calendar.session_window(observation.event_time)
        if is_refusal(window):
            return window
        if window.value is None:
            return policy(
                "session", "all baseline quote facts fall inside an open calendar session"
            )
        if type(window.value) is not SessionWindow:
            return invalid("session_window", "official calendar returns a typed SessionWindow")
        contains = window.value.contains(observation.event_time)
        if is_refusal(contains):
            return contains
        if not contains.value:
            return policy("session", "official session window contains the quote event time")
        occurrence = fingerprint(
            {
                "class": "qmn-sqs-session-occurrence-v1",
                "calendar_identity": identity.fp1_identity(),
                "calendar_registration_fp1": registration_fp.value,
                "open_ns": window.value.open_instant.value_ns,
                "close_ns": window.value.close_instant.value_ns,
                "zone": window.value.zone,
            }
        )
        if is_refusal(occurrence):
            return occurrence
        occurrences[occurrence.value.value] = occurrence.value
    if not occurrences:
        return invalid("session", "at least one checked session occurrence is required")
    return Ok(tuple(occurrences[key] for key in sorted(occurrences)))


def _conditioned_session_id(
    session_id: str,
    calendar_registration_fp: Fingerprint,
) -> Result[str]:
    encoded = canonical_bytes(
        {
            "class": "qmn-sqs-session-conditioning-v1",
            "session_id": session_id,
            "calendar_registration_fp1": calendar_registration_fp.value,
        }
    )
    if is_refusal(encoded):
        return encoded
    return Ok(encoded.value.decode("utf-8"))


def _derive_statistic(
    spreads: list[int], *, instrument: Instrument, scale: int, statistic: str
) -> Result[PriceDelta]:
    if not spreads:
        return invalid("statistic", "at least one complete bid/ask spread is required")
    if statistic == SqsBaselineStatistic.MEAN:
        numerator, denominator = sum(spreads), len(spreads)
    elif statistic == SqsBaselineStatistic.MEDIAN:
        ordered = sorted(spreads)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            numerator, denominator = ordered[middle], 1
        else:
            numerator, denominator = ordered[middle - 1] + ordered[middle], 2
    else:
        return unavailable("statistic", "statistic is not implemented by this exact producer")
    multiplier = 1
    result_scale = scale
    while numerator * multiplier % denominator != 0 and result_scale < _MAX_PRICE_SCALE:
        multiplier *= 10
        result_scale += 1
    if numerator * multiplier % denominator != 0:
        return unavailable(
            "rounding",
            "statistic is not exactly representable within the declared decimal scale range",
        )
    return PriceDelta.try_create(numerator * multiplier // denominator, instrument, result_scale)


def _token(value: object, field: str) -> Result[str]:
    if type(value) in (SqsBaselineStatistic, SqsRoundingPolicy):
        value = cast(StrEnum, value).value
    if type(value) is not str or not value.strip():
        return invalid(field, "conditioning is an explicitly declared nonblank token")
    return Ok(value)
