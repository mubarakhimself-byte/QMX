"""Shared test bridge from recorded frontiers into the real hosted root."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from qmb.runloop import CancelToken, DeclaredStream, ScriptedLimitProbe, StreamSet
from qmf.core import (
    Account,
    DataDrivenClock,
    Instant,
    Ok,
    SinkAck,
    SinkResult,
    VenueId,
    WriterId,
    is_refusal,
)
from qmf.data.journal_producer import JournalWriter
from qmf.data.store import JournalStore
from qmn.host.decision_root import HostedDecisionRoot, HostedDecisionTranscript
from qmn.loop import CommandStreamLoop, RecordingAccumulator, clear_first_writer_registry
from qmn.mis import SQS_PRODUCER_ID, SignalSnapshot, mint_signal_snapshot
from qmn.order.identity import NativeExecutionMap
from qmn.seats import SeatTransitionStream


def _omit_absent(value: object) -> object:
    """Map optional fields to omission, matching QMF identity JSON rules."""
    if isinstance(value, Mapping):
        body = cast(Mapping[str, object], value)
        return {key: _omit_absent(item) for key, item in body.items() if item is not None}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_omit_absent(item) for item in cast(Sequence[object], value)]
    return value


class _RecordedObservationSink:
    """Persist input observations to their own checked QMF stream."""

    def __init__(self, writer: JournalWriter) -> None:
        self.writer = writer

    def emit(self, _row: Mapping[str, object], /) -> SinkResult:
        observation: object = _row.get("observation")
        if not isinstance(observation, Mapping):
            raise AssertionError("accumulator emits the typed observation row")
        observation_row = cast(Mapping[str, object], observation)
        at_ns = observation_row.get("receive_wall_time_ns")
        instant = Instant.try_create(at_ns)
        if is_refusal(instant):
            return instant
        recorded = self.writer.record_control_action(
            "recorded-frontier-observation",
            instant=instant.value,
            payload=cast(Mapping[str, object], _omit_absent(_row)),
        )
        if is_refusal(recorded):
            return recorded
        return Ok(SinkAck(detail={"complete": True}))


class _RecordedJournalSink:
    def __init__(self, writer: JournalWriter) -> None:
        self.writer = writer

    def append(self, _row: object, /) -> SinkResult:
        if not isinstance(_row, Mapping):
            raise AssertionError("accumulator journals typed mapping rows")
        row = cast(Mapping[str, object], _row)
        instant = Instant.try_create(row.get("receive_wall_time_ns"))
        if is_refusal(instant):
            return instant
        recorded = self.writer.record_control_action(
            "recorded-frontier-cursor",
            instant=instant.value,
            payload=cast(Mapping[str, object], _omit_absent(row)),
        )
        if is_refusal(recorded):
            return recorded
        return Ok(SinkAck(detail={"complete": True}))


class _HostedFrontierHandler:
    def __init__(
        self,
        root: HostedDecisionRoot,
        snapshot: SignalSnapshot,
        intent_state: dict[str, object],
    ) -> None:
        self.root = root
        self.snapshot = snapshot
        self.intent_state = intent_state
        self.transcripts: list[HostedDecisionTranscript] = []

    def update_stream(self, _stream_id: str, _observation: object, _frontier: Instant):
        return Ok(None)

    def scheduled_position_event(self, _stream_id: str, _frontier: Instant):
        return Ok(None)

    def execute_resting(self, _intent: object, _observation: object, _frontier: Instant):
        return Ok(False)

    def update_closed_data(self, _stream_id: str, _observation: object, _frontier: Instant):
        return Ok(None)

    def mint_intents(self, _stream_id: str, frontier: Instant):
        current = mint_signal_snapshot(
            frontier_instant=frontier,
            environment=self.snapshot.environment,
            feed_state=self.snapshot.feed_state,
            producers=tuple(self.snapshot.producers.values()),
            decision_freshness_bound=self.snapshot.decision_freshness_bound,
            degraded_sensors=self.snapshot.degraded_sensors,
        )
        if is_refusal(current):
            return current
        decision_at = Instant.try_create(frontier.value_ns + 1_000_000_000)
        if is_refusal(decision_at):
            return decision_at
        transcript = self.root.run_slice(
            snapshot=current.value,
            decision_at=decision_at.value,
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=ScriptedLimitProbe(elapsed_ns=(0, 1), memory_bytes=(1, 1)),
        )
        if is_refusal(transcript):
            return transcript
        self.transcripts.append(transcript.value)
        # The harness selects no intent after the first-frontier action. This
        # bounds the fixture's economic action; it does not characterize a
        # production duplicate-intent/idempotency rule.
        self.intent_state["intents"] = ()
        return Ok(())


def drive_two_recorded_frontiers(
    *,
    root: HostedDecisionRoot,
    snapshot: SignalSnapshot,
    journal: JournalStore,
    intent_state: dict[str, object],
    frontier_instants: tuple[Instant, Instant],
) -> tuple[tuple[object, object], tuple[HostedDecisionTranscript, HostedDecisionTranscript]]:
    """Drive two closed observations through accumulator → QMB → hosted root."""
    clear_first_writer_registry()
    sqs_slot = snapshot.producers.get(SQS_PRODUCER_ID)
    if sqs_slot is None or sqs_slot.sqs is None:
        raise AssertionError("the governed snapshot carries its required SQS reading")
    venue = sqs_slot.sqs.baseline_key.venue
    account = root.path.account
    path_venue = root.path.venue_id
    if (
        not isinstance(account, Account)
        or account.venue != venue
        or not isinstance(path_venue, VenueId)
        or path_venue != venue
    ):
        raise AssertionError("recorded accumulator uses the admitted Book path account/venue")
    writer = WriterId.try_create(
        "fixture-node",
        "recorded-observations",
        f"{venue.value}:{account.account_id}",
        "fixture-boot",
    )
    if is_refusal(writer):
        raise AssertionError(writer)
    input_writer_id = WriterId.try_create(
        "fixture-node", "recorded-observation", "frontier-observations", "fixture-boot"
    )
    cursor_writer_id = WriterId.try_create(
        "fixture-node", "recording-accumulator", "frontier-cursor", "fixture-boot"
    )
    if is_refusal(input_writer_id) or is_refusal(cursor_writer_id):
        raise AssertionError((input_writer_id, cursor_writer_id))
    input_writer = JournalWriter.resume(
        journal, input_writer_id.value, stream_name="frontier-observations"
    )
    cursor_writer = JournalWriter.resume(
        journal, cursor_writer_id.value, stream_name="frontier-cursor"
    )
    if is_refusal(input_writer) or is_refusal(cursor_writer):
        raise AssertionError((input_writer, cursor_writer))
    accumulator_result = RecordingAccumulator.try_create(
        venue_id=venue,
        account=account,
        writer_id=writer.value,
        observation_sink=_RecordedObservationSink(input_writer.value),
        journal_sink=_RecordedJournalSink(cursor_writer.value),
        accumulator_bound=8,
        writer_name="fixture-recording-accumulator",
    )
    if is_refusal(accumulator_result):
        raise AssertionError(accumulator_result)
    handler = _HostedFrontierHandler(root, snapshot, intent_state)
    native_map = root.path.native_execution_map
    if not isinstance(native_map, NativeExecutionMap):
        raise AssertionError("recorded streamset uses the hosted native execution map")
    mappings = native_map.mappings
    if not mappings or any(mapping.instrument.venue != venue for mapping in mappings):
        raise AssertionError("recorded streamset is pinned to the hosted native instrument map")
    stream_id = mappings[0].instrument.symbol
    declared = DeclaredStream.try_create(stream_id)
    if is_refusal(declared):
        raise AssertionError(declared)
    stream = StreamSet.try_create([declared.value])
    if is_refusal(stream):
        raise AssertionError(stream)
    clock = DataDrivenClock(
        boot_epoch_id="fixture-boot",
        wall_instants=frontier_instants,
        monotonic_ns=(100, 101, 200, 201),
    )
    loop_result = CommandStreamLoop.try_create(
        accumulator=accumulator_result.value,
        stream_set=stream.value,
        clock=clock,
        max_slice_latency=1_000_000_000,
        handler=handler,
    )
    if is_refusal(loop_result):
        raise AssertionError(loop_result)
    loop = loop_result.value
    outcomes: list[object] = []
    for index, frontier in enumerate(frontier_instants):
        pushed = loop.accumulator.push(
            observation_id=f"frontier-{index}",
            stream_id=stream_id,
            receive_wall=frontier,
            payload={"kind": "tick", "fixture": "recorded-frontier"},
            kind="tick",
            closed=True,
        )
        if is_refusal(pushed):
            raise AssertionError(pushed)
        driven = loop.close_frontier()
        if is_refusal(driven):
            raise AssertionError(driven)
        outcomes.append(driven.value)
    assert len(handler.transcripts) == 2
    return (
        (outcomes[0], outcomes[1]),
        (handler.transcripts[0], handler.transcripts[1]),
    )
