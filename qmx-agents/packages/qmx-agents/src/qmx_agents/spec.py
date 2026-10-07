"""Parse AgentSpecs and compile their named tools and sub-agents with Deep Agents."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import yaml
from deepagents import (
    CompiledSubAgent,
    FilesystemPermission,
    create_deep_agent,  # pyright: ignore[reportUnknownVariableType] - upstream generic overload
)
from deepagents.backends.protocol import BackendProtocol
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qmx_agents.router import ModelRouter, RunContext, model_selector


class MemorySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["task", "workflow", "session", "global"] = "task"


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


def load_spec(path: str | Path) -> AgentSpec:
    source = Path(path).resolve()
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
    tools: dict[str, BaseTool] = field(default_factory=dict[str, BaseTool])
    workflows: dict[str, Runnable[Any, Any]] = field(default_factory=dict[str, Runnable[Any, Any]])
    backend: BackendProtocol | None = None
    checkpointer: BaseCheckpointSaver[Any] | None = None


async def build_agent(
    spec: AgentSpec, ctx: BuildContext
) -> CompiledStateGraph[Any, RunContext, Any, Any]:
    """Await discovery once; invoke MCP graphs asynchronously on the same loop."""
    return await _build(spec, ctx, ())


async def _build(
    spec: AgentSpec, ctx: BuildContext, ancestors: tuple[Path, ...]
) -> CompiledStateGraph[Any, RunContext, Any, Any]:
    if spec.background_tasks:
        raise NotImplementedError("background_tasks require the qmx-control task tools (P11)")
    if any(spec.interrupt_on.values()) and ctx.checkpointer is None:
        raise ValueError("interrupt_on requires a checkpointer")
    tools = [ctx.tools[name] for name in spec.tools]
    if spec.mcp_servers:
        # The official adapter is optional at import time and emits its documented beta warning.
        from langchain.mcp import MCPAdapter  # noqa: PLC0415

        servers = {name: ctx.router.config.mcp_servers[name] for name in spec.mcp_servers}
        async with MCPAdapter({"mcpServers": servers}) as adapter:
            tools.extend(await adapter.list_tools())
    names = [tool.name for tool in tools]
    if len(names) != len(set(names)):
        raise ValueError("Agent tool names must be unique")
    subagents: list[CompiledSubAgent] = []
    for reference in spec.subagents:
        if reference.ref is not None:
            path = reference.ref.resolve()
            if path in ancestors:
                raise ValueError(f"Cyclic sub-agent reference: {path}")
            child = load_spec(path)
            child_run = replace(ctx.run, subagent=child.model)
            graph = await _build(child, replace(ctx, run=child_run), (*ancestors, path))
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
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=spec.system_prompt.read_text(encoding="utf-8"),
        middleware=ctx.router.middleware(run, spec.name),
        subagents=subagents,
        skills=spec.skills or None,
        permissions=spec.permissions.rules(),
        backend=ctx.backend,
        interrupt_on=dict(spec.interrupt_on) or None,
        context_schema=RunContext,
        checkpointer=ctx.checkpointer,
        name=spec.name,
    )
