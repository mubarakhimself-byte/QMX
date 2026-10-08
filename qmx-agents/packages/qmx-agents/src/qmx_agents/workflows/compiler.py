"""Compile authored graphs directly to LangGraph nodes, routers and barriers."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
from dataclasses import dataclass, field, replace
from pprint import pformat
from typing import Annotated, Any, TypedDict, cast

from deepagents import CompiledSubAgent
from jsonschema import Draft202012Validator
from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.graph.message import add_messages  # pyright: ignore[reportMissingTypeStubs]
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.types import Send, interrupt
from qmx_tools import DomainContext, default_tool_registry
from qmx_tools.service import Artifact, json_value

from qmx_agents.spec import BuildContext, build_agent, load_spec
from qmx_agents.workflows.models import Node, WorkflowSpec, load_graph


def merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {**left, **right}


class WorkflowState(TypedDict, total=False):
    inputs: dict[str, Any]
    values: Annotated[dict[str, Any], merge]
    routes: Annotated[dict[str, Any], merge]
    iterations: Annotated[dict[str, Any], merge]
    messages: Annotated[list[AnyMessage], add_messages]
    structured_response: dict[str, Any]
    phase: str


@dataclass
class Bindings:
    tools: dict[str, BaseTool] | None = None
    apps: dict[str, dict[str, BaseTool]] = field(default_factory=dict[str, dict[str, BaseTool]])
    agents: BuildContext | None = None
    workflows: dict[str, WorkflowSpec] = field(default_factory=dict[str, WorkflowSpec])
    artifacts: DomainContext = field(default_factory=DomainContext.from_environment)

    def registry(self) -> dict[str, BaseTool]:
        return self.tools if self.tools is not None else default_tool_registry(self.artifacts)


def pointer(value: Any, path: str) -> Any:
    if not path:
        return value
    if not path.startswith("/"):
        raise ValueError("Use a JSON Pointer beginning with / in templates")
    for token in path[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        value = cast("list[Any]", value)[int(key)] if isinstance(value, list) else value[key]
    return value


def template(value: Any, view: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        value = cast("dict[str, Any]", value)
        if "$input" in value:
            try:
                return pointer(view, value["$input"])
            except KeyError, IndexError, TypeError:
                if "default" in value:
                    return value["default"]
                raise ValueError(f"Template input {value['$input']} is unavailable") from None
        return {key: template(child, view) for key, child in value.items()}
    if isinstance(value, list):
        return [template(child, view) for child in cast("list[Any]", value)]
    return value


def input_view(spec: WorkflowSpec, node: Node, state: WorkflowState) -> dict[str, Any]:
    ports: dict[str, Any] = {}
    for name, port in node.inputs.items():
        values = [
            state.get("values", {})[edge.source.node][edge.source.port]
            for edge in spec.edges
            if edge.target.node == node.id
            and edge.target.port == name
            and edge.source.node in state.get("values", {})
        ]
        if values:
            for value in values:
                Draft202012Validator(port.json_schema).validate(value)  # pyright: ignore[reportUnknownMemberType] - upstream optional schema
            ports[name] = values if port.cardinality == "many" else values[0]
        elif port.required:
            raise ValueError(f"Required input {node.id}.{name} has no runtime value")
    return {"inputs": state.get("inputs", {}), "ports": ports, "values": state.get("values", {})}


def function(path: str) -> Any:
    module, _, name = path.rpartition(".")
    if not module:
        raise ValueError("Python nodes require a dotted module.function path")
    result = getattr(importlib.import_module(module), name)
    if not callable(result):
        raise ValueError(f"{path} is not callable")
    return result


def agent_context(
    bindings: Bindings,
    node: Node,
    spec: WorkflowSpec,
    checkpointer: BaseCheckpointSaver[Any] | None,
) -> BuildContext:
    if bindings.agents is None:
        raise ValueError("Agent nodes require a host BuildContext")
    return replace(
        bindings.agents,
        run=replace(bindings.agents.run, workflow_id=spec.name),
        checkpointer=checkpointer,
        general_purpose_subagent=node.general_purpose_subagent,
        memory=None,
        memory_role="headless",
        memory_resources=[],
    )


def node_action(
    spec: WorkflowSpec,
    node: Node,
    bindings: Bindings,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> RunnableLambda[Any, Any]:
    def prepare(state: WorkflowState) -> tuple[dict[str, Any], dict[str, Any]]:
        view = input_view(spec, node, state)
        args = cast("dict[str, Any]", template(node.args, view))
        return view, args

    def finish(state: WorkflowState, value: Any, view: dict[str, Any]) -> WorkflowState:
        result = json_value(value)
        outputs: dict[str, Any] = {}
        for name, port in node.outputs.items():
            item = pointer(result, port.select)
            Draft202012Validator(port.json_schema).validate(item)  # pyright: ignore[reportUnknownMemberType] - upstream optional schema
            outputs[name] = item
        update: WorkflowState = {"values": {node.id: outputs}}
        if node.kind == "condition":
            update["routes"] = {node.id: "true" if pointer(view, node.predicate or "") else "false"}
        elif node.kind == "loop":
            count = int(state.get("iterations", {}).get(node.id, 0))
            repeat = count < (node.max_iterations or 0)
            update["iterations"] = {node.id: count + 1 if repeat else count}
            update["routes"] = {node.id: "repeat" if repeat else "done"}
        return update

    def deterministic(view: dict[str, Any], args: dict[str, Any]) -> Any:
        if node.kind == "python":
            return function(node.function or "")(**args)
        if node.kind == "human_gate":
            return interrupt({"node": node.id, "prompt": node.prompt, "inputs": view["ports"]})
        return args or view["ports"]

    def sync(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
        view, args = prepare(state)
        if node.kind in {"tool", "app_call"}:
            tools = bindings.registry() if node.kind == "tool" else bindings.apps[node.app_id or ""]
            value = tools[node.tool or ""].invoke(args, config)
        elif node.kind == "agent":
            ctx = agent_context(bindings, node, spec, checkpointer)
            graph = asyncio.run(build_agent(load_spec(node.agent or ""), ctx))
            try:
                value = cast("Runnable[Any, Any]", graph).invoke(
                    args, config=config, context=ctx.run
                )
            finally:
                asyncio.run(ctx.close_memory())
        elif node.kind == "subworkflow":
            child = compile(bindings.workflows[node.workflow or ""], bindings=bindings)
            value = cast("Runnable[Any, Any]", child).invoke(args, config)
        else:
            value = deterministic(view, args)
            if inspect.isawaitable(value):
                raise ValueError("Async Python nodes must be called through ainvoke")
        return finish(state, value, view)

    async def async_action(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
        view, args = prepare(state)
        if node.kind in {"tool", "app_call"}:
            tools = bindings.registry() if node.kind == "tool" else bindings.apps[node.app_id or ""]
            value = await tools[node.tool or ""].ainvoke(args, config)
        elif node.kind == "agent":
            ctx = agent_context(bindings, node, spec, checkpointer)
            graph = await build_agent(load_spec(node.agent or ""), ctx)
            try:
                value = await cast("Runnable[Any, Any]", graph).ainvoke(
                    args, config=config, context=ctx.run
                )
            finally:
                await ctx.close_memory()
        elif node.kind == "subworkflow":
            child = compile(bindings.workflows[node.workflow or ""], bindings=bindings)
            value = await cast("Runnable[Any, Any]", child).ainvoke(args, config)
        else:
            value = (
                await asyncio.to_thread(deterministic, view, args)
                if node.kind == "python"
                else deterministic(view, args)
            )
            if inspect.isawaitable(value):
                value = await value
        return finish(state, value, view)

    return RunnableLambda(sync, afunc=async_action)


def router(spec: WorkflowSpec, node: Node) -> Any:
    edges = [edge for edge in spec.edges if edge.source.node == node.id]

    def route(state: WorkflowState) -> str | list[Send]:
        if node.kind == "parallel":
            return [Send(name, state) for name in dict.fromkeys(edge.target.node for edge in edges)]
        selected = state.get("routes", {})[node.id]
        return next(edge.target.node for edge in edges if edge.route == selected)

    return route


def finalize(spec: WorkflowSpec, bindings: Bindings) -> Any:
    def finish(state: WorkflowState) -> WorkflowState:
        if state.get("phase") == "cancelled":
            return {"phase": "cancelled"}
        ref = bindings.artifacts.save(
            Artifact(name=spec.name, kind="workflow-result", content=state.get("values", {}))
        )
        return {
            "phase": "completed",
            "structured_response": ref,
            "messages": [AIMessage(content=json.dumps(ref))],
        }

    return finish


def wiring(spec: WorkflowSpec) -> tuple[list[tuple[Any, str]], list[Node]]:
    nodes = {node.id: node for node in spec.nodes}
    edges: list[tuple[Any, str]] = [(START, spec.entry)]
    routed = [node for node in spec.nodes if node.kind in {"condition", "parallel", "loop"}]
    joins = {node.id for node in spec.nodes if node.kind == "join"}
    for join in joins:
        sources = list(
            dict.fromkeys(edge.source.node for edge in spec.edges if edge.target.node == join)
        )
        if any(nodes[name].kind in {"condition", "loop", "parallel"} for name in sources):
            raise ValueError("A join barrier needs branch terminal nodes, not routing nodes")
        if sources:
            edges.append((sources, join))
    ordinary = {
        (edge.source.node, edge.target.node)
        for edge in spec.edges
        if nodes[edge.source.node].kind not in {"condition", "parallel", "loop"}
        and edge.target.node not in joins
    }
    edges.extend(sorted(ordinary))
    leaves = [
        node.id
        for node in spec.nodes
        if not any(edge.source.node == node.id for edge in spec.edges)
    ]
    edges.extend((name, "__finish__") for name in leaves)
    edges.append(("__finish__", END))
    return edges, routed


def compile(
    spec: WorkflowSpec,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
    *,
    bindings: Bindings | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    spec = load_graph(spec.model_dump(mode="json", by_alias=True))
    bindings = bindings or Bindings()
    builder = StateGraph(WorkflowState)
    for node in spec.nodes:
        builder.add_node(node.id, node_action(spec, node, bindings, checkpointer))  # pyright: ignore[reportUnknownMemberType] - upstream cache generic
    builder.add_node("__finish__", finalize(spec, bindings), defer=True)  # pyright: ignore[reportUnknownMemberType] - upstream cache generic
    edges, routed = wiring(spec)
    for source, target in edges:
        builder.add_edge(source, target)
    for node in routed:
        builder.add_conditional_edges(
            node.id,
            router(spec, node),
            list(
                dict.fromkeys(
                    edge.target.node for edge in spec.edges if edge.source.node == node.id
                )
            ),
        )
    graph = builder.compile(checkpointer=checkpointer)  # pyright: ignore[reportUnknownMemberType] - upstream saver/cache generics
    return graph.with_config(
        {
            "recursion_limit": len(spec.nodes)
            * (2 + sum(node.max_iterations or 0 for node in spec.nodes))
            + 5
        }
    )


def as_subagent(
    spec: WorkflowSpec,
    *,
    bindings: Bindings | None = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledSubAgent:
    graph = compile(spec, checkpointer, bindings=bindings)

    def prepare(state: dict[str, Any]) -> WorkflowState:
        request = state["messages"][-1].content
        try:
            inputs = json.loads(request)
        except json.JSONDecodeError, TypeError:
            inputs = {"request": request}
        if not isinstance(inputs, dict):
            inputs = {"request": inputs}
        return {"inputs": inputs, "messages": state["messages"]}

    return CompiledSubAgent(
        name=spec.name,
        description=f"Run workflow {spec.name}; returns an artifact reference",
        runnable=RunnableLambda(prepare) | graph,
    )


def to_python(spec: WorkflowSpec) -> str:
    """Emit editable graph wiring while sharing the node execution semantics."""
    edges, routed = wiring(spec)
    lines = [
        "from langgraph.graph import StateGraph",
        "from qmx_agents.workflows import Bindings, load_graph",
        "from qmx_agents.workflows.compiler import WorkflowState, node_action, router, finalize",
        "",
        "spec = load_graph(\n"
        + pformat(spec.model_dump(mode="json", by_alias=True), sort_dicts=False, width=88)
        + "\n)",
        "",
        "def build(bindings=None, checkpointer=None):",
        "    bindings = bindings or Bindings()",
        "    builder = StateGraph(WorkflowState)",
    ]
    for index, node in enumerate(spec.nodes):
        lines.append(
            f"    builder.add_node({node.id!r}, "
            f"node_action(spec, spec.nodes[{index}], bindings, checkpointer))"
        )
    lines.append("    builder.add_node('__finish__', finalize(spec, bindings), defer=True)")
    for source, target in edges:
        lines.append(f"    builder.add_edge({source!r}, {target!r})")
    for node in routed:
        index = spec.nodes.index(node)
        targets = list(
            dict.fromkeys(edge.target.node for edge in spec.edges if edge.source.node == node.id)
        )
        lines.append(
            f"    builder.add_conditional_edges({node.id!r}, "
            f"router(spec, spec.nodes[{index}]), {targets!r})"
        )
    limit = len(spec.nodes) * (2 + sum(node.max_iterations or 0 for node in spec.nodes)) + 5
    lines.append(
        "    return builder.compile(checkpointer=checkpointer)"
        f".with_config({{'recursion_limit': {limit}}})"
    )
    return "\n".join(lines) + "\n"
