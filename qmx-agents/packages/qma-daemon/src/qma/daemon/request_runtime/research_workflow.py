"""A bounded research workflow with one graph cursor and scoped delegation.

Supplied, retained corpus -> named specialist -> QMX domain operation -> durable
result. The specialist owns no grants and each job gets a separate agent thread.
This is a local library composition, independent of a commercial Agent Server.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import END, START
from langgraph.graph.state import StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.types import Command, interrupt
from langsmith.run_helpers import (
    tracing_context,  # pyright: ignore[reportUnknownVariableType] - upstream Mapping generic
)
from qma.daemon.hooks.registry import HookRegistry
from qma.daemon.knowledge.service import KnowledgeService
from qmf.core import is_refusal

from .agent_extensions import AgentExtensions
from .contracts import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
)
from .durable_memory import JournalMemoryProvider
from .graph_storage import JournalCheckpointer, JournalRecords
from .memory_projection import MemoryProjection
from .providers import ProviderCancelled, ProviderError
from .scoped_memory import ResearchMemoryScope, ScopedResearchMemory
from .service import RequestRuntime
from .tool_loop import LoopLimits, ToolBinding, ToolLoopProvider


@dataclass(frozen=True, slots=True)
class SpecialistDefinition:
    """Persistent behavior definition; authority always comes from the job."""

    specialist_id: str
    version: str
    instructions: str
    allowed_tools: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (
            not self.specialist_id.strip()
            or not self.version.strip()
            or not self.instructions.strip()
        ):
            raise ValueError("Named, versioned specialist instructions are required")
        if self.allowed_tools:
            raise ValueError(
                "Research analysis specialist is inference-only in this bounded workflow"
            )


@dataclass(frozen=True, slots=True)
class RetainedCorpus:
    knowledge: KnowledgeService
    source_id: str
    snapshot_ref: str
    locators: tuple[str, ...]
    max_bytes: int = 32_768
    retain_supplied: bool = False

    def retrieve(self) -> list[dict[str, str]]:
        """Read only host-supplied pins from KnowledgeService's retained copies."""
        if (
            not self.locators
            or len(set(self.locators)) != len(self.locators)
            or self.max_bytes <= 0
        ):
            raise ProviderError("invalid_input", "Explicit bounded corpus scope required")
        documents: list[dict[str, str]] = []
        size = 0
        for locator in self.locators:
            if self.retain_supplied:
                retained = self.knowledge.cite(
                    self.source_id,
                    self.snapshot_ref,
                    locator,
                    evidence_label="host-supplied-corpus",
                    authored_by="host-research-workflow",
                )
                if is_refusal(retained):
                    raise ProviderError("corpus_unavailable", "Supplied corpus retention refused")
            retrieved = self.knowledge.retrieve(self.source_id, self.snapshot_ref, locator)
            if is_refusal(retrieved):
                raise ProviderError("corpus_unavailable", "Supplied corpus has no retained copy")
            size += len(retrieved.value)
            if size > self.max_bytes:
                raise ProviderError("loop_limit", "Supplied corpus exceeds job byte budget")
            try:
                content = retrieved.value.decode("utf-8")
            except UnicodeError as exc:
                raise ProviderError("corpus_unavailable", "Research corpus must be UTF-8") from exc
            documents.append(
                {
                    "locator": locator,
                    "content": content,
                    "sha256": hashlib.sha256(retrieved.value).hexdigest(),
                }
            )
        return documents


class ResearchState(TypedDict):
    documents: list[dict[str, str]]
    analysis: str
    operation_result: dict[str, Any]
    result: str


class ResearchWorkflowProvider:
    """Host-composed ProviderAdapter; request admission stays in RequestRuntime.

    Ordinary in-scope steps run unattended. A missing host operation permission
    interrupts at the workflow boundary before retrieval or disclosure. Resume
    always revalidates the original job binding and current grants. A scope
    change requires a new admitted request; resume does not expand a job.
    """

    def __init__(
        self,
        provider: ProviderAdapter,
        *,
        provider_id: str,
        specialist: SpecialistDefinition,
        corpus: RetainedCorpus,
        operation_name: str,
        operation: ToolBinding,
        operation_arguments: Mapping[str, object],
        profile_tools: Mapping[str, frozenset[str]],
        now: Callable[[], str],
        limits: LoopLimits | None = None,
        hooks: HookRegistry | None = None,
        agent_extensions: AgentExtensions | None = None,
    ) -> None:
        if (
            provider.capabilities.execution_kind != "inference"
            or provider.capabilities.native_tools
            or provider.capabilities.resume
        ):
            raise ValueError("Research specialist requires an inference backend")
        self.provider = provider
        self._capabilities = ProviderCapabilities(provider_id)
        self.specialist = specialist
        self.corpus = corpus
        self.operation_name = operation_name
        self.operation = operation
        self.operation_arguments = dict(operation_arguments)
        self.profile_tools = dict(profile_tools)
        self.now = now
        self.limits = limits or LoopLimits(max_model_calls=1, max_tool_calls=1)
        self._explicit_limits = limits is not None
        self.hooks = hooks
        self.agent_extensions = agent_extensions
        self.runtime: RequestRuntime | None = None

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def bind_runtime(self, runtime: RequestRuntime) -> None:
        if self.runtime is not None and self.runtime is not runtime:
            raise ValueError("Workflow already bound to another authority")
        self.runtime = runtime

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        if self.runtime is None or not request.request_id:
            raise ProviderError("unbound_loop", "Workflow requires an admitted request")
        runtime = self.runtime
        row = runtime.get(request.request_id)
        if is_refusal(row):
            raise ProviderError("unbound_loop", "Workflow owner unavailable")
        profile_id = row.value.spec.profile.profile_id
        deadline = time.monotonic() + request.timeout_seconds
        records = JournalRecords(runtime.journal)
        definition_key = f"{self.specialist.specialist_id}:{self.specialist.version}"
        selection = (
            self.agent_extensions.select(
                profile_id, row.value.spec.product_session_id, definition_key
            )
            if self.agent_extensions is not None
            else None
        )
        extensions_enabled = bool(selection and (selection.sources or selection.middleware))
        child_limits = (
            LoopLimits() if extensions_enabled and not self._explicit_limits else self.limits
        )
        definition = asdict(self.specialist)
        definition["allowed_tools"] = list(self.specialist.allowed_tools)
        known_definition = records.get("specialist", definition_key)
        if known_definition is None:
            records.put("specialist", definition_key, definition)
        elif known_definition != definition:
            raise ProviderError("definition_changed", "Specialist version has changed content")
        manifest = {
            "specialist": definition,
            "source": self.corpus.source_id,
            "snapshot": self.corpus.snapshot_ref,
            "locators": list(self.corpus.locators),
            "corpus_max_bytes": self.corpus.max_bytes,
            "retain_supplied": self.corpus.retain_supplied,
            "instructions": request.instructions,
            "profile_tools": sorted(self.profile_tools.get(profile_id, frozenset())),
            "operation": self.operation_name,
            "descriptor": dict(self.operation.descriptor.to_payload()),
            "contribution": asdict(self.operation.contribution),
            "instance_binding": asdict(self.operation.instance),
            "argument_scope": list(self.operation.argument_scope),
            "arguments": self.operation_arguments,
            "grant": self.operation.grant_id,
            "instance": self.operation.instance.instance_id,
            "revision": self.operation.instance.config_revision,
            "provider": self.provider.capabilities.provider_id,
            "limits": asdict(self.limits),
        }
        if self.agent_extensions is not None:
            manifest["extensions"] = selection.binding() if selection is not None else {}
            manifest["child_limits"] = asdict(child_limits)
        manifest = json.loads(json.dumps(manifest, sort_keys=True))
        prior_manifest = records.get("workflow", request.request_id)
        if prior_manifest is None:
            records.put("workflow", request.request_id, manifest)
        elif prior_manifest != manifest:
            raise ProviderError("context_changed", "Workflow binding changed before resume")
        # Shared across jobs of this profile and corpus, never across session authority.
        session = runtime.product_sessions.get(row.value.spec.product_session_id)
        if is_refusal(session):
            raise ProviderError("context_changed", "Research memory application scope unavailable")
        memory_scope = ResearchMemoryScope(
            row.value.spec.principal,
            session.value.app_instance_id or "home",
            profile_id,
            row.value.context_binding,
            self.corpus.source_id,
            self.corpus.snapshot_ref,
            self.corpus.locators,
        )
        gateway = ToolLoopProvider(
            self.provider,
            provider_id=self.capabilities.provider_id,
            tools={self.operation_name: self.operation},
            profile_tools=self.profile_tools,
            now=self.now,
            limits=self.limits,
        )
        gateway.bind_runtime(runtime)

        def validate() -> None:
            if cancellation.is_set():
                raise ProviderCancelled()
            gateway.validate_continuation(request, cancellation, deadline)

        def project_memory(canonical: JournalMemoryProvider) -> MemoryProjection:
            bindings = runtime.memory_bindings
            if bindings is None:
                return canonical
            return bindings.project(
                row.value.spec, canonical, desk="research", request_id=request.request_id
            )

        memory = ScopedResearchMemory(
            records,
            memory_scope,
            validate,
            hooks=self.hooks,
            projection=project_memory,
            max_bytes=2 * self.limits.max_response_bytes + 8192,
        )

        def boundary(state: ResearchState) -> dict[str, Any]:
            validate()
            allowed = self.profile_tools.get(profile_id, frozenset())
            if self.operation_name not in allowed:
                interrupt(
                    {"reason": "operation_outside_job_scope", "operation": self.operation_name}
                )
                validate()
                if self.operation_name not in self.profile_tools.get(profile_id, frozenset()):
                    raise ProviderError("tool_denied", "Resume cannot widen the admitted job")
            return {}

        def retrieve(state: ResearchState) -> dict[str, Any]:
            validate()
            documents = self.corpus.retrieve()
            emit(ProviderEvent("workflow_corpus_retrieved", {"documents": len(documents)}))
            return {"documents": documents}

        def delegate(state: ResearchState) -> dict[str, Any]:
            validate()
            invocation_input = records.get("delegation_input", request.request_id)
            if invocation_input is None:
                # Freeze cross-job memory as this invocation's context before
                # entering a resumable child graph. Shared memory may evolve.
                body = json.dumps(
                    {
                        "request": request.prompt,
                        "corpus": state["documents"],
                        "scoped_memory": memory.recall(),
                    },
                    ensure_ascii=False,
                    allow_nan=False,
                )
                records.put("delegation_input", request.request_id, {"body": body})
            else:
                body = str(invocation_input["body"])
            child = ToolLoopProvider(
                self.provider,
                provider_id=self.capabilities.provider_id,
                tools={},
                profile_tools={profile_id: frozenset()},
                now=self.now,
                limits=child_limits,
                extensions=self.agent_extensions if extensions_enabled else None,
                workflow_id=definition_key,
            )
            child.bind_runtime(runtime)
            emit(
                ProviderEvent(
                    "workflow_delegated",
                    {
                        "specialist": definition_key,
                        "thread": f"{request.request_id}:specialist:{definition_key}",
                    },
                )
            )
            result = child.execute(
                replace(
                    request,
                    prompt=body,
                    instructions=request.instructions
                    + "\nSpecialist behavior: "
                    + self.specialist.instructions,
                    graph_thread_id=f"{request.request_id}:specialist:{definition_key}",
                    timeout_seconds=deadline - time.monotonic(),
                ),
                emit,
                cancellation,
            )
            return {"analysis": result.content}

        def operate(state: ResearchState) -> dict[str, Any]:
            validate()
            result = gateway.dispatch(
                request,
                self.operation_name,
                self.operation_arguments,
                f"{request.request_id}:workflow:operation",
                emit,
                cancellation,
                records=records,
            )
            return {"operation_result": dict(result)}

        def persist(state: ResearchState) -> dict[str, Any]:
            validate()
            content = json.dumps(
                {
                    "analysis": state["analysis"],
                    "operation": state["operation_result"],
                    "specialist": definition_key,
                    "corpus": [
                        {"locator": item["locator"], "sha256": item["sha256"]}
                        for item in state["documents"]
                    ],
                },
                ensure_ascii=False,
            )
            if len(content.encode("utf-8")) > self.limits.max_result_bytes:
                raise ProviderError("loop_limit", "Workflow result byte budget exhausted")
            records.put("result", request.request_id, {"content": content})
            memory.retain(
                state["analysis"],
                request_id=request.request_id,
                specialist=definition_key,
                occurrence_time=int(datetime.fromisoformat(self.now()).timestamp() * 1_000_000_000),
                result_ref=f"journal://agent_graph/result/{request.request_id}",
            )
            emit(ProviderEvent("workflow_result_persisted", {"request_id": request.request_id}))
            return {"result": content}

        graph = StateGraph(ResearchState)
        nodes = [
            ("scope_boundary", boundary),
            ("retrieve", retrieve),
            ("delegate", delegate),
            ("domain_operation", operate),
            ("persist", persist),
        ]
        previous = START
        for name, node in nodes:
            graph.add_node(name, node)  # pyright: ignore[reportUnknownMemberType]
            graph.add_edge(previous, name)
            previous = name
        graph.add_edge(previous, END)
        saver = JournalCheckpointer(runtime.journal)
        compiled: Any = graph.compile(checkpointer=saver)  # pyright: ignore[reportUnknownMemberType]
        config: RunnableConfig = {"configurable": {"thread_id": f"{request.request_id}:research"}}
        prior = saver.get_tuple(config)
        snapshot = compiled.get_state(config) if prior else None
        graph_input: Any = (
            Command(resume=True)
            if snapshot and snapshot.interrupts
            else None
            if prior
            else {
                "documents": [],
                "analysis": "",
                "operation_result": {},
                "result": "",
            }
        )
        with tracing_context(enabled=False, parent=False):
            outcome = compiled.invoke(graph_input, config=config, durability="sync")
        if outcome.get("__interrupt__"):
            raise ProviderError("scope_interrupt", "Workflow stopped at the job scope boundary")
        validate()
        return ProviderResult(outcome["result"], thread_id=f"{request.request_id}:research")
