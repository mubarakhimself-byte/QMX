"""Shared provider-free CT-10/12/13 fixture for recorded replay studies.

This helper composes existing QMB CT-33, CT-12 request, CT-10 archive, Book,
and execution-port builders. Its no-rollover calendar is an explicit recorded
fixture double; prices, request/source bytes, and CT-13 writes use QMF storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar, cast

from qmb.config import (
    STARTING_CAPITAL_KEY,
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
from qmb.host.replay_request import (
    ReplayInputRequest,
    persist_replay_request,
    resolve_replay_request,
)
from qmb.optimize import ReplayTrialBindings
from qmb.optimize.sampler import ProposedTrial
from qmb.orchestrator.ledger import LedgerSink
from qmb.runloop import STREAM_SET_KEY
from qmf.core import (
    AccountRole,
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
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole
from qmf.data.store import EvidenceStore, JournalStore, jsonl_opener
from qmf.registry import RegistrationRecord
from qml.declaration.bot import BotDefinition
from qml.protocol import BotStateScope

# Existing test modules provide the canonical builders exercised by their own
# regression suites. These imports keep the integrated fixture aligned with
# those builders while avoiding duplicate CT-22/27/33 and Book grammars.
from test_alternative_execution import _NS, _split, _writer
from test_book_handler import (
    BookOrderPolicy,
    _instrument,
    _NeverRolloverCalendar,
    _OffsetStop,
)
from test_ql7_host import (
    _SEED,
    _defaults,
    _definition,
    _fragments_with_bot,
    _record,
    _scope,
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
            writer=_writer(),
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


def _entry_source_tree() -> dict[str, str]:
    return {
        "research_bot/__init__.py": "",
        "research_bot/bot.py": "def on_instant(self, evidence):\n    return ()\n",
        "research_bot/factory.py": (
            "from qml.protocol import FunctionFactory\n"
            "from qmf.core import Instrument, PriceDelta, VenueId\n"
            "from qmf.risk.door import Direction, EntryIntent, ReasonCode\n"
            "from qmf.risk.paper import ExecutionTarget\n"
            "def _entry():\n"
            "    venue = VenueId('replay-venue')\n"
            "    instrument = Instrument(venue, 'EURUSD')\n"
            "    target_venue = VenueId('venue-replay')\n"
            "    target = ExecutionTarget.try_create('demo', target_venue, 'acct-replay').value\n"
            "    reason = ReasonCode.try_create('breakout', 'family').value\n"
            "    stop = PriceDelta.try_create(500, instrument, 5).value\n"
            "    return EntryIntent.try_create(instrument, Direction.LONG, reason, target, "
            "advisory_stop_proposal=stop).value\n"
            "def _logic(evidence):\n"
            "    if evidence.evaluation_instant.value_ns != 1700000000000000000:\n"
            "        return ()\n"
            "    return (_entry(),)\n"
            "factory = FunctionFactory(logic=_logic)\n"
        ),
    }


def _entry_bot_definition(source_tree: dict[str, str]) -> BotDefinition:
    from qml.logic import mint_logic_identity

    base = _definition()
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
        book_fragment, bms_fragment, port, _ = _fragments_with_bot(bot_record)
        run_spec: dict[str, object] = {
            "bot": bot_record.stable_id,
            STARTING_CAPITAL_KEY: _SEED,
            **proposal.assignment,
        }
        config = compile_run_config(
            port,
            book_fragment=book_fragment,
            bms_fragment=bms_fragment,
            run_spec=run_spec,
            workspace_defaults=self._workspace_defaults(self.slippage_adapter),
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
        writer_id = _ok(
            WriterId.try_create("qmb-study-fixture", "replay", "positions", "boot-1")
        )
        writer = JournalWriter(journal, writer_id, stream_name="positions")
        reader = JournalReader(journal)
        admission = self._admission(binding, writer, reader)
        if is_refusal(admission):
            return admission
        return Ok(
            ReplayTrialBindings(
                request=resolved_request.value,
                expected_split_fp1=self.expected_split_fp1,
                config=resolved_config,
                bound_execution=bound.value,
                admission=admission.value,
                journal_reader=reader,
                ledger=ledger,
            )
        )

    @staticmethod
    def _admission(
        binding: object, writer: JournalWriter, reader: JournalReader
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
            exit_logic_module=_OffsetStop(),
            requested_r=_ok(ExactRational.try_create(1, 1, UnitKind.R_MULTIPLE)),
            r_unit_price=_ok(ExactRational.try_create(100, 1, UnitKind.RATE)),
            value_factor=_ok(ValueFactor.try_create(20_000, 1, _instrument(), "USD")),
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
                "exit:family:protective_stop": stop_policy,
            },
            journal_writer=writer,
            journal_reader=reader,
            rollover_calendar=_NeverRolloverCalendar(),
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
            **_defaults(),
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
                percent=_ok(
                    ExactRational.try_create(1, 10_000, UnitKind.DIMENSIONLESS_RATIO)
                ),
            )
        )
        result[SLIPPAGE_CALIBRATION_KEY] = slippage
        return result


def make_recorded_replay_fixture(
    root: Path,
    *,
    slippage_adapter: str = SLIPPAGE_ADAPTER_CONSTANT_PERCENT,
) -> RecordedReplayFixture:
    """Persist CT-10 and retain CT-12 pins for assignment-specific durable requests."""
    store_root = root / "ct10-room"
    split, seal = _split()
    boundary = SourceObservationBoundary(EvidenceStore(store_root, seal=seal))
    observations: tuple[SourceObservation, ...] = (
        _observation_at("bid", 0, _NS, 1_09500),
        _observation_at("ask", 1, _NS, 1_09520),
        _observation_at("bid", 2, _NS + 1, 1_09500),
        _observation_at("ask", 3, _NS + 1, 1_09520),
        _observation_at("bid", 4, _NS + 2, 1_09000),
        _observation_at("ask", 5, _NS + 2, 1_09020),
    )
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
    source_tree = _entry_source_tree()
    declaration = _entry_bot_definition(source_tree)
    bot_record = _record("bot-definition", declaration.body())
    scope: BotStateScope = _scope(declaration)
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
