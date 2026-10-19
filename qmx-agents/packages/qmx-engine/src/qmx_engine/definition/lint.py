"""SOLUTION-DESIGN 2.4 step 4: what no definition may hold, whoever wrote it.

No node writes Settings or creates a trigger, no parameter names a money act (PROMPT-ENGINE
rule 6, AD-8), no token-shaped literal appears anywhere (the shapes of `ledger.redact`, AD-37), a
node's credentials name only `qmx/tool/<name>` keys, a list never fans into a model node by
`broadcast`, a loop names its `max_iterations` (so every loop ends), and a `human_gate` sits only
in front of an `irreversible_external` effect. No limit is ever required: QMX sets no usage limit
of its own (ruling 106, AD-40), and a `limits` value he wrote is refused only below 1.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Final

from pydantic import JsonValue
from qma.harness import named_money_act

from qmx_engine.definition.folder import Problem
from qmx_engine.definition.model import Limits, Workflow, edges
from qmx_engine.definition.registry import Registry
from qmx_engine.ledger.redact import SHAPES, redact

__all__ = ["lint", "redact"]

SETTINGS_WRITE: Final = frozenset({"settings_write", "settings_put", "settings_update"})
TRIGGER_CREATION: Final = frozenset(
    {"workflow_triggers_create", "triggers_create", "trigger_create", "create_trigger"}
)
TOOL_KEY: Final = re.compile(r"qmx/tool/[a-z0-9][a-z0-9_-]{0,39}")
"""The only credential a node may name: a tool key a Settings `[credentials.tools]` row declares
(AD-24). Provider keys stay relay-only (AD-28) and broker keys never reach a node."""
SEGMENTS: Final = re.compile(r"__|[.:]")
BARE_NOUNS: Final = frozenset(
    {"order", "position", "protection", "sizing", "binding", "mode", "control", "size"}
)
"""The deny-list matches these single words as act families, but alone in a parameter they are a
field or a sort key (`"sort_by": "position"`, `items.size`), not an act. Every verb phrase
(`place_order`, `close_position`, `resize`) is still refused."""


def lint(workflow: Workflow, registry: Registry) -> Iterator[Problem]:
    nodes = {node.name: node for node in workflow.nodes}
    yield from (
        Problem("secret_literal", path, "a token-shaped literal; name a qmx/* keyring ref instead")
        for path, text in strings(workflow.model_dump(mode="json", by_alias=True), "")
        if SHAPES.search(text)
    )
    # A value that is no qmx/* ref at all is validate's `credential_not_ref`.
    yield from (
        Problem(
            "credential_not_tool_key",
            f"nodes[{i}].credentials.{name}",
            "a node names only a qmx/tool/<name> key; provider and broker keys never reach it",
        )
        for i, node in enumerate(workflow.nodes)
        for name, ref in node.credentials.items()
        if ref.startswith("qmx/") and not TOOL_KEY.fullmatch(ref)
    )
    yield from below_one(workflow.settings.limits, "settings.limits")
    for i, node in enumerate(workflow.nodes):
        kind = registry.kind(node.type)
        yield from below_one(node.limits, f"nodes[{i}].limits")
        for path, text in [
            (f"nodes[{i}].type", node.type),
            *strings(node.parameters, f"nodes[{i}].parameters"),
        ]:
            operation = names_operation(text)
            act = money_act(text)
            if operation & SETTINGS_WRITE:
                yield Problem("settings_write", path, "no node may write Settings")
            if operation & TRIGGER_CREATION:
                yield Problem("trigger_creation", path, "no node may create a trigger")
            if act is not None:
                yield Problem("money_act", path, f"names the money act {act!r}; money is read-only")
        if kind is None:
            continue
        if kind.name == "loop":
            cap = node.parameters.get("max_iterations")
            if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
                yield Problem(
                    "loop_max_iterations_missing",
                    f"nodes[{i}].parameters",
                    "a loop needs max_iterations",
                )
        if kind.name == "human_gate":
            after = [
                nodes[edge.target.node]
                for edge in edges(workflow)
                if edge.source == node.name and edge.target.node in nodes
            ]
            if not after or any(
                effect(registry, target.type, target.effect) != "irreversible_external"
                for target in after
            ):
                yield Problem(
                    "human_gate_misplaced",
                    f"nodes[{i}]",
                    "a human_gate sits only in front of an irreversible_external effect",
                )
    for edge in edges(workflow):
        target = nodes.get(edge.target.node)
        kind = None if target is None else registry.kind(target.type)
        if edge.target.map == "broadcast" and kind is not None and kind.model_bearing:
            yield Problem(
                "chunk_required",
                edge.path,
                f"a list into a {kind.name} node uses map: chunk, not broadcast",
            )


def below_one(limits: Limits | None, path: str) -> Iterator[Problem]:
    if limits is None:
        return
    for name, value in limits.model_dump(exclude_none=True).items():
        if value < 1:
            yield Problem(
                "limit_below_one", f"{path}.{name}", f"{name} is {value}; a limit is 1 or more"
            )


def effect(registry: Registry, type_name: str, declared: str | None) -> str | None:
    kind = registry.kind(type_name)
    return declared or (None if kind is None else kind.effect)


def strings(value: JsonValue, path: str) -> Iterator[tuple[str, str]]:
    """Every string in the value, keys included, so `{"place_order": true}` and a tool map keyed
    by MCP name are read like a list of names."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}.{key}" if path else key
            yield here, key
            yield from strings(item, here)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f"{path}[{index}]")


def candidates(text: str) -> list[str]:
    """The whole text and its last segment, so `mcp__broker__place_order` and `qmb.submit_order`
    are read as the tool or operation they end in."""
    return [text, SEGMENTS.split(text)[-1]]


def names_operation(text: str) -> set[str]:
    found: set[str] = set()
    for candidate in candidates(text):
        token = re.sub(r"[\s./-]+", "_", candidate.strip().casefold())
        found |= {
            op
            for op in SETTINGS_WRITE | TRIGGER_CREATION
            if token == op or token.endswith(f"_{op}")
        }
    return found


def money_act(text: str) -> str | None:
    for candidate in candidates(text):
        if candidate.strip().casefold() in BARE_NOUNS:
            continue
        if act := named_money_act(candidate):
            return act
    return None
