"""The AD-5 node-kind registry: each kind's ports, default effect, role rule and availability.

A capability pack adds types named `<pack>.<name>`, each checked against its `base_kind`'s entry,
so the vocabulary stays closed. `note` is the one draft-only type and has no base kind.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Literal

type Effect = Literal["none", "reversible", "compensable", "irreversible", "irreversible_external"]


class RoleRule(StrEnum):
    REQUIRED = "required"
    FORBIDDEN = "forbidden"
    LLM_MODE = "llm_mode"
    """Required when `parameters.mode` is `llm`, forbidden otherwise (the grader's judge mode)."""


@dataclass(frozen=True)
class Kind:
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    effect: Effect
    role: RoleRule = RoleRule.FORBIDDEN
    outputs_param: str | None = None
    """A parameter whose list of names are the output ports (a `human_gate`'s options)."""
    versions: frozenset[int] = frozenset({1})
    available: bool = False
    model_bearing: bool = False
    unavailable_modes: frozenset[str] = frozenset()
    """Values of `parameters.mode` whose executor is not built yet; validation refuses them."""


IN: Final = ("in",)
MAIN: Final = ("main",)
LOOP_BACK_PORT: Final = "next"
"""A loop takes its first value on `in` and each later one on `next`; it sends the value on `body`
while it iterates and on `done` once a stop fires (settled in EP6). An edge into `next` closes the
body; graph checks leave it out, so the body's cycle is the one cycle a definition may hold."""

# Every kind is unavailable until the PR that builds its executor flips it (EP6 to EP11).
BASE_KINDS: Final[Mapping[str, Kind]] = MappingProxyType(
    {
        kind.name: kind
        for kind in (
            Kind("trigger", (), MAIN, "none", available=True),
            Kind("script", IN, MAIN, "reversible", available=True),
            Kind("rule", IN, ("true", "false"), "none", available=True),
            Kind("loop", ("in", LOOP_BACK_PORT), ("body", "done"), "none", available=True),
            Kind("join", IN, MAIN, "none", available=True),
            Kind("wait", IN, MAIN, "none", available=True),
            Kind("human_gate", IN, (), "none", outputs_param="options"),
            Kind(
                "llm",
                IN,
                MAIN,
                "irreversible",
                RoleRule.REQUIRED,
                available=True,
                model_bearing=True,
            ),
            Kind(
                "agent",
                IN,
                MAIN,
                "irreversible",
                RoleRule.REQUIRED,
                available=True,
                model_bearing=True,
            ),
            Kind("rlm", IN, MAIN, "irreversible"),
            Kind("subworkflow", IN, MAIN, "irreversible", available=True),
            Kind(
                "grader",
                IN,
                ("pass", "fail"),
                "none",
                RoleRule.LLM_MODE,
                available=True,
                unavailable_modes=frozenset({"llm"}),
            ),
            Kind("monitor", IN, ("changed", "silent"), "none", available=True),
            Kind("app_op", IN, MAIN, "irreversible"),
            Kind("library", IN, MAIN, "compensable"),
            Kind("claude_workflow", IN, MAIN, "irreversible"),
        )
    }
)
NOTE: Final = Kind("note", (), (), "none")
PACK_TYPE: Final = re.compile(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*")


@dataclass(frozen=True)
class Registry:
    kinds: Mapping[str, Kind] = BASE_KINDS
    packs: Mapping[str, str] = field(default_factory=dict[str, str])
    """Pack type name to its base kind name."""

    def with_pack(self, type_name: str, base_kind: str) -> Registry:
        if not PACK_TYPE.fullmatch(type_name):
            raise ValueError(f"pack type {type_name!r} is not <pack>.<name>")
        if base_kind not in self.kinds:
            raise ValueError(f"pack type {type_name!r} names no base kind {base_kind!r}")
        return replace(self, packs={**self.packs, type_name: base_kind})

    def kind(self, type_name: str) -> Kind | None:
        """The contract a node of this `type` follows: its own kind, its pack's base kind, or
        `note`. None for an unknown type."""
        if type_name == NOTE.name:
            return NOTE
        return self.kinds.get(self.packs.get(type_name, type_name))


REGISTRY: Final = Registry()
