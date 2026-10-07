"""The editor's versioned graph and the legacy topology/port refusal rules."""

from __future__ import annotations

import json
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, model_validator

Kind = Literal[
    "python",
    "agent",
    "tool",
    "app_call",
    "condition",
    "parallel",
    "join",
    "loop",
    "human_gate",
    "subworkflow",
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Port(Model):
    kind: Literal["reference", "data", "event", "control"] = "data"
    cardinality: Literal["one", "many"] = "one"
    json_schema: dict[str, Any] = Field(default_factory=dict[str, Any], alias="schema")
    select: str = ""
    required: bool = False

    @model_validator(mode="after")
    def valid_schema(self) -> Port:
        Draft202012Validator.check_schema(self.json_schema)
        reject_external_refs(self.json_schema)
        if self.select and not self.select.startswith("/"):
            raise ValueError("Port select must be a JSON Pointer beginning with /")
        return self


def reject_external_refs(value: Any) -> None:
    if isinstance(value, dict):
        value = cast("dict[str, Any]", value)
        for key, child in value.items():
            if key in {"$ref", "$dynamicRef"} and not str(child).startswith("#"):
                raise ValueError(
                    "Port schemas must use local references; remote resolution is disabled"
                )
            reject_external_refs(child)
    elif isinstance(value, list):
        for child in cast("list[Any]", value):
            reject_external_refs(child)


REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "python": ("function",),
    "agent": ("agent",),
    "tool": ("tool",),
    "app_call": ("app_id", "tool"),
    "condition": ("predicate",),
    "loop": ("max_iterations",),
    "subworkflow": ("workflow",),
}


def node_schema(schema: dict[str, Any]) -> None:
    schema["allOf"] = [
        {
            "if": {"properties": {"kind": {"const": kind}}, "required": ["kind"]},
            "then": {
                "required": list(fields),
                "properties": {
                    name: {"type": "integer", "minimum": 1}
                    if name == "max_iterations"
                    else {"type": "string", "minLength": 1}
                    for name in fields
                },
            },
        }
        for kind, fields in REQUIREMENTS.items()
    ]


class Node(Model):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, json_schema_extra=node_schema)
    id: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    kind: Kind
    inputs: dict[str, Port] = Field(default_factory=dict[str, Port])
    outputs: dict[str, Port] = Field(default_factory=lambda: {"result": Port()})
    args: dict[str, Any] = Field(default_factory=dict[str, Any])
    function: str | None = None
    agent: str | None = None
    tool: str | None = None
    app_id: str | None = None
    workflow: str | None = None
    predicate: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=1000)
    prompt: str = "Approve this workflow step"
    general_purpose_subagent: bool = False

    @model_validator(mode="after")
    def requirements(self) -> Node:
        for name in REQUIREMENTS.get(self.kind, ()):
            if not getattr(self, name):
                raise ValueError(f"{self.kind} node {self.id} requires {name}")
        if self.predicate and not self.predicate.startswith("/"):
            raise ValueError("predicate must be a JSON Pointer into the node's inputs")
        return self


class Endpoint(Model):
    node: str
    port: str


class Edge(Model):
    source: Endpoint
    target: Endpoint
    mapping: Literal["one", "zip", "broadcast", "keyed-join", "cartesian"]
    cartesian: bool = False
    route: Literal["true", "false", "repeat", "done"] | None = None


def compatible(source: dict[str, Any], target: dict[str, Any]) -> bool:
    """Conservative structural check; the complete schemas also validate at runtime."""
    if not target or source == target:
        return True
    if "const" in target and source.get("const") != target["const"]:
        return False
    if "enum" in target and (
        "enum" not in source or any(item not in target["enum"] for item in source["enum"])
    ):
        return False
    source_type = source.get("type")
    target_type = target.get("type")
    if target_type:
        sources = set(
            cast("list[str]", source_type) if isinstance(source_type, list) else [source_type]
        )
        targets = set(
            cast("list[str]", target_type) if isinstance(target_type, list) else [target_type]
        )
        if "number" in targets:
            targets.add("integer")
        if not sources <= targets:
            return False
    if target_type == "object":
        for name in target.get("required", []):
            if name not in source.get("required", []):
                return False
        for name, schema in source.get("properties", {}).items():
            if name in target.get("properties", {}) and not compatible(
                schema, target["properties"][name]
            ):
                return False
            if not compatible(
                source.get("properties", {}).get(name, {}),
                target.get("properties", {}).get(name, {}),
            ):
                return False
    return target_type != "array" or compatible(source.get("items", {}), target.get("items", {}))


class WorkflowSpec(Model):
    version: Literal["workflow.v1"] = "workflow.v1"
    name: str = Field(min_length=1)
    entry: str
    nodes: list[Node] = Field(min_length=1)
    edges: list[Edge] = Field(default_factory=list[Edge])

    @model_validator(mode="after")
    def topology(self) -> WorkflowSpec:
        nodes = {node.id: node for node in self.nodes}
        if len(nodes) != len(self.nodes):
            raise ValueError("Node IDs must be unique")
        if self.entry not in nodes:
            raise ValueError("entry must name an existing node")
        adjacency: dict[str, list[str]] = {name: [] for name in nodes}
        acyclic: dict[str, list[str]] = {name: [] for name in nodes}
        seen: set[tuple[str, str, str, str]] = set()
        bindings: set[tuple[str, str]] = set()
        for edge in self.edges:
            src, dst = edge.source, edge.target
            if src.node not in nodes or dst.node not in nodes:
                raise ValueError("Edge references an unknown node")
            if src.port not in nodes[src.node].outputs or dst.port not in nodes[dst.node].inputs:
                raise ValueError("Edge references an unknown port")
            key = (src.node, src.port, dst.node, dst.port)
            if key in seen:
                raise ValueError("Duplicate edge")
            seen.add(key)
            bindings.add((dst.node, dst.port))
            output, input_port = nodes[src.node].outputs[src.port], nodes[dst.node].inputs[dst.port]
            if output.kind != input_port.kind or not compatible(
                output.json_schema, input_port.json_schema
            ):
                raise ValueError(
                    f"Port types do not match: {src.node}.{src.port} -> {dst.node}.{dst.port}"
                )
            if edge.mapping == "cartesian" and not edge.cartesian:
                raise ValueError("Cartesian mapping requires cartesian: true")
            if (
                output.cardinality == "many"
                and input_port.cardinality == "one"
                and edge.mapping
                not in {
                    "one",
                    "zip",
                    "keyed-join",
                    "cartesian",
                }
            ):
                raise ValueError("many -> one requires an explicit reducing mapping")
            if (
                output.cardinality == "one"
                and input_port.cardinality == "many"
                and edge.mapping
                not in {
                    "broadcast",
                    "cartesian",
                }
            ):
                raise ValueError("one -> many requires broadcast or cartesian mapping")
            kind = nodes[src.node].kind
            allowed = {"condition": {"true", "false"}, "loop": {"repeat", "done"}}
            if kind in allowed and edge.route not in allowed[kind]:
                raise ValueError(f"{kind} edges require a route from {allowed[kind]}")
            if kind not in allowed and edge.route is not None:
                raise ValueError("Only condition and loop nodes accept routed edges")
            adjacency[src.node].append(dst.node)
            if not (kind == "loop" and edge.route == "repeat"):
                acyclic[src.node].append(dst.node)
        for node in self.nodes:
            for name, port in node.inputs.items():
                if port.required and (node.id, name) not in bindings:
                    raise ValueError(f"Required input {node.id}.{name} has no edge")
                incoming = [
                    edge
                    for edge in self.edges
                    if edge.target.node == node.id and edge.target.port == name
                ]
                if port.cardinality == "one" and len(incoming) > 1:
                    raise ValueError(
                        "A one input port needs a single binding; "
                        "use distinct ports or cardinality many"
                    )
            if node.kind in {"condition", "loop"}:
                routes = [edge.route for edge in self.edges if edge.source.node == node.id]
                expected = {"true", "false"} if node.kind == "condition" else {"repeat", "done"}
                if len(routes) != 2 or set(routes) != expected:
                    raise ValueError(f"{node.kind} requires exactly one edge per route")
        reached: set[str] = set()

        def reach(name: str) -> None:
            if name not in reached:
                reached.add(name)
                for child in adjacency[name]:
                    reach(child)

        reach(self.entry)
        if reached != set(nodes):
            raise ValueError("Every node must be reachable from entry")
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(name: str) -> None:
            if name in temporary:
                raise ValueError("Cycle requires a bounded loop repeat edge")
            if name in permanent:
                return
            temporary.add(name)
            for child in acyclic[name]:
                visit(child)
            temporary.remove(name)
            permanent.add(name)

        for name in nodes:
            visit(name)
        return self


def load_graph(document: str | dict[str, Any]) -> WorkflowSpec:
    return WorkflowSpec.model_validate(
        json.loads(document) if isinstance(document, str) else document
    )
