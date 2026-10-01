"""Registered ATC policy execution over persisted CT-10 replay evidence.

This module owns the generic QMB execution seam for AlternativeRunConfig. Policy
interpretation is supplied by a trusted, exact-identity registration; QMB does not
infer financial meaning from opaque PolicyPair tokens. Each evaluator transition
is persisted as a CT-13 decision before its state becomes part of the accepted run.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol, cast, runtime_checkable

from qmf.core import Fingerprint, Instant, Ok, Result, TypedRefusal, World, fingerprint, is_refusal
from qmf.data.journal import DecisionOutcome, JournalEventType
from qmf.data.journal_producer import JournalAppendReceipt, JournalReader, JournalWriter
from qmf.data.observation import SourceObservation
from qmf.data.splits import SegmentRole
from qmf.data.store import JournalStore

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
from qmb.runloop.loop import EventSlice, SliceObservation

__all__ = [
    "ATCJournalReference",
    "AlternativeEvaluationRequest",
    "AlternativeInterpreterRegistry",
    "AlternativePolicyEvaluation",
    "AlternativePolicyInterpreter",
    "AlternativeRunReceipt",
    "InternalSimulatedAction",
    "PolicyInterpreterRegistration",
    "execute_alternative_run",
]


def _exact_value(value: object, field: str) -> object | TypedRefusal:
    """Normalize supported exact values to canonical JSON data, refusing floats."""
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Fingerprint):
        return value.value
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                return invalid(field, "exact state and action mappings use named string keys")
            normalized = _exact_value(item, field)
            if is_refusal(normalized):
                return normalized
            result[key] = normalized
        return result
    if isinstance(value, (tuple, list)):
        result_list: list[object] = []
        for item in value:
            normalized = _exact_value(item, field)
            if is_refusal(normalized):
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


def _freeze_mapping(value: object, field: str) -> Mapping[str, object] | object:
    if not isinstance(value, Mapping):
        return invalid(field, "an ATC state/action body is a mapping")
    normalized = _exact_value(value, field)
    if is_refusal(normalized):
        return normalized
    if not isinstance(normalized, dict):
        return normalized

    def freeze(item: object) -> object:
        if isinstance(item, dict):
            return MappingProxyType({key: freeze(child) for key, child in item.items()})
        if isinstance(item, list):
            return tuple(freeze(child) for child in item)
        return item

    return cast("Mapping[str, object]", freeze(normalized))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


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
        if not isinstance(frozen, Mapping):
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

    @classmethod
    def try_create(
        cls,
        *,
        accounting_state: object,
        risk_verdict: object,
        risk_accepted: object,
        actions: object,
    ) -> Result[AlternativePolicyEvaluation]:
        state = _freeze_mapping(accounting_state, "accounting_state")
        if not isinstance(state, Mapping):
            return state
        if not isinstance(risk_verdict, str) or not risk_verdict.strip():
            return invalid("risk_verdict", "an evaluator returns its explicit risk verdict")
        if not isinstance(risk_accepted, bool):
            return invalid("risk_accepted", "risk acceptance is an explicit bool")
        if isinstance(actions, (str, bytes)) or not isinstance(actions, Sequence):
            return invalid("actions", "internal simulated actions are an ordered sequence")
        action_list = tuple(actions)
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
        return Ok(cls(state, risk_verdict, risk_accepted, action_list))

    def identity(self) -> dict[str, object]:
        return {
            "accounting_state": _plain(self.accounting_state),
            "actions": [action.identity() for action in self.actions],
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
        if is_refusal(pair_hash):
            return pair_hash
        impl_fp = _fingerprint(interpreter_fp1, "interpreter_fp1")
        if is_refusal(impl_fp):
            return impl_fp
        if not isinstance(interpreter_id, str) or not interpreter_id.strip():
            return invalid("interpreter_id", "a trusted interpreter has a stable id")
        if not callable(getattr(interpreter, "evaluate", None)):
            return invalid("interpreter", "a registered policy interpreter implements evaluate")
        identity = {
            "class": "qmb-atc-policy-interpreter-registration-v1",
            "interpreter_fp1": impl_fp.value,
            "interpreter_id": interpreter_id,
            "interpreter_version": interpreter_version,
            "policy_pair_hash": pair_hash.value,
            "policy_pair_id": policy_pair_id,
            "policy_pair_version": policy_pair_version,
        }
        stamped = fingerprint(identity)
        if is_refusal(stamped):
            return stamped
        return Ok(
            cls(
                policy_pair_id,
                policy_pair_version,
                pair_hash,
                interpreter_id,
                interpreter_version,
                impl_fp,
                cast("AlternativePolicyInterpreter", interpreter),
                stamped.value,
            )
        )

    def identity(self) -> dict[str, object]:
        return {
            "class": "qmb-atc-policy-interpreter-registration-v1",
            "interpreter_fp1": self.interpreter_fp1.value,
            "interpreter_id": self.interpreter_id,
            "interpreter_version": self.interpreter_version,
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
    sequence: int
    output_fingerprint: Fingerprint

    def identity(self) -> dict[str, object]:
        return {
            "event_fp1": self.event_fingerprint.value,
            "frontier_ns": self.frontier.value_ns,
            "output_fp1": self.output_fingerprint.value,
            "sequence": self.sequence,
            "store_receipt_fp1": self.store_fingerprint.value,
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
    initial_accounting_state_fingerprint: Fingerprint
    final_accounting_state: Mapping[str, object]
    final_accounting_state_fingerprint: Fingerprint
    journal_references: tuple[ATCJournalReference, ...]
    fingerprint: Fingerprint

    def fp1_identity(self) -> dict[str, object]:
        return {
            "class": "qmb-alternative-run-result-v1",
            "composition_fp1": self.config.composition_fp.value,
            "final_accounting_state_fp1": self.final_accounting_state_fingerprint.value,
            "initial_accounting_state_fp1": self.initial_accounting_state_fingerprint.value,
            "interpreter_registration_fp1": self.interpreter_registration.fingerprint.value,
            "journal_refs": [reference.identity() for reference in self.journal_references],
            "policy_pair_identity": self.config.policy_pair.identity(),
            "registry_fp1": self.registry_fingerprint.value,
            "source_fp1": self.source_fingerprint.value,
            "split_fp1": self.split_fingerprint.value,
            "split_role": self.split_role.value,
        }


def _validate_source(source: object) -> object:
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
    for index, observation in enumerate(source.observations):
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
    for observation in source.observations:
        frontier = max(observation.event_time.value_ns, observation.known_at.value_ns)
        expected.setdefault(frontier, []).append(observation)
    frontiers = sorted(expected)
    if len(frontiers) != len(source.slices):
        return policy("slices", "every recorded CT-10 frontier has exactly one replay slice")
    for index, (frontier_ns, event_slice) in enumerate(zip(frontiers, source.slices, strict=True)):
        if not isinstance(event_slice, EventSlice) or len(event_slice.observations) != 1:
            return invalid(
                "slices", "each recorded frontier has one stream observation", index=index
            )
        slice_observation = event_slice.observations[0]
        if (
            not isinstance(slice_observation, SliceObservation)
            or slice_observation.stream_id != source.stream_id
            or not slice_observation.closed
            or slice_observation.instant.value_ns != frontier_ns
        ):
            return policy(
                "slices", "replay frontier matches CT-10 known-at observations", index=index
            )
    return expected


def execute_alternative_run(
    config_payload: object,
    recorded_source: object,
    registry: object,
    *,
    initial_accounting_state: object,
    expected_command_owner_epoch: object,
    journal_writer: object,
    journal_store: object,
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
    source_data = _validate_source(recorded_source)
    if is_refusal(source_data):
        return source_data
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
    if is_refusal(registration):
        return registration
    if not isinstance(journal_writer, JournalWriter) or not isinstance(journal_store, JournalStore):
        return invalid("journal", "ATC execution requires the QMF CT-13 writer and store")
    if journal_writer.world is not World.REPLAY or journal_store.world is not World.REPLAY:
        return policy("journal", "ATC decision evidence is written to the replay CT-13 room")
    if journal_writer.writer.stream != journal_writer.stream_name:
        return policy("journal_writer", "the CT-13 WriterId owns its named stream")
    state = _freeze_mapping(initial_accounting_state, "initial_accounting_state")
    if not isinstance(state, Mapping):
        return state
    initial_fp = fingerprint({"class": "qmb-atc-accounting-state-v1", "state": _plain(state)})
    if is_refusal(initial_fp):
        return initial_fp

    simulated = simulate_alternative_run(config, writer=journal_writer.writer)
    if is_refusal(simulated):
        return simulated
    simulate = simulated.value
    working_state = state
    working_fp = initial_fp.value
    references: list[ATCJournalReference] = []
    expected_events: dict[int, Fingerprint] = {}
    frontiers = cast("dict[int, list[SourceObservation]]", source_data)
    for frontier_ns in sorted(frontiers):
        instant = Instant(value_ns=frontier_ns)
        observations = tuple(frontiers[frontier_ns])
        input_fp = fingerprint(
            {
                "class": "qmb-atc-frontier-input-v1",
                "frontier_ns": frontier_ns,
                "observations": [item.fingerprint.value for item in observations],
                "source_fp1": cast("RecordedReplaySource", recorded_source).fingerprint.value,
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
        if is_refusal(evaluated):
            return evaluated
        if not isinstance(evaluated, Ok):
            return invalid("evaluation", "a policy interpreter returns a QMF Result")
        evaluated = evaluated.value
        if not isinstance(evaluated, AlternativePolicyEvaluation):
            return invalid("evaluation", "a policy interpreter returns AlternativePolicyEvaluation")
        checked = AlternativePolicyEvaluation.try_create(
            accounting_state=evaluated.accounting_state,
            risk_verdict=evaluated.risk_verdict,
            risk_accepted=evaluated.risk_accepted,
            actions=evaluated.actions,
        )
        if is_refusal(checked):
            return checked
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
            "composition_class": "alternative",
            "composition_fp1": config.composition_fp.value,
            "frontier_input_fp1": input_fp.value.value,
            "interpreter_registration_fp1": registration.fingerprint.value,
            "output_fp1": output_fp.value.value,
            "policy_pair_identity": config.policy_pair.identity(),
            "recorded_source_fp1": cast("RecordedReplaySource", recorded_source).fingerprint.value,
            "simulate_token_fp1": simulate.simulate_token.value,
            "split_fp1": cast("RecordedReplaySource", recorded_source).split_fp1.value,
            "split_role": cast("RecordedReplaySource", recorded_source).split_role.value,
            "command_owner_epoch": config.command.command_owner_epoch,
            "risk_accepted": checked.value.risk_accepted,
            "risk_verdict": checked.value.risk_verdict,
        }
        if not checked.value.risk_accepted:
            payload["refusing_door"] = f"atc-policy:{config.policy_pair.policy_pair_id}"
        appended = journal_writer.record(
            JournalEventType.DECISION,
            payload,
            instant=instant,
            outcome=(
                DecisionOutcome.AUTHORIZED
                if checked.value.risk_accepted
                else DecisionOutcome.REFUSED_BY_DOOR
            ),
            correlation_id=config.composition_fp.value,
        )
        if is_refusal(appended):
            return appended
        receipt: JournalAppendReceipt = appended.value
        if receipt.event.writer != journal_writer.writer or receipt.event.world is not World.REPLAY:
            return policy("journal", "persisted ATC decision matches its writer and replay world")
        references.append(
            ATCJournalReference(
                frontier=instant,
                event_fingerprint=receipt.event.fingerprint,
                store_fingerprint=receipt.store_receipt.fingerprint,
                sequence=receipt.event.sequence,
                output_fingerprint=output_fp.value,
            )
        )
        expected_events[receipt.event.sequence] = receipt.event.fingerprint
        working_state = checked.value.accounting_state
        working_fp = state_after_fp.value

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
    identity = {
        "class": "qmb-alternative-run-result-v1",
        "composition_fp1": config.composition_fp.value,
        "final_accounting_state_fp1": working_fp.value,
        "initial_accounting_state_fp1": initial_fp.value.value,
        "interpreter_registration_fp1": registration.fingerprint.value,
        "journal_refs": [reference.identity() for reference in references],
        "policy_pair_identity": config.policy_pair.identity(),
        "registry_fp1": registry.fingerprint.value,
        "source_fp1": cast("RecordedReplaySource", recorded_source).fingerprint.value,
        "split_fp1": cast("RecordedReplaySource", recorded_source).split_fp1.value,
        "split_role": cast("RecordedReplaySource", recorded_source).split_role.value,
    }
    result_fp = fingerprint(identity)
    if is_refusal(result_fp):
        return result_fp
    return Ok(
        AlternativeRunReceipt(
            config=config,
            simulate=simulate,
            source_fingerprint=cast("RecordedReplaySource", recorded_source).fingerprint,
            split_fingerprint=cast("RecordedReplaySource", recorded_source).split_fp1,
            split_role=cast("RecordedReplaySource", recorded_source).split_role,
            registry_fingerprint=registry.fingerprint,
            interpreter_registration=registration,
            initial_accounting_state_fingerprint=initial_fp.value,
            final_accounting_state=working_state,
            final_accounting_state_fingerprint=working_fp,
            journal_references=tuple(references),
            fingerprint=result_fp.value,
        )
    )
