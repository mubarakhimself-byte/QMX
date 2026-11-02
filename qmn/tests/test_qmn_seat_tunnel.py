"""Story 26.15 / E12-F05 — ungoverned Python-bot tunnel cannot bypass node gates."""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import TypeVar, cast

import pytest
from qmb.runloop import CancelToken, ScriptedLimitProbe
from qmf.core import (
    Account,
    AccountRole,
    DataDrivenClock,
    Duration,
    ExactRational,
    Fingerprint,
    Instant,
    Instrument,
    JournalSink,
    Money,
    MonotonicReading,
    Ok,
    Price,
    PriceDelta,
    Quantity,
    RefusalCategory,
    Result,
    SinkAck,
    UnitKind,
    ValueFactor,
    VenueId,
    World,
    WriterId,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import CalendarIdentity
from qmf.data import (
    JournalAppendReceipt,
    JournalEventType,
    JournalReader,
    JournalWriter,
)
from qmf.data import (
    JournalEvent as QmfJournalEvent,
)
from qmf.data.store import EvidenceStore, JournalStore
from qmf.data.store.engines.jsonl import jsonl_opener
from qmf.risk.binding import (
    STATE_CARRY_COUNTERS,
    BmsInstanceId,
    BookBindingRecord,
    BookBindingRequirements,
    BookInstanceId,
    CapabilityCheckResult,
    PositionModel,
    StateCarry,
    StateCarryChoice,
    VenueBindingProfile,
    bind_time_capability_check,
)
from qmf.risk.control_rank import ControlActionKind, ControlRankRow, ControlRankTable
from qmf.risk.door import (
    CitedEvidence,
    Direction,
    EntryIntent,
    EvidenceSlot,
    ExitIntent,
    ExitKind,
    ExitLogicRef,
    ReasonCode,
    StopMoveDirection,
    TightenProtectiveStop,
)
from qmf.risk.exit_policy import ExitPolicy
from qmf.risk.footprint_requirements import FootprintRequirements
from qmf.risk.paper import ExecutionTarget
from qmf.venue.commands import (
    CommandObservation,
    SubmissionOutcome,
    SubmissionResult,
)
from qmf.venue.commands import (
    JournalEvent as VenueJournalEvent,
)
from qmf.venue.ctrader import RoundingMode
from qml.conformance import (
    admit_ungoverned_tunnel,
    gate_registration,
    lint_declaration,
    run_layer2_suite,
)
from qml.declaration import BotDefinition, mint_bot_definition, mint_confluence
from qml.families import mint_strategy_family
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qml.protocol import (
    PROTOCOL_FORMAT_VERSION,
    FunctionFactory,
    construct_bot,
    mint_state_scope,
)
from qmn.config import compile_node_config
from qmn.data.observation_sink import QmfLiveJournalSink, QmfLiveObservationSink
from qmn.host.decision_root import (
    DECISION_TRANSCRIPT_CLASS,
    HostedDecisionRoot,
    OrderPathTiming,
    QmfHostedDecisionJournal,
)
from qmn.journal_dispatch import RecordingJournalSink
from qmn.ledger import (
    AttributedFill,
    EntryReservationEvent,
    EntryReservationRecovery,
    NativePositionEvidence,
    QmfEntryReservationJournal,
    seed_binding_ledger,
)
from qmn.ledger.binding_ledger import BindingVirtualLedger
from qmf.readings import (
    CanonicalFeedState,
    ProducerReadiness,
    ProducerSlot,
    SqsReading,
    mint_signal_snapshot,
    sqs_baseline_key,
)
from qmn.order import (
    CommandIdentityBinder,
    CommandOrdinalStore,
    ConnectionCommandPacer,
    OrderPath,
    OrderPathTerminalResolution,
)
from qmn.order.amend import AmendAtomicity, BookDynamicProtectionPolicy
from qmn.order.identity import NativeExecutionMap, NativeExecutionMapping
from qmn.order.protection import ENTRY_RELATIVE_FORM
from qmn.promotion import AdmissionLayerFreshState
from qmn.protection.ksa import KsaEnforcementScope, mint_level_epoch
from qmn.protection.ksa_journal import KSA_EPOCH_CLASS, KsaJournalProjection
from qmn.seats import (
    ADMISSION_LAYER_NAMES,
    FORBIDDEN_SEAT_SURFACE_KEYS,
    INTENT_PATH_HOPS,
    SEAT_ADMISSION_PROOFS,
    SEAT_ADMISSION_SURFACE,
    UNGOVERNED_EVIDENCE_KINDS,
    UNGOVERNED_TUNNEL_NAMES,
    AdmittedNodeSeat,
    BookPathContext,
    NativeExitAuthority,
    SeatContainment,
    SeatTransitionStream,
    cite_governed_seat_occurrence,
    construct_governed_seat,
    dispatch_hosted_intents,
    dispatch_seat_intents,
    inject_seat_callback,
    propose_node_seat,
    refuse_bot_constructed_ct19,
    refuse_composition_root_ungoverned_import,
    refuse_ungoverned_tunnel_seat,
    scan_production_src_for_ungoverned_tunnel,
    ungoverned_tunnel_names_in_tree,
)
from qmn.venue import (
    Command,
    CommandIdBindingRegistry,
    CommandKind,
    ConformanceDouble,
    OrderParameters,
    OrderType,
    QmfCommandIdBindingJournal,
    TimeInForce,
    VenueClientKind,
)

T = TypeVar("T")

_NS = 1_700_000_000_000_000_000
_SOURCE: dict[str, str] = {
    "research_bot/__init__.py": "",
    "research_bot/bot.py": "def on_instant(self, evidence):\n    return ()\n",
}
_VENUE_CAPS: frozenset[str] = frozenset({"trading", "time-interval"})
_MISSING = object()


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _refusal(result: Result[T]):
    assert is_refusal(result), result
    return result


def _instant(ns: int = _NS) -> Instant:
    return _ok(Instant.try_create(ns))


def _duration(ns: int = 1_000_000_000) -> Duration:
    return _ok(Duration.try_create(ns))


def _pinned(tag: str) -> ProducerBinding:
    return _ok(ProducerBinding.try_create(_ok(fingerprint({"class": "test-producer", "tag": tag}))))


def _containment() -> SeatContainment:
    return _ok(
        SeatContainment.try_create(
            callback_deadline=_duration(),
            memory_ceiling_bytes=10_000_000,
        )
    )


def _world() -> dict[str, object]:
    zone = _pinned("zone")
    sma = _pinned("sma")
    family = _ok(mint_strategy_family("trend-follow"))
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": zone}]))
    calendar = _ok(CalendarIdentity.try_create("forex-17NY", "v3", "2025.2"))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [calendar],
            [zone, sma],
        )
    )
    logic = _ok(mint_logic_identity("research-bot", "1.0.0", _SOURCE))
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id=family.family_id.value,
            confluence_set=[confluence],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 200},
                    "step": 1,
                    "default": 20,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            permitted_exit_intents=(),
            logic_reference=logic,
        )
    )
    return {
        "confluence": confluence,
        "declaration": declaration,
        "family": family,
        "logic": logic,
        "producers": [zone, sma],
        "source": _SOURCE,
    }


def _candidate(world: dict[str, object], *, factory: FunctionFactory | None = None):
    declaration = cast(BotDefinition, world["declaration"])
    layer1 = lint_declaration(
        declaration,
        family_catalog=[world["family"]],
        confluence_catalog=[world["confluence"]],
        producer_catalog=world["producers"],
        logic_catalog=[world["logic"]],
    )
    scope = _ok(
        mint_state_scope(
            os="windows-11",
            logic_identity=declaration.logic_reference,
            protocol_format_version=PROTOCOL_FORMAT_VERSION,
            arithmetic_reference_build="none",
        )
    )
    layer2 = run_layer2_suite(
        declaration=declaration,
        factory=factory if factory is not None else FunctionFactory(logic=lambda evidence: ()),
        source_tree=cast(dict[str, str], world["source"]),
        state_scope=scope,
        state_bound=256,
    )
    return gate_registration(layer1=layer1, layer2=layer2)


def _layers(*, layer1: bool = True, layer2: bool = True, layer3: bool = True):
    return _ok(
        AdmissionLayerFreshState.try_create(
            layer1_linters_passed=layer1,
            layer2_shakedown_passed=layer2,
            layer3_operator_signature_present=layer3,
        )
    )


def _book_binding_record() -> BookBindingRecord:
    venue = _venue()
    account = "acct-1"
    requirements = _ok(
        BookBindingRequirements.try_create(
            "USD", {"protective-stop-attachment"}, {"sqs-eurusd"}, {}
        )
    )
    profile = _ok(
        VenueBindingProfile.try_create({"protective-stop-attachment"}, PositionModel.HEDGING, "USD")
    )
    ranks = _ok(
        ControlRankTable.try_create(
            (
                ControlRankRow(ControlActionKind.FLATTEN, 0),
                ControlRankRow(ControlActionKind.DRAIN, 1),
                ControlRankRow(ControlActionKind.SUSPEND_NEW, 2),
                ControlRankRow(ControlActionKind.RESUME, 3),
            )
        )
    )
    capability_result: CapabilityCheckResult = _ok(
        bind_time_capability_check(
            requirements=requirements,
            profile=profile,
            bms_rank_table=ranks,
            sensor_baselines_present={"sqs-eurusd"},
            live_path_rung_baseline_present=True,
            is_second_book_on_account=False,
            overlapping_instrument_set=False,
        )
    )
    state_carry = _ok(
        StateCarry.try_create(dict.fromkeys(STATE_CARRY_COUNTERS, StateCarryChoice.RESET))
    )
    bms_version = _ok(fingerprint({"bms-version": "seat-test"}))
    return _ok(
        BookBindingRecord.try_create(
            _ok(BookInstanceId.try_create("book-inst-seat-test")),
            _ok(BmsInstanceId.derive(bms_version, account, venue, World.LIVE)),
            venue,
            account,
            World.LIVE,
            _ok(fingerprint({"book-version": "seat-test"})),
            bms_version,
            state_carry,
            capability_result,
        )
    )


def _exit_policy(family_id: str = "trend-follow") -> ExitPolicy:
    ref = _ok(ExitLogicRef.try_create("book.default.evidence_stop", {"style": "structure"}))
    return _ok(ExitPolicy.try_create({family_id: ref}, permitted_exit_intent_kinds=()))


def _requirements() -> FootprintRequirements:
    return _ok(FootprintRequirements.try_create(()))


def _propose(
    *,
    factory: object | None = None,
    world: dict[str, object] | None = None,
    candidate: object = _MISSING,
    admission_layers: object | None = None,
    assignment: object = None,
    binding_ref: object = _MISSING,
    bms_instance_id: object = _MISSING,
    callback: object = None,
    hosted: object = None,
    tunnel: object = None,
    clock: object = None,
    book: object = None,
    venue: object = None,
    signal_snapshot: object = None,
    exit_policy: object | None = None,
    venue_capabilities: object = _VENUE_CAPS,
) -> Result[AdmittedNodeSeat]:
    binding = _book_binding_record()
    resolved_binding_ref = (
        _ok(binding.fingerprint()).value if binding_ref is _MISSING else binding_ref
    )
    resolved_bms = binding.bms_instance_id.value if bms_instance_id is _MISSING else bms_instance_id
    bundle = world if world is not None else _world()
    layer2_factory = factory if isinstance(factory, FunctionFactory) else None
    ticket = _ok(_candidate(bundle, factory=layer2_factory)) if candidate is _MISSING else candidate
    logic: object = factory if factory is not None else FunctionFactory(logic=lambda evidence: ())
    return propose_node_seat(
        logic,
        seat_id="seat-alpha",
        binding_ref=resolved_binding_ref,
        bms_instance_id=resolved_bms,
        declaration=bundle["declaration"],
        containment=_containment(),
        candidate=ticket,
        admission_layers=admission_layers if admission_layers is not None else _layers(),
        exit_policy=exit_policy if exit_policy is not None else _exit_policy(),
        footprint_requirements=_requirements(),
        venue_capabilities=venue_capabilities,
        account_role=AccountRole.DEMO,
        assignment=assignment,
        read_surfaces={},
        stream_id="stream-eurusd",
        clock=clock,
        book=book,
        venue=venue,
        signal_snapshot=signal_snapshot,
        callback=callback,
        hosted=hosted,
        tunnel=tunnel,
    )


def _venue() -> VenueId:
    return _ok(VenueId.try_create("ctrader"))


def _instrument() -> Instrument:
    return Instrument(venue=_venue(), symbol="EURUSD")


def _account() -> Account:
    return _ok(Account.try_create("acct-1", _venue(), AccountRole.DEMO))


def _price(value: int) -> Price:
    return _ok(Price.try_create(value, _instrument(), 5))


def _r(numerator: int = 1, denominator: int = 1) -> ExactRational:
    return _ok(ExactRational.try_create(numerator, denominator, UnitKind.R_MULTIPLE))


def _rate() -> ExactRational:
    return _ok(ExactRational.try_create(1_000, 1, UnitKind.RATE))


def _entry(direction: Direction = Direction.LONG) -> EntryIntent:
    slot = _ok(EvidenceSlot.try_create("sqs", "sqs-ref-1", _instant()))
    cited = _ok(CitedEvidence.try_create(sqs_reading=slot))
    return _ok(
        EntryIntent.try_create(
            _instrument(),
            direction,
            _ok(ReasonCode.try_create("momentum-break", "scalper-v1")),
            _ok(ExecutionTarget.try_create("demo", _venue(), "acct-1")),
            proposed_r=_r(1),
            cited_evidence=cited,
        )
    )


def _append_live_source_event(
    *,
    store: EvidenceStore,
    writer: JournalWriter,
    venue_id: VenueId,
    account_id: int,
    session_epoch: str,
    wire_kind: str,
    native_id: str,
    instant: Instant,
    raw_payload: Mapping[str, object],
    journal_raw_payload: Mapping[str, object] | None = None,
) -> QmfJournalEvent:
    observation_sink = QmfLiveObservationSink(store=store, writer=writer)
    journal_store = _ok(store.for_world(World.LIVE)).journal
    journal_sink = QmfLiveJournalSink(
        writer=writer, journal_store=journal_store, evidence_store=store
    )
    observation = {
        "observation": {
            "payload": {
                "event_time_ns": instant.value_ns,
                "known_at_ns": instant.value_ns,
                "source": "ctrader-conformance-fixture",
                "source_native_id": native_id,
                "revision": "1",
                "venue_id": venue_id.value,
                "response_account_id": account_id,
                "response_session_epoch": session_epoch,
                "session_epoch": session_epoch,
                "wire_kind": wire_kind,
            }
        },
        "raw_payload": raw_payload,
    }
    recorded = _ok(observation_sink.emit(observation))
    appended = _ok(
        journal_sink.append(
            {
                "event_type": "data quality",
                "event_time_ns": instant.value_ns,
                "known_at_ns": instant.value_ns,
                "source": "ctrader-conformance-fixture",
                "source_native_id": native_id,
                "revision": "1",
                "venue_id": venue_id.value,
                "trader_account_id": account_id,
                "session_epoch": session_epoch,
                "wire_kind": wire_kind,
                "raw_payload": dict(
                    raw_payload if journal_raw_payload is None else journal_raw_payload
                ),
                "_observation_ack": recorded,
            }
        )
    )
    receipt = cast(JournalAppendReceipt, appended.detail["journal_append_receipt"])
    return receipt.event


class _OffsetStopModule:
    def derive_full_loss_price(
        self, *, entry_price: Price, direction: Direction, cited_evidence: CitedEvidence
    ) -> Result[Price]:
        del cited_evidence
        if direction is Direction.LONG:
            value = entry_price.value - 1_000
        else:
            value = entry_price.value + 1_000
        return Price.try_create(value, entry_price.instrument, entry_price.scale)


def _path(
    *,
    bms: str | None = None,
    binding_record: BookBindingRecord | None = None,
    ledger_epoch: Fingerprint | None = None,
    reservation_recovery: EntryReservationRecovery | None = None,
    reservation_journal: JournalSink[object] | None = None,
) -> BookPathContext:
    binding = binding_record if binding_record is not None else _book_binding_record()
    epoch = _ok(binding.fingerprint())
    position_epoch = ledger_epoch if ledger_epoch is not None else epoch
    reservation_journal = (
        RecordingJournalSink() if reservation_journal is None else reservation_journal
    )
    recovery = (
        EntryReservationRecovery(position_epoch, (), 0, True)
        if reservation_recovery is None
        else reservation_recovery
    )
    return BookPathContext(
        entry_price=_price(110_000),
        exit_logic_ref=_ok(
            ExitLogicRef.try_create("book.default.evidence_stop", {"style": "structure"})
        ),
        module=_OffsetStopModule(),
        book_resolved_requested_r=_r(1),
        r_unit_price=_rate(),
        value_factor=_ok(ValueFactor.try_create(100_000, 1, _instrument(), "USD")),
        money_scale=2,
        account=_account(),
        venue_id=_venue(),
        session_epoch="session-26-15",
        ordering_ordinal=0,
        bms_instance_id=bms if bms is not None else binding.bms_instance_id.value,
        protective_stop_forms={"market": ENTRY_RELATIVE_FORM},
        position_ledger=_ok(
            seed_binding_ledger(
                binding_epoch=position_epoch,
                seed=_ok(Money.try_create(100_000, "USD", 2)),
                recorded_at=_instant(),
                reservation_journal=reservation_journal,
                reservation_recovery=recovery,
            )
        ),
        native_execution_map=_ok(
            NativeExecutionMap.try_create(
                (
                    _ok(
                        NativeExecutionMapping.try_create(
                            _ok(ExecutionTarget.try_create("demo", _venue(), "acct-1")),
                            _instrument(),
                            native_account_id=42,
                            native_symbol_id=7,
                        )
                    ),
                ),
                registry_as_of_fingerprint=_ok(fingerprint({"registry": "seat-test"})),
                binding_epoch=epoch,
            )
        ),
        decision_at=_instant(),
        binding_record=binding,
    )


def _drive_probe() -> ScriptedLimitProbe:
    return ScriptedLimitProbe(elapsed_ns=(0, 1), memory_bytes=(1, 1))


# Public fixture aliases for cross-test composition without copying builders.
fixture_ok = _ok
fixture_instant = _instant
fixture_duration = _duration
fixture_book_binding_record = _book_binding_record
fixture_path = _path
fixture_venue = _venue
fixture_account = _account
fixture_propose = _propose
fixture_evidence_store = EvidenceStore
fixture_conformance_double = ConformanceDouble
fixture_entry_relative_form = ENTRY_RELATIVE_FORM


# --- surface ----------------------------------------------------------------


def test_admission_surface_and_closed_proof_roster() -> None:
    assert SEAT_ADMISSION_SURFACE == "qmn.seats.admission"
    assert SEAT_ADMISSION_PROOFS == (
        "registered_ct33",
        "qml_runtime_protocol",
        "prediction_linter",
        "declared_footprint",
        "canonical_assignment",
        "book_binding",
        "admission_layers",
    )
    assert ADMISSION_LAYER_NAMES == (
        "layer1_linters",
        "layer2_shakedown",
        "layer3_operator_signature",
    )
    assert INTENT_PATH_HOPS == ("book", "bms", "protection", "order")
    assert "admit_ungoverned_tunnel" in UNGOVERNED_TUNNEL_NAMES
    assert "ungoverned" in UNGOVERNED_EVIDENCE_KINDS
    assert "clock" in FORBIDDEN_SEAT_SURFACE_KEYS


# --- AC1: ungoverned tunnel cannot occupy a node seat -----------------------


def test_ungoverned_tunnel_access_is_refused_as_a_node_seat() -> None:
    access = _ok(admit_ungoverned_tunnel())
    refused = _refusal(_propose(candidate=access))
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["seat_allowed"] is False
    assert refused.context["tunnel_open"] is True
    missing = _refusal(_propose(candidate=None))
    assert missing.context["field"] == "candidate"
    explicit = refuse_ungoverned_tunnel_seat()
    assert explicit.category is RefusalCategory.POLICY_REJECTION


def test_missing_conformance_ticket_and_admission_layers_refuse() -> None:
    world = _world()
    refused = _refusal(_propose(world=world, candidate=object()))
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "candidate"
    incomplete = _refusal(_propose(world=world, admission_layers=_layers(layer3=False)))
    assert incomplete.context["field"] == "admission_layers"
    no_bms = _refusal(_propose(world=world, bms_instance_id=""))
    assert no_bms.category is RefusalCategory.INVALID_INPUT
    no_binding = _refusal(_propose(world=world, binding_ref=""))
    assert no_binding.category is RefusalCategory.INVALID_INPUT


def test_prediction_linter_and_canonical_assignment_run_at_seat_time() -> None:
    world = _world()
    unknown_family = _ok(
        ExitPolicy.try_create(
            {"other-family": _ok(ExitLogicRef.try_create("book.other", {"style": "structure"}))},
            permitted_exit_intent_kinds=(),
        )
    )
    predicted = _refusal(_propose(world=world, exit_policy=unknown_family))
    assert predicted.category is RefusalCategory.POLICY_REJECTION
    tuned = _refusal(_propose(world=world, assignment={"lookback": 21}))
    assert "canonical assignment" in str(tuned.context["reason"])
    caps = _refusal(_propose(world=world, venue_capabilities=frozenset({"trading"})))
    assert caps.context["field"] == "venue_capabilities"


def test_direct_callback_injection_refuses() -> None:
    def injected_callback(evidence: object) -> object:
        del evidence
        return ()

    world = _world()
    injected = _refusal(_propose(world=world, callback=injected_callback))
    assert injected.context["field"] == "callback"
    hosted = _ok(
        construct_bot(
            FunctionFactory(logic=lambda evidence: ()),
            declaration=world["declaration"],
            assignment={"lookback": 20},
            read_surfaces={},
        )
    )
    as_factory = _refusal(
        propose_node_seat(
            hosted,
            seat_id="seat-alpha",
            binding_ref="binding-live-1",
            bms_instance_id="bms-1",
            declaration=world["declaration"],
            containment=_containment(),
            candidate=_ok(_candidate(world)),
            admission_layers=_layers(),
            exit_policy=_exit_policy(),
            footprint_requirements=_requirements(),
            venue_capabilities=_VENUE_CAPS,
        )
    )
    assert as_factory.context["field"] == "factory"
    raw = _refusal(
        _propose(
            world=world,
            factory=injected_callback,
            candidate=_ok(_candidate(world)),
        )
    )
    assert raw.context["field"] == "factory"
    helper = inject_seat_callback(object())
    assert helper.category is RefusalCategory.POLICY_REJECTION


def test_clock_book_venue_and_signal_snapshot_are_refused_at_the_seat_door() -> None:
    clock = DataDrivenClock(
        boot_epoch_id="boot",
        wall_instants=(_instant(),),
        monotonic_ns=(0,),
    )
    assert _refusal(_propose(clock=clock)).category is RefusalCategory.POLICY_REJECTION
    assert _refusal(_propose(book=object())).category is RefusalCategory.POLICY_REJECTION
    assert _refusal(_propose(venue=object())).category is RefusalCategory.POLICY_REJECTION
    assert _refusal(_propose(signal_snapshot=object())).category is RefusalCategory.POLICY_REJECTION


def test_composition_root_ungoverned_imports_refuse() -> None:
    scanned = scan_production_src_for_ungoverned_tunnel()
    assert is_ok(scanned)
    helper = refuse_composition_root_ungoverned_import()
    assert helper.category is RefusalCategory.POLICY_REJECTION
    tree = ast.parse("from qml.conformance import admit_ungoverned_tunnel\n")
    assert ungoverned_tunnel_names_in_tree(tree) == ("admit_ungoverned_tunnel",)
    clean = ast.parse("from qmn.seats import propose_node_seat\n")
    assert ungoverned_tunnel_names_in_tree(clean) == ()


def test_governed_proposal_records_every_named_proof() -> None:
    admitted = _ok(_propose())
    assert isinstance(admitted, AdmittedNodeSeat)
    assert admitted.proof.proofs == SEAT_ADMISSION_PROOFS
    assert admitted.proof.assignment_is_canonical is True
    assert admitted.proof.candidate.ticket.layer1_passed is True
    assert admitted.proof.candidate.ticket.layer2_passed is True
    assert admitted.proof.admission_layers.all_passed is True
    assert admitted.proof.bms_instance_id == _book_binding_record().bms_instance_id.value
    assert admitted.seat.assignment_is_canonical is True
    identity = admitted.proof.fp1_identity()
    assert identity["class"] == "seat-admission-proof"
    assert identity["proofs"] == list(SEAT_ADMISSION_PROOFS)


# --- AC2: hosted intents cross Book/BMS/protection/order --------------------


def test_hosted_entry_crosses_book_bms_protection_and_order() -> None:
    factory = FunctionFactory(logic=lambda evidence: (_entry(),))
    admitted = _ok(_propose(factory=factory))
    receipt = _ok(
        dispatch_seat_intents(
            admitted,
            _instant(),
            path=_path(),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )
    assert receipt.hops == INTENT_PATH_HOPS
    assert receipt.bms_instance_id == admitted.proof.bms_instance_id
    assert len(receipt.authorized) == 1
    assert len(receipt.commands) == 1
    assert receipt.commands[0].kind is CommandKind.PLACE_ORDER
    assert receipt.authorized[0].requested_r == _r(1)
    assert not hasattr(receipt.authorized[0].admitted, "bot_quantity")


def test_hosted_entry_reservation_survives_dispatch_until_terminal_resolution() -> None:
    admitted = _ok(_propose())
    path = _path()
    first = _ok(dispatch_hosted_intents(admitted, (_entry(),), path=path))
    duplicate = _refusal(dispatch_hosted_intents(admitted, (_entry(),), path=path))
    assert duplicate.context["field"] == "has_open_virtual_position"
    command_id = _ok(first.commands[0].fingerprint())
    unknown = SubmissionResult(
        command_fp1=command_id,
        kind=first.commands[0].kind,
        outcome=SubmissionOutcome.UNKNOWN,
        observation=CommandObservation(
            command_fp1=command_id,
            kind=first.commands[0].kind,
            outcome=SubmissionOutcome.UNKNOWN,
            receive_instant=_instant(),
            detail="test UNKNOWN state",
        ),
        journal_event=VenueJournalEvent.for_outcome(
            command_id, first.commands[0].kind, SubmissionOutcome.UNKNOWN
        ),
    )
    _ok(
        cast(BindingVirtualLedger, path.position_ledger).observe_submission_outcome(
            "EURUSD", command_id, unknown
        )
    )
    still_unknown = _refusal(dispatch_hosted_intents(admitted, (_entry(),), path=path))
    assert still_unknown.context["field"] == "has_open_virtual_position"
    rejected = SubmissionResult(
        command_fp1=command_id,
        kind=first.commands[0].kind,
        outcome=SubmissionOutcome.REJECTED_BY_VENUE,
        observation=CommandObservation(
            command_fp1=command_id,
            kind=first.commands[0].kind,
            outcome=SubmissionOutcome.REJECTED_BY_VENUE,
            receive_instant=_instant(),
            venue_code="rejected",
        ),
        journal_event=VenueJournalEvent.for_outcome(
            command_id, first.commands[0].kind, SubmissionOutcome.REJECTED_BY_VENUE
        ),
    )
    _ok(
        cast(BindingVirtualLedger, path.position_ledger).observe_submission_outcome(
            "EURUSD", command_id, rejected
        )
    )
    _ok(dispatch_hosted_intents(admitted, (_entry(),), path=path))


def test_pending_entry_recovers_from_committed_journal_events_after_restart() -> None:
    admitted = _ok(_propose())
    journal = RecordingJournalSink()
    path = _path(reservation_journal=journal)
    _ok(dispatch_hosted_intents(admitted, (_entry(),), path=path))
    parsed_events = tuple(
        _ok(EntryReservationEvent.from_mapping(event)) for event in journal.appended
    )
    recovery = EntryReservationRecovery(
        _ok(cast(BookBindingRecord, path.binding_record).fingerprint()),
        parsed_events,
        len(parsed_events),
        True,
    )
    stale_projection = EntryReservationRecovery(recovery.binding_epoch, (), 0, True)
    downgrade = _refusal(
        cast(BindingVirtualLedger, path.position_ledger).recover_entry_reservations(
            stale_projection
        )
    )
    assert downgrade.context["field"] == "reservation_recovery"
    recovered_path = _path(
        binding_record=cast(BookBindingRecord, path.binding_record),
        reservation_recovery=recovery,
    )
    refused = _refusal(dispatch_hosted_intents(admitted, (_entry(),), path=recovered_path))
    assert refused.context["field"] == "has_open_virtual_position"


def test_uncertain_reservation_append_latches_entry_admission_closed() -> None:
    journal = RecordingJournalSink()
    path = _path(reservation_journal=journal)
    ledger = cast(BindingVirtualLedger, path.position_ledger)
    journal.partial = True
    identity = _ok(fingerprint({"command": "uncertain-reservation-test"}))
    refused = _refusal(ledger.reserve_entry("EURUSD", identity))
    assert refused.context["field"] == "reservation_journal"
    retry = _refusal(ledger.reserve_entry("EURUSD", identity))
    assert retry.context["field"] == "reservation_journal"
    incomplete = EntryReservationRecovery(
        _ok(cast(BookBindingRecord, path.binding_record).fingerprint()), (), 0, False
    )
    not_recovered = _refusal(ledger.recover_entry_reservations(incomplete))
    assert not_recovered.context["field"] == "reservation_recovery"
    empty_recovery = EntryReservationRecovery(incomplete.binding_epoch, (), 0, True)
    _ok(ledger.recover_entry_reservations(empty_recovery))
    assert ledger.reservation_admission_ready


class _AckWithoutCompletion:
    def __init__(self, detail: Mapping[str, object]) -> None:
        self.detail = detail

    def append(self, _event: object, /) -> Result[SinkAck]:
        return Ok(SinkAck(self.detail))


def test_reservation_append_requires_explicit_complete_true_ack() -> None:
    for detail in ({}, {"complete": False}, {"complete": "true"}):
        path = _path(reservation_journal=_AckWithoutCompletion(detail))
        ledger = cast(BindingVirtualLedger, path.position_ledger)
        identity = _ok(fingerprint({"missing-completion": repr(detail)}))
        refused = _refusal(ledger.reserve_entry("EURUSD", identity))
        assert refused.context["field"] == "reservation_journal"
        assert not ledger.has_pending_entry("EURUSD")
        assert not ledger.reservation_admission_ready


class _ConfiguredRootRecordSink:
    def write(self, _record: object, /) -> Result[SinkAck]:
        return Ok(SinkAck())


fixture_configured_root_record_sink = _ConfiguredRootRecordSink


def _exercise_configured_decision_root(
    tmp_path: Path,
    *,
    direction: Direction = Direction.LONG,
    after_root_ready: Callable[
        [HostedDecisionRoot, object, JournalStore, dict[str, object]], None
    ]
    | None = None,
) -> None:
    evidence = EvidenceStore(tmp_path / "evidence")
    world = _ok(evidence.for_world(World.LIVE))
    reservation_writer_id = _ok(
        WriterId.try_create("node-test", "risk", "entry-reservations", "boot-1")
    )
    reservation_journal = _ok(
        QmfEntryReservationJournal.resume(
            world.journal,
            reservation_writer_id,
            stream_name="entry-reservations",
            instant=_instant,
        )
    )
    binding = _book_binding_record()
    binding_epoch = _ok(binding.fingerprint())
    recovered = _ok(reservation_journal.recover(binding_epoch))
    path = _path(
        binding_record=binding,
        reservation_recovery=recovered,
        reservation_journal=reservation_journal,
    )
    ledger = cast(BindingVirtualLedger, path.position_ledger)

    decision_writer_id = _ok(
        WriterId.try_create("node-test", "supervisor", "hosted-decisions", "boot-1")
    )
    decision_journal = _ok(
        QmfHostedDecisionJournal.resume(
            world.journal,
            decision_writer_id,
            stream_name="hosted-decisions",
            instant=_instant,
        )
    )
    global_scope = KsaEnforcementScope.global_scope()
    stream_scope = _ok(KsaEnforcementScope.stream(_venue(), _account().account_id))
    global_epoch = _ok(
        mint_level_epoch(epoch_id="global-epoch-1", scope=global_scope, opened_at=_instant())
    )
    stream_epoch = _ok(
        mint_level_epoch(epoch_id="stream-epoch-1", scope=stream_scope, opened_at=_instant())
    )
    ksa_writer_id = _ok(WriterId.try_create("node-test", "risk", "ksa-state", "boot-1"))
    ksa_writer = _ok(JournalWriter.resume(world.journal, ksa_writer_id, stream_name="ksa-state"))
    for epoch in (global_epoch, stream_epoch):
        _ok(
            ksa_writer.record_control_action(
                "ksa-level-epoch",
                instant=_instant(),
                payload={
                    "class": KSA_EPOCH_CLASS,
                    "epoch_fp1": _ok(fingerprint(epoch.fp1_identity())).value,
                    "epoch_id": epoch.epoch_id,
                    "scope": epoch.scope.token(),
                },
            )
        )
    ksa_projection = _ok(
        KsaJournalProjection.try_create(
            reader=JournalReader(world.journal),
            world=World.LIVE,
            stream_name="ksa-state",
            global_epoch=global_epoch,
            stream_epoch=stream_epoch,
            authorized_writers=frozenset({ksa_writer_id}),
        )
    )
    record_sink = _ConfiguredRootRecordSink()
    ordinal_store = _ok(CommandOrdinalStore.try_create(_venue(), _account(), record_sink))
    _ok(ordinal_store.recover(0))
    binder = _ok(CommandIdentityBinder.try_create(record_sink, injective_total=False))
    pacer = _ok(
        ConnectionCommandPacer.try_create(
            local_queue_bound=_duration(5_000_000_000),
            protective_reserve_capacity=2,
            general_capacity=1,
        )
    )
    client = _ok(ConformanceDouble.try_create(World.LIVE, _venue()))
    assert client.kind is VenueClientKind.CONFORMANCE
    _ok(client.open_session(_account()))
    _ok(client.verify_capabilities())

    def timing_for(_command: object) -> Result[OrderPathTiming]:
        return Ok(
            OrderPathTiming(
                enqueued_at=_ok(MonotonicReading.try_create(100, "boot-1")),
                now_mono=_ok(MonotonicReading.try_create(200, "boot-1")),
                handed_off_at=_instant(_NS + 5),
            )
        )

    order_path = _ok(
        OrderPath.try_create(
            ordinal_store=ordinal_store,
            binder=binder,
            pacer=pacer,
            client=client,
            forms_per_order_type={"market": ENTRY_RELATIVE_FORM},
            submission_deadline_duration=_duration(5_000_000_000),
            command_journal=decision_journal,
            amend_journal=decision_journal,
            amend_atomicity=AmendAtomicity.ATOMIC,
            position_ledger=ledger,
        )
    )
    _ok(order_path.open_sequencer())
    bot_world = _world()
    bot_world["declaration"] = replace(
        cast(BotDefinition, bot_world["declaration"]),
        permitted_exit_intents=(
            ExitKind.CLOSE_FULL.value,
            ExitKind.TIGHTEN_PROTECTIVE_STOP.value,
        ),
    )
    exit_logic = _ok(ExitLogicRef.try_create("book.default.evidence_stop", {"style": "structure"}))
    exit_policy = _ok(
        ExitPolicy.try_create(
            {"trend-follow": exit_logic},
            permitted_exit_intent_kinds=(
                ExitKind.CLOSE_FULL,
                ExitKind.TIGHTEN_PROTECTIVE_STOP,
            ),
        )
    )
    ratchet_config = _ok(
        compile_node_config(
            book={
                "breakeven_ratchet_trigger": {
                    "value": {"numerator": 1, "denominator": 10, "unit_kind": "r-multiple"},
                    "value_status": "ratified",
                },
                "breakeven_ratchet_offset": {
                    "value": {
                        "value": 2,
                        "instrument": {"venue": _venue().value, "symbol": "EURUSD"},
                        "scale": 5,
                    },
                    "value_status": "ratified",
                },
                "amend_min_improvement": {
                    "value": {"numerator": 0, "denominator": 1, "unit_kind": "r-multiple"},
                    "value_status": "ratified",
                },
            }
        )
    )
    plan_writer_id = _ok(WriterId.try_create("node-test", "risk", "protection-plans", "boot-1"))
    plan_writer = _ok(
        JournalWriter.resume(world.journal, plan_writer_id, stream_name="protection-plans")
    )
    intent_state: dict[str, object] = {}
    factory = FunctionFactory(
        logic=lambda _evidence: intent_state.get("intents", (_entry(direction),))
    )
    admitted = _ok(_propose(factory=factory, world=bot_world, exit_policy=exit_policy))
    path = replace(
        path,
        exit_policy=exit_policy,
        resolved_node_config=ratchet_config,
        protection_plan_writer=plan_writer,
        protection_plan_journal=world.journal,
        amend_atomicity=AmendAtomicity.ATOMIC,
        dynamic_protection_policy=BookDynamicProtectionPolicy.SINGLE_SIDED_BREAKEVEN_RATCHET,
    )
    native_map = cast(NativeExecutionMap, path.native_execution_map)
    altered_row = replace(native_map.mappings[0], native_symbol_id=999)
    stale_native_map = replace(native_map, mappings=(altered_row, *native_map.mappings[1:]))
    stale_path = replace(path, native_execution_map=stale_native_map)
    stale_root = _refusal(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=stale_path,
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    assert stale_root.context["field"] == "native_execution_map"
    root = _ok(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=path,
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    sqs_key = _ok(sqs_baseline_key(_venue(), "demo", _instrument()))
    sqs = _ok(
        SqsReading.try_create(
            sqs_key,
            readiness=ProducerReadiness.OK,
            labeler_version="sqs-test-v1",
            score=_ok(ExactRational.try_create(1, 1, UnitKind.DIMENSIONLESS_RATIO)),
            hard_block=False,
        )
    )
    sqs_slot = _ok(
        ProducerSlot.try_create(
            "sqs", readiness=ProducerReadiness.OK, labeler_version="sqs-test-v1", sqs=sqs
        )
    )
    feed_slot = _ok(
        ProducerSlot.try_create(
            "feed_state",
            readiness=ProducerReadiness.OK,
            labeler_version="feed-test-v1",
            marker_detail="canonical",
        )
    )
    frontier = _instant(_NS - 1_000_000_000)
    snapshot = _ok(
        mint_signal_snapshot(
            frontier_instant=frontier,
            environment="demo",
            feed_state=CanonicalFeedState.LIVE,
            producers=(sqs_slot, feed_slot),
            decision_freshness_bound=_duration(5_000_000_000),
            degraded_sensors=(),
        )
    )
    demo_sqs_key = _ok(sqs_baseline_key(_venue(), "live", _instrument()))
    demo_sqs = _ok(
        SqsReading.try_create(
            demo_sqs_key,
            readiness=ProducerReadiness.OK,
            labeler_version="sqs-test-v1",
            score=_ok(ExactRational.try_create(1, 1, UnitKind.DIMENSIONLESS_RATIO)),
            hard_block=False,
        )
    )
    demo_snapshot = _ok(
        mint_signal_snapshot(
            frontier_instant=frontier,
            environment="live",
            feed_state=CanonicalFeedState.LIVE,
            producers=(
                _ok(
                    ProducerSlot.try_create(
                        "sqs",
                        readiness=ProducerReadiness.OK,
                        labeler_version="sqs-test-v1",
                        sqs=demo_sqs,
                    )
                ),
                feed_slot,
            ),
            decision_freshness_bound=_duration(5_000_000_000),
            degraded_sensors=(),
        )
    )
    if after_root_ready is not None:
        after_root_ready(root, snapshot, world.journal, intent_state)
        return
    wrong_environment = _refusal(
        root.run_slice(
            snapshot=demo_snapshot,
            decision_at=_instant(),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )
    assert wrong_environment.context["field"] == "snapshot_environment"
    transcript = _ok(
        root.run_slice(
            snapshot=snapshot,
            decision_at=_instant(),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )

    assert transcript.snapshot_fingerprint == _ok(snapshot.fingerprint())
    assert transcript.dispatch.commands[0].kind is CommandKind.PLACE_ORDER
    assert len(transcript.submissions) == 1
    submission = transcript.submissions[0]
    assert not isinstance(submission, OrderPathTerminalResolution)
    assert submission.result.outcome is SubmissionOutcome.ACCEPTED_BY_VENUE
    assert len(transcript.ksa_epoch_fingerprints) == 2
    assert len(transcript.ksa_event_fingerprints) == 2
    assert transcript.executed_stages[:3] == (
        "mis_snapshot_consumed_by_book",
        "mis_snapshot_consumed_by_ksa",
        "governed_seat_callback_completed",
    )
    checked = _ok(
        JournalReader(world.journal).read_checked("hosted-decisions", for_world=World.LIVE)
    )
    decision_rows = [
        event.payload
        for event in checked
        if event.payload.get("class") == "qmn-hosted-decision-transcript"
    ]
    assert len(decision_rows) == 2
    final_results = decision_rows[-1].get("order_results")
    assert isinstance(final_results, (list, tuple)) and final_results
    final_result = cast("Mapping[str, object]", final_results[0])
    assert final_result.get("outcome") == "accepted-by-venue"
    assert ledger.has_pending_entry("EURUSD") is True

    opening_command = transcript.dispatch.commands[0]
    opening_fp = _ok(opening_command.fingerprint())
    bind_writer_id = _ok(WriterId.try_create("node-test", "risk", "command-id-bindings", "boot-1"))
    bind_journal = _ok(
        QmfCommandIdBindingJournal.resume(
            world.journal,
            bind_writer_id,
            instant=lambda: Ok(_instant()),
            authorized_writers=(bind_writer_id,),
        )
    )
    registry = _ok(CommandIdBindingRegistry.try_create(bind_journal))
    _ok(
        registry.bind_before_submission(
            opening_command,
            venue_client_id="native-client-1",
            injective_total=False,
        )
    )
    command_binding = registry.binding_for("native-client-1")
    assert command_binding is not None
    faces = transcript.dispatch.authorized[0].faces
    quantity = transcript.dispatch.authorized[0].admitted_quantity
    opened = _ok(
        ledger.fold_fill(
            fill=AttributedFill(
                command_identity=opening_fp,
                venue_native_id="native-deal-1",
                instrument="EURUSD",
                quantity=quantity,
                realized_cash=None,
                recorded_at=_instant(),
            ),
            bot_id=admitted.proof.candidate.fingerprint.value,
            admission_identity=_ok(fingerprint(transcript.dispatch.authorized[0].fp1_identity())),
            faces=faces,
            admitted_quantity=quantity,
            entry_terminal=True,
        )
    )
    native_writer_id = _ok(
        WriterId.try_create("node-test", "venue", "native-observations", "boot-1")
    )
    native_writer = _ok(
        JournalWriter.resume(world.journal, native_writer_id, stream_name="native-observations")
    )
    lineage = {
        "positionId": 44,
        "accountId": 42,
        "symbolId": 7,
        "clientOrderId": "native-client-1",
        "orderId": 101,
        "dealId": 201,
        "sessionEpoch": path.session_epoch,
    }
    fill_event = _ok(
        native_writer.record(
            JournalEventType.FILL,
            {"raw_payload": lineage},
            instant=_instant(),
        )
    )
    raw_position = {
        "positionId": 44,
        "tradeData": {"symbolId": 7},
        "stopLoss": 1.09 if direction is Direction.LONG else 1.11,
        "positions": [lineage],
    }
    readback_event = _append_live_source_event(
        store=evidence,
        writer=native_writer,
        venue_id=_venue(),
        account_id=42,
        session_epoch=cast(str, path.session_epoch),
        wire_kind="position-readback",
        native_id="native-position-44-readback",
        instant=_instant(_NS + 2),
        raw_payload=raw_position,
        journal_raw_payload={"positions": [lineage]},
    )
    spot_event = _append_live_source_event(
        store=evidence,
        writer=native_writer,
        venue_id=_venue(),
        account_id=42,
        session_epoch=cast(str, path.session_epoch),
        wire_kind="spot",
        native_id="native-spot-44-ratchet",
        instant=_instant(_NS + 3),
        raw_payload=(
            {"bid": 110_150, "ask": 110_152}
            if direction is Direction.LONG
            else {"bid": 109_850, "ask": 109_852}
        ),
    )
    evidence_pair = NativePositionEvidence(
        fill_event=fill_event.event,
        readback_event=readback_event,
        fill_stream="native-observations",
        readback_stream="native-observations",
    )
    projection_writer_id = _ok(
        WriterId.try_create("node-test", "risk", "native-projections", "boot-1")
    )
    projection_writer = _ok(
        JournalWriter.resume(world.journal, projection_writer_id, stream_name="native-projections")
    )
    target = _ok(ExecutionTarget.try_create("demo", _venue(), _account().account_id))
    authority = NativeExitAuthority(
        journal=world.journal,
        authorized_writers=(native_writer_id,),
        command_binding_journal=bind_journal,
        evidence_by_position_ref={opened.position.position_ref.value: evidence_pair},
        binding_by_position_ref={opened.position.position_ref.value: command_binding},
        target=target,
        composition_fp=_ok(fingerprint({"composition": "native-exit-root-test"})),
        position_model=PositionModel.HEDGING,
        binding_id="binding-native-test",
        projection_writer=projection_writer,
        subject_present_at_submission=True,
        subject_observations=(),
        evidence_store=evidence,
        spot_events_by_position_ref={opened.position.position_ref.value: (spot_event,)},
        price_digits=5,
        price_rounding=RoundingMode.HALF_EVEN,
    )
    exit_path = replace(path, native_exit_authority=authority)
    exit_intent = _ok(
        ExitIntent.try_create(
            ExitKind.CLOSE_FULL,
            _ok(ReasonCode.try_create("risk-cut", "trend-follow")),
            opened.position.position_ref,
        )
    )
    other_world = _world()
    other_declaration = cast(BotDefinition, other_world["declaration"])
    other_logic = _ok(mint_logic_identity("research-bot", "2.0.0", _SOURCE))
    other_world["logic"] = other_logic
    other_world["declaration"] = replace(
        other_declaration,
        permitted_exit_intents=(ExitKind.CLOSE_FULL.value,),
        logic_reference=other_logic,
    )
    other_seat = _ok(_propose(factory=factory, world=other_world, exit_policy=exit_policy))
    foreign_account = _ok(Account.try_create("foreign-account", _venue(), AccountRole.DEMO))
    exit_refusals = (
        (
            admitted,
            replace(exit_path, account=foreign_account),
            "binding_epoch",
        ),
        (
            admitted,
            replace(exit_path, bms_instance_id="foreign-bms"),
            "bms_instance_id",
        ),
        (
            other_seat,
            exit_path,
            "book_exit_identity",
        ),
        (
            admitted,
            replace(
                exit_path,
                exit_logic_ref=_ok(ExitLogicRef.try_create("book.foreign.exit", {})),
            ),
            "exit_logic_ref",
        ),
        (
            admitted,
            replace(exit_path, module=object()),
            "exit_logic_ref",
        ),
        (
            admitted,
            replace(
                exit_path,
                native_exit_authority=replace(
                    authority,
                    binding_by_position_ref={
                        opened.position.position_ref.value: replace(
                            command_binding, session_epoch="foreign-session"
                        )
                    },
                ),
            ),
            "native_exit_identity",
        ),
        (
            admitted,
            replace(exit_path, decision_at=_instant()),
            "native_exit_frontier",
        ),
        (
            admitted,
            replace(
                exit_path,
                native_exit_authority=replace(
                    authority,
                    evidence_by_position_ref={},
                    binding_by_position_ref={},
                ),
            ),
            "native_evidence",
        ),
    )
    before_denied_decisions = _ok(
        JournalReader(world.journal).read_checked("hosted-decisions", for_world=World.LIVE)
    )
    before_denied_projections = _ok(
        JournalReader(world.journal).read_checked("native-projections", for_world=World.LIVE)
    )
    before_denied_ordinal = ordinal_store.high_water
    before_denied_ledger = ledger.records
    before_denied_venue = _ok(client.observations())
    for rejected_seat, rejected_path, expected_field in exit_refusals:
        refused_exit = _refusal(
            dispatch_hosted_intents(rejected_seat, (exit_intent,), path=rejected_path)
        )
        assert refused_exit.context["field"] == expected_field
        assert not _ok(
            JournalReader(world.journal).read_checked("native-projections", for_world=World.LIVE)
        )
    intent_state["intents"] = (exit_intent,)
    denied_policy = _ok(
        ExitPolicy.try_create({"trend-follow": exit_logic}, permitted_exit_intent_kinds=())
    )
    missing_book_binding = _refusal(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=replace(exit_path, binding_record=None),
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    assert missing_book_binding.context["field"] == "binding_record"
    denied_root = _ok(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=replace(exit_path, exit_policy=denied_policy),
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    denied = _refusal(
        denied_root.run_slice(
            snapshot=snapshot,
            decision_at=_instant(),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )
    assert denied.context["field"] == "exit_policy"
    after_denied_decisions = _ok(
        JournalReader(world.journal).read_checked("hosted-decisions", for_world=World.LIVE)
    )
    after_denied_projections = _ok(
        JournalReader(world.journal).read_checked("native-projections", for_world=World.LIVE)
    )
    assert after_denied_decisions == before_denied_decisions
    assert after_denied_projections == before_denied_projections == []
    assert ordinal_store.high_water == before_denied_ordinal
    assert ledger.records == before_denied_ledger
    assert _ok(client.observations()) == before_denied_venue
    tighten = _ok(
        TightenProtectiveStop.try_create(
            StopMoveDirection.TIGHTEN,
            _ok(PriceDelta.try_create(2_000, _instrument(), 5)),
        )
    )
    tighten_intent = _ok(
        ExitIntent.try_create(
            ExitKind.TIGHTEN_PROTECTIVE_STOP,
            _ok(ReasonCode.try_create("risk-cut", "trend-follow")),
            opened.position.position_ref,
            tighten=tighten,
        )
    )
    below_required_move = _ok(
        TightenProtectiveStop.try_create(
            StopMoveDirection.TIGHTEN,
            _ok(PriceDelta.try_create(997, _instrument(), 5)),
        )
    )
    too_small_bound = _ok(
        ExitIntent.try_create(
            ExitKind.TIGHTEN_PROTECTIVE_STOP,
            _ok(ReasonCode.try_create("risk-cut", "trend-follow")),
            opened.position.position_ref,
            tighten=below_required_move,
        )
    )
    bound_refusal = _refusal(
        dispatch_hosted_intents(
            admitted,
            (too_small_bound,),
            path=replace(exit_path, decision_at=_instant(_NS + 4)),
        )
    )
    assert bound_refusal.context["field"] == "tighten_bound"
    assert _ok(
        JournalReader(world.journal).read_checked("native-projections", for_world=World.LIVE)
    ) == before_denied_projections
    assert ordinal_store.high_water == before_denied_ordinal
    assert ledger.records == before_denied_ledger
    assert _ok(client.observations()) == before_denied_venue
    refused_tighten = _refusal(
        dispatch_hosted_intents(
                admitted,
                (tighten_intent,),
                path=replace(
                    exit_path,
                    decision_at=_instant(_NS + 4),
                    native_exit_authority=replace(
                    authority,
                    evidence_store=None,
                    spot_events_by_position_ref=None,
                ),
            ),
        )
    )
    assert refused_tighten.context["field"] == "protection_evidence"
    assert _ok(
        JournalReader(world.journal).read_checked("hosted-decisions", for_world=World.LIVE)
    ) == before_denied_decisions
    assert _ok(
        JournalReader(world.journal).read_checked("native-projections", for_world=World.LIVE)
    ) == before_denied_projections
    assert ordinal_store.high_water == before_denied_ordinal
    assert ledger.records == before_denied_ledger
    assert _ok(client.observations()) == before_denied_venue
    intent_state["intents"] = (tighten_intent,)
    ratchet_root = _ok(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=exit_path,
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    ratchet_transcript = _ok(
        ratchet_root.run_slice(
            snapshot=snapshot,
            decision_at=_instant(_NS + 4),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )
    assert len(ratchet_transcript.dispatch.commands) == 1
    ratchet_command = ratchet_transcript.dispatch.commands[0]
    assert ratchet_command.kind is CommandKind.AMEND_PROTECTION
    assert ratchet_command.subject_reference == "44"
    assert ratchet_command.protection_amendment is not None
    expected_signed_offset = -2 if direction is Direction.LONG else 2
    assert ratchet_command.protection_amendment.new_distance.value == expected_signed_offset
    ratchet_level = _ok(
        ratchet_command.protection_amendment.reference_price.add(
            ratchet_command.protection_amendment.new_distance
        )
    )
    assert ratchet_level.value == (109_998 if direction is Direction.LONG else 110_002)
    assert len(ratchet_transcript.dispatch.ratchet_authorizations) == 1
    ratchet_submission = ratchet_transcript.submissions[0]
    assert not isinstance(ratchet_submission, OrderPathTerminalResolution)
    assert ratchet_submission.result.outcome is SubmissionOutcome.ACCEPTED_BY_VENUE
    assert ledger.position_by_ref(opened.position.position_ref) == opened.position
    intent_state["intents"] = (exit_intent,)
    exit_root = _ok(
        HostedDecisionRoot.try_open(
            seat=admitted,
            path=exit_path,
            order_path=order_path,
            reservation_journal=reservation_journal,
            ksa_projection=ksa_projection,
            decision_journal=decision_journal,
            timing_for=timing_for,
        )
    )
    exit_transcript = _ok(
        exit_root.run_slice(
            snapshot=snapshot,
            decision_at=_instant(_NS + 5),
            stream=SeatTransitionStream(),
            cancel=CancelToken(),
            probe=_drive_probe(),
        )
    )
    assert exit_transcript.dispatch.commands[0].kind is CommandKind.CLOSE_POSITION
    assert exit_transcript.dispatch.commands[0].subject_reference == "44"
    assert (
        exit_transcript.dispatch.exit_attributions[0].virtual_position_ref
        == opened.position.position_ref
    )
    close_submission = exit_transcript.submissions[0]
    assert not isinstance(close_submission, OrderPathTerminalResolution)
    assert close_submission.result.outcome is SubmissionOutcome.ACCEPTED_BY_VENUE
    world.journal.close()
    reopened = JournalStore(
        World.LIVE,
        journal_dir=tmp_path / "evidence" / "live" / "journal",
        open_stream=jsonl_opener(),
    )
    reopened_decisions = _ok(
        JournalReader(reopened).read_checked("hosted-decisions", for_world=World.LIVE)
    )
    assert any(
        event.payload.get("class") == "qmn-hosted-decision-transcript"
        and "exit_attributions" in cast("Mapping[str, object]", event.payload.get("dispatch", {}))
        for event in reopened_decisions
    )
    reopened_projection = _ok(
        JournalReader(reopened).read_checked("native-projections", for_world=World.LIVE)
    )
    assert len(reopened_projection) == 2
    current = ledger.position_by_ref(opened.position.position_ref)
    assert current is not None and current.status.value == "open"
    reopened.close()


def test_configured_decision_root_replays_mis_book_ksa_reservation_and_orderpath(
    tmp_path: Path,
) -> None:
    _exercise_configured_decision_root(tmp_path)


def test_configured_decision_root_signs_nonzero_offset_for_short_stop(
    tmp_path: Path,
) -> None:
    _exercise_configured_decision_root(tmp_path, direction=Direction.SHORT)


fixture_exercise_configured_decision_root = _exercise_configured_decision_root


@pytest.mark.parametrize("fake_value", [None, "ack"])
def test_hosted_decision_sink_refuses_untyped_qmf_ack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fake_value: object,
) -> None:
    evidence = EvidenceStore(tmp_path / "evidence")
    world = _ok(evidence.for_world(World.LIVE))
    writer_id = _ok(WriterId.try_create("node-test", "supervisor", "hosted", "boot-1"))
    journal = _ok(
        QmfHostedDecisionJournal.resume(
            world.journal,
            writer_id,
            stream_name="hosted",
            instant=_instant,
        )
    )

    def malformed_record(
        _writer: JournalWriter, *_args: object, **_kwargs: object
    ) -> Result[JournalAppendReceipt]:
        return cast("Result[JournalAppendReceipt]", Ok(fake_value))

    monkeypatch.setattr(JournalWriter, "record", malformed_record)

    refused = _refusal(journal.append({"class": DECISION_TRANSCRIPT_CLASS}))

    assert refused.context["field"] == "decision_journal"


@pytest.mark.parametrize("damage", ["event", "store_receipt", "sequence"])
def test_hosted_decision_sink_verifies_full_physical_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    evidence = EvidenceStore(tmp_path / "evidence")
    world = _ok(evidence.for_world(World.LIVE))
    writer_id = _ok(WriterId.try_create("node-test", "supervisor", "hosted", "boot-1"))
    journal = _ok(
        QmfHostedDecisionJournal.resume(
            world.journal,
            writer_id,
            stream_name="hosted",
            instant=_instant,
        )
    )
    original = cast("Callable[..., Result[JournalAppendReceipt]]", JournalWriter.record)

    def damaged_record(
        writer: JournalWriter, *args: object, **kwargs: object
    ) -> Result[JournalAppendReceipt]:
        result = original(writer, *args, **kwargs)
        assert is_ok(result)
        receipt = result.value
        if damage == "event":
            receipt = replace(receipt, event=None)  # type: ignore[arg-type]
        elif damage == "store_receipt":
            receipt = replace(receipt, store_receipt=None)  # type: ignore[arg-type]
        else:
            receipt = replace(
                receipt,
                store_receipt=replace(receipt.store_receipt, sequence=999),
            )
        return cast("Result[JournalAppendReceipt]", Ok(receipt))

    monkeypatch.setattr(JournalWriter, "record", damaged_record)

    refused = _refusal(journal.append({"class": DECISION_TRANSCRIPT_CLASS}))

    assert refused.context["field"] == "decision_journal"


def test_hosted_decision_physical_sequence_spans_writer_boot_epochs(tmp_path: Path) -> None:
    stamp = _instant()
    store_one = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_one = _ok(WriterId.try_create("node-test", "supervisor", "hosted", "boot-1"))
    journal_one = _ok(
        QmfHostedDecisionJournal.resume(
            store_one,
            writer_one,
            stream_name="hosted",
            instant=lambda: stamp,
        )
    )
    assert is_ok(journal_one.append({"class": DECISION_TRANSCRIPT_CLASS, "boot": 1}))
    store_one.close()

    store_two = JournalStore(World.LIVE, journal_dir=tmp_path, open_stream=jsonl_opener())
    writer_two = _ok(WriterId.try_create("node-test", "supervisor", "hosted", "boot-2"))
    journal_two = _ok(
        QmfHostedDecisionJournal.resume(
            store_two,
            writer_two,
            stream_name="hosted",
            instant=lambda: stamp,
        )
    )

    appended = journal_two.append({"class": DECISION_TRANSCRIPT_CLASS, "boot": 2})

    assert is_ok(appended)
    assert appended.value.detail["complete"] is True
    events = _ok(JournalReader(store_two).read_checked("hosted", for_world=World.LIVE))
    assert len(events) == 2
    assert all(event.event_type is JournalEventType.DATA_QUALITY for event in events)
    store_two.close()


def test_ledger_binding_epoch_must_match_admitted_binding() -> None:
    admitted = _ok(_propose())
    path = _path(ledger_epoch=_ok(fingerprint({"wrong-binding-epoch": True})))
    refused = _refusal(dispatch_hosted_intents(admitted, (_entry(),), path=path))
    assert refused.context["field"] == "binding_epoch"


def test_bot_supplied_size_and_direct_ct19_refuse() -> None:
    admitted = _ok(_propose())
    sized = _refusal(
        dispatch_hosted_intents(
            admitted,
            {"kind": "entry", "quantity": _ok(Quantity.try_create(3, "lot", 0))},
            path=_path(),
        )
    )
    assert sized.category is RefusalCategory.INVALID_INPUT
    params = _ok(
        OrderParameters.try_create(
            OrderType.MARKET,
            TimeInForce.GOOD_TILL_CANCEL,
            _ok(Quantity.try_create(1, "lot", 0)),
        )
    )
    command = _ok(Command.place_order(_venue(), _account(), "session-26-15", 0, params))
    ct19 = _refusal(dispatch_hosted_intents(admitted, command, path=_path()))
    assert ct19.context["field"] == "ct19"
    helper = refuse_bot_constructed_ct19(command)
    assert helper.category is RefusalCategory.POLICY_REJECTION


def test_raw_ql7_construct_cannot_enter_the_money_path() -> None:
    world = _world()
    raw = _ok(
        construct_governed_seat(
            FunctionFactory(logic=lambda evidence: (_entry(),)),
            seat_id="seat-alpha",
            binding_ref="binding-live-1",
            declaration=world["declaration"],
            containment=_containment(),
            assignment={"lookback": 20},
            read_surfaces={},
        )
    )
    refused = _refusal(dispatch_hosted_intents(raw, (_entry(),), path=_path()))
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "seat"
    mismatched = _ok(_propose())
    bms = _refusal(dispatch_hosted_intents(mismatched, (_entry(),), path=_path(bms="bms-other")))
    assert bms.context["field"] == "bms_instance_id"


def test_ungoverned_evidence_cannot_cite_a_governed_seat() -> None:
    admitted = _ok(_propose())
    ungoverned = _refusal(
        cite_governed_seat_occurrence(
            seat=admitted,
            candidate=admitted.proof.candidate,
            evidence_kind="ungoverned",
        )
    )
    assert ungoverned.category is RefusalCategory.POLICY_REJECTION
    assert ungoverned.context["citation_allowed"] is False
    missing_ticket = _refusal(
        cite_governed_seat_occurrence(
            seat=admitted,
            candidate=None,
            evidence_kind="governed-evidence",
        )
    )
    assert missing_ticket.category is RefusalCategory.POLICY_REJECTION
    world = _world()
    raw = _ok(
        construct_governed_seat(
            FunctionFactory(logic=lambda evidence: ()),
            seat_id="seat-alpha",
            binding_ref="binding-live-1",
            declaration=world["declaration"],
            containment=_containment(),
        )
    )
    raw_cite = _refusal(
        cite_governed_seat_occurrence(
            seat=raw,
            candidate=admitted.proof.candidate,
            evidence_kind="governed-evidence",
        )
    )
    assert raw_cite.context["field"] == "seat"
    cited = _ok(
        cite_governed_seat_occurrence(
            seat=admitted,
            candidate=admitted.proof.candidate,
            evidence_kind="governed-evidence",
        )
    )
    assert cited.kind.value == "governed-evidence"
    assert cited.fingerprint == admitted.proof.candidate.fingerprint
