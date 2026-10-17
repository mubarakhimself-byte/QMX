"""SOLUTION-DESIGN 2.4 step 4: what no definition may hold, whoever wrote it.

No node writes Settings or creates a trigger, no parameter names a money act (PROMPT-ENGINE
rule 6, AD-8), no token-shaped literal appears anywhere, a list never fans into a model node by
`broadcast`, an agent names its `max_turns`, a loop names its `max_iterations` (so every loop
ends), and a `human_gate` sits only in front of an
`irreversible_external` effect. A missing runaway guard is not an error: it takes the defaults,
and no USD figure is ever asked for (ruling 27).
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Final

from pydantic import JsonValue
from qma.core.barriers.money_path import (
    MONEY_PATH_COMPOUND_NOUNS,
    MONEY_PATH_FAMILY_NOUNS,
    MONEY_PATH_MONEY_VERBS,
    MONEY_PATH_MUTATING_VERBS,
    MONEY_PATH_NON_MONEY_OBJECTS,
    match_money_path_act,
)

from qmx_engine.definition.folder import Problem
from qmx_engine.definition.model import Runaway, Settings, Workflow, edges
from qmx_engine.definition.registry import Registry
from qmx_engine.settings import DEFAULTS

SETTINGS_WRITE: Final = frozenset({"settings_write", "settings_put", "settings_update"})
TRIGGER_CREATION: Final = frozenset(
    {"workflow_triggers_create", "triggers_create", "trigger_create", "create_trigger"}
)
TOKEN_SHAPES: Final = re.compile(
    r"(?<![A-Za-z0-9_-])(?:"
    + "|".join(
        (
            r"sk-(?=[A-Za-z_-]*[0-9])[A-Za-z0-9_-]{20,}",
            r"AKIA[0-9A-Z]{16}",
            r"AIza[0-9A-Za-z_-]{35}",
            r"xox[baprs]-[0-9A-Za-z-]{10,}",
            r"gh[pousr]_[A-Za-z0-9]{36,}",
            r"github_pat_[A-Za-z0-9_]{22,}",
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.",
            r"-----BEGIN[A-Z ]*PRIVATE KEY-----",
        )
    )
    + ")"
)
"""Provider key shapes, each starting a word, so `risk-adjusted-returns` is not an `sk-` key."""
SEGMENTS: Final = re.compile(r"__|[.:]")
CAMEL: Final = re.compile(r"([a-z0-9])([A-Z])")
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
        if TOKEN_SHAPES.search(text)
    )
    for i, node in enumerate(workflow.nodes):
        kind = registry.kind(node.type)
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
        if kind.name == "agent":
            turns = node.parameters.get("max_turns")
            if not isinstance(turns, int) or isinstance(turns, bool) or turns < 1:
                yield Problem(
                    "agent_max_turns_missing", f"nodes[{i}].parameters", "an agent needs max_turns"
                )
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


def redact(text: str) -> str:
    return TOKEN_SHAPES.sub("[redacted]", text)


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
        if act := match_money_path_act(candidate) or word_act(candidate):
            return act
    return None


def word_act(text: str) -> str | None:
    """An identifier (no spaces) holding a money verb (`paper_buy`), or a mutating verb with an
    order, position or protection noun (`closeAllPositions`, `update_stop_loss`). The deny-list's
    exact match misses these, and prose is left alone so a prompt can talk about markets."""
    if re.search(r"\s", text.strip()):
        return None
    raw = [w for w in re.split(r"[^a-z0-9]+", CAMEL.sub(r"\1_\2", text).casefold()) if w]
    words: list[str] = []
    for word in raw:
        if words and (compound := MONEY_PATH_COMPOUND_NOUNS.get((words[-1], word))):
            words[-1] = compound
        else:
            singular = word.removesuffix("s")
            words.append(singular if singular in MONEY_PATH_FAMILY_NOUNS else word)
    if money := next((w for w in words if w in MONEY_PATH_MONEY_VERBS), None):
        return money
    verb = next((w for w in words if w in MONEY_PATH_MUTATING_VERBS), None)
    noun = next((w for w in words if w in MONEY_PATH_FAMILY_NOUNS), None)
    if verb and noun and not MONEY_PATH_NON_MONEY_OBJECTS & set(words):
        return f"{verb}_{noun}"
    return None


def effective_runaway(settings: Settings) -> Runaway:
    """The run's runaway guard: the definition's own limits, the defaults for the rest."""
    defaults = Runaway.model_validate(
        {k: DEFAULTS[f"runaway.{k}"] for k in ("tokens", "agents", "wall_seconds")}
        | {"on_runaway": DEFAULTS["on_runaway"]}
    )
    own = settings.runaway or Runaway()
    return defaults.model_copy(update=own.model_dump(exclude_none=True))
