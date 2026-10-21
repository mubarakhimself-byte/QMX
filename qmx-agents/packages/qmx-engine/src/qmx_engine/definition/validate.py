"""SOLUTION-DESIGN 2.4 steps 1 to 5: schema, graph, names, lint, and the draft-only allowances.

`validate` returns every problem it finds as `(code, path, message)`, never the first alone, so an
editor can mark them all at once. An empty list means the folder is in the `validated` state.
"""

from __future__ import annotations

import ast
import json
from collections import defaultdict
from collections.abc import Collection, Iterator, Sequence
from itertools import combinations
from pathlib import Path, PurePosixPath
from typing import Final

from pydantic import BaseModel, JsonValue, ValidationError

from qmx_engine.core.joins import JoinSpec
from qmx_engine.core.loops import LoopSpec
from qmx_engine.core.waits import WaitSpec
from qmx_engine.definition.expr import RuleRefused, check
from qmx_engine.definition.folder import DEFINITION, Problem, WorkflowFolder, load
from qmx_engine.definition.lint import lint, redact
from qmx_engine.definition.model import Edge, Node, OutputFile, Workflow, edges
from qmx_engine.definition.registry import LOOP_BACK_PORT, NOTE, REGISTRY, Kind, Registry, RoleRule
from qmx_engine.settings import DEFAULTS

PLACEMENTS: Final = frozenset({"pc", "contabo", "qmb"})
STAGING: Final = ".staging"
"""The folder under a run's `work/` where commits are staged; no declared output may touch it."""
NOT_ROLES: Final = frozenset({"test_only", "test_order", "live_order"})
DEFAULT_ROLES: Final = frozenset(
    role
    for key in DEFAULTS
    if key.startswith("roles.") and (role := key.removeprefix("roles.")) not in NOT_ROLES
)
SPECS: Final[dict[str, type[BaseModel]]] = {"loop": LoopSpec, "join": JoinSpec, "wait": WaitSpec}
"""The kinds whose parameters the core parses; validation parses them the same way (B-22)."""
EXPRESSIONS: Final = {"rule": "expr", "loop": "predicate"}
"""The parameter that holds each kind's `definition.expr` expression (B-90)."""
EXPRESSION_NAMES: Final = frozenset({"items", "inputs"})
"""The names an expression may read: `items` is the `in` port, `inputs` every port."""


def validate(
    folder: WorkflowFolder,
    *,
    roles: Collection[str] = DEFAULT_ROLES,
    placements: Collection[str] = PLACEMENTS,
    registry: Registry = REGISTRY,
    publish: bool = False,
) -> list[Problem]:
    """`roles` are the names in the Settings `[roles]` document; `publish` adds step 5's
    refusals of note and unconnected nodes. No message quotes a document value, and a path
    (which can hold a node name or a key) has any token shape redacted."""
    return [
        Problem(code, redact(path), redact(message))
        for code, path, message in problems(folder, roles, placements, registry, publish=publish)
    ]


def problems(
    folder: WorkflowFolder,
    roles: Collection[str],
    placements: Collection[str],
    registry: Registry,
    *,
    publish: bool,
) -> Iterator[Problem]:
    yield from folder.problems
    if folder.document is None:
        return
    try:
        workflow = Workflow.model_validate(folder.document)
    except ValidationError as error:
        yield from (Problem("schema_invalid", where(e["loc"]), e["msg"]) for e in error.errors())
        return
    if workflow.extends is not None:
        yield Problem(
            "extends_unresolved",
            "extends",
            "resolve the variant over its parent first; only a full snapshot validates",
        )
    yield from graph(workflow, registry, publish=publish)
    yield from nesting(workflow, registry)
    yield from parameters(workflow, registry)
    yield from blocks(folder, workflow)
    yield from names(workflow, registry, roles, placements)
    yield from writers(workflow, registry)
    yield from lint(workflow, registry)


def runnable(workflow: Workflow, registry: Registry = REGISTRY) -> list[Problem]:
    """What a run refuses that a draft may hold: a kind whose executor is not built yet, and a
    need (`meta.needs`) that nothing meets yet."""
    found = [
        Problem("kind_not_available", f"nodes[{i}].type", "this node kind cannot run yet")
        for i, node in enumerate(workflow.nodes)
        if (kind := registry.kind(node.type)) is not None and not node.disabled
        if kind is not NOTE and not kind.available
    ]
    if workflow.meta.needs:
        found.append(Problem("needs_unmet", "meta.needs", needs_line(workflow.meta.needs)))
    return found


def needs_line(needs: Sequence[str]) -> str:
    return f"needs: {', '.join(needs)}"


def checked(root: Path) -> tuple[WorkflowFolder, Workflow] | list[Problem]:
    """A folder that validates and that a run accepts, or every problem in it."""
    folder = load(root)
    found = validate(folder)
    if found:
        return found
    workflow = Workflow.model_validate(folder.document)
    return runnable(workflow) or (folder, workflow)


def where(loc: tuple[int | str, ...]) -> str:
    return "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in loc).lstrip(".")


def outputs(kind: Kind, node: Node) -> tuple[str, ...]:
    if kind.outputs_param is None:
        return kind.outputs
    declared = node.parameters.get(kind.outputs_param)
    return tuple(p for p in declared if isinstance(p, str)) if isinstance(declared, list) else ()


def graph(workflow: Workflow, registry: Registry, *, publish: bool) -> Iterator[Problem]:
    by_name: dict[str, tuple[int, Node, Kind | None]] = {}
    seen_ids: set[str] = set()
    for i, node in enumerate(workflow.nodes):
        kind = registry.kind(node.type)
        if kind is None:
            yield Problem("kind_unknown", f"nodes[{i}].type", "no node kind has this type")
        elif node.type_version not in kind.versions:
            yield Problem(
                "type_version_unknown",
                f"nodes[{i}].typeVersion",
                f"this kind has no typeVersion {node.type_version}",
            )
        if node.name in by_name:
            yield Problem("node_name_duplicate", f"nodes[{i}].name", "another node has this name")
        if node.id in seen_ids:
            yield Problem("node_id_duplicate", f"nodes[{i}].id", "another node has this id")
        if ":" in node.id:
            yield Problem(
                "node_id_invalid",
                f"nodes[{i}].id",
                "a node id may not hold ':', which separates an idempotency key's parts",
            )
        by_name.setdefault(node.name, (i, node, kind))
        seen_ids.add(node.id)

    triggers = [
        name
        for name, (_, node, kind) in by_name.items()
        if kind is not None and kind.name == "trigger" and not node.disabled
    ]
    if len(triggers) != 1:
        yield Problem("trigger_count", "nodes", f"needs exactly one trigger, found {len(triggers)}")

    forward: dict[str, list[str]] = defaultdict(list)
    wired: set[str] = set()
    for edge in edges(workflow):
        source, target = by_name.get(edge.source), by_name.get(edge.target.node)
        if source is None or target is None:
            end = "source" if source is None else "target"
            yield Problem("edge_unknown_node", edge.path, f"the edge's {end} names no node")
            continue
        (_, source_node, source_kind), (_, _, target_kind) = source, target
        wired |= {edge.source, edge.target.node}
        if source_kind is not None and edge.port not in outputs(source_kind, source_node):
            yield Problem("edge_unknown_port", edge.path, "the source kind has no such output port")
        if target_kind is not None and edge.target.port not in target_kind.inputs:
            yield Problem(
                "edge_unknown_port",
                edge.path,
                "the target kind has no such input port",
            )
        if edge.target.map == "cartesian" and not edge.target.explicit:
            yield Problem(
                "cartesian_not_explicit", edge.path, "a cartesian edge needs explicit: true"
            )
        if edge.target.map == "keyed-join" and not edge.target.key:
            yield Problem("keyed_join_without_key", edge.path, "a keyed-join edge needs a key")
        if edge.target.map == "chunk" and edge.target.chunk is None:
            yield Problem("chunk_spec_missing", edge.path, "a chunk edge needs chunk: {by, ...}")
        loop_back = target_kind is not None and target_kind.name == "loop"
        if not (loop_back and edge.target.port == LOOP_BACK_PORT):
            forward[edge.source].append(edge.target.node)

    yield from cycles(forward, {name: i for name, (i, _, _) in by_name.items()})

    reached: set[str] = set()
    frontier = list(triggers)
    while frontier:
        name = frontier.pop()
        if name not in reached:
            reached.add(name)
            frontier.extend(forward[name])
    for name, (i, node, kind) in by_name.items():
        if name in reached or node.disabled or not triggers:
            continue
        if kind is NOTE:
            if publish:
                yield Problem(
                    "note_at_publish", f"nodes[{i}]", "a note must be disabled to publish"
                )
        elif name not in wired:
            if publish:
                yield Problem("unconnected_at_publish", f"nodes[{i}]", "the node has no edges")
        else:
            yield Problem("node_unreachable", f"nodes[{i}]", "no path from the trigger reaches it")


def cycles(forward: dict[str, list[str]], index: dict[str, int]) -> Iterator[Problem]:
    """One problem per edge that closes a cycle, found by depth-first search."""
    done: set[str] = set()
    for start in list(forward):
        if start in done:
            continue
        on_path: list[str] = [start]
        stack = [iter(forward[start])]
        while stack:
            child = next(stack[-1], None)
            if child is None:
                stack.pop()
                done.add(on_path.pop())
            elif child in on_path:
                loop = [*on_path[on_path.index(child) :], child]
                yield Problem(
                    "cycle",
                    f"nodes[{index[on_path[-1]]}]",
                    " -> ".join(f"nodes[{index[name]}]" for name in loop),
                )
            elif child not in done:
                on_path.append(child)
                stack.append(iter(forward[child]))


def kind_name(registry: Registry, node: Node) -> str | None:
    found = registry.kind(node.type)
    return found.name if found is not None else None


def partitioned(workflow: Workflow, registry: Registry) -> set[str]:
    """The nodes that run one slot per partition: each node a fanning edge feeds, and what reads
    one through `one` edges, up to a `join`, which collects the partitions back into one slot, or
    a `loop`, which `nesting` refuses on fanned input."""
    by_name = {node.name: node for node in workflow.nodes}
    ones: dict[str, set[str]] = defaultdict(set)
    fanned: set[str] = set()
    for edge in edges(workflow):
        if edge.target.map == "one":
            ones[edge.source].add(edge.target.node)
        else:
            fanned.add(edge.target.node)
    found = set(fanned)
    frontier = list(fanned)
    while frontier:
        for target in ones[frontier.pop()]:
            node = by_name.get(target)
            stops = node is not None and kind_name(registry, node) in ("join", "loop")
            if target not in found and not stops:
                found.add(target)
                frontier.append(target)
    return found


def nesting(workflow: Workflow, registry: Registry) -> Iterator[Problem]:
    """AD-5: v1 fans out one level deep. A fanning edge out of a node that already runs per
    partition, a loop fed by such a node, and a loop inside another loop's body are refused here
    rather than parked at run time (B-20). A loop body may call a `subworkflow` whose child holds
    its own loop: the child runs in its own ledger namespace, so that nesting is allowed."""
    index = {node.name: i for i, node in enumerate(workflow.nodes)}
    by_name = {node.name: node for node in workflow.nodes}
    split = partitioned(workflow, registry)
    for edge in edges(workflow):
        target = by_name.get(edge.target.node)
        if edge.source not in split or target is None:
            continue
        where = f"nodes[{index[target.name]}]"
        source = by_name[edge.source].id
        if kind_name(registry, target) == "loop":
            yield Problem(
                "nesting_unsupported",
                where,
                f"loop {target.id} reads {source}, which runs per partition; a loop over fanned "
                "input is not run in v1",
            )
        elif edge.target.map != "one":
            yield Problem(
                "nesting_unsupported",
                where,
                f"node {target.id} fans out what {source} already fanned out; nested fan-out is "
                "not run in v1",
            )
    for outer in workflow.nodes:
        if kind_name(registry, outer) != "loop":
            continue
        for name in sorted(body(workflow, outer), key=index.__getitem__):
            inner = by_name[name]
            if kind_name(registry, inner) == "loop":
                yield Problem(
                    "nesting_unsupported",
                    f"nodes[{index[name]}]",
                    f"loop {inner.id} sits in the body of loop {outer.id}; a loop inside a loop "
                    "body is not run in v1 (call a subworkflow that holds it)",
                )


def body(workflow: Workflow, loop: Node) -> set[str]:
    """The names of the nodes the loop's `body` port reaches, edges back into a loop left out."""
    forward: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges(workflow):
        forward[edge.source].append(edge)
    reached: set[str] = set()
    frontier = [e.target.node for e in forward[loop.name] if e.port == "body"]
    while frontier:
        name = frontier.pop()
        if name in reached or name == loop.name:
            continue
        reached.add(name)
        frontier.extend(e.target.node for e in forward[name] if e.target.port != LOOP_BACK_PORT)
    return reached


def parameters(workflow: Workflow, registry: Registry) -> Iterator[Problem]:
    """The parameters the core and the executors read: loop, join and wait specs and a join's one
    inbound `one` edge (B-22), every expression (B-90), and a mode the registry marks as not
    built yet (B-46)."""
    into: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges(workflow):
        into[edge.target.node].append(edge)
    for i, node in enumerate(workflow.nodes):
        kind = registry.kind(node.type)
        if kind is None or node.disabled:
            continue
        here = f"nodes[{i}].parameters"
        spec = SPECS.get(kind.name)
        if spec is not None:
            try:
                spec.model_validate(node.parameters)
            except ValidationError as error:
                for found in error.errors():
                    if kind.name == "loop" and found["loc"] == ("max_iterations",):
                        continue  # the lint names a missing max_iterations
                    yield Problem(
                        "parameters_invalid",
                        f"{here}.{where(found['loc'])}".rstrip("."),
                        f"node {node.id}: {found['msg']}",
                    )
        if kind.name == "join":
            inbound = into.get(node.name, [])
            if len(inbound) != 1 or inbound[0].target.map != "one":
                yield Problem(
                    "join_inbound_invalid",
                    f"nodes[{i}]",
                    f"join {node.id} takes exactly one inbound one-edge, found {len(inbound)} "
                    "edge(s)",
                )
        name = EXPRESSIONS.get(kind.name)
        expr = node.parameters.get(name) if name is not None else None
        if isinstance(expr, str):
            yield from expression(expr, f"{here}.{name}", node)
        mode = node.parameters.get("mode")
        if isinstance(mode, str) and mode in kind.unavailable_modes:
            yield Problem(
                "mode_unavailable",
                f"{here}.mode",
                f"node {node.id}: a {kind.name} in mode {mode} cannot run yet",
            )


def expression(expr: str, path: str, node: Node) -> Iterator[Problem]:
    try:
        tree = check(expr)
    except RuleRefused as refused:
        yield Problem("expression_invalid", path, f"node {node.id}: {refused}")
        return
    for name in sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}):
        if name not in EXPRESSION_NAMES:
            yield Problem(
                "expression_invalid",
                path,
                f"node {node.id}: the expression reads {name!r}; it may read only "
                f"{' and '.join(sorted(EXPRESSION_NAMES))}",
            )


def blocks(folder: WorkflowFolder, workflow: Workflow) -> Iterator[Problem]:
    """A child a `subworkflow` names inside this folder admits this caller (AD-5, B-27): its
    `caller_policy` is checked here whenever the child resolves, and again at dispatch."""
    for i, node in enumerate(workflow.nodes):
        block = node.parameters.get("workflow")
        if node.type != "subworkflow" or not isinstance(block, str):
            continue
        path = f"nodes[{i}].parameters.workflow"
        text = folder.refs.get(f"{PurePosixPath(block).as_posix()}/{DEFINITION}")
        if text is None:
            continue
        try:
            child: JsonValue = json.loads(text)
        except ValueError:
            yield Problem("subworkflow_invalid", path, f"node {node.id}: the child is not JSON")
            continue
        settings = child.get("settings") if isinstance(child, dict) else None
        policy = settings.get("caller_policy") if isinstance(settings, dict) else None
        if policy == "none":
            yield Problem(
                "caller_refused",
                path,
                f"node {node.id}: the child's caller_policy admits no caller",
            )


def names(
    workflow: Workflow, registry: Registry, roles: Collection[str], placements: Collection[str]
) -> Iterator[Problem]:
    """Step 3: roles, placements and credentials resolve by name. Reachability is preflight's."""
    for i, node in enumerate(workflow.nodes):
        kind = registry.kind(node.type)
        if kind is None:
            continue
        needs_role = kind.role is RoleRule.REQUIRED or (
            kind.role is RoleRule.LLM_MODE and node.parameters.get("mode") == "llm"
        )
        if needs_role and node.role is None:
            yield Problem("role_required", f"nodes[{i}].role", f"a {kind.name} node needs a role")
        elif not needs_role and node.role is not None:
            yield Problem("role_forbidden", f"nodes[{i}].role", f"a {kind.name} node takes no role")
        elif node.role is not None and node.role not in roles:
            yield Problem("role_unknown", f"nodes[{i}].role", "the role is not in [roles]")
        for placement in [node.runs_on] if isinstance(node.runs_on, str) else node.runs_on:
            if placement not in placements:
                yield Problem(
                    "placement_unknown", f"nodes[{i}].runs_on", "the placement is not registered"
                )
        for name, ref in node.credentials.items():
            if not ref.startswith("qmx/"):
                yield Problem(
                    "credential_not_ref",
                    f"nodes[{i}].credentials.{name}",
                    "a credential is a qmx/* keyring reference, never a value",
                )


def leaves_work(path: str) -> bool:
    """True for an output path that could leave a run's `work/` or touch its staging folder."""
    pure = PurePosixPath(path)
    return (
        not pure.parts
        or "\\" in path
        or pure.is_absolute()
        or ":" in pure.parts[0]
        or ".." in pure.parts
        or pure.parts[0] == STAGING
    )


def writers(workflow: Workflow, registry: Registry) -> Iterator[Problem]:
    """AD-51: two writers that may run at once never share a declared path, unless it is
    partition-templated or both name the same merge. Two partitions of one node may run at once,
    and so may two nodes with no path between them."""
    index = {node.name: i for i, node in enumerate(workflow.nodes)}
    forward: dict[str, set[str]] = defaultdict(set)
    for edge in edges(workflow):
        forward[edge.source].add(edge.target.node)
    split = partitioned(workflow, registry)
    declared: list[tuple[int, Node, int, OutputFile]] = []
    for i, node in enumerate(workflow.nodes):
        files = node.outputs.files if node.outputs is not None and not node.disabled else []
        for j, output in enumerate(files):
            path = f"nodes[{i}].outputs.files[{j}].path"
            if leaves_work(output.path.replace("<partition>", "0")):
                yield Problem("output_path_invalid", path, "an output path must stay inside work/")
            elif (
                node.name in split
                and output.merge == "replace"
                and "<partition>" not in output.path
            ):
                yield Problem(
                    "zone_writer_concurrent",
                    path,
                    "two partitions of this node write this path; template it with <partition> "
                    "or name a merge",
                )
            declared.append((i, node, j, output))
    for (_, a, _, first), (i, b, j, second) in combinations(declared, 2):
        if a.name == b.name or not overlap(first.path, second.path):
            continue
        if first.merge == second.merge != "replace":
            continue
        if reaches(forward, a.name, b.name) or reaches(forward, b.name, a.name):
            continue
        yield Problem(
            "zone_writer_concurrent",
            f"nodes[{i}].outputs.files[{j}].path",
            f"nodes[{index[a.name]}] may run at the same time and writes this path too",
        )


def overlap(first: str, second: str) -> bool:
    return (
        first == second
        or PurePosixPath(first).full_match(second)
        or PurePosixPath(second).full_match(first)
    )


def reaches(forward: dict[str, set[str]], start: str, goal: str) -> bool:
    seen: set[str] = set()
    frontier = [start]
    while frontier:
        name = frontier.pop()
        if name == goal:
            return True
        if name not in seen:
            seen.add(name)
            frontier.extend(forward[name])
    return False
