"""The `qmx.workflow/1` document (SOLUTION-DESIGN 2.1 as 27d left it).

The stored document holds no `version`, `content_hash` or lifecycle field: the semver is a
Library annotation, the lifecycle is a ref fact, and the hash is computed (AD-11, AD-14).
Graph rules that carry their own error code (a keyed-join key, an explicit cartesian, a chunk
spec) live in `validate`, not here, so each failure names its code.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from qmx_engine.definition.registry import Effect

type EdgeMap = Literal["one", "zip", "broadcast", "chunk", "keyed-join", "cartesian"]
type JsonObject = dict[str, JsonValue]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class Chunk(Strict):
    by: Literal["items", "tokens"]
    size: int | None = Field(default=None, gt=0)
    fill: float | None = Field(default=None, gt=0, le=1)


class Target(Strict):
    node: str
    port: str
    map: EdgeMap
    key: str | None = None
    explicit: bool = False
    chunk: Chunk | None = None


type Connections = dict[str, dict[str, list[list[Target]]]]
"""Source node name, then output port, then lists of targets."""


class Retry(Strict):
    max_tries: int | None = Field(default=None, ge=1)
    backoff_seconds: list[int] | None = None
    retry_on: list[str] | None = None


class Timeout(Strict):
    run_seconds: int | None = Field(default=None, gt=0)
    idle_seconds: int | None = Field(default=None, gt=0)


class Node(Strict):
    id: str
    name: str
    type: str
    type_version: int = Field(alias="typeVersion")
    position: tuple[float, float] | None = None
    parameters: JsonObject = Field(default_factory=dict[str, JsonValue])
    role: str | None = None
    effect: Effect | None = None
    retry: Retry | None = None
    timeout: Timeout | None = None
    runs_on: str | list[str] = "pc"
    credentials: dict[str, str] = Field(default_factory=dict[str, str])
    disabled: bool = False
    notes: str | None = None


class Runaway(Strict):
    """The runaway guard (AD-16). It has no USD field, so a definition cannot name a spend cap."""

    tokens: int | None = Field(default=None, gt=0)
    agents: int | None = Field(default=None, gt=0)
    tool_calls: int | None = Field(default=None, gt=0)
    wall_seconds: int | None = Field(default=None, gt=0)
    on_runaway: Literal["pause", "degrade"] | None = None


class Memory(Strict):
    scopes: list[str] = Field(default_factory=list[str])


class Settings(Strict):
    timezone: str | None = None
    runaway: Runaway | None = None
    on_error: str | None = None
    error_workflow: str | None = None
    caller_policy: Literal["any", "workflows_only", "none"] | None = None
    inline_limit_bytes: int | None = Field(default=None, gt=0)
    memory: Memory | None = None
    claude_workflow_enabled: bool = False


class Patch(Strict):
    """One RFC 6902 operation. Only `add`, `remove` and `replace` are part of the format."""

    op: Literal["add", "remove", "replace"]
    path: str
    value: JsonValue = None


class Extends(Strict):
    workflow_item: str
    object_id: str
    patches: list[Patch] = Field(default_factory=list[Patch])


type Need = Literal[
    "trading-node",
    "risk-session",
    "broker-read-token",
    "qmb-door",
    "real-library",
    "rlm",
    "sandbox",
    "app-op",
]
"""A piece of QMX a template waits for (ENGINE-PLAN Appendix I). A workflow that names one
validates and stays a draft: its test run and its enable are refused with the need named."""


class Meta(BaseModel):
    """Layout and authorship, outside the content hash. Any other key is kept as written."""

    model_config = ConfigDict(extra="allow", frozen=True)

    needs: list[Need] = Field(default_factory=list[Need])


class Workflow(Strict):
    schema_: Literal["qmx.workflow/1"] = Field(alias="schema")
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    extends: Extends | None = None
    inputs: JsonObject = Field(default_factory=dict[str, JsonValue])
    outputs: JsonObject = Field(default_factory=dict[str, JsonValue])
    settings: Settings = Field(default_factory=Settings)
    nodes: list[Node]
    connections: Connections = Field(default_factory=dict[str, dict[str, list[list[Target]]]])
    pin_data: dict[str, dict[str, list[JsonValue]]] | None = Field(default=None, alias="pinData")
    meta: Meta = Field(default_factory=Meta)


def json_schema() -> dict[str, JsonValue]:
    """The schema shipped as `schema/qmx.workflow.1.json`, for editors and other tools."""
    return Workflow.model_json_schema(by_alias=True)


class Edge(NamedTuple):
    path: str
    source: str
    port: str
    target: Target


def edges(workflow: Workflow) -> Iterator[Edge]:
    for source, ports in workflow.connections.items():
        for port, lists in ports.items():
            for i, targets in enumerate(lists):
                for j, target in enumerate(targets):
                    yield Edge(f"connections.{source}.{port}[{i}][{j}]", source, port, target)
