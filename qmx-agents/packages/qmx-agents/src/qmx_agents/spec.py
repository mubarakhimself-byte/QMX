"""Parse AgentSpecs and compile their named tools and sub-agents with Deep Agents."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import urlsplit
from uuid import uuid4

import yaml
from deepagents import (
    CompiledSubAgent,
    FilesystemPermission,
    SubAgent,
    create_deep_agent,  # pyright: ignore[reportUnknownVariableType] - upstream generic overload
)
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import BackendProtocol, SandboxBackendProtocol
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents.middleware import (
    AgentMiddleware,
    ContextEditingMiddleware,
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
)
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from qmx_broker.server import create_server as create_broker_server
from qmx_broker.service import BrokerService
from qmx_control.service import ControlService
from qmx_ledger.journal import RunJournal
from qmx_tools import default_tool_registry

from qmx_agents.guards import AdmissionBackend, AdmissionGate, check_tool
from qmx_agents.guards.admission import AdmissionSandboxBackend
from qmx_agents.guards.hooks import AppHooksMiddleware, watch_breakers
from qmx_agents.guards.middleware import (
    AdmissionStateMiddleware,
    JournalApprovals,
    JournalMiddleware,
    MoneyPathMiddleware,
)
from qmx_agents.guards.money_path import BrokerOrderProposalTool
from qmx_agents.memory import (
    Approval,
    MemoryContext,
    MemoryManager,
    Scope,
    StoreMemoryProvider,
    load_provider,
    memory_path,
)
from qmx_agents.research import ResearchLibraryMiddleware
from qmx_agents.router import FIRECRAWL_SERVER, ModelRouter, RunContext, credential, model_selector


class MemorySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["task", "workflow", "session", "global"] = "task"
    provider: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    profile_cap: int = Field(default=2000, gt=0)
    prefetch_cap: int = Field(default=10000, ge=256)


class SubagentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ref: Path | None = None
    workflow: str | None = None

    @model_validator(mode="after")
    def one_reference(self) -> SubagentSpec:
        if (self.ref is None) == (self.workflow is None):
            raise ValueError("A sub-agent must have exactly one ref or workflow")
        return self


class Permissions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    write: list[str] | None = None
    deny_write: list[str] = Field(default_factory=list)

    def rules(self) -> list[FilesystemPermission]:
        rules: list[FilesystemPermission] = []
        if self.deny_write:
            rules.append(
                FilesystemPermission(operations=["write"], paths=self.deny_write, mode="deny")
            )
        if self.write is not None:
            if self.write:
                rules.append(
                    FilesystemPermission(operations=["write"], paths=self.write, mode="allow")
                )
            rules.append(FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"))
        return rules


class Budget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_calls: int | None = Field(default=None, gt=0)
    tool_calls: int | None = Field(default=None, gt=0)


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    model: str
    system_prompt: Path
    tools: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    memory: MemorySpec = Field(default_factory=MemorySpec)
    subagents: list[SubagentSpec] = Field(default_factory=list[SubagentSpec])
    background_tasks: list[Path] = Field(default_factory=list[Path])
    interrupt_on: dict[str, bool] = Field(default_factory=dict)
    permissions: Permissions = Field(default_factory=Permissions)
    budget: Budget = Field(default_factory=Budget)

    @field_validator("model")
    @classmethod
    def valid_model(cls, value: str) -> str:
        return model_selector(value)


def load_spec(path: str | Path | None = None) -> AgentSpec:
    source = (
        Path(path) if path is not None else Path(__file__).with_name("agents") / "copilot.yaml"
    ).resolve()
    spec = AgentSpec.model_validate(yaml.safe_load(source.read_text(encoding="utf-8")))
    spec.system_prompt = (source.parent / spec.system_prompt).resolve()
    # Fail during loading, before models or MCP connections are constructed.
    spec.system_prompt.read_text(encoding="utf-8")
    for subagent in spec.subagents:
        if subagent.ref is not None:
            subagent.ref = (source.parent / subagent.ref).resolve()
    spec.background_tasks = [(source.parent / item).resolve() for item in spec.background_tasks]
    return spec


@dataclass
class BuildContext:
    router: ModelRouter
    run: RunContext = field(default_factory=RunContext)
    tools: dict[str, BaseTool] = field(default_factory=default_tool_registry)
    workflows: dict[str, Runnable[Any, Any]] = field(default_factory=dict[str, Runnable[Any, Any]])
    backend: BackendProtocol | None = None
    checkpointer: BaseCheckpointSaver[Any] | None = None
    journal: RunJournal | None = None
    journal_resources: list[RunJournal] = field(default_factory=list[RunJournal])
    admission: AdmissionGate | None = None
    budget: Budget | None = None
    qmx_home: Path | None = None
    memory: MemoryManager | None = None
    memory_role: Literal["primary", "subagent", "scheduled", "headless"] = "primary"
    memory_approval: Approval | None = None
    memory_resources: list[MemoryManager] = field(default_factory=list[MemoryManager])
    general_purpose_subagent: bool = True
    broker: BrokerService | None = None
    # Reuse the node's owner so supervisor events reach the Copilot between turns.
    control: ControlService | None = None
    agent_backends: dict[str, BackendProtocol] = field(default_factory=dict[str, BackendProtocol])
    mcp_targets: dict[str, Any] = field(default_factory=dict[str, Any])
    background_resources: list[Any] = field(default_factory=list[Any])
    explicit_publish: bool = False

    async def close_memory(self) -> None:
        for tasks in self.background_resources:
            await tasks.close()
        self.background_resources.clear()
        for manager in reversed(self.memory_resources):
            await manager.close()
        self.memory_resources.clear()
        self.memory = None
        for journal in self.journal_resources:
            journal.close()
        self.journal_resources.clear()


class _NoDelegation(AgentMiddleware[Any, Any, Any]):
    @property
    def name(self) -> str:
        # Deep Agents replaces its default middleware when a name matches.
        return "SubAgentMiddleware"


async def build_agent(
    spec: AgentSpec, ctx: BuildContext
) -> CompiledStateGraph[Any, RunContext, Any, Any]:
    """Await discovery once; invoke MCP graphs asynchronously on the same loop."""
    return await _build(spec, ctx, ())


def mcp_configuration(spec: AgentSpec, ctx: BuildContext) -> dict[str, dict[str, Any]]:
    servers = {"firecrawl": dict(FIRECRAWL_SERVER), **ctx.router.config.mcp_servers}
    servers["firecrawl"] = {**FIRECRAWL_SERVER, **servers["firecrawl"]}
    if ctx.qmx_home is not None and (ctx.qmx_home / "settings.toml").exists():
        with (ctx.qmx_home / "settings.toml").open("rb") as file:
            settings = tomllib.load(file).get("mcp_servers", {})
        for name, values in settings.items():
            servers[name] = {**servers.get(name, {}), **values}
    names = list(spec.mcp_servers)
    if (
        spec.name == "researcher"
        and servers["firecrawl"].get("enabled") is True
        and "firecrawl" not in names
    ):
        names.append("firecrawl")
    selected: dict[str, dict[str, Any]] = {}
    for name in names:
        if name == "qmx-broker" or name in ctx.mcp_targets:
            continue
        server = dict(servers[name])
        if server.pop("enabled", True) is False:
            continue
        reference = server.pop("credential_ref", None)
        if name == "firecrawl":
            # This paid provider always gets its bearer token from the vault.
            reference = "qmx/firecrawl"
            server.pop("headers", None)
            url = urlsplit(str(server.get("url", "")))
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
                or url.query
                or url.fragment
            ):
                raise ValueError("Firecrawl requires an HTTPS URL without embedded credentials.")
        if reference is not None:
            if (
                not isinstance(reference, str)
                or not reference.startswith("qmx/")
                or "/" in reference[4:]
            ):
                raise ValueError("MCP credentials must reference qmx/<provider>.")
            server["auth"] = credential(reference[4:])
        selected[name] = server
    return selected


async def _build(
    spec: AgentSpec, ctx: BuildContext, ancestors: tuple[Path, ...]
) -> CompiledStateGraph[Any, RunContext, Any, Any]:
    if spec.background_tasks and ctx.control is None:
        raise NotImplementedError("background_tasks require the owning qmx-control service")
    if any(spec.interrupt_on.values()) and ctx.checkpointer is None:
        raise ValueError("interrupt_on requires a checkpointer")
    tools = [ctx.tools[name] for name in spec.tools]
    if spec.background_tasks:
        from qmx_agents.tasks import BackgroundTasks  # noqa: PLC0415

        tasks = BackgroundTasks(spec.background_tasks, ctx)
        ctx.background_resources.append(tasks)
        tools.extend(tasks.tools())
    servers = mcp_configuration(spec, ctx)
    if servers or spec.mcp_servers:
        # The official adapter is optional at import time and emits its documented beta warning.
        from langchain.mcp import MCPAdapter  # noqa: PLC0415

        if servers:
            async with MCPAdapter({"mcpServers": servers}) as adapter:
                tools.extend(await adapter.list_tools())
        for name in spec.mcp_servers:
            if name in ctx.mcp_targets:
                async with MCPAdapter(ctx.mcp_targets[name]) as adapter:
                    discovered = await adapter.list_tools()
                tools.extend(
                    tool
                    if name == "qmx-control"
                    else tool.model_copy(update={"name": f"{name}_{tool.name}"})
                    for tool in discovered
                )
        if "qmx-broker" in spec.mcp_servers:
            if ctx.broker is None and ctx.qmx_home is None:
                raise ValueError(
                    "qmx-broker requires the node's qmx_home or an injected BrokerService"
                )
            broker = ctx.broker or BrokerService(cast(Path, ctx.qmx_home))
            ctx.broker = broker
            async with MCPAdapter(create_broker_server(broker)) as adapter:
                broker_tools = await adapter.list_tools()
            tools.extend(tool for tool in broker_tools if tool.name != "propose_order")
            # Never trust a remote tool by name or annotations. Only the local
            # concrete writer receives the proposal exception in the barrier.
            tools.append(BrokerOrderProposalTool(service=broker))
    names = [tool.name for tool in tools]
    for tool in tools:
        check_tool(tool)
    if len(names) != len(set(names)):
        raise ValueError("Agent tool names must be unique")
    subagents: list[CompiledSubAgent | SubAgent] = []
    for reference in spec.subagents:
        if reference.ref is not None:
            path = reference.ref.resolve()
            if path in ancestors:
                raise ValueError(f"Cyclic sub-agent reference: {path}")
            child = load_spec(path)
            child_run = replace(
                ctx.run,
                subagent=child.model,
                workflow_id=ctx.run.workflow_id or ctx.run.session_id or uuid4().hex,
                task_id=ctx.run.task_id or uuid4().hex,
            )
            graph = await _build(
                child,
                replace(
                    ctx,
                    run=child_run,
                    memory_role="subagent",
                    memory=None,
                    backend=ctx.agent_backends.get(child.name, ctx.backend),
                ),
                (*ancestors, path),
            )
            subagents.append(
                CompiledSubAgent(
                    name=child.name, description=f"Delegate to {child.name}", runnable=graph
                )
            )
        else:
            workflow = reference.workflow
            if workflow is None:
                raise ValueError("Missing workflow reference")
            subagents.append(
                CompiledSubAgent(
                    name=workflow.rsplit("/", 1)[-1],
                    description=f"Run workflow {workflow}",
                    runnable=ctx.workflows[workflow],
                )
            )
    if len({item["name"] for item in subagents}) != len(subagents):
        raise ValueError("Sub-agent names must be unique")
    run = replace(ctx.run, agent_node=ctx.run.agent_node or spec.model)
    model = ctx.router.resolve_model(run, spec.name)
    memory = ctx.memory
    if memory is None and ctx.qmx_home is not None:
        profile = f"app:{run.app_id}" if run.app_id else "copilot"
        memory = MemoryManager(
            StoreMemoryProvider.from_home(ctx.qmx_home, profile, approval=ctx.memory_approval),
            load_provider(spec.memory.provider)
            if spec.memory.provider is not None and spec.memory.provider != "sqlite"
            else None,
            spill_dir=memory_path(ctx.qmx_home, profile).parent / "memory-recall",
            profile_cap=spec.memory.profile_cap,
            prefetch_cap=spec.memory.prefetch_cap,
            approval=ctx.memory_approval,
        )
        await memory.open(
            MemoryContext(
                profile=profile,
                role=ctx.memory_role,
                session_id=run.session_id,
                workflow_id=run.workflow_id,
                task_id=run.task_id,
            ),
            spec.memory.config,
        )
        # The composition root closes the run's memory manager after using its graph.
        ctx.memory = memory
        ctx.memory_resources.append(memory)
    memory_middleware: list[AgentMiddleware[Any, RunContext]] = []
    backend = ctx.backend
    if memory is not None:
        memory.spill_dir.mkdir(parents=True, exist_ok=True)
        backend = CompositeBackend(
            default=backend or StateBackend(),
            routes={
                "/memory-recall/": FilesystemBackend(
                    root_dir=memory.spill_dir.resolve(), virtual_mode=True
                )
            },
        )
        tools.extend(memory.tools(Scope(spec.memory.scope)))
        if spec.name == "copilot" and ctx.memory_role == "primary":
            tools.extend(
                tool.model_copy(update={"name": tool.name + "_global"})
                for tool in memory.tools(Scope.GLOBAL)
                if tool.name in {"memory_put", "memory_search"}
            )
        memory_middleware.extend(memory.middleware(Scope(spec.memory.scope)))
        memory_middleware.append(memory.summarization(model, backend))
    elif spec.memory.provider not in {None, "sqlite"}:
        raise ValueError("An external memory provider requires qmx_home or an opened MemoryManager")
    if len({tool.name for tool in tools}) != len(tools):
        raise ValueError("Agent tool names must be unique")
    for tool in tools:
        check_tool(tool)
    budget = ctx.budget or spec.budget
    control = ctx.control
    if control is None and ctx.qmx_home is not None:
        control = ControlService(ctx.qmx_home)
        ctx.control = control
    if control is not None and ctx.memory_role == "primary" and run.session_id is not None:
        watch_breakers(control, run.session_id)

    def guards(agent: str) -> list[AgentMiddleware[Any, RunContext]]:
        middleware: list[AgentMiddleware[Any, RunContext]] = []
        if ctx.journal:
            middleware.append(JournalMiddleware(ctx.journal, agent, run))
        middleware.extend(ctx.router.middleware(run, agent))
        if spec.name == "copilot":
            middleware.append(ContextEditingMiddleware())
        if agent == spec.name:
            middleware.extend(memory_middleware)
        middleware.extend([AdmissionStateMiddleware(), MoneyPathMiddleware()])
        middleware.append(
            AppHooksMiddleware(
                control, [tool.name for tool in tools], explicit_publish=ctx.explicit_publish
            )
        )
        if ctx.qmx_home is not None and "firecrawl" in servers:
            middleware.append(ResearchLibraryMiddleware(ControlService(ctx.qmx_home)))
        if budget.model_calls is not None:
            middleware.append(
                ModelCallLimitMiddleware(run_limit=budget.model_calls, exit_behavior="end")
            )
        if budget.tool_calls is not None:
            middleware.append(
                ToolCallLimitMiddleware(run_limit=budget.tool_calls, exit_behavior="error")
            )
        if ctx.journal and any(spec.interrupt_on.values()):
            middleware.append(JournalApprovals(ctx.journal, dict(spec.interrupt_on)))
        return middleware

    sandbox = ctx.backend if isinstance(ctx.backend, SandboxBackendProtocol) else None
    wrapper = AdmissionSandboxBackend if sandbox is not None else AdmissionBackend
    backend = wrapper(
        backend or StateBackend(),
        ctx.admission or AdmissionGate(ctx.journal),
        guarded_prefixes=(
            "/artifacts/",
            "/memories/" if spec.memory.scope == "global" else "/memories/global/",
        ),
        write=spec.permissions.write,
        deny_write=spec.permissions.deny_write,
    )
    if isinstance(backend, AdmissionSandboxBackend) and sandbox is not None:
        backend.execution = sandbox
    # The SDK's automatic general-purpose agent omits custom middleware. Give it
    # an explicit spec so delegation retains the same guards and finite budgets.
    effective = run.effective_models[spec.name]
    harness_profile: dict[str, Any] = {}
    model_name = str(getattr(model, "model_name", getattr(model, "model", "")))
    for key in (effective.split(":", 1)[0], effective, model_name):
        harness_profile.update(
            ctx.router.config.harness_profiles.get(key, {}).get("general_purpose_subagent", {})
        )
    if (
        ctx.general_purpose_subagent
        and harness_profile.get("enabled") is not False
        and not any(item["name"] == "general-purpose" for item in subagents)
    ):
        subagents.append(
            SubAgent(
                name="general-purpose",
                description=harness_profile.get(
                    "description", "Delegate an isolated research task"
                ),
                system_prompt=harness_profile.get(
                    "system_prompt", "Complete the assigned task and return a concise result."
                ),
                model=model,
                tools=tools,
                middleware=cast(
                    "list[AgentMiddleware[Any, Any]]", guards(f"{spec.name}/general-purpose")
                ),
                skills=spec.skills,
                permissions=spec.permissions.rules() if sandbox is None else [],
                interrupt_on={} if ctx.journal else dict(spec.interrupt_on),
            )
        )
    middleware = guards(spec.name)
    if not ctx.general_purpose_subagent:
        middleware.append(
            SubAgentMiddleware(backend=backend, subagents=subagents)
            if subagents
            else _NoDelegation()
        )
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=spec.system_prompt.read_text(encoding="utf-8"),
        middleware=middleware,
        subagents=subagents,
        skills=spec.skills or None,
        # Deep Agents cannot combine its filesystem permissions with execution.
        # The admission backend keeps file checks; the target owns execution isolation.
        permissions=spec.permissions.rules() if sandbox is None else [],
        backend=backend,
        interrupt_on=dict(spec.interrupt_on) or None,
        context_schema=RunContext,
        checkpointer=ctx.checkpointer,
        name=spec.name,
    )
