"""The reading runner over a recorded day, and the golden replay across unit, QMB and runner.

The recorded day is six EURUSD quotes in a typed ``ticks`` partition, the market-data store's
own format. The runner reads it from the store and writes reading records through Part B's
journal writer. QMB replays the same partition through its typed replay reader. A unit
computes the same readings itself, quote by quote, as its ``compute_here`` fallback would.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import TypeVar

from qmb.host.replay import (
    PinnedInstrumentPriceMetadata,
    TypedPartitionRef,
    read_typed_replay_source,
)
from qmf.core import (
    Duration,
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    Price,
    PriceDelta,
    UnitKind,
    VenueId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.refusal import Result
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmf.data.series import SeriesKey, SeriesStore
from qmf.readings import (
    SPREAD_STATE_PRODUCER_ID,
    SQS_PRODUCER_ID,
    SqsBaselineArtifact,
    configure_mis_producer,
    sqs_baseline_key,
)
from qmf.readings.record import Health, ReadingRecord, ReadingRef, ReadingSource, Tier, TimeBase
from qmf.readings.runner import Quote, ReadingBinding, ReadingRunner, Readings, outputs_of

T = TypeVar("T")

_SCALE = 5
_MS = 1_000_000
_FIRST_MS = 1_760_000_000_000
_MARKET = "fx.EURUSD"
_SPREADS = (12, 20, 15, 30, 16, 10)
"""Points between bid and ask at each quote; the SQS baseline spread is 10."""

_SECTION_7 = {
    "reading",
    "source",
    "machine",
    "market_id",
    "instrument",
    "tier",
    "time_base",
    "value",
    "percentile",
    "word",
    "health",
    "data_level",
    "fallback_step",
    "estimate",
    "inputs_received_at",
    "computed_at",
    "stale_after_s",
    "corrects",
}
_OPTIONAL = {"value", "percentile", "word", "estimate", "corrects"}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instrument() -> Instrument:
    return _ok(Instrument.try_create(_ok(VenueId.try_create("dukascopy")), "EURUSD"))


def _ratio(num: int, den: int = 1) -> ExactRational:
    return _ok(ExactRational.try_create(num, den, UnitKind.DIMENSIONLESS_RATIO))


def _duration(ns: int) -> Duration:
    return _ok(Duration.try_create(ns))


def _delta(value: int) -> PriceDelta:
    return _ok(PriceDelta.try_create(value, _instrument(), _SCALE))


def _rows() -> list[tuple[object, ...]]:
    return [
        (_FIRST_MS + index * 60_000, 1_095_00 + index, 1_095_00 + index + spread, 1.0, 1.0)
        for index, spread in enumerate(_SPREADS)
    ]


def _recorded_day(root: Path) -> tuple[SeriesStore, SeriesKey, TypedPartitionRef]:
    store = SeriesStore(root / "market")
    key = _ok(SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2025, 10))
    receipt = _ok(store.commit(key, _rows()))
    ref = _ok(
        TypedPartitionRef.try_create(
            path=receipt.path,
            series=key.series,
            month=f"{key.year:04d}-{key.month:02d}",
            fingerprint=receipt.fingerprint,
        )
    )
    return store, key, ref


def _quote(at_ns: int, bid: int, ask: int) -> Quote:
    instrument = _instrument()
    return Quote(
        at=_ok(Instant.try_create(at_ns)),
        bid=_ok(Price.try_create(bid, instrument, _SCALE)),
        ask=_ok(Price.try_create(ask, instrument, _SCALE)),
    )


def _store_quotes(store: SeriesStore, key: SeriesKey) -> list[Quote]:
    rows = _ok(store.read(key)).rows
    return [
        _quote(int(str(row["t"])) * _MS, int(str(row["bid"])), int(str(row["ask"])))
        for row in rows
    ]


def _qmb_quotes(ref: TypedPartitionRef) -> list[Quote]:
    instrument = _instrument()
    identity: dict[str, object] = {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "c08-golden-day-v1",
        "price_scale": _SCALE,
        "source_policy": {"kind": "typed-partition-test"},
    }
    metadata = _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=_SCALE,
            metadata_identity=identity,
            metadata_fp1=_ok(fingerprint(identity)),
        )
    )
    source = _ok(
        read_typed_replay_source(partitions=(ref,), stream_id="eurusd", instrument_metadata=metadata)
    )
    quotes: list[Quote] = []
    for path in source.execution_paths:
        assert path.bar_start is not None and path.bid is not None and path.ask is not None
        quotes.append(Quote(at=path.bar_start, bid=path.bid, ask=path.ask))
    return quotes


def _bindings() -> tuple[ReadingBinding, ...]:
    instrument = _instrument()
    spread_state = _ok(
        configure_mis_producer(
            SPREAD_STATE_PRODUCER_ID,
            parameters={
                "normal_max": _ok(ExactRational.try_create(12, 1, UnitKind.COUNT)),
                "elevated_max": _ok(ExactRational.try_create(25, 1, UnitKind.COUNT)),
            },
            warm_up=1,
        )
    )
    sqs = _ok(
        configure_mis_producer(
            SQS_PRODUCER_ID,
            parameters={
                "hard_block_threshold": _ratio(3, 5),
                "hysteresis_band": _ratio(1, 20),
                "outlier_guard_multiple": _ratio(4, 1),
                "sample_cadence": "quote",
                "staleness_horizon": _duration(2_000_000_000),
                "baseline_statistic": "mean",
                "session_window_id": "london",
                "decision_freshness_bound": _duration(5_000_000_000),
            },
            calendar_requirements=("market-hours-calendar:forex-17NY",),
            warm_up=1,
        )
    )
    baseline = SqsBaselineArtifact(
        key=_ok(sqs_baseline_key(instrument.venue, "demo", instrument)),
        average_spread=_delta(10),
        session_window_id="london",
        statistic="mean",
        refit_series_id="sqs-refit-series-1",
        refit_policy_fp=_print("sqs-refit-policy"),
        dispersion=_delta(2),
    )
    return (
        ReadingBinding(spread_state, Tier.TICK, TimeBase.TICKS, data_level=2, stale_after_s=2),
        ReadingBinding(
            sqs, Tier.TICK, TimeBase.TICKS, data_level=2, stale_after_s=2, sqs_baseline=baseline
        ),
    )


def _print(label: str) -> Fingerprint:
    return _ok(fingerprint({"class": "cite", "label": label}))


def _readings() -> Readings:
    return Readings(_bindings(), instrument=_instrument(), environment="demo", pip=_delta(1))


def _scope(world: JournalWorld) -> WriterScope:
    return WriterScope(
        stream=JournalStream.READINGS,
        subject=f"node.{_MARKET}",
        world=world,
        machine="this-pc",
        role="node",
        build="c08-golden",
    )


def _clock() -> itertools.count[int]:
    return itertools.count(1_760_000_000_500_000_000, 1_000)


def _hot_runner(root: Path) -> tuple[ReadingRunner, JournalWriter]:
    tick = _clock()
    writer = _ok(
        JournalWriter.open(
            root / "journals",
            _scope(JournalWorld.DEMO),
            clock=lambda: next(tick),
            boot_epoch_id="boot-1",
        )
    )
    tick_compute = _clock()
    runner = _ok(
        ReadingRunner.open(
            _readings(),
            writer,
            source=ReadingSource.NODE,
            market_id=_MARKET,
            clock=lambda: next(tick_compute),
            clock_ok=True,
        )
    )
    return runner, writer


def _committed_bodies(root: Path) -> list[dict[str, object]]:
    bodies: list[dict[str, object]] = []
    for folder in stream_folders(root / "journals"):
        for line in _ok(read_committed(folder)):
            assert isinstance(line, JournalLine)
            body = line.record["body"]
            assert isinstance(body, dict)
            bodies.append(dict(body))  # pyright: ignore[reportUnknownArgumentType]
    return bodies


def _outputs(records: list[dict[str, object]]) -> dict[str, list[tuple[object, ...]]]:
    """Per ``id@version``: (received at, value, word, health) in quote order."""
    by_reading: dict[str, list[tuple[object, ...]]] = {}
    for body in records:
        reading = body["reading"]
        assert isinstance(reading, dict)
        name = f"{reading['id']}@{reading['version']}"
        by_reading.setdefault(name, []).append(
            (body["inputs_received_at"], body.get("value"), body.get("word"), body["health"])
        )
    return by_reading


def _q(num: int, den: int) -> dict[str, object]:
    return {"num": num, "den": den, "unit_kind": "dimensionless-ratio"}


def _ns(index: int) -> int:
    return (_FIRST_MS + index * 60_000) * _MS


_SPREAD_STATE_PRINT = "fp1:sha256:f24898460de4944bebdbd7c7affda177da35ea731764171b0cbad8e28ed35429"
_SQS_PRINT = "fp1:sha256:b424391cf78ba92d9a302e4e442423c19e17e3f2613a7f2b4312c408b4e8f265"

_GOLDEN: dict[str, list[tuple[object, ...]]] = {
    "spread_state@v1": [
        (_ns(0), None, "normal", "fresh"),
        (_ns(1), None, "elevated", "fresh"),
        (_ns(2), None, "elevated", "fresh"),
        (_ns(3), None, "extreme", "fresh"),
        (_ns(4), None, "elevated", "fresh"),
        (_ns(5), None, "normal", "fresh"),
    ],
    "sqs@v1": [
        (_ns(0), _q(5, 6), "pass", "fresh"),
        (_ns(1), _q(1, 2), "hard-block", "fresh"),
        (_ns(2), _q(2, 3), "pass", "fresh"),
        (_ns(3), _q(1, 3), "hard-block", "fresh"),
        (_ns(4), _q(5, 8), "hard-block", "fresh"),
        (_ns(5), _q(1, 1), "pass", "fresh"),
    ],
}


def test_the_runner_writes_every_field_of_section_7_through_the_journal_writer(
    tmp_path: Path,
) -> None:
    store, key, _ = _recorded_day(tmp_path)
    runner, writer = _hot_runner(tmp_path)
    records = _ok(runner.run(_store_quotes(store, key)))
    _ok(writer.close())

    bodies = _committed_bodies(tmp_path)
    assert len(records) == len(bodies) == 12
    assert bodies == [record.body() for record in records]
    for body in bodies:
        assert _SECTION_7 - _OPTIONAL <= set(body) <= _SECTION_7
        assert body["source"] == "node"
        assert body["machine"] == "this-pc"
    sqs_first = bodies[1]
    assert sqs_first == {
        "reading": {
            "id": "sqs",
            "version": "v1",
            "fingerprint": _SQS_PRINT,
        },
        "source": "node",
        "machine": "this-pc",
        "market_id": "fx.EURUSD",
        "instrument": "EURUSD",
        "tier": "tick",
        "time_base": "ticks",
        "health": "fresh",
        "data_level": 2,
        "fallback_step": 0,
        "inputs_received_at": 1_760_000_000_000_000_000,
        "computed_at": 1_760_000_000_500_000_000,
        "stale_after_s": 2,
        "value": {"num": 5, "den": 6, "unit_kind": "dimensionless-ratio"},
        "word": "pass",
    }


def test_golden_replay_agrees_across_unit_qmb_and_runner_per_reading_and_version(
    tmp_path: Path,
) -> None:
    store, key, ref = _recorded_day(tmp_path)

    runner, writer = _hot_runner(tmp_path)
    _ok(runner.run(_store_quotes(store, key)))
    _ok(writer.close())
    from_runner = _outputs(_committed_bodies(tmp_path))

    bundle_tick = _clock()
    bundle = _ok(
        JournalWriter.open_bundle(
            tmp_path / "qmb-run",
            _scope(JournalWorld.BACKTEST),
            clock=lambda: next(bundle_tick),
        )
    )
    qmb_tick = _clock()
    qmb_runner = _ok(
        ReadingRunner.open(
            _readings(),
            bundle,
            source=ReadingSource.NODE,
            market_id=_MARKET,
            clock=lambda: next(qmb_tick),
            clock_ok=True,
        )
    )
    qmb_records: tuple[ReadingRecord, ...] = _ok(qmb_runner.run(_qmb_quotes(ref)))
    _ok(bundle.close())
    from_qmb = _outputs([record.body() for record in qmb_records])

    unit = _readings()
    by_unit: list[dict[str, object]] = []
    for quote in _store_quotes(store, key):
        for binding, emission in zip(unit.bindings, _ok(unit.step(quote)), strict=True):
            said = outputs_of(binding, emission)
            score = said.value
            by_unit.append(
                {
                    "reading": {"id": emission.producer_id, "version": emission.labeler_version},
                    "inputs_received_at": quote.at.value_ns,
                    "value": None if score is None else _q(score.numerator, score.denominator),
                    "word": said.word,
                    "health": said.health.value,
                }
            )
    from_unit = _outputs(by_unit)

    assert from_runner == from_qmb == from_unit == _GOLDEN
    printed = {record.reading.id: record.reading.fingerprint.value for record in qmb_records}
    assert printed == {"spread_state": _SPREAD_STATE_PRINT, "sqs": _SQS_PRINT}


def test_a_runner_refuses_a_writer_for_another_stream_or_subject(tmp_path: Path) -> None:
    tick = _clock()
    wrong_subject = _ok(
        JournalWriter.open(
            tmp_path / "journals",
            WriterScope(
                stream=JournalStream.READINGS,
                subject="mis.fx.EURUSD",
                world=JournalWorld.DEMO,
                machine="this-pc",
                role="node",
                build="c08-golden",
            ),
            clock=lambda: next(tick),
            boot_epoch_id="boot-1",
        )
    )
    refused = ReadingRunner.open(
        _readings(),
        wrong_subject,
        source=ReadingSource.NODE,
        market_id=_MARKET,
        clock=lambda: next(tick),
        clock_ok=True,
    )
    assert is_refusal(refused)
    assert refused.context["expected"] == "node.fx.EURUSD"
    _ok(wrong_subject.close())


def test_a_record_with_every_optional_field_set_writes_all_eighteen_fields() -> None:
    record = ReadingRecord(
        reading=ReadingRef("order_flow_pressure", "v1", _print("order-flow-block")),
        source=ReadingSource.MIS,
        machine="this-pc",
        market_id=_MARKET,
        instrument="EURUSD",
        tier=Tier.TICK,
        time_base=TimeBase.CLOCK,
        health=Health.DEGRADED,
        data_level=3,
        fallback_step=1,
        inputs_received_at=10,
        computed_at=11,
        stale_after_s=2,
        value=_ratio(-3, 4),
        percentile=_ratio(9, 10),
        word="selling",
        estimate="broker-side",
        corrects="node@this-pc/41",
    )

    assert set(record.body()) == _SECTION_7
    assert record.body() == {
        "reading": {
            "id": "order_flow_pressure",
            "version": "v1",
            "fingerprint": _print("order-flow-block").value,
        },
        "source": "mis",
        "machine": "this-pc",
        "market_id": "fx.EURUSD",
        "instrument": "EURUSD",
        "tier": "tick",
        "time_base": "clock",
        "health": "degraded",
        "data_level": 3,
        "fallback_step": 1,
        "inputs_received_at": 10,
        "computed_at": 11,
        "stale_after_s": 2,
        "value": {"num": -3, "den": 4, "unit_kind": "dimensionless-ratio"},
        "percentile": {"num": 9, "den": 10, "unit_kind": "dimensionless-ratio"},
        "word": "selling",
        "estimate": "broker-side",
        "corrects": "node@this-pc/41",
    }
