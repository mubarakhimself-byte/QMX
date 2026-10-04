"""Finite host-authored behavior catalog. Definitions never confer grants."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

from qma.daemon.taskgraph.compiler import GraphTemplateCatalog
from qma.daemon.taskgraph.records import GraphTemplate
from qmf.core import is_refusal


def canonical(value: object) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > 32768:
        raise ValueError("bounded nonempty host text required")
    return value


def _node_id(value: object) -> str:
    text = _text(value)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", text) is None:
        raise ValueError("workflow step requires a bounded graph node name")
    return text


def _items(value: object, maximum: int = 16) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError("bounded nonempty catalog array required")
    items = cast("list[Any]", value)
    if not 1 <= len(items) <= maximum:
        raise ValueError("bounded nonempty catalog array required")
    return items


def _object(value: object, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("unsupported host catalog fields")
    raw = cast("dict[object, object]", value)
    if any(not isinstance(key, str) for key in raw) or set(raw) - fields:
        raise ValueError("unsupported host catalog fields")
    return cast("dict[str, Any]", raw)


def _names(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("bounded catalog names required")
    raw = cast("list[object]", value)
    if len(raw) > 16:
        raise ValueError("bounded catalog names required")
    names = tuple(_text(item) for item in raw)
    if len(set(names)) != len(names):
        raise ValueError("duplicate catalog names")
    return names


def _limit(value: Any, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError("bounded positive host budget required")
    return value


@dataclass(frozen=True)
class ActorRole:
    role_id: str
    version: str
    instructions: str
    tools: tuple[str, ...]
    max_model_calls: int
    max_tool_calls: int

    @property
    def key(self) -> str:
        return f"{self.role_id}:{self.version}"


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    kind: str
    role: str | None = None
    tool: str | None = None
    arguments_json: str = "{}"


@dataclass(frozen=True)
class ActorWorkflow:
    workflow_id: str
    version: str
    steps: tuple[WorkflowStep, ...]
    author: str | None = None
    edges_json: str | None = None
    operations_json: str | None = None

    @property
    def graph_sha256(self) -> str | None:
        if self.author is None:
            return None
        return digest(
            {
                "id": self.workflow_id,
                "version": self.version,
                "author": self.author,
                "steps": [asdict(s) for s in self.steps],
                "edges": json.loads(self.edges_json or "[]"),
                "operations": json.loads(self.operations_json or "{}"),
            }
        )

    def template(self) -> GraphTemplate:
        if self.author is None:
            raise ValueError("authored graph binding required")
        has_agent = any(s.kind == "agent" for s in self.steps)
        return GraphTemplate(
            self.workflow_id,
            self.version,
            tuple(
                {
                    "id": s.step_id,
                    "kind": (
                        "agent"
                        if s.kind == "agent"
                        else "task"
                        if not has_agent and s == self.steps[-1]
                        else "join"
                        if s.kind == "collect"
                        else "artifact_dependency"
                        if s.kind == "read"
                        else "deterministic_script"
                    ),
                    "binding": asdict(s),
                    "graph_sha256": self.graph_sha256,
                }
                for s in self.steps
            ),
            tuple(json.loads(self.edges_json or "[]")),
        )

    @property
    def key(self) -> str:
        return f"{self.workflow_id}:{self.version}"


@dataclass(frozen=True)
class ActorRoute:
    profile_id: str
    actor_id: str
    workflow: str
    tools: tuple[str, ...]


@dataclass(frozen=True)
class ActorCatalog:
    roles: tuple[ActorRole, ...]
    workflows: tuple[ActorWorkflow, ...]
    routes: tuple[ActorRoute, ...]
    max_children: int
    max_depth: int
    max_model_calls: int

    @property
    def identity(self) -> str:
        payload = asdict(self)
        payload["workflows"] = [workflow_payload(flow) for flow in self.workflows]
        return digest(payload)

    def role(self, key: str) -> ActorRole:
        return next(role for role in self.roles if role.key == key)

    def workflow(self, key: str) -> ActorWorkflow:
        return next(flow for flow in self.workflows if flow.key == key)


def _duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate host catalog field")
        result[key] = value
    return result


def load_actor_catalog(root: Path) -> ActorCatalog | None:
    path = root / "actor-workflows.json"
    if not path.exists():
        return None
    if path.stat().st_size > 131072:
        raise ValueError("actor catalog exceeds host byte budget")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_duplicates)
        row = _object(data, {"roles", "workflows", "routes", "limits"})
        limits = _object(row["limits"], {"max_children", "max_depth", "max_model_calls"})
        children = _limit(limits["max_children"], 8)
        depth = _limit(limits["max_depth"], 1)  # finite leaf delegation; no recursion
        calls = _limit(limits["max_model_calls"], 32)
        roles: list[ActorRole] = []
        for raw_item in _items(row["roles"]):
            item = _object(
                raw_item,
                {"id", "version", "instructions", "tools", "max_model_calls", "max_tool_calls"},
            )
            roles.append(
                ActorRole(
                    _text(item["id"]),
                    _text(item["version"]),
                    _text(item["instructions"]),
                    _names(item["tools"]),
                    _limit(item["max_model_calls"], 8),
                    _limit(item["max_tool_calls"], 8),
                )
            )
        workflows: list[ActorWorkflow] = []
        for raw_item in _items(row["workflows"]):
            item = _object(raw_item, {"id", "version", "steps", "graph"})
            steps: list[WorkflowStep] = []
            for raw_step in _items(item["steps"], 12):
                step = _object(raw_step, {"id", "kind", "role", "tool", "arguments"})
                kind = step["kind"]
                if kind not in {"normalize", "agent", "read", "collect"}:
                    raise ValueError("only installed finite workflow steps are supported")
                if (kind == "agent") != ("role" in step) or (kind == "read") != ("tool" in step):
                    raise ValueError("step kind requires its exact host binding")
                if "arguments" in step and (
                    kind != "read" or not isinstance(step["arguments"], dict)
                ):
                    raise ValueError("read step requires data arguments")
                steps.append(
                    WorkflowStep(
                        _node_id(step["id"]),
                        kind,
                        _text(step["role"]) if "role" in step else None,
                        _text(step["tool"]) if "tool" in step else None,
                        json.dumps(step.get("arguments", {}), sort_keys=True, allow_nan=False),
                    )
                )
            if not 1 <= len(steps) <= 12 or len({s.step_id for s in steps}) != len(steps):
                raise ValueError("finite unique steps required")
            flow = ActorWorkflow(_text(item["id"]), _text(item["version"]), tuple(steps))
            if "graph" in item:
                if sum(s.kind == "agent" for s in steps) > 1:
                    raise ValueError("bounded authored adapter admits one inference specialist")
                graph = _object(item["graph"], {"author", "edges", "sha256", "operations"})
                raw_edges = graph["edges"]
                if not isinstance(raw_edges, list) or len(cast("list[object]", raw_edges)) > 11:
                    raise ValueError("bounded authored edges required")
                edges = [
                    _object(edge, {"from", "to", "mapping", "from_port", "to_port"})
                    for edge in cast("list[object]", raw_edges)
                ]
                operations = _object(
                    graph.get("operations", {}), {s.step_id for s in steps if s.kind == "read"}
                )
                if set(operations) != {s.step_id for s in steps if s.kind == "read"}:
                    raise ValueError("every authored read requires an exact operation/version pin")
                for operation in operations.values():
                    pin = _object(operation, {"op_id", "version"})
                    _text(pin["op_id"])
                    _limit(pin["version"], 2147483647)
                flow = ActorWorkflow(
                    flow.workflow_id,
                    flow.version,
                    flow.steps,
                    _text(graph["author"]),
                    json.dumps(edges, sort_keys=True),
                    json.dumps(operations, sort_keys=True),
                )
                validated = GraphTemplateCatalog().register(flow.template())
                if is_refusal(validated):
                    raise ValueError("authored topology refused")
                # The first adapter admits only explicit one-to-one paths. No
                # implicit ordering, collection fanout, branch or join semantics.
                expected = [(a.step_id, b.step_id) for a, b in pairwise(steps)]
                if (
                    len(edges) != len(expected)
                    or [(e.get("from"), e.get("to")) for e in edges] != expected
                ):
                    raise ValueError(
                        "authored path requires one explicit predecessor; ambiguous join refused"
                    )
                for edge in edges:
                    if (
                        set(edge) != {"from", "to", "mapping", "from_port", "to_port"}
                        or edge["mapping"] != "one"
                        or edge["from_port"] != "data"
                        or edge["to_port"] != "data"
                    ):
                        raise ValueError("authored adapter requires one data value per predecessor")
                if "sha256" in graph and graph["sha256"] != flow.graph_sha256:
                    raise ValueError("stale authored graph digest")
            workflows.append(flow)
        routes: list[ActorRoute] = []
        for raw_item in _items(row["routes"]):
            item = _object(raw_item, {"profile_id", "actor_id", "workflow", "tools"})
            routes.append(
                ActorRoute(
                    _text(item["profile_id"]),
                    _text(item["actor_id"]),
                    _text(item["workflow"]),
                    _names(item["tools"]),
                )
            )
        catalog = ActorCatalog(
            tuple(roles), tuple(workflows), tuple(routes), children, depth, calls
        )
        if not all(1 <= len(items) <= 16 for items in (roles, workflows, routes)):
            raise ValueError("bounded nonempty host catalog required")
        if (
            len({r.key for r in roles}) != len(roles)
            or len({w.key for w in workflows}) != len(workflows)
            or len({r.profile_id for r in routes}) != len(routes)
        ):
            raise ValueError("catalog identities must be unique")
        for route in routes:
            if not route.actor_id.startswith("quant:"):
                raise ValueError("persistent Quant identity required")
            flow = catalog.workflow(route.workflow)
            agents = [s for s in flow.steps if s.kind == "agent"]
            if (
                len(agents) > children
                or sum(catalog.role(s.role or "").max_model_calls for s in agents) > calls
            ):
                raise ValueError("workflow exceeds host child/model budgets")
            if any(s.kind == "read" and s.tool not in route.tools for s in flow.steps):
                raise ValueError("workflow read cannot widen the parent tool ceiling")
            if any(set(catalog.role(s.role or "").tools) - set(route.tools) for s in agents):
                raise ValueError("child role cannot widen the parent tool ceiling")
        return catalog
    except (KeyError, TypeError, StopIteration, UnicodeError, RecursionError) as exc:
        raise ValueError("invalid actor catalog") from exc


def workflow_payload(flow: ActorWorkflow) -> dict[str, Any]:
    """Preserve all pre-authored catalog, definition and memory source hashes."""
    payload = asdict(flow)
    if flow.author is None:
        for field in ("author", "edges_json", "operations_json"):
            payload.pop(field)
    return payload


def parse_graph_job_data(model_output: str) -> dict[str, Any]:
    row = _object(
        json.loads(model_output, object_pairs_hook=_duplicates),
        {"workflow", "graph_sha256", "goal"},
    )
    if set(row) != {"workflow", "graph_sha256", "goal"}:
        raise ValueError("proposal requires exact graph/job fields")
    _text(row["goal"])
    return row


def require_host_text(value: object) -> str:
    return _text(value)
