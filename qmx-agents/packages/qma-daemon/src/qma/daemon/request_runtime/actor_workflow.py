"""Persistent host Quants, per-job sessions and finite SDK-owned workflow cursors.

QMA alone owns background jobs and cancellation. StateGraph owns deterministic
step ordering; create_agent owns each bounded child loop. No autonomous planner,
recursive spawn, new server, skill parser or journal implementation is added.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import END, START
from langgraph.graph.state import StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langsmith.run_helpers import (
    tracing_context,  # pyright: ignore[reportUnknownVariableType] - upstream Mapping generic
)
from qma.core.ports.memory import MemoryCandidate
from qma.daemon.hooks.registry import HookRegistry
from qmf.core import is_refusal

from .actor_profiles import (
    ActorCatalog,
    ActorRoute,
    WorkflowStep,
    canonical,
    digest,
    load_actor_catalog,
)
from .agent_extensions import AgentExtensions
from .contracts import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestSpec,
)
from .daemon_bridge import AgentRequestPolicy
from .durable_memory import ActorMemoryScope, DurableMemory, JournalMemoryProvider, MemorySource
from .graph_storage import JournalCheckpointer, JournalRecords
from .providers import ProviderError
from .service import RequestRuntime
from .tool_loop import LoopLimits, ToolBinding, ToolLoopProvider


class WorkflowState(TypedDict):
    input: str
    outputs: dict[str, Any]


def _pin(records: JournalRecords, kind: str, key: str, body: dict[str, Any]) -> None:
    body = canonical(body)
    prior = records.get(kind, key)
    if prior is None:
        records.put(kind, key, body)
    elif prior != body:
        raise ProviderError("definition_changed", "Host version content changed")


class ActorWorkflowProvider:
    def __init__(
        self,
        runtime: RequestRuntime,
        provider: ProviderAdapter,
        *,
        identity: str,
        catalog: ActorCatalog,
        routes: tuple[ActorRoute, ...],
        tools: Callable[[ProviderRequest], Mapping[str, ToolBinding]],
        now: Callable[[], str],
        admission_tools: Callable[[RequestSpec], Mapping[str, ToolBinding]] | None = None,
        extensions: AgentExtensions | None = None,
        hooks: HookRegistry | None = None,
    ) -> None:
        if provider.capabilities != ProviderCapabilities(provider.capabilities.provider_id):
            raise ValueError("actor steps require a bounded inference adapter")
        self.runtime, self.provider = runtime, provider
        self.catalog, self.routes, self.tools, self.now = catalog, routes, tools, now
        self.extensions, self.hooks = extensions, hooks
        self.admission_tools = admission_tools
        self.capabilities = ProviderCapabilities(identity)

    def bindings_for_spec(self, spec: RequestSpec) -> Mapping[str, ToolBinding]:
        route = next(r for r in self.routes if r.profile_id == spec.profile.profile_id)
        if not route.tools:
            return {}
        if self.admission_tools is None:
            raise ProviderError("tool_denied", "Joined route has no host admission resolver")
        bindings = self.admission_tools(spec)
        if set(route.tools) - set(bindings):
            raise ProviderError("tool_denied", "Required host callback is unavailable")
        return {name: bindings[name] for name in route.tools}

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        records = JournalRecords(self.runtime.journal)
        loaded = self.runtime.get(request.request_id)
        if is_refusal(loaded):
            raise ProviderError("unbound_loop", "Actor requires an admitted job")
        row = loaded.value
        route = next(r for r in self.routes if r.profile_id == row.spec.profile.profile_id)
        flow = self.catalog.workflow(route.workflow)
        deadline = time.monotonic() + request.timeout_seconds
        gateway = ToolLoopProvider(
            self.provider,
            provider_id=self.capabilities.provider_id,
            tools={},
            profile_tools={},
            now=self.now,
        )
        gateway.bind_runtime(self.runtime)

        def validate() -> None:
            gateway.validate_continuation(request, cancellation, deadline)

        validate()
        _pin(
            records,
            "quant",
            route.actor_id,
            {"actor_id": route.actor_id, "principal": row.spec.principal},
        )
        _pin(
            records,
            "actor_job",
            request.request_id,
            {
                "actor_id": route.actor_id,
                "workflow": flow.key,
                "catalog": self.catalog.identity,
                "authority": row.context_binding,
                "session": row.spec.product_session_id,
                "execution_agent": f"agent:{request.request_id}",
                "thread": f"{request.request_id}:workflow",
            },
        )
        needed = set(route.tools)
        bindings = dict(self.tools(request)) if needed else {}
        if needed - set(bindings):
            raise ProviderError("tool_denied", "Required host resource is unavailable")
        # The resolver revalidates independently available resources. It creates
        # no grant; every actual dispatch still runs ProductSession invocation.
        tools = {name: bindings[name] for name in needed}
        for name, binding in tools.items():
            checked = self.runtime.validate_tool_binding(request.request_id, name, binding)
            if is_refusal(checked):
                raise ProviderError(
                    "tool_denied", "Actual host callback differs from admitted authority"
                )
        gateway.tools = tools
        gateway.profile_tools = {route.profile_id: frozenset(route.tools)}

        def run_step(step: WorkflowStep, state: WorkflowState) -> dict[str, Any]:
            validate()
            output: Any
            if step.kind == "normalize":
                return {"input": " ".join(state["input"].split())}
            if step.kind == "collect":
                return {}
            if step.kind == "read":
                output = gateway.dispatch(
                    request,
                    step.tool or "",
                    json.loads(step.arguments_json),
                    f"{request.request_id}:step:{step.step_id}",
                    emit,
                    cancellation,
                    records=records,
                )
            else:
                role = self.catalog.role(step.role or "")
                activity_id = f"{request.request_id}:child:{step.step_id}"
                child_thread = f"{activity_id}:thread"
                source = MemorySource(
                    "host-workflow:" + flow.key,
                    digest(asdict(flow)),
                    (role.key,),
                    row.context_binding,
                )
                scope = ActorMemoryScope(row.spec.principal, route.actor_id, role.key, source)
                memory_provider = JournalMemoryProvider(
                    records, scope.namespace, source, validate, now_ns=time.time_ns
                )
                memory = DurableMemory(memory_provider, hooks=self.hooks)
                frozen = records.get("actor_input", activity_id)
                if frozen is None:
                    frozen = {
                        "body": json.dumps(
                            {
                                "request": state["input"],
                                "outputs": state["outputs"],
                                "actor_memory": memory.context(max_bytes=8192, max_tokens=8192),
                            },
                            sort_keys=True,
                        )
                    }
                    records.put("actor_input", activity_id, frozen)
                prior = records.get("actor_activity", activity_id)
                activity: dict[str, Any] = {
                    "activity_id": activity_id,
                    "actor_id": route.actor_id,
                    "execution_agent": f"agent:{activity_id}",
                    "thread": child_thread,
                    "role": role.key,
                    "depth": 1,
                    "status": "running",
                    "parent_request_id": request.request_id,
                    "step_id": step.step_id,
                }
                if prior and prior["status"] == "completed":
                    # Child completion may precede the parent's checkpoint write.
                    # Reconcile its already observed result; never replay it.
                    output = prior["result"]
                else:
                    records.put("actor_activity", activity_id, activity)
                    emit(ProviderEvent("child_started", activity))
                    child = ToolLoopProvider(
                        self.provider,
                        provider_id=self.capabilities.provider_id,
                        tools={name: tools[name] for name in role.tools},
                        profile_tools={route.profile_id: frozenset(role.tools)},
                        now=self.now,
                        limits=LoopLimits(
                            max_model_calls=role.max_model_calls, max_tool_calls=role.max_tool_calls
                        ),
                        extensions=self.extensions,
                        workflow_id=role.key,
                        effect_namespace=activity_id,
                    )
                    child.bind_runtime(self.runtime)
                    try:
                        result = child.execute(
                            replace(
                                request,
                                prompt=frozen["body"],
                                instructions=request.instructions
                                + "\nHost role: "
                                + role.instructions,
                                thread_id=None,
                                graph_thread_id=child_thread,
                                timeout_seconds=deadline - time.monotonic(),
                            ),
                            emit,
                            cancellation,
                        )
                        validate()
                        output = result.content
                        memory_id = activity_id + ":summary"
                        history = memory_provider.history(memory_id)
                        if is_refusal(history):
                            raise ProviderError("memory_denied", "Actor memory history refused")
                        occurred = (
                            history.value[0].occurrence_time
                            if history.value
                            else int(datetime.fromisoformat(self.now()).timestamp() * 1_000_000_000)
                        )
                        candidate = MemoryCandidate(
                            id=memory_id,
                            scope=scope.namespace,
                            proposer=role.key,
                            occurrence_time=occurred,
                            provenance={
                                "request_id": request.request_id,
                                "source_id": source.source_id,
                                "snapshot_ref": source.snapshot_ref,
                                "locators": list(source.locators),
                                "authority_binding": source.authority_binding,
                            },
                            supporting_artifacts=(
                                f"journal://agent_graph/actor_activity/{activity_id}",
                            ),
                            content={"memory_type": "summary", "text": output},
                        )
                        memory.admit(candidate)
                        validate()
                        activity.update(status="completed", result=output)
                        records.put("actor_activity", activity_id, activity)
                        emit(ProviderEvent("child_completed", activity))
                    except Exception as exc:
                        code = getattr(exc, "code", type(exc).__name__)
                        activity.update(
                            status="cancelled"
                            if code == "cancelled"
                            else "interrupted"
                            if code in {"outcome_unknown", "scope_interrupt"}
                            else "failed",
                            error=str(code),
                        )
                        # Shutdown freezes the owner before closing the journal;
                        # late callback writes are prohibited by active validation.
                        current = self.runtime.get(request.request_id)
                        if not is_refusal(current) and current.value.status in {
                            "running",
                            "cancellation_requested",
                        }:
                            records.put("actor_activity", activity_id, activity)
                        raise
            validate()
            outputs = dict(state["outputs"])
            outputs[step.step_id] = output
            return {"outputs": outputs}

        graph = StateGraph(WorkflowState)
        previous = START
        for step in flow.steps:

            def node(state: WorkflowState, selected: WorkflowStep = step) -> dict[str, Any]:
                return run_step(selected, state)

            graph.add_node(step.step_id, node)  # pyright: ignore[reportUnknownMemberType]
            graph.add_edge(previous, step.step_id)
            previous = step.step_id
        graph.add_edge(previous, END)
        saver = JournalCheckpointer(self.runtime.journal)
        compiled: Any = graph.compile(checkpointer=saver)  # pyright: ignore[reportUnknownMemberType]
        config: RunnableConfig = {
            "configurable": {"thread_id": f"{request.request_id}:workflow"},
            "recursion_limit": 16,
        }
        with tracing_context(enabled=False, parent=False):
            outcome = compiled.invoke(
                None if saver.get_tuple(config) else {"input": request.prompt, "outputs": {}},
                config=config,
                durability="sync",
            )
        validate()
        content = json.dumps(
            {"actor_id": route.actor_id, "workflow": flow.key, "outputs": outcome["outputs"]},
            sort_keys=True,
        )
        if len(content.encode()) > 65536:
            raise ProviderError("loop_limit", "Workflow result exceeds byte budget")
        return ProviderResult(content, thread_id=f"{request.request_id}:workflow")


def bind_actor_workflows(
    root: Path,
    runtime: RequestRuntime,
    providers: Mapping[str, ProviderAdapter],
    wrapped: Mapping[str, ProviderAdapter],
    policies: Mapping[str, AgentRequestPolicy],
    profile_tools: Mapping[str, frozenset[str]],
    *,
    now: Callable[[], str],
    extensions: AgentExtensions | None = None,
    hooks: HookRegistry | None = None,
) -> tuple[Mapping[str, ProviderAdapter], Mapping[str, AgentRequestPolicy]]:
    catalog = load_actor_catalog(root)
    if catalog is None:
        return wrapped, policies
    records = JournalRecords(runtime.journal)
    try:
        for role in catalog.roles:
            _pin(records, "actor_role", role.key, asdict(role))
        for flow in catalog.workflows:
            _pin(records, "actor_definition", flow.key, asdict(flow))
    except ProviderError as exc:
        raise ValueError("versioned host actor definition refused") from exc
    for route in catalog.routes:
        if route.profile_id not in policies or set(route.tools) - set(
            profile_tools.get(route.profile_id, frozenset())
        ):
            raise ValueError("actor route cannot widen host profile authority")
        if policies[route.profile_id].authoring_task_id is not None:
            raise ValueError("actor workflow cannot inherit experiment-authoring authority")
    bound_providers, bound_policies = dict(wrapped), dict(policies)
    for alias in {policies[r.profile_id].provider_id for r in catalog.routes}:
        identity = alias + ":actor:" + catalog.identity
        routes = tuple(r for r in catalog.routes if policies[r.profile_id].provider_id == alias)

        # Existing session resolver remains the sole target/grant selector. This
        # internal composition seam is isolated here for parent-owned adaptation.
        def resolve(
            request: ProviderRequest, adapter: Any = wrapped[alias]
        ) -> Mapping[str, ToolBinding]:
            return {"research_browse": adapter._binding(request)}

        def resolve_spec(
            spec: RequestSpec, adapter: Any = wrapped[alias]
        ) -> Mapping[str, ToolBinding]:
            return {"research_browse": adapter.binding_for_spec(spec)}

        bound_providers[identity] = ActorWorkflowProvider(
            runtime,
            providers[alias],
            identity=identity,
            catalog=catalog,
            routes=routes,
            tools=resolve,
            admission_tools=resolve_spec,
            now=now,
            extensions=extensions,
            hooks=hooks,
        )
        for route in routes:
            bound_policies[route.profile_id] = replace(
                policies[route.profile_id], provider_id=identity
            )
    return bound_providers, bound_policies


def activity_receipts(runtime: RequestRuntime, request_id: str) -> list[dict[str, Any]]:
    """Call only after bridge ownership and current disclosure have succeeded."""
    records = JournalRecords(runtime.journal)
    job = records.get("actor_job", request_id)
    if job is None:
        queued = runtime.get(request_id)
        if is_refusal(queued):
            return []
        provider = runtime.providers.get(queued.value.spec.provider_id)
        if not isinstance(provider, ActorWorkflowProvider):
            return []
        route = next(
            r for r in provider.routes if r.profile_id == queued.value.spec.profile.profile_id
        )
        job = {"workflow": route.workflow}
    definition = records.get("actor_definition", job["workflow"])
    if definition is None:
        raise ProviderError("storage_failure", "Pinned workflow definition missing")
    row = runtime.get(request_id)
    if is_refusal(row):
        raise ProviderError("storage_failure", "Activity owner missing")
    receipts: list[dict[str, Any]] = []
    for step in definition["steps"]:
        if step["kind"] != "agent":
            continue
        activity_id = f"{request_id}:child:{step['step_id']}"
        activity = records.get("actor_activity", activity_id)
        if activity is None:
            activity = {"activity_id": activity_id, "role": step["role"], "status": "queued"}
        elif activity["status"] == "running" and row.value.status != "running":
            activity["status"] = (
                "cancellation_requested"
                if row.value.status == "cancellation_requested"
                else "interrupted"
            )
            activity["error"] = "owner_lost"
        if activity["status"] == "queued" and row.value.status in {"cancelled", "failed"}:
            activity["status"] = "cancelled" if row.value.status == "cancelled" else "not_started"
        receipts.append(activity)
    return receipts
