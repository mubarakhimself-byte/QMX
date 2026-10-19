"""The `qmx.workflow/1` document (SOLUTION-DESIGN 2.1 as 27d left it).

The stored document holds no `version`, `content_hash` or lifecycle field: the semver is a
Library annotation, the lifecycle is a ref fact, and the hash is computed (AD-11, AD-14).
Graph rules that carry their own error code (a keyed-join key, an explicit cartesian, a chunk
spec) live in `validate`, not here, so each failure names its code.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar, Literal, NamedTuple, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ModelWrapValidatorHandler,
    PrivateAttr,
    field_validator,
    model_validator,
)
from qma.harness import known_toolset

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
    required: bool = False
    """The target runs only when this edge carried output (AD-5 readiness, B-87)."""


type Connections = dict[str, dict[str, list[list[Target]]]]
"""Source node name, then output port, then lists of targets."""


class Retry(Strict):
    max_tries: int | None = Field(default=None, ge=1)
    backoff_seconds: list[int] | None = None
    retry_on: list[str] | None = None


class Legacy(Strict):
    """A part that drops fields older documents carried and QMX no longer has (AD-40). Each
    dropped field is named in `dropped`, so a run can say once that it was ignored."""

    _gone: ClassVar[frozenset[str]] = frozenset()
    _dropped: tuple[str, ...] = PrivateAttr(default=())

    @model_validator(mode="wrap")
    @classmethod
    def _drop(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        dropped: tuple[str, ...] = ()
        if isinstance(data, dict) and cls._gone:
            found = cast(dict[str, Any], data)
            dropped = tuple(sorted(cls._gone & found.keys()))
            data = {k: v for k, v in found.items() if k not in cls._gone}
        model = handler(data)
        model._dropped = dropped
        return model

    @property
    def dropped(self) -> tuple[str, ...]:
        return self._dropped


class Timeout(Legacy):
    """The stuck detector's windows (AD-16). No run timeout exists (AD-40)."""

    _gone: ClassVar[frozenset[str]] = frozenset({"run_seconds"})
    idle_seconds: int | None = Field(default=None, gt=0)
    in_tool_seconds: int | None = Field(default=None, gt=0)


class Limits(Strict):
    """Limits he wrote on a node; honoured as a pause (AD-16). No template ships one, and none
    exists by default. The lint refuses a value below 1."""

    tokens: int | None = None
    turns: int | None = None
    tool_calls: int | None = None


class RunLimits(Limits):
    """Limits he wrote on a workflow. `wall_seconds` counts active time only."""

    wall_seconds: int | None = None


type Merge = Literal["replace", "append", "keyed"]


class OutputFile(Strict):
    """A path an attempt commits from its overlay into the run's shared zone `work/` (AD-51).
    `path` is a glob relative to `work/`, and `<partition>` in it stands for the attempt's
    partition. `append` adds the attempt's bytes to the shared file and `keyed` merges a JSON
    object into it, so concurrent writers may share the path. `delete` is a tombstone: the
    matching shared files are removed at commit."""

    path: str
    merge: Merge = "replace"
    delete: bool = False


class Outputs(Strict):
    files: list[OutputFile] = Field(default_factory=list[OutputFile])


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
    limits: Limits | None = None
    runs_on: str | list[str] = "pc"
    credentials: dict[str, str] = Field(default_factory=dict[str, str])
    outputs: Outputs | None = Field(default=None, exclude_if=lambda value: value is None)
    """Left out of a dump when unset, so a node keeps the memo key it had before outputs."""
    toolsets: list[str] | None = Field(default=None, exclude_if=lambda value: value is None)
    """An `agent` node's QMX toolsets (AD-4, AD-62), checked references: a core toolset, or
    an `app:`, `mcp:` or `run:` one. The Surface turns them into the chat's tools; unset is
    none. Left out of a dump when unset, like `outputs`."""
    skills: list[str] | None = Field(default=None, exclude_if=lambda value: value is None)
    """An `agent` node's skills filter, by name or `plugin:skill`; unset is none."""
    disabled: bool = False
    notes: str | None = None

    @field_validator("toolsets")
    @classmethod
    def _known(cls, value: list[str] | None) -> list[str] | None:
        unknown = [name for name in value or [] if not known_toolset(name)]
        if unknown:
            raise ValueError(f"unknown toolsets {unknown}")
        return value


class Memory(Strict):
    scopes: list[str] = Field(default_factory=list[str])


class Settings(Legacy):
    _gone: ClassVar[frozenset[str]] = frozenset({"runaway"})
    timezone: str | None = None
    limits: RunLimits | None = None
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


def dropped(workflow: Workflow) -> list[str]:
    """The paths of fields the document carried that QMX no longer has, such as an old `runaway`
    block or a node's `timeout.run_seconds`."""
    found = [f"settings.{name}" for name in workflow.settings.dropped]
    for i, node in enumerate(workflow.nodes):
        if node.timeout is not None:
            found += [f"nodes[{i}].timeout.{name}" for name in node.timeout.dropped]
    return found


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
