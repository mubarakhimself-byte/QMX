"""Shared provider-free CT-10/12/13 fixture for recorded replay studies.

This helper composes existing QMB CT-33, CT-12 request, CT-10 archive, Book,
and execution-port builders. Its no-rollover calendar is an explicit recorded
fixture double; prices, request/source bytes, and CT-13 writes use QMF storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path
from typing import TypeVar, cast

from qmb._refuse import invalid
from qmb.analysis import CT29ProjectionSource
from qmb.config import (
    STARTING_CAPITAL_KEY,
    ReplayBinding,
    compile_run_config,
)
from qmb.execution import (
    COST_ADAPTER_KEY,
    COST_ADAPTER_PER_LOT,
    COST_CALIBRATION_KEY,
    FILL_ADAPTER_DECLARED_PATH,
    FILL_ADAPTER_KEY,
    FILL_BASIS_KEY,
    FINANCING_SCHEDULE_KEY,
    SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    SLIPPAGE_ADAPTER_KEY,
    SLIPPAGE_ADAPTER_ZERO,
    SLIPPAGE_CALIBRATION_KEY,
    CommissionCalibration,
    SlippageCalibration,
    bind_execution_ports,
)
from qmb.execution.fill import FILL_BASIS_OPTIMISTIC_EXACT
from qmb.host.book_handler import BookAdmissionContext
from qmb.host.replay import PinnedInstrumentPriceMetadata
from qmb.host.replay_execution import execute_recorded_replay_request
from qmb.host.replay_request import (
    ReplayInputRequest,
    persist_replay_request,
    resolve_replay_request,
)
from qmb.optimize import ReplayTrialBindings
from qmb.optimize.sampler import ProposedTrial
from qmb.orchestrator.ledger import LedgerSink
from qmb.results.ct29 import CT29ClosedTrade
from qmb.results.ct32 import PerformanceResult
from qmb.runloop import STREAM_SET_KEY
from qmf.core import (
    AccountRole,
    CalendarIdentity,
    ExactRational,
    Instrument,
    Ok,
    Result,
    UnitKind,
    ValueFactor,
    VenueId,
    World,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import Instant, WriterId
from qmf.core.exact import Money
from qmf.core.fingerprint import Fingerprint, fingerprint
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistrationRecord
from qml.declaration.bot import BotDefinition
from qml.protocol import BotStateScope

# Public shared-fixture adapters keep this integration fixture aligned with
# builders owned and tested by their source suites.
from test_alternative_execution import (
    STUDY_FIXTURE_EPOCH_NS,
    study_fixture_split,
    study_fixture_writer,
)
from test_book_handler import (
    BookOrderPolicy,
    NeverRolloverCalendarFixture,
    OffsetStopFixture,
    study_fixture_instrument,
)
from test_ql7_host import (
    study_fixture_defaults,
    study_fixture_definition,
    study_fixture_fragments_with_bot,
    study_fixture_record,
    study_fixture_scope,
    study_fixture_seed,
)

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _observation_at(side: str, sequence: int, event_ns: int, price: int) -> SourceObservation:
    instant = _ok(Instant.try_create(event_ns))
    return _ok(
        SourceObservation.try_create(
            event_time=instant,
            known_at=instant,
            source="qmb-optimizer-recorded-fixture",
            source_native_id=f"study-{sequence}-{side}",
            revision="1",
            receive_wall_time=instant,
            writer=study_fixture_writer(),
            sequence=sequence,
            world=World.REPLAY,
            foreign_money=_ok(ForeignMoney.try_create(price, 5)),
            market_data=_ok(
                MarketDataContext.try_create(
                    venue="replay-venue",
                    symbol="EURUSD",
                    resolution="tick",
                    side=side,
                    license_tag="local-fixture",
                    provenance={"source_kind": "persisted-study-test"},
                )
            ),
        )
    )


def _entry_source_tree(entry_instants: tuple[int, ...]) -> dict[str, str]:
    allowed = ", ".join(str(value) for value in entry_instants)
    codes = tuple(
        "breakout" if index == 0 else f"breakout-{index}"
        for index in range(len(entry_instants))
    )
    code_rows = ", ".join(repr(code) for code in codes)
    return {
        "research_bot/__init__.py": "",
        "research_bot/bot.py": "def on_instant(self, evidence):\n    return ()\n",
        "research_bot/factory.py": (
            "from qml.protocol import FunctionFactory\n"
            "from qmf.core import Instrument, PriceDelta, VenueId\n"
            "from qmf.risk.door import Direction, EntryIntent, ReasonCode\n"
            "from qmf.risk.paper import ExecutionTarget\n"
            "def _entry(code):\n"
            "    venue = VenueId('replay-venue')\n"
            "    instrument = Instrument(venue, 'EURUSD')\n"
            "    target_venue = VenueId('venue-replay')\n"
            "    target = ExecutionTarget.try_create('demo', target_venue, 'acct-replay').value\n"
            "    reason = ReasonCode.try_create(code, 'family').value\n"
            "    stop = PriceDelta.try_create(500, instrument, 5).value\n"
            "    return EntryIntent.try_create(instrument, Direction.LONG, reason, target, "
            "advisory_stop_proposal=stop).value\n"
            "def _logic(evidence):\n"
            f"    instants = ({allowed},)\n"
            f"    codes = ({code_rows},)\n"
            "    if evidence.evaluation_instant.value_ns not in instants:\n"
            "        return ()\n"
            "    return (_entry(codes[instants.index(evidence.evaluation_instant.value_ns)]),)\n"
            "factory = FunctionFactory(logic=_logic)\n"
        ),
    }


def _entry_bot_definition(source_tree: dict[str, str]) -> BotDefinition:
    from qml.logic import mint_logic_identity

    base = study_fixture_definition()
    logic = _ok(mint_logic_identity("research-bot", "1.0.0", source_tree))
    payload = base.identity_payload()
    body = dict(cast(Mapping[str, object], payload["body"]))
    body["logic_reference"] = logic.as_logic_reference()
    payload["body"] = body
    return _ok(BotDefinition.try_from_mapping(payload))


@dataclass(frozen=True, slots=True)
class RecordedReplayFixture:
    """Persisted CT-10 and CT-12 inputs used to resolve one request per trial."""

    expected_split_fp1: Fingerprint
    split: object
    archive_fingerprints: tuple[str, ...]
    price_metadata: PinnedInstrumentPriceMetadata
    declaration: BotDefinition
    source_tree: dict[str, str]
    state_scope: BotStateScope
    raw_store_root: Path
    request_root: Path
    bot_record: RegistrationRecord
    slippage_adapter: str

    def prepare_trial(
        self,
        root: Path,
        ledger: LedgerSink,
        generation: int,
        proposal: ProposedTrial,
        label: dict[str, object],
    ) -> Result[ReplayTrialBindings]:
        """Compile one exact CT-33 candidate and its actual Book/CT-13 ports."""
        request = ReplayInputRequest.try_create(
            split=self.split,
            split_role=SegmentRole.TRAIN,
            archive_fingerprints=self.archive_fingerprints,
            stream_id="primary",
            price_metadata=self.price_metadata,
            bot_identity=self.declaration.identity_payload(),
            source_tree=self.source_tree,
            assignment=proposal.assignment,
            state_scope=self.state_scope.to_mapping(),
            state_bound=256,
            conformance_timeout_seconds=30,
        )
        if is_refusal(request):
            return request
        request_ref = persist_replay_request(
            request_root=self.request_root,
            request=request.value,
        )
        if is_refusal(request_ref):
            return request_ref
        resolved_request = resolve_replay_request(
            request_root=self.request_root,
            request_ref=request_ref.value,
            split=None,
            expected_split_fp1=self.expected_split_fp1,
            raw_store_root=self.raw_store_root,
            holdout_months=18,
        )
        if is_refusal(resolved_request):
            return resolved_request
        bot_record = self.bot_record
        book_fragment, bms_fragment, port, _ = study_fixture_fragments_with_bot(bot_record)
        run_spec: dict[str, object] = {
            "bot": bot_record.stable_id,
            STARTING_CAPITAL_KEY: study_fixture_seed(),
            **proposal.assignment,
        }
        config = compile_run_config(
            port,
            book_fragment=book_fragment,
            bms_fragment=bms_fragment,
            run_spec=run_spec,
            workspace_defaults={
                **study_fixture_defaults(),
                **self._workspace_defaults(self.slippage_adapter),
            },
            study_trial_label=label,
        )
        if is_refusal(config):
            return config
        resolved_config = config.value
        binding = resolved_config.replay_binding
        if binding is None:
            raise AssertionError("compiled replay config contains a CT-28 binding")
        bound = bind_execution_ports(resolved_config)
        if is_refusal(bound):
            return bound

        journal = JournalStore(
            World.REPLAY,
            journal_dir=root / f"ct13-{generation}-{proposal.ask_index}",
            open_stream=jsonl_opener(),
        )
        writer_id = _ok(WriterId.try_create("qmb-study-fixture", "replay", "positions", "boot-1"))
        writer = JournalWriter(journal, writer_id, stream_name="positions")
        reader = JournalReader(journal)
        admission = self._admission(binding, writer, reader)
        if is_refusal(admission):
            return admission
        return Ok(
            ReplayTrialBindings(
                request=resolved_request.value,
                expected_split_fp1=self.expected_split_fp1,
                request_root=self.request_root,
                raw_store_root=self.raw_store_root,
                holdout_months=18,
                config=resolved_config,
                bound_execution=bound.value,
                admission=admission.value,
                journal_reader=reader,
                ledger=ledger,
            )
        )

    @staticmethod
    def _admission(
        binding: ReplayBinding, writer: JournalWriter, reader: JournalReader
    ) -> Result[BookAdmissionContext]:
        from qmb.execution.fill import OrderType
        from qmf.core import (
            Quantity,
        )
        from qmf.risk.door import ExitLogicRef, ReasonCode
        from qmf.risk.exit_record import CloseReason, ExitResultLabel
        from qmf.risk.paper import ExecutionTarget

        stop_reason = _ok(ReasonCode.try_create("protective_stop", "family"))
        target = _ok(
            ExecutionTarget.try_create(
                AccountRole.DEMO.value,
                binding.record.venue_id,
                binding.record.account_id,
            )
        )
        stop_policy = BookOrderPolicy(OrderType.STOP)
        return BookAdmissionContext.try_create(
            binding=binding,
            exit_logic_ref=_ok(ExitLogicRef.try_create("book.stop", {})),
            exit_logic_module=OffsetStopFixture(),
            requested_r=_ok(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)),
            r_unit_price=_ok(ExactRational.try_create(100, 1, UnitKind.RATE)),
            value_factor=_ok(ValueFactor.try_create(20_000, 1, study_fixture_instrument(), "USD")),
            money_scale=2,
            lot_step=_ok(Quantity.try_create(1, "lot", 0)),
            position_cap=_ok(Quantity.try_create(5, "lot", 0)),
            execution_target=target,
            result_label=_ok(ExitResultLabel.try_create(AccountRole.DEMO, World.REPLAY)),
            opening_bot_id="qmb-study-test-bot",
            close_reason_by_code={
                "exit:family:protective_stop": CloseReason.PROTECTIVE_STOP_FILL,
            },
            order_policy_by_code={
                "entry:family:breakout": BookOrderPolicy(OrderType.MARKET),
                **{
                    f"entry:family:breakout-{index}": BookOrderPolicy(OrderType.MARKET)
                    for index in range(1, 64)
                },
                "exit:family:protective_stop": stop_policy,
            },
            journal_writer=writer,
            journal_reader=reader,
            rollover_calendar=NeverRolloverCalendarFixture(),
            protective_stop_reason=stop_reason,
        )

    @staticmethod
    def _workspace_defaults(
        slippage_adapter: str = SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    ) -> dict[str, object]:
        commission = _ok(
            CommissionCalibration.try_create(
                COST_ADAPTER_PER_LOT,
                "replay-broker",
                currency="USD",
                per_lot=_ok(Money.try_create(100, "USD", 2)),
            )
        )
        result: dict[str, object] = {
            **study_fixture_defaults(),
            STREAM_SET_KEY: ("primary",),
            COST_ADAPTER_KEY: COST_ADAPTER_PER_LOT,
            COST_CALIBRATION_KEY: commission,
            FILL_ADAPTER_KEY: FILL_ADAPTER_DECLARED_PATH,
            FILL_BASIS_KEY: FILL_BASIS_OPTIMISTIC_EXACT,
            FINANCING_SCHEDULE_KEY: "replay-swap-table",
            SLIPPAGE_ADAPTER_KEY: slippage_adapter,
        }
        if slippage_adapter == SLIPPAGE_ADAPTER_ZERO:
            return result
        slippage = _ok(
            SlippageCalibration.try_create(
                slippage_adapter,
                "replay-broker",
                percent=_ok(ExactRational.try_create(1, 10_000, UnitKind.DIMENSIONLESS_RATIO)),
            )
        )
        result[SLIPPAGE_CALIBRATION_KEY] = slippage
        return result



@dataclass(frozen=True, slots=True)
class ProjectionReplayFixture:
    source: CT29ProjectionSource
    performance_result: PerformanceResult
    closed_trades: tuple[CT29ClosedTrade, ...]


def build_projection_replay(
    root: Path,
    *,
    registry_as_of: Instant,
    entry_offsets_hours: tuple[int, ...] = (0,),
    entry_start_ns: int = STUDY_FIXTURE_EPOCH_NS,
) -> Result[ProjectionReplayFixture]:
    """Run a real selected-bot replay and return its checked CT13/CT32 lineage."""
    fixture = make_recorded_replay_fixture(
        root,
        slippage_adapter=SLIPPAGE_ADAPTER_ZERO,
        entry_offsets_hours=entry_offsets_hours,
        entry_start_ns=entry_start_ns,
    )
    request = ReplayInputRequest.try_create(
        split=fixture.split,
        split_role=SegmentRole.TRAIN,
        archive_fingerprints=fixture.archive_fingerprints,
        stream_id="primary",
        price_metadata=fixture.price_metadata,
        bot_identity=fixture.declaration.identity_payload(),
        source_tree=fixture.source_tree,
        assignment={"lookback": 20, "sma_period": 20},
        state_scope=fixture.state_scope.to_mapping(),
        state_bound=256,
        conformance_timeout_seconds=30,
    )
    if is_refusal(request):
        return request
    request_ref = persist_replay_request(request_root=fixture.request_root, request=request.value)
    if is_refusal(request_ref):
        return request_ref
    resolved = resolve_replay_request(
        request_root=fixture.request_root,
        request_ref=request_ref.value,
        split=fixture.split,
        expected_split_fp1=fixture.expected_split_fp1,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
    )
    if is_refusal(resolved):
        return resolved
    book_fragment, bms_fragment, port, _ = study_fixture_fragments_with_bot(fixture.bot_record)
    config = compile_run_config(
        port,
        book_fragment=book_fragment,
        bms_fragment=bms_fragment,
        run_spec={
            "bot": fixture.bot_record.stable_id,
            STARTING_CAPITAL_KEY: study_fixture_seed(),
            "lookback": 20,
            "sma_period": 20,
            STREAM_SET_KEY: (resolved.value.source.stream_id,),
            "registry_as_of": registry_as_of,
        },
        workspace_defaults={
            **study_fixture_defaults(),
            **fixture._workspace_defaults(  # pyright: ignore[reportPrivateUsage]
                fixture.slippage_adapter
            ),
        },
    )
    if is_refusal(config):
        return config
    binding = config.value.replay_binding
    if binding is None:
        return invalid("binding", "projection fixture config carries its minted CT-28 binding")
    bound = bind_execution_ports(config.value)
    if is_refusal(bound):
        return bound
    journal = JournalStore(
        World.REPLAY,
        journal_dir=root / "projection-ct13",
        open_stream=jsonl_opener(),
    )
    writer_id = WriterId.try_create("qmb-projection-fixture", "replay", "positions", "boot-1")
    if is_refusal(writer_id):
        return writer_id
    writer = JournalWriter(journal, writer_id.value, stream_name="positions")
    reader = JournalReader(journal)
    admission = fixture._admission(  # pyright: ignore[reportPrivateUsage]
        binding, writer, reader
    )
    if is_refusal(admission):
        return admission
    admitted = replace(admission.value, opening_bot_id=config.value.bot_fp1.value)
    terminal_ledger = make_trial_ledger(root / "projection-terminal")
    executed = execute_recorded_replay_request(
        request=resolved.value,
        expected_request_ref=request_ref.value,
        request_root=fixture.request_root,
        raw_store_root=fixture.raw_store_root,
        holdout_months=18,
        expected_split_fp1=fixture.expected_split_fp1,
        config=config.value,
        bound_execution=bound.value,
        admission=admitted,
        journal_reader=reader,
        terminal_ledger=terminal_ledger,
    )
    if is_refusal(executed):
        return executed
    result_label = admitted.result_label
    descriptor = CT29ProjectionSource.try_create(
        journal_reader=reader,
        stream_name="positions",
        writer=writer_id.value,
        binding_epoch=binding.fingerprint,
        result_label=result_label,
        run_config=config.value,
        replay_request=resolved.value,
        terminal_ledger_root=terminal_ledger.root,
        ledger_role="confirmation",
    )
    if is_refusal(descriptor):
        return descriptor
    return Ok(
        ProjectionReplayFixture(
            source=descriptor.value,
            performance_result=executed.value.performance_result,
            closed_trades=tuple(executed.value.closed_trades),
        )
    )


def _projection_split(entry_start_ns: int):
    """A local CT-12 train window spanning the deliberately separated frontiers."""
    calendar = _ok(CalendarIdentity.try_create("analysis-fixture-calendar", "v1", "2025a"))
    boundaries = tuple(
        _ok(Instant.try_create(entry_start_ns + hours * 3_600_000_000_000))
        for hours in (72, 144, 216)
    )
    segments = _ok(SplitManifest.default_split_segments(boundaries))
    split = _ok(
        SplitManifest.try_create(
            calendar_identity=calendar,
            segments=segments,
            seal_boundary=_ok(SplitBoundary.try_create(boundaries[-1])),
            purge_width=0,
            embargo_width=0,
            world=World.REPLAY,
        )
    )
    return split, _ok(HoldoutSeal.from_manifest(split, 18))


def make_recorded_replay_fixture(
    root: Path,
    *,
    slippage_adapter: str = SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
    entry_offsets_hours: tuple[int, ...] = (0,),
    entry_start_ns: int = STUDY_FIXTURE_EPOCH_NS,
) -> RecordedReplayFixture:
    """Persist CT-10 and retain CT-12 pins for assignment-specific durable requests."""
    if (
        not entry_offsets_hours
        or any(type(offset) is not int or offset < 0 for offset in entry_offsets_hours)
        or tuple(sorted(set(entry_offsets_hours))) != entry_offsets_hours
        or any(right - left < 1 for left, right in pairwise(entry_offsets_hours))
    ):
        raise ValueError("projection fixture entry offsets are ordered unique non-negative hours")
    store_root = root / "ct10-room"
    if entry_start_ns == STUDY_FIXTURE_EPOCH_NS and entry_offsets_hours == (0,):
        split, seal = study_fixture_split()
    else:
        split, seal = _projection_split(entry_start_ns)
    boundary = SourceObservationBoundary(EvidenceStore(store_root, seal=seal))
    entry_instants = tuple(
        entry_start_ns + offset * 3_600_000_000_000 for offset in entry_offsets_hours
    )
    frontiers = tuple(
        instant + phase
        for instant in entry_instants
        for phase in (0, 1, 2)
    )
    observation_rows: list[SourceObservation] = []
    for frontier_index, event_ns in enumerate(frontiers):
        is_stop = frontier_index % 3 == 2
        bid = 1_09000 if is_stop else 1_09500
        ask = 1_09020 if is_stop else 1_09520
        observation_rows.extend(
            (
                _observation_at("bid", frontier_index * 2, event_ns, bid),
                _observation_at("ask", frontier_index * 2 + 1, event_ns, ask),
            )
        )
    observations = tuple(observation_rows)
    refs = tuple(
        _ok(boundary.admit(observation)).archive.fingerprint.value for observation in observations
    )
    venue = _ok(VenueId.try_create("replay-venue"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    metadata_identity = {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "local-replay-fixture-v1",
        "price_scale": 5,
        "source_policy": {"kind": "persisted-test-fixture"},
    }
    metadata = _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=5,
            metadata_identity=metadata_identity,
            metadata_fp1=_ok(fingerprint(metadata_identity)),
        )
    )
    source_tree = _entry_source_tree(entry_instants)
    declaration = _entry_bot_definition(source_tree)
    bot_record = study_fixture_record("bot-definition", declaration.body())
    scope: BotStateScope = study_fixture_scope(declaration)
    return RecordedReplayFixture(
        expected_split_fp1=split.fingerprint,
        split=split,
        archive_fingerprints=refs,
        price_metadata=metadata,
        declaration=declaration,
        source_tree=source_tree,
        state_scope=scope,
        raw_store_root=store_root,
        request_root=root / "replay-requests",
        bot_record=bot_record,
        slippage_adapter=slippage_adapter,
    )


def make_trial_ledger(root: Path) -> LedgerSink:
    """One actual append/readback ledger shared by the sequential Study asks."""
    return _ok(
        LedgerSink.try_create(
            root,
            machine="qmb-study-test-machine",
            worker_slot="study-trial-slot",
            boot_epoch_id="study-fixture-boot-1",
        )
    )
