"""Registered ATC policy execution over persisted CT-10 replay evidence.

This module owns the generic QMB execution seam for AlternativeRunConfig. Policy
interpretation is supplied by a trusted, exact-identity registration; QMB does not
infer financial meaning from opaque PolicyPair tokens. Each evaluator transition
is persisted as a CT-13 decision before its state becomes part of the accepted run.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Protocol, cast, runtime_checkable

from qmf.core import (
    ExactRational,
    Fingerprint,
    Instant,
    Money,
    Ok,
    Result,
    TypedRefusal,
    UnitKind,
    World,
    WriteOutcome,
    fingerprint,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.core.exact import MONEY_STORAGE_SCALE
from qmf.data.journal import DecisionOutcome, JournalEvent, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.observation import SourceObservation
from qmf.data.splits import SegmentRole
from qmf.data.store import JournalStore
from qmf.data.store.receipts import StoreReceipt
from qmf.data.store.rooms import RoomRole

from qmb._refuse import invalid, policy, unavailable
from qmb.config.alternative import (
    ADAPTER_INTERNAL_SIMULATE,
    VERDICT_ADMITTED_SIMULATE,
    AlternativeRunConfig,
    AtcSimulateReceipt,
    simulate_alternative_run,
    validate_alternative_run_config,
)
from qmb.host.replay import RecordedReplaySource
from qmb.optimize.sampler import validate_trial_label
from qmb.runloop.loop import EventSlice, SliceObservation

__all__ = [
    "ATCJournalReference",
    "AlternativeEvaluationRequest",
    "AlternativeInterpreterRegistry",
    "AlternativeMeasure",
    "AlternativeMeasureDeclaration",
    "AlternativePolicyEvaluation",
    "AlternativePolicyInterpreter",
    "AlternativeRunReceipt",
    "InternalSimulatedAction",
    "PolicyInterpreterRegistration",
    "execute_alternative_run",
    "recover_alternative_run_receipt",
]


def _exact_value(value: object, field: str) -> object | TypedRefusal:
    """Normalize supported exact values to canonical JSON data, refusing floats."""
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Fingerprint):
        return value.value
    if isinstance(value, Mapping):
        entries = cast("Mapping[object, object]", value)
        result: dict[str, object] = {}
        for key, item in entries.items():
            if not isinstance(key, str) or not key.strip():
                return invalid(field, "exact state and action mappings use named string keys")
            normalized = _exact_value(item, field)
            if isinstance(normalized, TypedRefusal):
                return normalized
            result[key] = normalized
        return result
    if isinstance(value, (tuple, list)):
        items = cast("Sequence[object]", value)
        result_list: list[object] = []
        for item in items:
            normalized = _exact_value(item, field)
            if isinstance(normalized, TypedRefusal):
                return normalized
            result_list.append(normalized)
        return result_list
    identity = getattr(value, "fp1_identity", None)
    if callable(identity):
        try:
            return _exact_value(identity(), field)
        except Exception:
            return invalid(field, "exact value identity could not be read")
    return invalid(
        field,
        "ATC state and actions use exact JSON values or QMF values with fp1_identity; "
        "binary floats and opaque objects are refused",
        given=type(value).__name__,
    )


def _freeze_mapping(value: object, field: str) -> Mapping[str, object] | TypedRefusal:
    if not isinstance(value, Mapping):
        return invalid(field, "an ATC state/action body is a mapping")
    normalized = _exact_value(cast("Mapping[object, object]", value), field)
    if isinstance(normalized, TypedRefusal):
        return normalized
    if not isinstance(normalized, dict):
        return invalid(field, "an ATC state/action body is a named exact mapping")
    normalized_mapping = cast("dict[str, object]", normalized)

    def freeze(item: object) -> object:
        if isinstance(item, dict):
            entries = cast("dict[str, object]", item)
            frozen_entries = {key: freeze(child) for key, child in entries.items()}
            return MappingProxyType(frozen_entries)
        if isinstance(item, list):
            children = cast("list[object]", item)
            return tuple(freeze(child) for child in children)
        return item

    return cast("Mapping[str, object]", freeze(normalized_mapping))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        entries = cast("Mapping[str, object]", value)
        return {key: _plain(item) for key, item in entries.items()}
    if isinstance(value, tuple):
        items = cast("tuple[object, ...]", value)
        return [_plain(item) for item in items]
    return value


@dataclass(frozen=True, slots=True)
class AlternativeMeasure:
    """One policy-owned exact ATC measure with its explicit CT-01 unit-kind.

    This is QMB ATC evidence and carries no CT-32/Book performance contract.
    The registered PolicyPair/interpreter identity pins the measure's semantics.
    """

    measure_identity: str
    quantity: ExactRational | Money

    @classmethod
    def try_create(cls, measure_identity: object, quantity: object) -> Result[AlternativeMeasure]:
        if not isinstance(measure_identity, str) or not measure_identity.strip():
            return invalid("measure_identity", "an ATC measure has a named identity")
        if not isinstance(quantity, (ExactRational, Money)):
            return invalid(
                "quantity",
                "an ATC measure carries exact Money or ExactRational with a unit-kind",
            )
        return Ok(cls(measure_identity.strip(), quantity))

    @property
    def unit_kind(self) -> str:
        """The unit-kind carried by the exact QMF quantity."""
        return self.quantity.unit_kind.value

    @property
    def currency(self) -> str | None:
        """The declared currency for money-valued policy measures."""
        return self.quantity.currency if isinstance(self.quantity, Money) else None

    def fp1_identity(self) -> dict[str, object]:
        """Canonical ATC measure identity; intentionally independent of CT-32."""
        body: dict[str, object] = {
            "class": "qmb-alternative-measure-v1",
            "measure_identity": self.measure_identity,
            "quantity": self.quantity.fp1_identity(),
            "unit_kind": self.unit_kind,
        }
        if self.currency is not None:
            body["currency"] = self.currency
        return body


@dataclass(frozen=True, slots=True)
class AlternativeMeasureDeclaration:
    """A registered interpreter's declared measure identity and CT-01 units."""

    measure_identity: str
    unit_kind: str
    currency: str | None = None

    @classmethod
    def try_create(
        cls, measure_identity: object, unit_kind: object, currency: object = None
    ) -> Result[AlternativeMeasureDeclaration]:
        if not isinstance(measure_identity, str) or not measure_identity.strip():
            return invalid("measure_identity", "a declared ATC measure has a stable identity")
        if not isinstance(unit_kind, str) or unit_kind not in {item.value for item in UnitKind}:
            return invalid("unit_kind", "a declared ATC measure uses an explicit CT-01 unit-kind")
        parsed_currency: str | None = None
        if currency is not None:
            if not isinstance(currency, str) or not currency.strip():
                return invalid("currency", "a declared ATC measure currency is named")
            parsed_currency = currency.strip()
        if unit_kind == UnitKind.MONEY.value and parsed_currency is None:
            return invalid("currency", "money-valued ATC measures declare their currency")
        if unit_kind != UnitKind.MONEY.value and parsed_currency is not None:
            return invalid("currency", "non-money ATC measures carry no currency")
        return Ok(cls(measure_identity.strip(), unit_kind, parsed_currency))

    def fp1_identity(self) -> dict[str, object]:
        body: dict[str, object] = {
            "class": "qmb-alternative-measure-declaration-v1",
            "measure_identity": self.measure_identity,
            "unit_kind": self.unit_kind,
        }
        if self.currency is not None:
            body["currency"] = self.currency
        return body


@dataclass(frozen=True, slots=True)
class InternalSimulatedAction:
    """A policy's internal replay action; it can never carry a venue command."""

    action_id: str
    action_type: str
    body: Mapping[str, object]

    @classmethod
    def try_create(
        cls, *, action_id: object, action_type: object, body: object
    ) -> Result[InternalSimulatedAction]:
        if not isinstance(action_id, str) or not action_id.strip():
            return invalid("action_id", "an internal simulated action has a stable id")
        if not isinstance(action_type, str) or not action_type.strip():
            return invalid("action_type", "an internal simulated action has a named type")
        if action_type in {
            "place_order",
            "cancel_order",
            "close_position",
            "close_all",
            "amend_protection",
        }:
            return policy("action_type", "QMB ATC simulation does not issue venue commands")
        frozen = _freeze_mapping(body, "action_body")
        if isinstance(frozen, TypedRefusal):
            return frozen
        return Ok(cls(action_id=action_id, action_type=action_type, body=frozen))

    def identity(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "body": _plain(self.body),
        }


@dataclass(frozen=True, slots=True)
class AlternativePolicyEvaluation:
    """Exact evaluator result for one CT-10 frontier."""

    accounting_state: Mapping[str, object]
    risk_verdict: str
    risk_accepted: bool
    actions: tuple[InternalSimulatedAction, ...]
    measures: tuple[AlternativeMeasure, ...] = ()

    @classmethod
    def try_create(
        cls,
        *,
        accounting_state: object,
        risk_verdict: object,
        risk_accepted: object,
        actions: object,
        measures: object = (),
    ) -> Result[AlternativePolicyEvaluation]:
        state = _freeze_mapping(accounting_state, "accounting_state")
        if isinstance(state, TypedRefusal):
            return state
        if not isinstance(risk_verdict, str) or not risk_verdict.strip():
            return invalid("risk_verdict", "an evaluator returns its explicit risk verdict")
        if not isinstance(risk_accepted, bool):
            return invalid("risk_accepted", "risk acceptance is an explicit bool")
        if isinstance(actions, (str, bytes)) or not isinstance(actions, Sequence):
            return invalid("actions", "internal simulated actions are an ordered sequence")
        action_list = tuple(cast("Sequence[object]", actions))
        normalized_actions: list[InternalSimulatedAction] = []
        for action in action_list:
            if not isinstance(action, InternalSimulatedAction):
                return invalid("actions", "every action is an InternalSimulatedAction")
            normalized = InternalSimulatedAction.try_create(
                action_id=action.action_id,
                action_type=action.action_type,
                body=action.body,
            )
            if is_refusal(normalized):
                return normalized
            normalized_actions.append(normalized.value)
        action_list = tuple(normalized_actions)
        if len({action.action_id for action in action_list}) != len(action_list):
            return invalid("actions", "simulated action ids are unique within a frontier")
        if not risk_accepted and action_list:
            return policy("actions", "a risk-refused frontier cannot accept simulated actions")
        if isinstance(measures, (str, bytes)) or not isinstance(measures, Sequence):
            return invalid("measures", "policy measures are an ordered sequence of exact metrics")
        normalized_measures: list[AlternativeMeasure] = []
        for index, value in enumerate(cast("Sequence[object]", measures)):
            if not isinstance(value, AlternativeMeasure):
                return invalid(
                    "measures",
                    "policy outputs are typed exact AlternativeMeasure values",
                    index=index,
                )
            normalized = AlternativeMeasure.try_create(value.measure_identity, value.quantity)
            if is_refusal(normalized):
                return normalized
            normalized_measures.append(normalized.value)
        if len({measure.measure_identity for measure in normalized_measures}) != len(
            normalized_measures
        ):
            return invalid("measures", "each policy measure identity occurs once per frontier")
        return Ok(cls(state, risk_verdict, risk_accepted, action_list, tuple(normalized_measures)))

    def identity(self) -> dict[str, object]:
        return {
            "accounting_state": _plain(self.accounting_state),
            "actions": [action.identity() for action in self.actions],
            "measures": [measure.fp1_identity() for measure in self.measures],
            "risk_accepted": self.risk_accepted,
            "risk_verdict": self.risk_verdict,
        }


@dataclass(frozen=True, slots=True)
class AlternativeEvaluationRequest:
    """Immutable input passed to a registered policy interpreter."""

    config: AlternativeRunConfig
    frontier: Instant
    observations: tuple[SourceObservation, ...]
    input_fingerprint: Fingerprint
    prior_accounting_state: Mapping[str, object]
    prior_accounting_state_fingerprint: Fingerprint


@runtime_checkable
class AlternativePolicyInterpreter(Protocol):
    """Trusted interpreter for one exact PolicyPair identity."""

    def evaluate(
        self, request: AlternativeEvaluationRequest
    ) -> Result[AlternativePolicyEvaluation]:
        """Interpret configured accounting and risk values for one frontier."""
        ...


def _policy_key(config: AlternativeRunConfig) -> tuple[str, int, str]:
    return (
        config.policy_pair.policy_pair_id,
        config.policy_pair.policy_pair_version,
        config.policy_pair.policy_pair_hash.value,
    )


@dataclass(frozen=True, slots=True)
class PolicyInterpreterRegistration:
    """Trusted binding from exact PolicyPair identity to one interpreter version."""

    policy_pair_id: str
    policy_pair_version: int
    policy_pair_hash: Fingerprint
    interpreter_id: str
    interpreter_version: int
    interpreter_fp1: Fingerprint
    interpreter: AlternativePolicyInterpreter
    declared_measures: tuple[AlternativeMeasureDeclaration, ...]
    fingerprint: Fingerprint

    @classmethod
    def try_create(
        cls,
        *,
        policy_pair_id: object,
        policy_pair_version: object,
        policy_pair_hash: object,
        interpreter_id: object,
        interpreter_version: object,
        interpreter_fp1: object,
        interpreter: object,
        declared_measures: object = (),
    ) -> Result[PolicyInterpreterRegistration]:
        if not isinstance(policy_pair_id, str) or not policy_pair_id.strip():
            return invalid("policy_pair_id", "an interpreter registration pins a PolicyPair id")
        for value, field in (
            (policy_pair_version, "policy_pair_version"),
            (interpreter_version, "interpreter_version"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                return invalid(field, "identity versions are positive integers")
        pair_hash = _fingerprint(policy_pair_hash, "policy_pair_hash")
        if isinstance(pair_hash, TypedRefusal):
            return pair_hash
        impl_fp = _fingerprint(interpreter_fp1, "interpreter_fp1")
        if isinstance(impl_fp, TypedRefusal):
            return impl_fp
        if not isinstance(interpreter_id, str) or not interpreter_id.strip():
            return invalid("interpreter_id", "a trusted interpreter has a stable id")
        if not callable(getattr(interpreter, "evaluate", None)):
            return invalid("interpreter", "a registered policy interpreter implements evaluate")
        if isinstance(declared_measures, (str, bytes)) or not isinstance(
            declared_measures, Sequence
        ):
            return invalid("declared_measures", "interpreter measures are an ordered sequence")
        declarations: list[AlternativeMeasureDeclaration] = []
        for index, value in enumerate(cast("Sequence[object]", declared_measures)):
            if not isinstance(value, AlternativeMeasureDeclaration):
                return invalid("declared_measures", "each declared output is typed", index=index)
            checked_declaration = AlternativeMeasureDeclaration.try_create(
                value.measure_identity, value.unit_kind, value.currency
            )
            if is_refusal(checked_declaration):
                return checked_declaration
            declarations.append(checked_declaration.value)
        if len({item.measure_identity for item in declarations}) != len(declarations):
            return invalid("declared_measures", "declared ATC measure identities are unique")
        pair_version = cast(int, policy_pair_version)
        implementation_version = cast(int, interpreter_version)
        identity = {
            "class": "qmb-atc-policy-interpreter-registration-v1",
            "interpreter_fp1": impl_fp.value,
            "interpreter_id": interpreter_id,
            "interpreter_version": implementation_version,
            "declared_measures": [item.fp1_identity() for item in declarations],
            "policy_pair_hash": pair_hash.value,
            "policy_pair_id": policy_pair_id,
            "policy_pair_version": pair_version,
        }
        stamped = fingerprint(identity)
        if is_refusal(stamped):
            return stamped
        return Ok(
            cls(
                policy_pair_id,
                pair_version,
                pair_hash,
                interpreter_id,
                implementation_version,
                impl_fp,
                cast("AlternativePolicyInterpreter", interpreter),
                tuple(declarations),
                stamped.value,
            )
        )

    def identity(self) -> dict[str, object]:
        return {
            "class": "qmb-atc-policy-interpreter-registration-v1",
            "interpreter_fp1": self.interpreter_fp1.value,
            "interpreter_id": self.interpreter_id,
            "interpreter_version": self.interpreter_version,
            "declared_measures": [item.fp1_identity() for item in self.declared_measures],
            "policy_pair_hash": self.policy_pair_hash.value,
            "policy_pair_id": self.policy_pair_id,
            "policy_pair_version": self.policy_pair_version,
        }


def _fingerprint(value: object, field: str) -> Fingerprint | TypedRefusal:
    if isinstance(value, Fingerprint):
        return value
    parsed = Fingerprint.try_create(value)
    return (
        parsed.value
        if not is_refusal(parsed)
        else invalid(field, "a valid fp1 fingerprint is required")
    )


@dataclass(frozen=True, slots=True)
class AlternativeInterpreterRegistry:
    """Immutable registry whose keys include PolicyPair id, version, and hash."""

    registrations: Mapping[tuple[str, int, str], PolicyInterpreterRegistration]
    fingerprint: Fingerprint

    @classmethod
    def try_create(cls, registrations: object) -> Result[AlternativeInterpreterRegistry]:
        if isinstance(registrations, (str, bytes)) or not isinstance(registrations, Sequence):
            return invalid("registrations", "the interpreter registry is a sequence")
        resolved: dict[tuple[str, int, str], PolicyInterpreterRegistration] = {}
        for index, registration in enumerate(cast("Sequence[object]", registrations)):
            if not isinstance(registration, PolicyInterpreterRegistration):
                return invalid("registrations", "every registry entry is typed", index=index)
            checked = PolicyInterpreterRegistration.try_create(
                policy_pair_id=registration.policy_pair_id,
                policy_pair_version=registration.policy_pair_version,
                policy_pair_hash=registration.policy_pair_hash,
                interpreter_id=registration.interpreter_id,
                interpreter_version=registration.interpreter_version,
                interpreter_fp1=registration.interpreter_fp1,
                interpreter=registration.interpreter,
                declared_measures=registration.declared_measures,
            )
            if is_refusal(checked) or checked.value.fingerprint != registration.fingerprint:
                return policy(
                    "registrations",
                    "registration identity matches its fingerprint",
                    index=index,
                )
            checked_registration = checked.value
            key = (
                checked_registration.policy_pair_id,
                checked_registration.policy_pair_version,
                checked_registration.policy_pair_hash.value,
            )
            if key in resolved:
                return invalid("registrations", "each exact PolicyPair identity is registered once")
            resolved[key] = checked_registration
        stamped = fingerprint(
            {
                "class": "qmb-atc-policy-interpreter-registry-v1",
                "registrations": [item.identity() for item in resolved.values()],
            }
        )
        if is_refusal(stamped):
            return stamped
        return Ok(cls(MappingProxyType(resolved), stamped.value))

    def resolve(self, config: AlternativeRunConfig) -> Result[PolicyInterpreterRegistration]:
        registration = self.registrations.get(_policy_key(config))
        if registration is None:
            return unavailable(
                "policy_interpreter",
                "no explicitly registered interpreter matches exact PolicyPair id/version/hash",
                policy_pair_id=config.policy_pair.policy_pair_id,
                policy_pair_version=config.policy_pair.policy_pair_version,
                policy_pair_hash=config.policy_pair.policy_pair_hash.value,
            )
        return Ok(registration)


@dataclass(frozen=True, slots=True)
class ATCJournalReference:
    """One durable CT-13 decision and its underlying store receipt reference."""

    frontier: Instant
    event_fingerprint: Fingerprint
    store_fingerprint: Fingerprint
    store_sequence: int
    sequence: int
    output_fingerprint: Fingerprint

    def identity(self) -> dict[str, object]:
        return {
            "event_fp1": self.event_fingerprint.value,
            "frontier_ns": self.frontier.value_ns,
            "output_fp1": self.output_fingerprint.value,
            "sequence": self.sequence,
            "store_receipt_fp1": self.store_fingerprint.value,
            "store_sequence": self.store_sequence,
        }


@dataclass(frozen=True, slots=True)
class AlternativeRunReceipt:
    """ATC execution receipt; contains actual persisted CT-13 references, never CT-32."""

    config: AlternativeRunConfig
    simulate: AtcSimulateReceipt
    source_fingerprint: Fingerprint
    split_fingerprint: Fingerprint
    split_role: SegmentRole
    registry_fingerprint: Fingerprint
    interpreter_registration: PolicyInterpreterRegistration
    journal_writer: WriterId
    journal_stream: str
    initial_accounting_state_fingerprint: Fingerprint
    final_accounting_state: Mapping[str, object]
    final_accounting_state_fingerprint: Fingerprint
    final_measures: tuple[AlternativeMeasure, ...]
    journal_references: tuple[ATCJournalReference, ...]
    trial_label: Mapping[str, object] | None
    fingerprint: Fingerprint

    def fp1_identity(self) -> dict[str, object]:
        identity: dict[str, object] = {
            "class": "qmb-alternative-run-result-v1",
            "composition_fp1": self.config.composition_fp.value,
            "final_accounting_state_fp1": self.final_accounting_state_fingerprint.value,
            "initial_accounting_state_fp1": self.initial_accounting_state_fingerprint.value,
            "interpreter_registration_fp1": self.interpreter_registration.fingerprint.value,
            "journal_refs": [reference.identity() for reference in self.journal_references],
            "journal_stream": self.journal_stream,
            "journal_writer": {
                "boot_epoch_id": self.journal_writer.boot_epoch_id,
                "machine": self.journal_writer.machine,
                "role": self.journal_writer.role,
                "stream": self.journal_writer.stream,
            },
            "final_measures": [measure.fp1_identity() for measure in self.final_measures],
            "policy_pair_identity": self.config.policy_pair.identity(),
            "registry_fp1": self.registry_fingerprint.value,
            "source_fp1": self.source_fingerprint.value,
            "split_fp1": self.split_fingerprint.value,
            "split_role": self.split_role.value,
        }
        if self.trial_label is not None:
            identity["trial_label"] = _plain(self.trial_label)
        return identity


def _validate_source(source: object) -> dict[int, list[SourceObservation]] | TypedRefusal:
    if not isinstance(source, RecordedReplaySource):
        return invalid("recorded_source", "ATC execution consumes a validated RecordedReplaySource")
    if source.world is not World.REPLAY:
        return policy("world", "ATC internal execution is replay-world only")
    if source.split_fp1 is None or source.split_role is None:
        return policy("split", "an ATC run pins its CT-12 split manifest and segment role")
    if source.split_role is SegmentRole.SEALED_TEST:
        return policy("split_role", "sealed-test data is not admitted to ordinary ATC execution")
    if not source.observations or not source.slices:
        return invalid("recorded_source", "a recorded ATC source has observations and frontiers")
    observations = cast("tuple[object, ...]", source.observations)
    for index, observation_value in enumerate(observations):
        observation: object = observation_value
        if not isinstance(observation, SourceObservation):
            return invalid(
                "observations", "recorded replay observations are CT-10 values", index=index
            )
        stamped = fingerprint(observation.fp1_identity())
        if is_refusal(stamped) or stamped.value != observation.fingerprint:
            return policy(
                "observations", "CT-10 observation identity matches its fingerprint", index=index
            )
    stamped_source = fingerprint(source.fp1_identity())
    if is_refusal(stamped_source) or stamped_source.value != source.fingerprint:
        return policy("recorded_source", "recorded source identity matches its fingerprint")
    expected: dict[int, list[SourceObservation]] = {}
    for observation_value in observations:
        observation = cast(SourceObservation, observation_value)
        frontier = max(observation.event_time.value_ns, observation.known_at.value_ns)
        expected.setdefault(frontier, []).append(observation)
    frontiers = sorted(expected)
    if len(frontiers) != len(source.slices):
        return policy("slices", "every recorded CT-10 frontier has exactly one replay slice")
    for index, (frontier_ns, event_slice) in enumerate(zip(frontiers, source.slices, strict=True)):
        event_slice_value: object = cast(object, event_slice)
        if (
            not isinstance(event_slice_value, EventSlice)
            or len(event_slice_value.observations) != 1
        ):
            return invalid(
                "slices", "each recorded frontier has one stream observation", index=index
            )
        slice_observation_value: object = cast(object, event_slice_value.observations[0])
        if (
            not isinstance(slice_observation_value, SliceObservation)
            or slice_observation_value.stream_id != source.stream_id
            or not slice_observation_value.closed
            or slice_observation_value.instant.value_ns != frontier_ns
        ):
            return policy(
                "slices", "replay frontier matches CT-10 known-at observations", index=index
            )
    return expected


def _validate_append_receipt(
    receipt: object,
    *,
    expected_writer: JournalWriter,
    expected_sequence: int,
    expected_instant: Instant,
    expected_payload: Mapping[str, object],
    expected_outcome: DecisionOutcome,
    expected_correlation_id: str,
    store: JournalStore,
) -> Result[tuple[JournalEvent, StoreReceipt]]:
    """Bind the writer acknowledgment to a complete event and the stored raw row."""
    if not isinstance(receipt, JournalAppendReceipt):
        return invalid("journal_receipt", "record returns a typed JournalAppendReceipt")
    event_value: object = cast(object, receipt.event)
    store_receipt_value: object = cast(object, receipt.store_receipt)
    if not isinstance(event_value, JournalEvent) or not isinstance(
        store_receipt_value, StoreReceipt
    ):
        return invalid(
            "journal_receipt",
            "an append receipt contains a typed JournalEvent and StoreReceipt",
        )
    event = event_value
    store_receipt = store_receipt_value
    if receipt.edge_receipts:
        return policy("journal_receipt", "a single ATC decision has no unverified side writes")
    event_matches = (
        event.event_type is JournalEventType.DECISION
        and event.writer == expected_writer.writer
        and event.world is World.REPLAY
        and event.sequence == expected_sequence
        and event.instant == expected_instant
        and event.outcome is expected_outcome
        and _plain(event.payload) == _plain(expected_payload)
        and event.correlation_id == expected_correlation_id
    )
    if not event_matches:
        return policy(
            "journal_event",
            "the acknowledged event exactly matches the requested ATC decision",
            event_sequence=event.sequence,
            expected_sequence=expected_sequence,
            event_correlation=event.correlation_id,
            expected_correlation=expected_correlation_id,
            event_type=getattr(event.event_type, "value", event.event_type),
            writer_matches=event.writer == expected_writer.writer,
            world=getattr(event.world, "value", event.world),
            instant_matches=event.instant == expected_instant,
            outcome=getattr(event.outcome, "value", event.outcome),
            outcome_matches=event.outcome is expected_outcome,
            payload_matches=_plain(event.payload) == _plain(expected_payload),
        )
    event_identity = fingerprint(event.fp1_identity())
    if is_refusal(event_identity) or event_identity.value != event.fingerprint:
        return policy("journal_event", "the acknowledged event fingerprint is complete")
    sequence_value: object = cast(object, store_receipt.sequence)
    format_value: object = cast(object, store_receipt.format_version)
    if (
        store_receipt.world is not World.REPLAY
        or store_receipt.room_role is not RoomRole.JOURNAL
        or store_receipt.engine != "jsonl"
        or store_receipt.outcome not in (WriteOutcome.STORED, WriteOutcome.IDEMPOTENT)
        or store_receipt.is_evidence_bearing is not True
        or store_receipt.retained_forever is not True
        or sequence_value is None
        or isinstance(sequence_value, bool)
        or not isinstance(sequence_value, int)
        or sequence_value < 0
        or isinstance(format_value, bool)
        or not isinstance(format_value, int)
        or format_value != 1
    ):
        return policy(
            "store_receipt",
            "the physical store receipt proves complete retained replay-journal evidence",
        )
    raw = store.read_stream(expected_writer.stream_name, for_world=World.REPLAY)
    if is_refusal(raw):
        return raw
    physical_sequence = sequence_value
    if physical_sequence >= len(raw.value):
        return policy("store_receipt", "the physical sequence exists in the checked journal")
    row = raw.value[physical_sequence]
    row_fp = fingerprint(row)
    persisted_event = JournalEvent.from_row(row)
    if (
        is_refusal(row_fp)
        or row_fp.value != store_receipt.fingerprint
        or is_refusal(persisted_event)
        or persisted_event.value.fingerprint != event.fingerprint
    ):
        return policy(
            "store_receipt",
            "the physical receipt fingerprint identifies the acknowledged stored event row",
        )
    reopened = JournalReader(store).read_checked(
        expected_writer.stream_name, for_world=World.REPLAY
    )
    if is_refusal(reopened):
        return reopened
    if not any(
        stored.writer == event.writer
        and stored.sequence == event.sequence
        and stored.fingerprint == event.fingerprint
        for stored in reopened.value
    ):
        return policy("journal_readback", "the checked journal reopens the acknowledged event")
    return Ok((event, store_receipt))


def execute_alternative_run(
    config_payload: object,
    recorded_source: object,
    registry: object,
    *,
    initial_accounting_state: object,
    expected_command_owner_epoch: object,
    journal_writer: object,
    journal_store: object,
    trial_label: object = None,
) -> Result[AlternativeRunReceipt]:
    """Evaluate a selected ATC on recorded CT-10 data and durably journal each transition.

    ``JournalReader.read_checked`` reopens the stream after all writes; no run receipt is
    returned until every decision event and physical store receipt is read back intact.
    The function is provider-free and cannot issue venue commands.
    """
    validated = validate_alternative_run_config(config_payload)
    if is_refusal(validated):
        return validated
    config = validated.value
    normalized_trial_label: Mapping[str, object] | None = None
    if trial_label is not None:
        checked_label = validate_trial_label(trial_label)
        if is_refusal(checked_label):
            return checked_label
        normalized_trial_label = checked_label.value
    if (
        config.command.adapter_capability != ADAPTER_INTERNAL_SIMULATE
        or config.command.venue_kind is not None
    ):
        return policy("adapter_capability", "QMB ATC runtime uses internal-simulate without venue")
    if config.admission.verdict != VERDICT_ADMITTED_SIMULATE:
        return policy("admission", "ATC execution requires authoritative admitted_simulate")
    if (
        isinstance(expected_command_owner_epoch, bool)
        or not isinstance(expected_command_owner_epoch, int)
        or expected_command_owner_epoch != config.command.command_owner_epoch
    ):
        return policy(
            "command_owner_epoch",
            "the selected command owner epoch matches the current host epoch",
            expected=expected_command_owner_epoch,
            configured=config.command.command_owner_epoch,
        )
    if not isinstance(recorded_source, RecordedReplaySource):
        source_data = _validate_source(recorded_source)
        if isinstance(source_data, TypedRefusal):
            return source_data
        return invalid("recorded_source", "a validated RecordedReplaySource is required")
    source = recorded_source
    source_data = _validate_source(source)
    if isinstance(source_data, TypedRefusal):
        return source_data
    split_fingerprint = source.split_fp1
    split_role = source.split_role
    if split_fingerprint is None or split_role is None:
        return policy("split", "an ATC run pins its CT-12 split manifest and segment role")
    if not isinstance(registry, AlternativeInterpreterRegistry):
        return invalid("registry", "ATC execution receives a typed interpreter registry")
    checked_registry = AlternativeInterpreterRegistry.try_create(
        tuple(registry.registrations.values())
    )
    if is_refusal(checked_registry):
        return checked_registry
    if checked_registry.value.fingerprint != registry.fingerprint:
        return policy("registry", "interpreter registry fingerprint matches its entries")
    registry = checked_registry.value
    registration_result = registry.resolve(config)
    if is_refusal(registration_result):
        return registration_result
    registration = registration_result.value
    if not isinstance(journal_writer, JournalWriter) or not isinstance(journal_store, JournalStore):
        return invalid("journal", "ATC execution requires the QMF CT-13 writer and store")
    if journal_writer.world is not World.REPLAY or journal_store.world is not World.REPLAY:
        return policy("journal", "ATC decision evidence is written to the replay CT-13 room")
    if journal_writer.writer.stream != journal_writer.stream_name:
        return policy("journal_writer", "the CT-13 WriterId owns its named stream")
    state = _freeze_mapping(initial_accounting_state, "initial_accounting_state")
    if isinstance(state, TypedRefusal):
        return state
    initial_fp = fingerprint({"class": "qmb-atc-accounting-state-v1", "state": _plain(state)})
    if is_refusal(initial_fp):
        return initial_fp

    simulated = simulate_alternative_run(config, writer=journal_writer.writer)
    if is_refusal(simulated):
        return simulated
    simulate = simulated.value
    working_state: Mapping[str, object] = state
    working_fp = initial_fp.value
    working_measures: tuple[AlternativeMeasure, ...] = ()
    references: list[ATCJournalReference] = []
    expected_events: dict[int, Fingerprint] = {}
    frontiers = source_data
    for frontier_ns in sorted(frontiers):
        instant = Instant(value_ns=frontier_ns)
        observations = tuple(frontiers[frontier_ns])
        input_fp = fingerprint(
            {
                "class": "qmb-atc-frontier-input-v1",
                "frontier_ns": frontier_ns,
                "observations": [item.fingerprint.value for item in observations],
                "source_fp1": source.fingerprint.value,
            }
        )
        if is_refusal(input_fp):
            return input_fp
        request = AlternativeEvaluationRequest(
            config=config,
            frontier=instant,
            observations=observations,
            input_fingerprint=input_fp.value,
            prior_accounting_state=working_state,
            prior_accounting_state_fingerprint=working_fp,
        )
        try:
            evaluated = registration.interpreter.evaluate(request)
        except Exception as exc:
            return unavailable(
                "policy_interpreter",
                "registered interpreter failed; no result was accepted",
                exception=type(exc).__name__,
            )
        evaluated_value: object = cast(object, evaluated)
        if isinstance(evaluated_value, TypedRefusal):
            return evaluated_value
        if not isinstance(evaluated_value, Ok):
            return invalid("evaluation", "a policy interpreter returns a QMF Result")
        evaluation_value: object = cast("Ok[object]", evaluated_value).value
        if not isinstance(evaluation_value, AlternativePolicyEvaluation):
            return invalid("evaluation", "a policy interpreter returns AlternativePolicyEvaluation")
        evaluated = evaluation_value
        checked = AlternativePolicyEvaluation.try_create(
            accounting_state=evaluated.accounting_state,
            risk_verdict=evaluated.risk_verdict,
            risk_accepted=evaluated.risk_accepted,
            actions=evaluated.actions,
            measures=evaluated.measures,
        )
        if is_refusal(checked):
            return checked
        declarations = {item.measure_identity: item for item in registration.declared_measures}
        for measure in checked.value.measures:
            declared = declarations.get(measure.measure_identity)
            if (
                declared is None
                or declared.unit_kind != measure.unit_kind
                or declared.currency != measure.currency
            ):
                return policy(
                    "measure_contract",
                    "interpreter output matches its registered measure identity and CT-01 units",
                    measure_identity=measure.measure_identity,
                )
        state_after_fp = fingerprint(
            {
                "class": "qmb-atc-accounting-state-v1",
                "state": _plain(checked.value.accounting_state),
            }
        )
        if is_refusal(state_after_fp):
            return state_after_fp
        output_fp = fingerprint(
            {
                "class": "qmb-atc-frontier-output-v1",
                "input_fp1": input_fp.value.value,
                "interpreter_registration_fp1": registration.fingerprint.value,
                "policy_pair_identity": config.policy_pair.identity(),
                "prior_accounting_state_fp1": working_fp.value,
                "result": checked.value.identity(),
            }
        )
        if is_refusal(output_fp):
            return output_fp
        payload: dict[str, object] = {
            "accounting_state_after": _plain(checked.value.accounting_state),
            "accounting_state_after_fp1": state_after_fp.value.value,
            "accounting_state_before_fp1": working_fp.value,
            "actions": [action.identity() for action in checked.value.actions],
            "measures": [measure.fp1_identity() for measure in checked.value.measures],
            "composition_class": "alternative",
            "composition_fp1": config.composition_fp.value,
            "frontier_input_fp1": input_fp.value.value,
            "interpreter_registration_fp1": registration.fingerprint.value,
            "output_fp1": output_fp.value.value,
            "policy_pair_identity": config.policy_pair.identity(),
            "recorded_source_fp1": source.fingerprint.value,
            "simulate_token_fp1": simulate.simulate_token.value,
            "split_fp1": split_fingerprint.value,
            "split_role": split_role.value,
            "command_owner_epoch": config.command.command_owner_epoch,
            "risk_accepted": checked.value.risk_accepted,
            "risk_verdict": checked.value.risk_verdict,
        }
        if normalized_trial_label is not None:
            payload["trial_label"] = _plain(normalized_trial_label)
        if not checked.value.risk_accepted:
            payload["refusing_door"] = f"atc-policy:{config.policy_pair.policy_pair_id}"
        expected_sequence = journal_writer.next_sequence
        expected_outcome = (
            DecisionOutcome.AUTHORIZED
            if checked.value.risk_accepted
            else DecisionOutcome.REFUSED_BY_DOOR
        )
        appended = journal_writer.record(
            JournalEventType.DECISION,
            payload,
            instant=instant,
            outcome=expected_outcome,
            correlation_id=config.composition_fp.value,
        )
        appended_value: object = cast(object, appended)
        if isinstance(appended_value, TypedRefusal):
            return appended_value
        if not isinstance(appended_value, Ok):
            return invalid("journal_receipt", "record returns a QMF Result")
        validated_append = _validate_append_receipt(
            cast("Ok[object]", appended_value).value,
            expected_writer=journal_writer,
            expected_sequence=expected_sequence,
            expected_instant=instant,
            expected_payload=payload,
            expected_outcome=expected_outcome,
            expected_correlation_id=config.composition_fp.value,
            store=journal_store,
        )
        if is_refusal(validated_append):
            return validated_append
        event, store_receipt = validated_append.value
        if type(store_receipt.sequence) is not int or store_receipt.sequence < 0:
            return policy("journal_receipt", "physical CT-13 sequence is an exact non-negative int")
        references.append(
            ATCJournalReference(
                frontier=instant,
                event_fingerprint=event.fingerprint,
                store_fingerprint=store_receipt.fingerprint,
                store_sequence=store_receipt.sequence,
                sequence=event.sequence,
                output_fingerprint=output_fp.value,
            )
        )
        expected_events[event.sequence] = event.fingerprint
        working_state = checked.value.accounting_state
        working_fp = state_after_fp.value
        working_measures = checked.value.measures

    reopened = JournalReader(journal_store).read_checked(
        journal_writer.stream_name, for_world=World.REPLAY
    )
    if is_refusal(reopened):
        return reopened
    readback = {
        event.sequence: event
        for event in reopened.value
        if event.writer == journal_writer.writer and event.sequence in expected_events
    }
    if set(readback) != set(expected_events) or any(
        readback[sequence].fingerprint != expected for sequence, expected in expected_events.items()
    ):
        return policy("journal_readback", "every accepted ATC decision reopens byte-identically")
    identity: dict[str, object] = {
        "class": "qmb-alternative-run-result-v1",
        "composition_fp1": config.composition_fp.value,
        "final_accounting_state_fp1": working_fp.value,
        "initial_accounting_state_fp1": initial_fp.value.value,
        "interpreter_registration_fp1": registration.fingerprint.value,
        "journal_refs": [reference.identity() for reference in references],
        "journal_stream": journal_writer.stream_name,
        "journal_writer": {
            "boot_epoch_id": journal_writer.writer.boot_epoch_id,
            "machine": journal_writer.writer.machine,
            "role": journal_writer.writer.role,
            "stream": journal_writer.writer.stream,
        },
        "final_measures": [measure.fp1_identity() for measure in working_measures],
        "policy_pair_identity": config.policy_pair.identity(),
        "registry_fp1": registry.fingerprint.value,
        "source_fp1": source.fingerprint.value,
        "split_fp1": split_fingerprint.value,
        "split_role": split_role.value,
    }
    if normalized_trial_label is not None:
        identity["trial_label"] = _plain(normalized_trial_label)
    result_fp = fingerprint(identity)
    if is_refusal(result_fp):
        return result_fp
    return Ok(
        AlternativeRunReceipt(
            config=config,
            simulate=simulate,
            source_fingerprint=source.fingerprint,
            split_fingerprint=split_fingerprint,
            split_role=split_role,
            registry_fingerprint=registry.fingerprint,
            interpreter_registration=registration,
            journal_writer=journal_writer.writer,
            journal_stream=journal_writer.stream_name,
            initial_accounting_state_fingerprint=initial_fp.value,
            final_accounting_state=working_state,
            final_accounting_state_fingerprint=working_fp,
            final_measures=working_measures,
            journal_references=tuple(references),
            trial_label=normalized_trial_label,
            fingerprint=result_fp.value,
        )
    )


def recover_alternative_run_receipt(
    config_payload: object,
    recorded_source: object,
    registry: object,
    *,
    initial_accounting_state: object,
    expected_command_owner_epoch: object,
    journal_writer: object,
    journal_store: object,
    trial_label: object,
) -> Result[AlternativeRunReceipt]:
    """Reconstruct a completed ATC receipt from its exact durable CT-13 chain.

    This path never calls the registered interpreter. It succeeds only when every
    source frontier has exactly one checked decision event for the pinned writer,
    config, source, registration and trial label, and each event's physical raw row
    is independently identified. Partial or ambiguous chains remain unresolved.
    """
    validated = validate_alternative_run_config(config_payload)
    if is_refusal(validated):
        return validated
    config = validated.value
    if (
        isinstance(expected_command_owner_epoch, bool)
        or not isinstance(expected_command_owner_epoch, int)
        or expected_command_owner_epoch != config.command.command_owner_epoch
    ):
        return policy("command_owner_epoch", "recovered trial matches the pinned owner epoch")
    checked_label = validate_trial_label(trial_label)
    if is_refusal(checked_label):
        return checked_label
    if not isinstance(recorded_source, RecordedReplaySource):
        return invalid("recorded_source", "trial recovery uses a validated replay source")
    source_data = _validate_source(recorded_source)
    if isinstance(source_data, TypedRefusal):
        return source_data
    source = recorded_source
    if source.split_fp1 is None or source.split_role is None:
        return policy("split", "recovered ATC trial pins its source split")
    if not isinstance(registry, AlternativeInterpreterRegistry):
        return invalid("registry", "trial recovery resolves the registered interpreter")
    registration_result = registry.resolve(config)
    if is_refusal(registration_result):
        return registration_result
    registration = registration_result.value
    if not isinstance(journal_writer, JournalWriter) or not isinstance(journal_store, JournalStore):
        return invalid("journal", "trial recovery uses the operator-pinned CT-13 writer/store")
    if (
        journal_writer.world is not World.REPLAY
        or journal_store.world is not World.REPLAY
        or journal_writer.writer.stream != journal_writer.stream_name
    ):
        return policy("journal", "trial recovery is pinned to the replay CT-13 stream")
    state = _freeze_mapping(initial_accounting_state, "initial_accounting_state")
    if isinstance(state, TypedRefusal):
        return state
    initial_fp = fingerprint({"class": "qmb-atc-accounting-state-v1", "state": _plain(state)})
    if is_refusal(initial_fp):
        return initial_fp
    split_fingerprint = source.split_fp1
    split_role = source.split_role
    simulate_result = simulate_alternative_run(config, writer=journal_writer.writer)
    if is_refusal(simulate_result):
        return simulate_result
    checked_events = JournalReader(journal_store).read_checked(
        journal_writer.stream_name, for_world=World.REPLAY
    )
    if is_refusal(checked_events):
        return checked_events
    raw_rows = journal_store.read_stream(journal_writer.stream_name, for_world=World.REPLAY)
    if is_refusal(raw_rows):
        return raw_rows

    label = _plain(checked_label.value)
    label_fp = fingerprint(checked_label.value)
    if is_refusal(label_fp):
        return label_fp
    references: list[ATCJournalReference] = []
    expected_events: list[JournalEvent] = []
    working_state: Mapping[str, object] = state
    working_fp = initial_fp.value
    working_measures: tuple[AlternativeMeasure, ...] = ()
    expected_input_fps: set[str] = set()
    for frontier_ns in sorted(source_data):
        instant = Instant(value_ns=frontier_ns)
        observations = tuple(source_data[frontier_ns])
        input_fp = fingerprint(
            {
                "class": "qmb-atc-frontier-input-v1",
                "frontier_ns": frontier_ns,
                "observations": [item.fingerprint.value for item in observations],
                "source_fp1": source.fingerprint.value,
            }
        )
        if is_refusal(input_fp):
            return input_fp
        expected_input_fps.add(input_fp.value.value)
        matches = [
            event
            for event in checked_events.value
            if event.writer == journal_writer.writer
            and event.event_type is JournalEventType.DECISION
            and event.payload.get("frontier_input_fp1") == input_fp.value.value
            and (event_label_fp := fingerprint(event.payload.get("trial_label")))
            and not is_refusal(event_label_fp)
            and event_label_fp.value == label_fp.value
        ]
        if len(matches) != 1:
            return policy(
                "trial_recovery",
                "each expected ATC frontier has exactly one durable labeled decision",
                frontier_ns=frontier_ns,
            )
        event = matches[0]
        payload = event.payload
        if (
            event.instant != instant
            or event.correlation_id != config.composition_fp.value
            or payload.get("composition_class") != "alternative"
            or payload.get("composition_fp1") != config.composition_fp.value
            or payload.get("policy_pair_identity") != config.policy_pair.identity()
            or payload.get("interpreter_registration_fp1") != registration.fingerprint.value
            or payload.get("recorded_source_fp1") != source.fingerprint.value
            or payload.get("split_fp1") != split_fingerprint.value
            or payload.get("split_role") != split_role.value
            or payload.get("command_owner_epoch") != config.command.command_owner_epoch
            or payload.get("accounting_state_before_fp1") != working_fp.value
        ):
            return policy("trial_recovery", "CT-13 frontier is bound to the exact pinned trial")
        evaluation = _rebuild_evaluation(payload)
        if is_refusal(evaluation):
            return evaluation
        state_after_fp = fingerprint(
            {
                "class": "qmb-atc-accounting-state-v1",
                "state": _plain(evaluation.value.accounting_state),
            }
        )
        if (
            is_refusal(state_after_fp)
            or state_after_fp.value.value != payload.get("accounting_state_after_fp1")
        ):
            return policy("trial_recovery", "durable accounting state reproduces its fp1")
        output_fp = fingerprint(
            {
                "class": "qmb-atc-frontier-output-v1",
                "input_fp1": input_fp.value.value,
                "interpreter_registration_fp1": registration.fingerprint.value,
                "policy_pair_identity": config.policy_pair.identity(),
                "prior_accounting_state_fp1": working_fp.value,
                "result": evaluation.value.identity(),
            }
        )
        if is_refusal(output_fp) or output_fp.value.value != payload.get("output_fp1"):
            return policy("trial_recovery", "durable decision output reproduces its fp1")
        expected_outcome = (
            DecisionOutcome.AUTHORIZED
            if evaluation.value.risk_accepted
            else DecisionOutcome.REFUSED_BY_DOOR
        )
        if event.outcome is not expected_outcome:
            return policy("trial_recovery", "CT-13 outcome agrees with its risk verdict")
        physical_matches = [
            (index, raw)
            for index, raw in enumerate(raw_rows.value)
            if raw.get("fingerprint") == event.fingerprint.value
        ]
        if len(physical_matches) != 1:
            return policy("trial_recovery", "durable CT-13 event has one physical store row")
        physical, raw = physical_matches[0]
        raw_fp = fingerprint(raw)
        if is_refusal(raw_fp) or raw.get("fingerprint") != event.fingerprint.value:
            return policy("trial_recovery", "physical CT-13 row is independently fingerprinted")
        references.append(
            ATCJournalReference(
                frontier=event.instant,
                event_fingerprint=event.fingerprint,
                store_fingerprint=raw_fp.value,
                store_sequence=physical,
                sequence=event.sequence,
                output_fingerprint=output_fp.value,
            )
        )
        expected_events.append(event)
        working_state = evaluation.value.accounting_state
        working_fp = state_after_fp.value
        working_measures = evaluation.value.measures

    labeled_events = [
        event
        for event in checked_events.value
        if event.event_type is JournalEventType.DECISION
        and (event_label_fp := fingerprint(event.payload.get("trial_label")))
        and not is_refusal(event_label_fp)
        and event_label_fp.value == label_fp.value
    ]
    if (
        len(labeled_events) != len(expected_events)
        or any(
            event.writer != journal_writer.writer
            or event.payload.get("composition_fp1") != config.composition_fp.value
            or event.payload.get("policy_pair_identity") != config.policy_pair.identity()
            or event.payload.get("interpreter_registration_fp1") != registration.fingerprint.value
            or event.payload.get("recorded_source_fp1") != source.fingerprint.value
            or event.payload.get("split_fp1") != split_fingerprint.value
            or event.payload.get("split_role") != split_role.value
            or event.payload.get("command_owner_epoch") != config.command.command_owner_epoch
            for event in labeled_events
        )
        or {
            cast(str, event.payload.get("frontier_input_fp1")) for event in labeled_events
        }
        != expected_input_fps
    ):
        return policy("trial_recovery", "trial chain has no missing or extra labeled decisions")
    if len({event.sequence for event in expected_events}) != len(expected_events):
        return policy("trial_recovery", "recovered decision chain has unique logical sequences")
    recovered_sequences = [event.sequence for event in expected_events]
    if recovered_sequences != sorted(recovered_sequences):
        return policy("trial_recovery", "recovered decisions follow CT-13 logical order")
    identity: dict[str, object] = {
        "class": "qmb-alternative-run-result-v1",
        "composition_fp1": config.composition_fp.value,
        "final_accounting_state_fp1": working_fp.value,
        "initial_accounting_state_fp1": initial_fp.value.value,
        "interpreter_registration_fp1": registration.fingerprint.value,
        "journal_refs": [reference.identity() for reference in references],
        "journal_stream": journal_writer.stream_name,
        "journal_writer": {
            "boot_epoch_id": journal_writer.writer.boot_epoch_id,
            "machine": journal_writer.writer.machine,
            "role": journal_writer.writer.role,
            "stream": journal_writer.writer.stream,
        },
        "final_measures": [measure.fp1_identity() for measure in working_measures],
        "policy_pair_identity": config.policy_pair.identity(),
        "registry_fp1": registry.fingerprint.value,
        "source_fp1": source.fingerprint.value,
        "split_fp1": split_fingerprint.value,
        "split_role": split_role.value,
        "trial_label": label,
    }
    result_fp = fingerprint(identity)
    if is_refusal(result_fp):
        return result_fp
    return Ok(
        AlternativeRunReceipt(
            config=config,
            simulate=simulate_result.value,
            source_fingerprint=source.fingerprint,
            split_fingerprint=split_fingerprint,
            split_role=split_role,
            registry_fingerprint=registry.fingerprint,
            interpreter_registration=registration,
            journal_writer=journal_writer.writer,
            journal_stream=journal_writer.stream_name,
            initial_accounting_state_fingerprint=initial_fp.value,
            final_accounting_state=working_state,
            final_accounting_state_fingerprint=working_fp,
            final_measures=working_measures,
            journal_references=tuple(references),
            trial_label=cast("Mapping[str, object]", label),
            fingerprint=result_fp.value,
        )
    )


def _rebuild_evaluation(payload: Mapping[str, object]) -> Result[AlternativePolicyEvaluation]:
    state = payload.get("accounting_state_after")
    actions_value = payload.get("actions")
    measures_value = payload.get("measures")
    if not isinstance(actions_value, (tuple, list)) or not isinstance(
        measures_value, (tuple, list)
    ):
        return invalid("trial_recovery", "CT-13 carries typed actions and measures")
    actions: list[InternalSimulatedAction] = []
    for item in cast("Sequence[object]", actions_value):
        if not isinstance(item, Mapping):
            return invalid("trial_recovery", "persisted action is an identity mapping")
        action = cast("Mapping[str, object]", item)
        rebuilt = InternalSimulatedAction.try_create(
            action_id=action.get("action_id"),
            action_type=action.get("action_type"),
            body=action.get("body"),
        )
        if is_refusal(rebuilt):
            return rebuilt
        actions.append(rebuilt.value)
    measures: list[AlternativeMeasure] = []
    for item in cast("Sequence[object]", measures_value):
        if not isinstance(item, Mapping):
            return invalid("trial_recovery", "persisted measure is an identity mapping")
        measure = cast("Mapping[str, object]", item)
        quantity = measure.get("quantity")
        if not isinstance(quantity, Mapping):
            return invalid("trial_recovery", "persisted measure contains an exact quantity")
        body = cast("Mapping[str, object]", quantity)
        if body.get("class") == "money":
            numerator = body.get("num")
            denominator = body.get("den")
            currency = body.get("currency")
            if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
                return invalid("trial_recovery", "persisted money amount is exact")
            scaled = Fraction(numerator, denominator) * 10**MONEY_STORAGE_SCALE
            if scaled.denominator != 1:
                return invalid(
                    "trial_recovery", "persisted money is representable at storage scale"
                )
            exact: object = Money.try_create(scaled.numerator, currency, MONEY_STORAGE_SCALE)
        elif body.get("class") == "exact-rational":
            exact = ExactRational.try_create(
                body.get("num"), body.get("den"), body.get("unit_kind")
            )
        else:
            return invalid("trial_recovery", "persisted measure uses a known exact quantity")
        if is_refusal(cast(Result[object], exact)):
            return cast(Result[AlternativePolicyEvaluation], exact)
        quantity_value = cast("Ok[object]", exact).value
        if not isinstance(quantity_value, (Money, ExactRational)):
            return invalid("trial_recovery", "persisted quantity reconstructs as exact QMF value")
        rebuilt_measure = AlternativeMeasure.try_create(
            measure.get("measure_identity"), quantity_value
        )
        if is_refusal(rebuilt_measure):
            return rebuilt_measure
        if rebuilt_measure.value.fp1_identity() != dict(measure):
            return policy("trial_recovery", "persisted measure identity is canonical")
        measures.append(rebuilt_measure.value)
    return AlternativePolicyEvaluation.try_create(
        accounting_state=state,
        risk_verdict=payload.get("risk_verdict"),
        risk_accepted=payload.get("risk_accepted"),
        actions=actions,
        measures=measures,
    )
