"""Opt-in CT47 authoring from actual provider execution under a dispatched Task.

Profiles select behavior, not Actors. Startup binds a profile to an existing
Task; its current dispatch lease and a canonical frozen Agent supply authority.
Provider output proposes identity fields only. Deployment and receipt provenance
come from the host execution, and running requests are never replayed on restart.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from threading import RLock
from typing import cast

from qma.core.ports.experiments import ExperimentSpec, parse_experiment_spec
from qma.core.vocabulary.enums import TaskMissionState
from qma.daemon.capabilities.spawn import AgentCapabilityStore
from qma.daemon.experiments.service import ExperimentSpecService
from qma.daemon.taskgraph.dispatcher import TaskGraphDispatcher
from qma.daemon.taskgraph.records import DispatchLease, TaskRecord
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

from .contracts import RequestRecord, RequestSpec
from .daemon_bridge import AgentRequestPolicy
from .service import RequestRuntime

_EVENT = "experiment.authoring_receipt"
_PERMISSION = "experiment.register"


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    body: dict[str, object] = {}
    for key, value in pairs:
        if key in body:
            raise ValueError("duplicate authoring field")
        body[key] = value
    return body


@dataclass(frozen=True, slots=True)
class _Admission:
    task: TaskRecord
    lease: DispatchLease
    task_attempt: int
    request_attempt: int
    authority_sha256: str


class ExperimentAuthoring:
    """Host callbacks; no renderer-supplied Agent, lease, receipt or deployment."""

    def __init__(
        self,
        *,
        runtime: RequestRuntime,
        policies: Mapping[str, AgentRequestPolicy],
        dispatcher: TaskGraphDispatcher,
        agents: AgentCapabilityStore,
        experiments: ExperimentSpecService,
        now: Callable[[], str],
    ) -> None:
        self.runtime = runtime
        self.policies = dict(policies)
        self.dispatcher = dispatcher
        self.agents = agents
        self.experiments = experiments
        self.now = now
        self._admissions: dict[str, _Admission] = {}

    @property
    def authority_lock(self) -> RLock:
        return self.dispatcher.authority_lock

    def _task(self, row: RequestRecord) -> Result[_Admission | None]:
        policy = self.policies.get(row.spec.profile.profile_id)
        if policy is None or policy.authoring_task_id != row.spec.authoring_task_id:
            return policy_rejection(
                "authoring_task", "accepted authoring Task binding is immutable"
            )
        if policy.authoring_task_id is None:
            return Ok(None)
        task = self.dispatcher.task_for(policy.authoring_task_id)
        lease = self.dispatcher.dispatch_lease_for(policy.authoring_task_id)
        ledger = self.dispatcher.ledgers.get(policy.authoring_task_id)
        if (
            task is None
            or task.state is not TaskMissionState.RUNNING
            or lease is None
            or lease.task_id != task.id
            or lease.mission_id != task.mission_id
            or lease.owner != task.owner
            or ledger is None
            or type(ledger.attempt_no) is not int
            or ledger.attempt_no < 0
            or self.dispatcher.ledgers.lease_for(policy.authoring_task_id) != lease
        ):
            return policy_rejection(
                "authoring_task", "authoring requires a current dispatched Task"
            )
        durable = self.dispatcher.store.durable
        if durable is None:
            return policy_rejection("authoring_task", "authoring requires durable Task authority")
        graph = durable.graph_for_task(task.id)
        if graph is None or graph.task_by_id(task.id) != task:
            return policy_rejection(
                "authoring_task", "durable Task projection agrees with dispatch authority"
            )
        agent = self.agents.get(lease.holder_agent_id)
        recorded_capabilities = self.agents.recorded_capabilities(lease.holder_agent_id)
        if (
            agent is None
            or not agent.capabilities_frozen
            or recorded_capabilities is None
            or recorded_capabilities.tool_ids != agent.effective_tool_ids
            or agent.owner != task.owner
            or _PERMISSION not in agent.effective_permissions
            or task.inputs.get("agent_session_ref") != agent.session_id
            or task.inputs.get("authoring_product_session_ref") != row.spec.product_session_id
            or task.inputs.get("authoring_profile_id") != row.spec.profile.profile_id
            or policy.authority_profile != "authoring"
        ):
            return policy_rejection(
                "authoring_agent",
                "current frozen Agent and Task authorize this bound authoring request",
            )
        try:
            identity = {
                "task": dict(task.to_payload()),
                "lease": dict(lease.to_payload()),
                "task_attempt": ledger.attempt_no,
                "agent_session_ref": agent.session_id,
                "permissions": sorted(agent.effective_permissions),
                "tools": sorted(agent.effective_tool_ids),
            }
            digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        except ValueError, TypeError, UnicodeError, RecursionError:
            return invalid_input(
                "authoring_task", "admitted Task authority is bounded canonical JSON"
            )
        if (
            row.spec.authoring_authority_sha256 is not None
            and row.spec.authoring_authority_sha256 != digest
        ):
            return policy_rejection("authoring_task", "accepted Task authority remains unchanged")
        return Ok(_Admission(task, lease, ledger.attempt_no, row.attempt, digest))

    def bind_acceptance(self, spec: RequestSpec) -> Result[str | None]:
        with self.runtime.completion_guard(), self.authority_lock:
            authority = self._task(RequestRecord("pending-host-admission", spec))
            if is_refusal(authority):
                return authority
            return Ok(None if authority.value is None else authority.value.authority_sha256)

    def admit(self, row: RequestRecord) -> Result[None]:
        with self.runtime.completion_guard(), self.authority_lock:
            return self._admit(row)

    def _admit(self, row: RequestRecord) -> Result[None]:
        admitted = self._task(row)
        if is_refusal(admitted):
            return admitted
        if admitted.value is not None:
            if row.spec.authoring_authority_sha256 != admitted.value.authority_sha256:
                return policy_rejection(
                    "authoring_task", "authoring acceptance carries its authority digest"
                )
            recorded = self.runtime.journal.append_event(
                "experiment.authoring_admitted",
                payload={
                    "request_id": row.request_id,
                    "request_attempt": row.attempt,
                    "dispatch_lease": dict(admitted.value.lease.to_payload()),
                    "task_attempt": admitted.value.task_attempt,
                    "product_session_ref": row.spec.product_session_id,
                    "authority_sha256": admitted.value.authority_sha256,
                },
            )
            if is_refusal(recorded):
                return recorded
            self._admissions[row.request_id] = admitted.value
        return Ok(None)

    def complete(self, row: RequestRecord) -> Result[None]:
        with (
            self.runtime.completion_guard(),
            self.authority_lock,
            self.runtime.product_sessions.authority_lock,
        ):
            return self._complete(row)

    def _complete(self, row: RequestRecord) -> Result[None]:
        policy = self.policies.get(row.spec.profile.profile_id)
        if policy is None or policy.authoring_task_id is None:
            return Ok(None)
        previous = self._admissions.pop(row.request_id, None)
        if row.status != "completed":
            return Ok(None)
        current = self._task(row)
        if is_refusal(current):
            return current
        if previous is None or current.value != previous:
            return policy_rejection("authoring_task", "Task, lease and attempt remain as admitted")
        active = self.runtime.validate_active_request(row.request_id, now=self.now())
        if is_refusal(active):
            return active
        result = row.result
        if result is None or not result.deployment_id or not result.deployment_id.strip():
            return invalid_input(
                "deployment_id", "actual authoring execution reports its deployment"
            )
        proposed = self._spec(result.content, result.deployment_id, previous.task)
        if is_refusal(proposed):
            return proposed
        existing = self.experiments.resolve(proposed.value.spec_fp1)
        if not is_refusal(existing) and (
            existing.value.dispatch_lease != previous.lease
            or existing.value.registering_attempt_no != previous.task_attempt
            or existing.value.registering_deployment_ref != result.deployment_id
        ):
            return policy_rejection(
                "spec_fp1", "identical identity cannot transfer registration authority"
            )
        observed = self.runtime.journal.append_event(
            "experiment.authoring_output_observed",
            payload={
                "request_id": row.request_id,
                "request_attempt": row.attempt,
                "dispatch_lease": dict(previous.lease.to_payload()),
                "task_attempt": previous.task_attempt,
                "observed_deployment_ref": result.deployment_id,
                "provider_output_sha256": hashlib.sha256(result.content.encode()).hexdigest(),
                "proposed_spec_fp1": proposed.value.spec_fp1,
                "authority_sha256": previous.authority_sha256,
                "provider_result": {
                    "content": result.content,
                    "deployment_id": result.deployment_id,
                },
            },
        )
        if is_refusal(observed):
            return observed
        registered = self.experiments.register(
            proposed.value,
            dispatch_lease=previous.lease,
            registering_attempt_no=previous.task_attempt,
            model_deployment_ref=result.deployment_id,
        )
        if is_refusal(registered):
            return policy_rejection(
                "authoring_registration",
                "registration outcome requires host reconciliation",
                effect_may_have_occurred=True,
            )
        registered = self.experiments.resolve_durable(proposed.value.spec_fp1)
        if is_refusal(registered):
            return policy_rejection(
                "registration",
                "durable registration readback requires host reconciliation",
                effect_may_have_occurred=True,
            )
        if (
            registered.value.spec.spec_fp1 != proposed.value.spec_fp1
            or registered.value.dispatch_lease != previous.lease
            or registered.value.registering_attempt_no != previous.task_attempt
            or registered.value.registering_deployment_ref != result.deployment_id
        ):
            return policy_rejection(
                "registration",
                "returned registration binds this exact observed author",
                effect_may_have_occurred=True,
            )
        receipt = self.runtime.journal.append_event(
            _EVENT,
            payload={
                "class": "qma-experiment-authoring-receipt-v1",
                "request_id": row.request_id,
                "request_attempt": row.attempt,
                "product_session_ref": row.spec.product_session_id,
                "spec_fp1": registered.value.spec.spec_fp1,
                "dispatch_lease": dict(previous.lease.to_payload()),
                "task_attempt": previous.task_attempt,
                "observed_deployment_ref": result.deployment_id,
                "provider_output_sha256": hashlib.sha256(result.content.encode()).hexdigest(),
            },
        )
        return (
            policy_rejection(
                "authoring_receipt",
                "registration completed but receipt persistence failed",
                effect_may_have_occurred=True,
            )
            if is_refusal(receipt)
            else Ok(None)
        )

    @staticmethod
    def _spec(content: str, deployment: str, task: TaskRecord) -> Result[ExperimentSpec]:
        try:
            content_size = len(content.encode("utf-8"))
        except UnicodeError:
            return invalid_input("authoring_output", "authoring output is valid UTF-8")
        if content_size > 32768:
            return invalid_input("authoring_output", "authoring output is bounded JSON")
        try:
            body = json.loads(content, object_pairs_hook=_unique)
        except ValueError, TypeError, RecursionError:
            return invalid_input(
                "authoring_output", "authoring output is one unique-key JSON object"
            )
        required = {
            "data_ref",
            "environment_ref",
            "resolved_config_ref",
            "seed",
            "cost_assumptions",
        }
        if (
            not isinstance(body, dict)
            or not required <= body.keys()
            or body.keys() - required - {"code_ref", "mechanisms"}
        ):
            return invalid_input(
                "authoring_output", "provider proposes only ExperimentSpec identity fields"
            )
        fields = cast("dict[str, object]", body)
        for field in ("data_ref", "environment_ref", "resolved_config_ref"):
            if fields[field] != task.inputs.get("authoring_" + field):
                return policy_rejection(field, "authoring cites the Task's admitted input refs")
        return parse_experiment_spec(
            **fields,
            model_and_harness_version={"model": deployment, "harness": "qma-request-runtime-v1"},
        )

    def receipt(self, request_id: str) -> Result[Mapping[str, object] | None]:
        events = self.runtime.journal.read_events()
        if is_refusal(events):
            return events
        matches = [
            event.payload
            for event in events.value
            if event.event == _EVENT and event.payload.get("request_id") == request_id
        ]
        return Ok(matches[-1] if matches else None)

    def reconcile_receipt(self, request_id: str) -> Result[Mapping[str, object]]:
        """Explicit host maintenance, never a read query or a provider replay.

        Rebuild only a missing receipt for an existing registration whose exact
        observed provider output and original authority remain in the journal.
        A missing/foreign registration stays blocked; this path cannot mint it.
        """
        # Follow the same runtime->Task authority lock order as completion.
        with (
            self.runtime.completion_guard(),
            self.authority_lock,
            self.runtime.product_sessions.authority_lock,
        ):
            loaded = self.runtime.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if (
                row.status != "failed"
                or row.error != "authoring_effect_uncertain"
                or row.result is None
            ):
                return policy_rejection(
                    "request_state", "only an observed uncertain authoring effect reconciles"
                )
            context = self.runtime.validate_request_context(request_id, now=self.now())
            if is_refusal(context):
                return context
            current = self._task(row)
            if is_refusal(current):
                return current
            if current.value is None or not row.result.deployment_id:
                return policy_rejection(
                    "authoring_task", "original authoring authority still resolves"
                )
            events = self.runtime.journal.read_events()
            if is_refusal(events):
                return events
            observations = [
                event.payload
                for event in events.value
                if event.event == "experiment.authoring_output_observed"
                and event.payload.get("request_id") == request_id
                and event.payload.get("request_attempt") == row.attempt
            ]
            if len(observations) != 1:
                return policy_rejection(
                    "authoring_output", "one actual execution observation resolves"
                )
            observed = observations[0]
            authority = current.value
            if (
                observed.get("dispatch_lease") != dict(authority.lease.to_payload())
                or observed.get("task_attempt") != authority.task_attempt
                or observed.get("observed_deployment_ref") != row.result.deployment_id
                or observed.get("authority_sha256") != authority.authority_sha256
                or observed.get("provider_output_sha256")
                != hashlib.sha256(row.result.content.encode()).hexdigest()
            ):
                return policy_rejection(
                    "authoring_output", "original execution and authority match exactly"
                )
            spec = self._spec(row.result.content, row.result.deployment_id, authority.task)
            if is_refusal(spec):
                return spec
            registered = self.experiments.resolve_durable(observed.get("proposed_spec_fp1"))
            if is_refusal(registered):
                return registered
            if (
                registered.value.spec.spec_fp1 != spec.value.spec_fp1
                or registered.value.dispatch_lease != authority.lease
                or registered.value.registering_attempt_no != authority.task_attempt
                or registered.value.registering_deployment_ref != row.result.deployment_id
            ):
                return policy_rejection(
                    "registration", "reconciliation never transfers or mints authority"
                )
            existing_receipt = self.receipt(request_id)
            if is_refusal(existing_receipt):
                return existing_receipt
            if existing_receipt.value is not None:
                return Ok(existing_receipt.value)
            body: dict[str, object] = {
                "class": "qma-experiment-authoring-receipt-v1",
                "request_id": request_id,
                "request_attempt": row.attempt,
                "product_session_ref": row.spec.product_session_id,
                "spec_fp1": spec.value.spec_fp1,
                "dispatch_lease": dict(authority.lease.to_payload()),
                "task_attempt": authority.task_attempt,
                "observed_deployment_ref": row.result.deployment_id,
                "provider_output_sha256": observed["provider_output_sha256"],
                "reconciled": True,
            }
            appended = self.runtime.journal.append_event(_EVENT, payload=body)
            return appended if is_refusal(appended) else Ok(body)
