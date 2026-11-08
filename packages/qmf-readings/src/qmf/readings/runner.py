"""The reading runner: reading blocks over a market's quotes, records through Part B's writer.

One code for every place a reading is computed (MIS-04). :class:`Readings` turns each quote
into the block's frontier frame and evaluates every bound block on it; a unit computing a
reading itself (its ``compute_here`` fallback) uses it as it stands. :class:`ReadingRunner`
adds the place, the clock and the journal: the node and the ``mis`` app open it on a hot-path
writer, QMB on a bundle writer, and every result becomes one stamped reading record.

This runner is event-driven: each quote is a frontier. It carries what a block needs from the
previous frontier, the last SQS hard block for the score's hysteresis.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Final

from qmf.core import (
    Duration,
    ExactRational,
    Instant,
    Instrument,
    Ok,
    Price,
    PriceDelta,
    Result,
    is_refusal,
)
from qmf.data.journal_envelope import JournalStream, RowFacts
from qmf.data.journal_writer import JournalWriter
from qmf.readings._refuse import invalid
from qmf.readings.catalog import (
    ConfiguredMisProducer,
    FrontierFrame,
    ProducerEmission,
    SqsBaselineArtifact,
)
from qmf.readings.labelers import evaluate_mis_producer
from qmf.readings.liquidity import LiquidityFitArtifact
from qmf.readings.record import (
    READING_KIND,
    Health,
    ReadingRecord,
    ReadingRef,
    ReadingSource,
    Tier,
    TimeBase,
)
from qmf.readings.signal_snapshot import SQS_PRODUCER_ID, ProducerReadiness

__all__ = [
    "Quote",
    "ReadingBinding",
    "ReadingOutputs",
    "ReadingRunner",
    "Readings",
    "outputs_of",
]

_HEALTH: Final[Mapping[ProducerReadiness, Health]] = {
    ProducerReadiness.OK: Health.FRESH,
    ProducerReadiness.STALE: Health.STALE,
    ProducerReadiness.NOT_READY: Health.THIN,
    ProducerReadiness.UNAVAILABLE: Health.DEGRADED,
    ProducerReadiness.REFUSED: Health.DEGRADED,
}
_QUOTE_CADENCE: Final[str] = "quote"
Clock = Callable[[], int]
"""The compute time in epoch nanoseconds, injected by the composition root."""
_TICK_RESOLUTION: Final[str] = "tick"


@dataclass(frozen=True, slots=True)
class Quote:
    """One normalised quote: when it was known, and both sides."""

    at: Instant
    bid: Price
    ask: Price


@dataclass(frozen=True, slots=True)
class ReadingBinding:
    """One reading block the runner computes, with the labels its records carry."""

    producer: ConfiguredMisProducer
    tier: Tier
    time_base: TimeBase
    data_level: int
    stale_after_s: int
    shadow: bool = False
    estimate: str | None = None
    sqs_baseline: SqsBaselineArtifact | None = None
    liquidity_fit: LiquidityFitArtifact | None = None
    decision_freshness_bound: Duration | None = None


@dataclass(frozen=True, slots=True)
class ReadingOutputs:
    """What a block's emission says, in the record's terms: its value, word and health."""

    value: ExactRational | None
    word: str | None
    health: Health


def outputs_of(binding: ReadingBinding, emission: ProducerEmission) -> ReadingOutputs:
    """A shadow reading is always ``shadow``; otherwise the block's readiness decides.

    The word is the labeler's own marker, kept only when the reading is ready; the value is
    the SQS score, the one V1 block with a number.
    """
    readiness = ProducerReadiness(emission.readiness)
    return ReadingOutputs(
        value=None if emission.sqs is None else emission.sqs.score,
        word=emission.marker_detail if readiness is ProducerReadiness.OK else None,
        health=Health.SHADOW if binding.shadow else _HEALTH[readiness],
    )


class Readings:
    """The blocks bound for one instrument, evaluated on each quote's frontier frame."""

    def __init__(
        self,
        bindings: Iterable[ReadingBinding],
        *,
        instrument: Instrument,
        environment: str,
        pip: PriceDelta,
    ) -> None:
        self._bindings = tuple(bindings)
        self._instrument = instrument
        self._environment = environment
        self._pip = pip
        self._previous_sqs_block: bool | None = None

    @property
    def bindings(self) -> tuple[ReadingBinding, ...]:
        return self._bindings

    def frame(self, quote: Quote) -> FrontierFrame:
        """The frame a quote makes: known at its own instant, with the carried SQS block."""
        return FrontierFrame(
            frontier_instant=quote.at,
            instrument=self._instrument,
            environment=self._environment,
            resolution=_TICK_RESOLUTION,
            known_at=quote.at,
            bid=quote.bid,
            ask=quote.ask,
            pip=self._pip,
            last_tick_at=quote.at,
            sample_cadence=_QUOTE_CADENCE,
            previous_sqs_hard_block=self._previous_sqs_block,
        )

    def step(self, quote: Quote) -> Result[tuple[ProducerEmission, ...]]:
        """Every bound block's emission at this quote, in binding order."""
        frame = self.frame(quote)
        emissions: list[ProducerEmission] = []
        for binding in self._bindings:
            emitted = evaluate_mis_producer(
                binding.producer,
                frame,
                sqs_baseline=binding.sqs_baseline,
                liquidity_fit=binding.liquidity_fit,
                decision_freshness_bound=binding.decision_freshness_bound,
            )
            if is_refusal(emitted):
                return emitted
            emissions.append(emitted.value)
            if binding.producer.producer_id == SQS_PRODUCER_ID and emitted.value.sqs is not None:
                self._previous_sqs_block = emitted.value.sqs.hard_block
        return Ok(tuple(emissions))


class ReadingRunner:
    """Writes one reading record per bound block and quote through a ``journal-readings`` writer.

    The writer's scope names the machine; its subject must be ``<source>.<market id>``, the
    readings journal's rule, so a record's place and its stream never disagree.
    """

    def __init__(
        self,
        readings: Readings,
        writer: JournalWriter,
        *,
        source: ReadingSource,
        market_id: str,
        clock: Clock,
        clock_ok: bool,
    ) -> None:
        self._readings = readings
        self._writer = writer
        self._source = source
        self._market_id = market_id
        self._clock = clock
        self._clock_ok = clock_ok

    @classmethod
    def open(
        cls,
        readings: Readings,
        writer: JournalWriter,
        *,
        source: ReadingSource,
        market_id: str,
        clock: Clock,
        clock_ok: bool,
    ) -> Result[ReadingRunner]:
        scope = writer.scope
        if scope.stream is not JournalStream.READINGS:
            return invalid(
                "writer", "reading records go to the readings journal", given=scope.stream.value
            )
        subject = f"{source.value}.{market_id}"
        if scope.subject != subject:
            return invalid(
                "writer",
                "a readings writer's subject is <source>.<market id>",
                given=scope.subject,
                expected=subject,
            )
        return Ok(
            cls(
                readings,
                writer,
                source=source,
                market_id=market_id,
                clock=clock,
                clock_ok=clock_ok,
            )
        )

    def on_quote(self, quote: Quote) -> Result[tuple[ReadingRecord, ...]]:
        """Compute every bound reading at this quote and append its record."""
        emissions = self._readings.step(quote)
        if is_refusal(emissions):
            return emissions
        computed_at = self._clock()
        records: list[ReadingRecord] = []
        for binding, emission in zip(self._readings.bindings, emissions.value, strict=True):
            record = self._record(binding, emission, quote, computed_at)
            if is_refusal(record):
                return record
            appended = self._writer.append(
                READING_KIND,
                record.value.body(),
                RowFacts(
                    ts_recv=quote.at.value_ns,
                    clock_ok=self._clock_ok,
                    market_id=self._market_id,
                ),
            )
            if is_refusal(appended):
                return appended
            records.append(record.value)
        return Ok(tuple(records))

    def run(self, quotes: Iterable[Quote]) -> Result[tuple[ReadingRecord, ...]]:
        """Every record of a run over ``quotes``, stopping at the first refusal."""
        records: list[ReadingRecord] = []
        for quote in quotes:
            step = self.on_quote(quote)
            if is_refusal(step):
                return step
            records.extend(step.value)
        return Ok(tuple(records))

    def _record(
        self,
        binding: ReadingBinding,
        emission: ProducerEmission,
        quote: Quote,
        computed_at: int,
    ) -> Result[ReadingRecord]:
        producer = binding.producer
        printed = producer.fingerprint()
        if is_refusal(printed):
            return printed
        said = outputs_of(binding, emission)
        return Ok(
            ReadingRecord(
                reading=ReadingRef(producer.producer_id, producer.version, printed.value),
                source=self._source,
                machine=self._writer.scope.machine,
                market_id=self._market_id,
                instrument=quote.bid.instrument.symbol,
                tier=binding.tier,
                time_base=binding.time_base,
                health=said.health,
                data_level=binding.data_level,
                fallback_step=0,
                inputs_received_at=quote.at.value_ns,
                computed_at=computed_at,
                stale_after_s=binding.stale_after_s,
                value=said.value,
                word=said.word,
                estimate=binding.estimate,
            )
        )
