"""Host-only canonical attribution; existing Task/Job owners retain state authority.

No identities, grants, Tasks or handles are minted here. Bounded child records and
memory/effect keys stay unchanged. Missing authority and uncertain effects refuse
continuation, even when a request's own state appears terminal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Any

from qma.core.ontology import ActorId, Agent
from qma.core.ports.jobs import JobHandle
from qma.core.vocabulary.enums import GrantEvaluationMoment, JobHandleState, TaskMissionState
from qma.daemon.bus.mailbox import MailboxStore
from qma.daemon.capabilities.spawn import AgentCapabilityStore
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.taskgraph.dispatcher import TaskGraphDispatcher
from qma.daemon.taskgraph.execution import deterministic_task_id
from qma.daemon.taskgraph.join import JoinRetryPlan
from qma.daemon.taskgraph.records import DispatchLease
from qma.daemon.tools.registry import ToolRegistry
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import policy_rejection

from .actor_profiles import digest
from .actor_workflow import ActorWorkflowProvider
from .contracts import RequestRecord
from .graph_storage import JournalRecords
from .partition_retry import PartitionRetryAdmission, stage_partition_retry
from .providers import ProviderError
from .service import RequestRuntime
from .tool_loop import ToolBinding


@dataclass(frozen=True, slots=True)
class CanonicalJoinPlan:
    principal: str
    profile_id: str
    behavioral_actor_id: str
    canonical_owner: ActorId
    task_id: str
    mapping_revision: int = 1

    def __post_init__(self) -> None:
        if any(
            not v.strip()
            for v in (self.principal, self.profile_id, self.behavioral_actor_id, self.task_id)
        ):
            raise ValueError("canonical join requires explicit bounded host identities")
        if (
            is_refusal(ActorId.try_create(self.canonical_owner.value))
            or type(self.mapping_revision) is not int
            or self.mapping_revision < 1
        ):
            raise ValueError("canonical join requires a valid ActorId and positive revision")


class CanonicalRequestJoin:
    def __init__(
        self,
        *,
        runtime: RequestRuntime,
        plans: tuple[CanonicalJoinPlan, ...],
        dispatcher: TaskGraphDispatcher,
        agents: AgentCapabilityStore,
        mailboxes: MailboxStore,
        jobs: JobHandleService,
        tools: ToolRegistry | None = None,
    ) -> None:
        if len({p.profile_id for p in plans}) != len(plans):
            raise ValueError("one canonical join plan per behavioral profile")
        self.runtime, self.dispatcher, self.agents = runtime, dispatcher, agents
        self.mailboxes, self.jobs = mailboxes, jobs
        self.tools = tools
        # Persisted receipts are history; each process needs explicit admission.
        self._reconciled: dict[str, int] = {}
        self._partition_retries: dict[str, PartitionRetryAdmission] = {}
        self.plans = {p.profile_id: p for p in plans}
        for plan in plans:
            registered = self._register(plan)
            if is_refusal(registered):
                raise ValueError("canonical host mapping admission refused")

    def _events(self, kind: str) -> list[dict[str, Any]]:
        events = self.runtime.journal.read_events()
        if is_refusal(events):
            raise ProviderError("storage_failure", "Canonical join journal unavailable")
        return [dict(e.payload) for e in events.value if e.event == "canonical_request." + kind]

    def _save(self, kind: str, body: dict[str, Any]) -> Result[None]:
        saved = self.runtime.journal.append_event("canonical_request." + kind, payload=body)
        return saved if is_refusal(saved) else Ok(None)

    def _mapping_key(self, plan: CanonicalJoinPlan) -> str:
        return digest([plan.principal, plan.behavioral_actor_id])

    def _catalog(self, plan: CanonicalJoinPlan) -> Result[str]:
        providers = [
            p
            for p in self.runtime.providers.values()
            if isinstance(p, ActorWorkflowProvider)
            and any(
                r.profile_id == plan.profile_id and r.actor_id == plan.behavioral_actor_id
                for r in p.routes
            )
        ]
        if len(providers) != 1:
            return policy_rejection("canonical_join", "one exact behavioral catalog route resolves")
        return Ok(providers[0].catalog.identity)

    def _register(self, plan: CanonicalJoinPlan) -> Result[None]:
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            quant = self.mailboxes.quant_for(plan.canonical_owner)
            if quant is None or quant.retired:
                return policy_rejection(
                    "canonical_owner", "mapping requires an existing active Quant"
                )
            catalog = self._catalog(plan)
            if is_refusal(catalog):
                return catalog
            key = self._mapping_key(plan)
            if any(e["mapping_key"] == key for e in self._events("retired")):
                return policy_rejection(
                    "canonical_owner", "retired behavioral mapping cannot reactivate"
                )
            body = {
                "mapping_key": key,
                "principal": plan.principal,
                "behavioral_actor_id": plan.behavioral_actor_id,
                "canonical_owner": plan.canonical_owner.value,
                "mapping_revision": plan.mapping_revision,
                "catalog_sha256": catalog.value,
            }
            prior = [e for e in self._events("mapping") if e["mapping_key"] == key]
            if prior:
                latest = prior[-1]
                if latest == body:
                    return Ok(None)
                if (
                    latest["canonical_owner"] != body["canonical_owner"]
                    or plan.mapping_revision != latest["mapping_revision"] + 1
                ):
                    return policy_rejection(
                        "canonical_owner", "mapping owner is permanent and revision advances once"
                    )
            elif plan.mapping_revision != 1:
                return policy_rejection("mapping_revision", "initial mapping revision is one")
            return self._save("mapping", body)

    def retire(self, profile_id: str) -> Result[None]:
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            plan = self.plans.get(profile_id)
            if plan is None:
                return policy_rejection("profile_id", "canonical host mapping is absent")
            key = self._mapping_key(plan)
            if any(e["mapping_key"] == key for e in self._events("retired")):
                return Ok(None)
            return self._save("retired", {"mapping_key": key})

    def bind_task(self, profile_id: str, task_id: str) -> Result[None]:
        """Trusted routing update affects only new acceptance, never old receipts."""
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            if profile_id not in self.plans or not task_id.strip():
                return policy_rejection("canonical_task", "explicit known host route required")
            self.plans[profile_id] = replace(self.plans[profile_id], task_id=task_id)
            return Ok(None)

    def _authority(
        self,
        row: RequestRecord,
        plan: CanonicalJoinPlan,
        *,
        recovery: bool = False,
        restoring_lease: DispatchLease | None = None,
    ) -> Result[dict[str, Any]]:
        quant = self.mailboxes.quant_for(plan.canonical_owner)
        task = self.dispatcher.task_for(plan.task_id)
        lease = self.dispatcher.dispatch_lease_for(plan.task_id)
        ledger = self.dispatcher.ledgers.get(plan.task_id)
        handle = self.jobs.handle_for_task(plan.task_id)
        durable = self.dispatcher.store.durable
        if recovery and restoring_lease is not None and durable is not None:
            graph = durable.graph_for_task(plan.task_id)
            task = None if graph is None else graph.task_by_id(plan.task_id)
            lease = restoring_lease
            ledger = None if task is None else task.ledger
        if (
            quant is None
            or quant.retired
            or task is None
            or task.owner != quant.actor_id
            or task.state
            not in (
                {TaskMissionState.RUNNING, TaskMissionState.UNKNOWN}
                if recovery
                else {TaskMissionState.RUNNING}
            )
            or lease is None
            or lease.owner != task.owner
            or lease.task_id != task.id
            or lease.mission_id != task.mission_id
            or ledger is None
            or (restoring_lease is None and self.dispatcher.ledgers.lease_for(task.id) != lease)
            or durable is None
        ):
            return policy_rejection(
                "canonical_task", "existing durable Task and retained lease must agree"
            )
        graph = durable.graph_for_task(task.id)
        agent = self.agents.get(lease.holder_agent_id)
        caps = self.agents.recorded_capabilities(lease.holder_agent_id)
        if (
            graph is None
            or graph.mission_id != task.mission_id
            or graph.task_by_id(task.id) != task
            or not isinstance(agent, Agent)
            or caps is None
            or caps.tool_ids != agent.effective_tool_ids
            or not agent.capabilities_frozen
            or agent.owner != task.owner
            or task.inputs.get("agent_session_ref") != agent.session_id
            or task.inputs.get("request_product_session_ref") != row.spec.product_session_id
            or task.inputs.get("request_profile_id") != row.spec.profile.profile_id
        ):
            return policy_rejection(
                "canonical_agent",
                "actual frozen Agent and admitted Task references authorize the request",
            )
        if (
            handle is None
            or handle.owner != task.owner
            or handle.originating_product_session_ref != row.spec.product_session_id
            or handle.state
            not in (
                {JobHandleState.UNKNOWN}
                if recovery
                else {JobHandleState.QUEUED, JobHandleState.RUNNING}
            )
        ):
            return policy_rejection(
                "canonical_job",
                "one owned active JobHandle resolves; unknown requires reconciliation",
            )
        provider = self.runtime.providers.get(row.spec.provider_id)
        catalog = self._catalog(plan)
        if is_refusal(catalog):
            return catalog
        if (
            not isinstance(provider, ActorWorkflowProvider)
            or provider.catalog.identity != catalog.value
            or not any(
                r.profile_id == plan.profile_id and r.actor_id == plan.behavioral_actor_id
                for r in provider.routes
            )
        ):
            return policy_rejection(
                "canonical_agent",
                "one exact host actor route must resolve",
            )
        route = next(r for r in provider.routes if r.profile_id == plan.profile_id)
        flow = provider.catalog.workflow(route.workflow)
        anchor = (
            next((n for n in flow.template().nodes if n["kind"] in {"task", "agent"}), None)
            if flow.graph_sha256 is not None
            else None
        )
        if flow.graph_sha256 is not None and (
            graph.graph_template_ref != flow.workflow_id
            or len(graph.nodes) != len(flow.steps)
            or anchor is None
            or task.node_id != anchor["id"]
            or task.node_kind is None
            or task.node_kind.value != anchor["kind"]
            or task.id != deterministic_task_id(graph.id, str(anchor["id"]))
            or {n.id for n in graph.nodes} != {s.step_id for s in flow.steps}
            or any(n.config.get("graph_sha256") != flow.graph_sha256 for n in graph.nodes)
            or sorted((e.from_node, e.to_node, e.mapping.value) for e in graph.edges)
            != sorted(
                (e["from"], e["to"], e["mapping"]) for e in json.loads(flow.edges_json or "[]")
            )
            or len(graph.tasks) != 1
            or {n.id: (n.kind.value, dict(n.config)) for n in graph.nodes}
            != {
                str(n["id"]): (
                    n["kind"],
                    {k: v for k, v in n.items() if k not in {"id", "kind"}},
                )
                for n in flow.template().nodes
            }
        ):
            return policy_rejection(
                "authored_graph", "host must compile and admit the exact authored graph"
            )
        pins = self._tool_pins(row, provider, agent)
        if is_refusal(pins):
            return pins
        return Ok(
            {
                "tool_bindings": pins.value,
                "canonical_owner": task.owner.value,
                "execution_agent_id": agent.id,
                "agent_session_ref": agent.session_id,
                "task_id": task.id,
                "mission_id": task.mission_id,
                "graph_id": graph.id,
                "dispatch_lease": dict(lease.to_payload()),
                "task_attempt": ledger.attempt_no,
                "job_id": handle.job_id,
                "logical_run_id": handle.logical_run_id,
                "job_attempt": handle.attempt_id,
                "task_sha256": digest(
                    dict(
                        task.with_state(TaskMissionState.RUNNING).to_payload()
                        if recovery
                        else task.to_payload()
                    )
                ),
                "capabilities_sha256": digest(
                    [sorted(agent.effective_tool_ids), sorted(agent.effective_permissions)]
                ),
            }
        )

    def _binding_pin(
        self,
        row: RequestRecord,
        provider: ActorWorkflowProvider,
        agent: Agent,
        binding: ToolBinding,
    ) -> Result[dict[str, Any]]:
        identity = binding.host_identity
        if identity is None or binding.execute is not identity.execute or self.tools is None:
            return policy_rejection("canonical_tool", "versioned actual host callback required")
        record = self.tools.get(identity.tool_id)
        if record is None or identity.tool_id not in agent.effective_tool_ids:
            return policy_rejection("canonical_tool", "registered qualified tool is outside Agent")
        if not set(binding.descriptor.permission_requests) <= agent.effective_permissions:
            return policy_rejection(
                "canonical_permission", "operation exceeds frozen Agent permissions"
            )
        try:
            available = self.tools.is_available(identity.tool_id)
        except Exception:
            available = False
        expected_schema = {
            "required_keys": list(binding.descriptor.configuration.required_keys),
            "optional_keys": list(binding.descriptor.configuration.optional_keys),
        }
        if (
            not available
            or record.schema != expected_schema
            or binding.descriptor.op_id not in record.acts
        ):
            return policy_rejection(
                "canonical_tool", "available registry schema and act must match callback"
            )
        with self.runtime.product_sessions.authority_lock:
            granted = self.runtime.product_sessions.resolve_grant(
                row.spec.product_session_id, binding.grant_id
            )
            live = self.runtime.product_sessions.ledger.evaluate(
                grant_id=binding.grant_id, moment=GrantEvaluationMoment.ACCEPT, now=provider.now()
            )
            if is_refusal(granted) or is_refusal(live):
                return policy_rejection("canonical_grant", "current session grant is required")
            grant = granted.value
            if (
                grant.principal != row.spec.principal
                or grant.contribution.qualified_id != binding.contribution.qualified_id
                or grant.contribution.package_version != binding.contribution.package_version
                or grant.instance_id != binding.instance.instance_id
                or grant.config_revision != binding.instance.config_revision
                or grant.op_id != binding.descriptor.op_id
                or grant.op_version != binding.descriptor.version
                or grant.effect_class != binding.descriptor.effect_class
            ):
                return policy_rejection(
                    "canonical_grant", "grant must authorize exact callback target"
                )
            grant_bytes = grant.canonical_bytes()
            if is_refusal(grant_bytes):
                return grant_bytes
        return Ok(
            {
                "binding_version": 1,
                "canonical_tool_id": identity.tool_id,
                "adapter_id": identity.adapter_id,
                "adapter_revision": identity.revision,
                "descriptor_json": json.dumps(
                    dict(binding.descriptor.to_payload()), sort_keys=True
                ),
                "contribution": list(binding.contribution.as_tuple()),
                "instance_json": json.dumps(asdict(binding.instance), sort_keys=True),
                "grant_id": binding.grant_id,
                "grant_sha256": hashlib.sha256(grant_bytes.value).hexdigest(),
                "argument_scope": json.loads(json.dumps(binding.argument_scope)),
                "resource_identity": dict(binding.resource_identity),
                "registry_json": json.dumps(
                    {
                        "tool_id": record.tool_id,
                        "kind": record.kind.value,
                        "capability_rung": record.capability_rung.value,
                        "plugin_id": record.plugin_id,
                        "schema": dict(record.schema),
                        "acts": sorted(record.acts),
                        "tags": sorted(record.tags),
                        "requires_environment_kind": record.requires_environment_kind,
                        "money_path_act": record.money_path_act,
                    },
                    sort_keys=True,
                ),
            }
        )

    def _tool_pins(
        self,
        row: RequestRecord,
        provider: ActorWorkflowProvider,
        agent: Agent,
    ) -> Result[dict[str, Any]]:
        try:
            bindings = provider.bindings_for_spec(row.spec)
        except ProviderError, ValueError:
            return policy_rejection("canonical_tool", "host binding resolver refused candidate")
        pins: dict[str, Any] = {}
        identities: set[str] = set()
        for alias, binding in sorted(bindings.items()):
            pinned = self._binding_pin(row, provider, agent, binding)
            if is_refusal(pinned):
                return pinned
            identity = pinned.value["canonical_tool_id"]
            if identity in identities:
                return policy_rejection(
                    "canonical_tool", "aliases cannot collide on qualified callback identity"
                )
            identities.add(identity)
            pins[alias] = pinned.value
        return Ok(pins)

    def guard_binding(self, row: RequestRecord, alias: str, binding: ToolBinding) -> Result[None]:
        """Check the binding captured by the executor, before grant dispatch.

        This runs under runtime -> Job -> Task -> session order, never from
        underneath the grant dispatcher's callback/permission lock. Work already
        accepted by that dispatcher retains its existing completion semantics.
        """
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            accepted = self._accepted(row)
            if accepted is None:
                return policy_rejection("canonical_tool", "original binding receipt required")
            provider = self.runtime.providers.get(row.spec.provider_id)
            agent = self.agents.get(accepted["execution_agent_id"])
            if not isinstance(provider, ActorWorkflowProvider) or not isinstance(agent, Agent):
                return policy_rejection("canonical_tool", "original callback authority unavailable")
            checked = self._binding_pin(row, provider, agent, binding)
            if is_refusal(checked):
                return checked
            if accepted.get("tool_bindings", {}).get(alias) != checked.value:
                return policy_rejection(
                    "canonical_tool", "captured callback differs from accepted host pin"
                )
            return Ok(None)

    def accept(self, row: RequestRecord) -> Result[RequestRecord]:
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            provider = self.runtime.providers.get(row.spec.provider_id)
            if isinstance(provider, ActorWorkflowProvider):
                route = next(
                    (r for r in provider.routes if r.profile_id == row.spec.profile.profile_id),
                    None,
                )
                if (
                    route is not None
                    and provider.catalog.workflow(route.workflow).graph_sha256 is not None
                ):
                    try:
                        provider.bindings_for_spec(row.spec)
                    except ProviderError:
                        return policy_rejection(
                            "authored_graph", "exact host operation binding required"
                        )
            plan = self.plans.get(row.spec.profile.profile_id)
            if plan is None:
                return (
                    policy_rejection("canonical_join", "joined request has no host plan")
                    if row.spec.canonical_join_required
                    else Ok(row)
                )
            if row.spec.principal != plan.principal or row.spec.authoring_task_id is not None:
                return policy_rejection(
                    "canonical_join",
                    "principal must match and catalog cannot inherit CT47 authority",
                )
            retired = [
                e for e in self._events("retired") if e["mapping_key"] == self._mapping_key(plan)
            ]
            if retired:
                return policy_rejection("canonical_join", "behavioral mapping is retired")
            authority = self._authority(row, plan)
            if is_refusal(authority):
                return authority
            spec = replace(row.spec, canonical_join_required=True)
            content_sha256 = digest(asdict(replace(spec, canonical_join_required=False)))
            prior = [
                e
                for e in self._events("accepted")
                if e["task_id"] == plan.task_id
                and e["task_attempt"] == authority.value["task_attempt"]
            ]
            if any(
                e["task_id"] == plan.task_id
                and e["task_attempt"] != authority.value["task_attempt"]
                for e in self._events("accepted")
            ):
                return policy_rejection(
                    "canonical_task",
                    "replacement attempts require reconciled canonical ownership; "
                    "v1 accepts a separately admitted fresh Task",
                )
            if prior:
                receipt = prior[-1]
                if (
                    receipt["request_sha256"] != content_sha256
                    or receipt["context_binding"] != row.context_binding
                    or any(
                        receipt.get(k, {} if k == "tool_bindings" else None) != v
                        for k, v in authority.value.items()
                    )
                ):
                    return policy_rejection(
                        "canonical_task", "one logical Request per canonical Task attempt"
                    )
                return Ok(replace(row, request_id=receipt["request_id"], spec=spec))
            catalog = self._catalog(plan)
            if is_refusal(catalog):
                return catalog
            body = {
                "contract_version": 2 if authority.value["tool_bindings"] else 1,
                "request_id": row.request_id,
                "request_sha256": content_sha256,
                "principal": plan.principal,
                "profile_id": plan.profile_id,
                "behavioral_actor_id": plan.behavioral_actor_id,
                "mapping_key": self._mapping_key(plan),
                "mapping_revision": plan.mapping_revision,
                "catalog_sha256": catalog.value,
                "context_binding": row.context_binding,
                "product_session_ref": spec.product_session_id,
                **authority.value,
            }
            saved = self._save("accepted", body)
            return saved if is_refusal(saved) else Ok(replace(row, spec=spec))

    def _accepted(self, row: RequestRecord) -> dict[str, Any] | None:
        matches = [e for e in self._events("accepted") if e["request_id"] == row.request_id]
        return matches[-1] if matches else None

    def _original_plan(self, receipt: dict[str, Any]) -> CanonicalJoinPlan:
        return CanonicalJoinPlan(
            receipt["principal"],
            receipt["profile_id"],
            receipt["behavioral_actor_id"],
            ActorId(receipt["canonical_owner"]),
            receipt["task_id"],
            receipt["mapping_revision"],
        )

    def _observed_read_prefix(self, row: RequestRecord, plan: CanonicalJoinPlan) -> Result[None]:
        """Only an observed authored read prefix can admit a new successor.

        A prior specialist activity or memory effect needs its own reconciliation
        contract. This increment never replays a possibly started model call.
        """
        provider = self.runtime.providers.get(row.spec.provider_id)
        if not isinstance(provider, ActorWorkflowProvider):
            return policy_rejection("reconciliation", "original authored provider required")
        route = next((r for r in provider.routes if r.profile_id == plan.profile_id), None)
        if route is None:
            return policy_rejection("reconciliation", "original authored route required")
        flow = provider.catalog.workflow(route.workflow)
        if flow.graph_sha256 is None:
            return policy_rejection("reconciliation", "recovery is bounded to authored paths")
        events = self.runtime.journal.read_events()
        if is_refusal(events):
            return events
        effects: dict[str, dict[str, Any]] = {}
        for event in events.value:
            if event.event != "agent_graph.record":
                continue
            key, kind = str(event.payload.get("key", "")), event.payload.get("kind")
            if not key.startswith(row.request_id + ":"):
                continue
            if kind in {"actor_activity", "memory_projection_effect"}:
                return policy_rejection(
                    "reconciliation", "prior child/memory activity is not replayable"
                )
            if kind == "effect":
                effects[key] = json.loads(str(event.payload["body"]))
        remaining = dict(effects)
        observed = 0
        gap = False
        for step in flow.steps:
            if step.kind in {"agent", "collect"}:
                break
            if step.kind != "read":
                continue
            effect = remaining.pop(row.request_id + ":step:" + step.step_id, None)
            if effect is None:
                gap = True
                continue
            if (
                gap
                or effect.get("status") != "observed"
                or effect.get("tool") != step.tool
                or effect.get("input_hash")
                != hashlib.sha256(
                    json.dumps(json.loads(step.arguments_json), sort_keys=True).encode()
                ).hexdigest()
                or not isinstance(effect.get("result"), dict)
            ):
                return policy_rejection("reconciliation", "exact observed read prefix required")
            observed += 1
        if not observed or remaining or self._uncertain_effects(row.request_id):
            return policy_rejection(
                "reconciliation", "unobserved effects require separate resolution"
            )
        return Ok(None)

    def reconcile_owner(
        self,
        request_id: str,
        *,
        principal: str,
        owner: ActorId,
        dispatch_lease: DispatchLease,
    ) -> Result[None]:
        """Trusted host explicitly admits one original-owner successor continuation.

        The host first spawns the original frozen Agent through AgentCapabilityStore.
        Supplied owner/lease and every current pin must match acceptance exactly.
        This does not settle UNKNOWN, grant permissions, queue work or restore an
        environment lease. Paired resume remains a separate authorized action.
        """
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            loaded = self.runtime.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            receipt = self._accepted(row)
            if (
                receipt is None
                or not row.spec.canonical_join_required
                or row.status != "interrupted"
                or row.result is not None
                or principal != receipt["principal"]
                or owner.value != receipt["canonical_owner"]
                or dict(dispatch_lease.to_payload()) != receipt["dispatch_lease"]
            ):
                return policy_rejection(
                    "reconciliation", "original interrupted owner/lease required"
                )
            plan = self._original_plan(receipt)
            if self.plans.get(plan.profile_id) != plan or any(
                e["mapping_key"] == receipt["mapping_key"] for e in self._events("retired")
            ):
                return policy_rejection("reconciliation", "original active host mapping required")
            checked = self._observed_read_prefix(row, plan)
            if is_refusal(checked):
                return checked
            provider = self.runtime.providers.get(row.spec.provider_id)
            if not isinstance(provider, ActorWorkflowProvider):
                return policy_rejection("reconciliation", "original authored provider unavailable")
            context = self.runtime.validate_request_context(request_id, now=provider.now())
            if is_refusal(context):
                return context
            if self.runtime.memory_bindings is not None:
                try:
                    self.runtime.memory_bindings.validate(row.spec.memory_binding_sha256)
                except ProviderError:
                    return policy_rejection("reconciliation", "original memory binding required")
            elif row.spec.memory_binding_sha256 is not None:
                return policy_rejection("reconciliation", "original memory binding unavailable")
            current = self._authority(row, plan, recovery=True, restoring_lease=dispatch_lease)
            if is_refusal(current):
                return current
            catalog = self._catalog(plan)
            if is_refusal(catalog):
                return catalog
            if (
                any(
                    receipt.get(k, {} if k == "tool_bindings" else None) != v
                    for k, v in current.value.items()
                )
                or catalog.value != receipt["catalog_sha256"]
            ):
                return policy_rejection("reconciliation", "frozen acceptance pins remain immutable")
            target = row.attempt + 1
            if request_id in self._reconciled and self._reconciled[request_id] != target:
                return policy_rejection("reconciliation", "one successor per explicit admission")
            restored = self.dispatcher.restore_dispatch_authority(dispatch_lease)
            if is_refusal(restored):
                return restored
            task = self.dispatcher.task_for(dispatch_lease.task_id)
            if task is not None and task.state is not TaskMissionState.UNKNOWN:
                # Abrupt loss can precede the volatile dispatcher's UNKNOWN fold.
                # Apply the existing Job owner evidence; never invent a terminal.
                mapped = self.jobs.apply_to_task(receipt["job_id"])
                if is_refusal(mapped):
                    return mapped
            if request_id in self._reconciled:
                return Ok(None)
            saved = self._save(
                "owner_reconciled",
                {
                    "request_id": request_id,
                    "request_attempt": target,
                    "accepted_sha256": digest(receipt),
                    "canonical_owner": owner.value,
                    "dispatch_lease": dict(dispatch_lease.to_payload()),
                    "canonical_state": "unknown",
                    "contract_version": 1,
                },
            )
            if is_refusal(saved):
                return saved
            self._reconciled[request_id] = target
            return Ok(None)

    def reconcile_partition_retry(
        self,
        request_id: str,
        *,
        principal: str,
        owner: ActorId,
        dispatch_lease: DispatchLease,
        partition_id: str,
        definition_revision: int,
        join_revision: int,
    ) -> Result[JoinRetryPlan]:
        """Host admission for one known refused read; paired resume stays separate."""
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            loaded = self.runtime.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            receipt = self._accepted(row)
            provider = self.runtime.providers.get(row.spec.provider_id)
            durable = self.dispatcher.store.durable
            if (
                receipt is None
                or not isinstance(provider, ActorWorkflowProvider)
                or durable is None
            ):
                return policy_rejection(
                    "partition_retry", "original canonical authored authority required"
                )
            graph = durable.graph_for_task(receipt["task_id"])
            route = next(
                (r for r in provider.routes if r.profile_id == receipt["profile_id"]), None
            )
            if graph is None or route is None:
                return policy_rejection("partition_retry", "original graph route required")
            with durable.authority_lock:
                staged = stage_partition_retry(
                    row,
                    provider.catalog.workflow(route.workflow),
                    graph,
                    JournalRecords(self.runtime.journal),
                    partition_id=partition_id,
                    definition_revision=definition_revision,
                    join_revision=join_revision,
                )
                if is_refusal(staged):
                    return staged
                plan, evidence_sha256 = staged.value
                existing = durable.get_join(plan.join.join_id)
                if not is_refusal(existing) and existing.value != plan.join:
                    return policy_rejection(
                        "partition_retry", "exact original join snapshot required"
                    )
                restored = self.reconcile_owner(
                    request_id, principal=principal, owner=owner, dispatch_lease=dispatch_lease
                )
                if is_refusal(restored):
                    return restored
                if is_refusal(existing):
                    saved = durable.persist_join(plan.join)
                    if is_refusal(saved):
                        return saved
                admitted = PartitionRetryAdmission(row.attempt + 1, plan, evidence_sha256)
                if self._partition_retries.get(request_id) == admitted:
                    return Ok(plan)
                saved_receipt = self._save(
                    "partition_retry_admitted",
                    {
                        "request_id": request_id,
                        "request_attempt": row.attempt + 1,
                        "accepted_sha256": digest(receipt),
                        "evidence_sha256": evidence_sha256,
                        "join_sha256": digest(dict(plan.join.to_payload())),
                        "task_attempt": receipt["task_attempt"],
                        "job_attempt": receipt["job_attempt"],
                        "graph_id": receipt["graph_id"],
                        "join_id": plan.join.join_id,
                        "edge_id": plan.join.edge_id,
                        "partition_id": partition_id,
                        "contract_version": 1,
                    },
                )
                if is_refusal(saved_receipt):
                    return saved_receipt
                self._partition_retries[request_id] = admitted
                return Ok(plan)

    def _guard_partition_retry(self, action: str, row: RequestRecord) -> Result[None]:
        records = JournalRecords(self.runtime.journal)
        refusal = records.get("partition_refusal", row.request_id)
        admission = self._partition_retries.get(row.request_id)
        if refusal is None:
            return (
                Ok(None)
                if admission is None
                else policy_rejection(
                    "partition_retry", "admitted known refusal evidence remains present"
                )
            )
        target = row.attempt + 1 if action == "retry" else row.attempt
        if admission is None or admission.request_attempt != target:
            return policy_rejection(
                "partition_retry", "explicit current partition admission required"
            )
        durable = self.dispatcher.store.durable
        if durable is None:
            return policy_rejection("partition_retry", "original durable join required")
        with durable.authority_lock:
            current = durable.get_join(admission.plan.join.join_id)
            if is_refusal(current) or current.value != admission.plan.join:
                return policy_rejection(
                    "partition_retry", "admitted join snapshot remains immutable"
                )
            # Partition sorting is lexical; choose by the pinned successful identity.
            first = next(p for p in admission.plan.join.partitions if p.result_identity is not None)
            observed = records.get("effect", first.result_identity or "")
            if digest([refusal, observed]) != admission.evidence_sha256:
                return policy_rejection(
                    "partition_retry", "admitted refusal and successful effect remain immutable"
                )
            if action in {"retry", "execute"}:
                failed = admission.plan.join.partition(admission.plan.reinvoke_partition_ids[0])
                if (
                    failed is None
                    or records.get("effect", failed.logical_invocation_id or "") is not None
                ):
                    return policy_rejection(
                        "partition_retry", "failed read remains never dispatched before resume"
                    )
            return Ok(None)

    def guard(self, action: str, row: RequestRecord) -> Result[None]:
        if not row.spec.canonical_join_required:
            return Ok(None)
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            receipt = self._accepted(row)
            if receipt is None:
                return policy_rejection(
                    "canonical_join", "original canonical acceptance is required"
                )
            # Stopping the originally owned bounded execution does not grant
            # continuation or canonical terminal authority. Revocation and
            # missing live host records must never prevent its token being set.
            if action == "cancel":
                return Ok(None)
            if any(e["mapping_key"] == receipt["mapping_key"] for e in self._events("retired")):
                return policy_rejection("canonical_join", "behavioral mapping is retired")
            if action == "read":
                quant = self.mailboxes.quant_for(receipt["canonical_owner"])
                return (
                    Ok(None)
                    if quant is not None and not quant.retired
                    else policy_rejection(
                        "canonical_owner", "current disclosure requires active Quant"
                    )
                )
            plan = self._original_plan(receipt)
            target = self._reconciled.get(row.request_id)
            recovery = target is not None and target == (
                row.attempt + 1 if action == "retry" else row.attempt
            )
            if action == "retry" and not recovery:
                return policy_rejection(
                    "canonical_join", "explicit current owner reconciliation required"
                )
            if action == "retry":
                checked = self._observed_read_prefix(row, plan)
                if is_refusal(checked):
                    return checked
            partition_guard = self._guard_partition_retry(action, row)
            if is_refusal(partition_guard):
                return partition_guard
            current = self._authority(row, plan, recovery=recovery)
            if is_refusal(current):
                return current
            catalog = self._catalog(plan)
            if is_refusal(catalog):
                return catalog
            if (
                any(
                    receipt.get(k, {} if k == "tool_bindings" else None) != v
                    for k, v in current.value.items()
                )
                or catalog.value != receipt["catalog_sha256"]
            ):
                return policy_rejection(
                    "canonical_join", "accepted canonical authority and catalog remain immutable"
                )
            if action == "execute":
                handle = self.jobs.handle_for(receipt["job_id"])
                if handle is not None and handle.state is JobHandleState.QUEUED:
                    started = self.jobs.start(handle.job_id)
                    if is_refusal(started):
                        return started
            return Ok(None)

    def observe(self, row: RequestRecord) -> Result[None]:
        if not row.spec.canonical_join_required:
            return Ok(None)
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            receipt = self._accepted(row)
            if receipt is None:
                return policy_rejection(
                    "canonical_join", "observation requires original canonical acceptance"
                )
            body: dict[str, Any] = {
                "request_id": row.request_id,
                "request_attempt": row.attempt,
                "request_status": row.status,
            }
            if row.result is not None:
                body["result_sha256"] = hashlib.sha256(row.result.content.encode()).hexdigest()
                body["result_json"] = json.dumps(asdict(row.result), sort_keys=True)
            original_plan = self._original_plan(receipt)
            current = self._authority(
                row, original_plan, recovery=self._reconciled.get(row.request_id) == row.attempt
            )
            authority_lost = is_refusal(current) or any(
                receipt.get(k, {} if k == "tool_bindings" else None) != v
                for k, v in current.value.items()
            )
            if (
                row.status == "interrupted"
                or row.error
                in {
                    "outcome_unknown",
                    "storage_failure",
                    "authoring_effect_uncertain",
                }
                or self._uncertain_effects(row.request_id)
                or authority_lost
            ):
                handle = self.jobs.handle_for(receipt["job_id"])
                if handle is not None and not handle.is_terminal:
                    unknown = self.jobs.mark_unknown(receipt["job_id"], trigger="lost_supervisor")
                    if is_refusal(unknown):
                        return unknown
            admission = self._partition_retries.get(row.request_id)
            if row.status == "completed" and admission is not None:
                guarded = self._guard_partition_retry("observe", row)
                if is_refusal(guarded):
                    return guarded
                durable = self.dispatcher.store.durable
                if durable is None:
                    return policy_rejection("partition_retry", "original durable join required")
                partition_id = admission.plan.reinvoke_partition_ids[0]
                key = row.request_id + ":step:" + partition_id
                effect = JournalRecords(self.runtime.journal).get("effect", key)
                if effect is None or effect.get("status") != "observed":
                    return policy_rejection(
                        "partition_retry", "observed selected retry result required"
                    )
                folded = durable.apply_join_retry_result(
                    admission.plan.join.join_id,
                    partition_id=partition_id,
                    result_identity=key,
                    definition_revision=admission.plan.definition_revision,
                    join_revision=admission.plan.join_revision,
                )
                if is_refusal(folded):
                    return folded
                # Frozen completed disclosure evidence, never continuation authority.
                body["partition_join_seal"] = {
                    "join_id": folded.value.join_id,
                    "accepted_sha256": digest(receipt),
                    "join_sha256": digest(dict(folded.value.to_payload())),
                }
            saved = self._save("observed", body)
            if is_refusal(saved):
                return saved
            # Bounded success/failure remains evidence, not a Task-ledger author.
            # Existing canonical completion rules and first terminal remain sole owners.
            return Ok(None)

    def _uncertain_effects(self, request_id: str) -> bool:
        events = self.runtime.journal.read_events()
        if is_refusal(events):
            raise ProviderError("storage_failure", "Canonical effect certainty unavailable")
        effects: dict[tuple[str, str], dict[str, Any]] = {}
        for event in events.value:
            if (
                event.event == "agent_graph.record"
                and event.payload.get("kind") in {"effect", "memory_projection_effect"}
                and str(event.payload.get("key", "")).startswith(request_id + ":")
            ):
                effects[(str(event.payload["kind"]), str(event.payload["key"]))] = json.loads(
                    str(event.payload["body"])
                )
        return any(e.get("status") != "observed" for e in effects.values())

    def allow_canonical_cancel(self, handle: JobHandle) -> Result[None]:
        """Journal-only certainty guard: never acquire the runtime lock under Job lock.

        JobHandleService invokes this for both direct and paired cancellation.
        Bounded intent must be requested through the existing request door first.
        A cancelled snapshot follows a known stopped or never-started execution;
        running/unknown/completed request telemetry cannot fabricate cancellation.
        """
        accepted = [e for e in self._events("accepted") if e["job_id"] == handle.job_id]
        if not accepted:
            return Ok(None)
        request_id = accepted[-1]["request_id"]
        events = self.runtime.journal.read_events()
        if is_refusal(events):
            return events
        snapshots = [
            e.payload
            for e in events.value
            if e.event == "agent_request.snapshot" and e.payload.get("request_id") == request_id
        ]
        if (
            not snapshots
            or snapshots[-1].get("status") != "cancelled"
            or self._uncertain_effects(request_id)
        ):
            return policy_rejection(
                "canonical_cancel",
                "joined execution requires observed bounded noncompletion; "
                "cancel its Request first, reconcile unknown effects",
            )
        return Ok(None)

    def owns_job(self, job_id: str) -> bool:
        """A persisted acceptance, never renderer metadata, chooses this route."""
        return any(e["job_id"] == job_id for e in self._events("accepted"))

    def projection(self, row: RequestRecord) -> Result[dict[str, Any] | None]:
        if not row.spec.canonical_join_required:
            return Ok(None)
        with (
            self.runtime.completion_guard(),
            self.jobs.store.atomic(),
            self.dispatcher.authority_lock,
        ):
            receipt = self._accepted(row)
            if receipt is None:
                return policy_rejection(
                    "canonical_join", "canonical projection requires acceptance"
                )
            handle = self.jobs.handle_for(receipt["job_id"])
            observations = [
                e for e in self._events("observed") if e["request_id"] == row.request_id
            ]
            partition_projection = self._partition_projection(row, receipt)
            if is_refusal(partition_projection):
                return partition_projection
            certainty = (
                "settled"
                if handle is not None and handle.is_terminal
                else "unknown"
                if handle is None or handle.state is JobHandleState.UNKNOWN
                else "observed"
                if observations and observations[-1].get("result_sha256")
                else "pending"
            )
            return Ok(
                {
                    k: receipt[k]
                    for k in (
                        "contract_version",
                        "canonical_owner",
                        "behavioral_actor_id",
                        "execution_agent_id",
                        "task_id",
                        "job_id",
                        "logical_run_id",
                        "job_attempt",
                        "task_attempt",
                        "mapping_revision",
                        "catalog_sha256",
                    )
                }
                | {
                    "tool_bindings": receipt.get("tool_bindings", {}),
                    "canonical_state": "unknown" if handle is None else handle.state.value,
                    "request_status": row.status,
                    "certainty": certainty,
                    **partition_projection.value,
                }
            )

    def _partition_projection(
        self, row: RequestRecord, receipt: dict[str, Any]
    ) -> Result[dict[str, Any]]:
        admissions = [
            e for e in self._events("partition_retry_admitted") if e["request_id"] == row.request_id
        ]
        if not admissions:
            return Ok({})
        durable = self.dispatcher.store.durable
        if durable is None:
            return policy_rejection("partition_retry", "exact admitted join disclosure unavailable")
        admitted = admissions[-1]
        joined = durable.get_join(admitted["join_id"])
        if (
            is_refusal(joined)
            or joined.value.graph_run_id != receipt["graph_id"]
            or joined.value.edge_id != admitted["edge_id"]
        ):
            return policy_rejection("partition_retry", "exact admitted join disclosure required")
        if row.status == "completed" or row.result is not None:
            observations = [
                e
                for e in self._events("observed")
                if e["request_id"] == row.request_id
                and e["request_attempt"] == row.attempt
                and e["request_status"] == "completed"
            ]
            expected_seal = {
                "join_id": joined.value.join_id,
                "accepted_sha256": digest(receipt),
                "join_sha256": digest(dict(joined.value.to_payload())),
            }
            if not observations or observations[-1].get("partition_join_seal") != expected_seal:
                return policy_rejection(
                    "partition_retry", "completed join disclosure requires its exact observed seal"
                )
        return Ok({"partition_join": dict(joined.value.to_payload())})
