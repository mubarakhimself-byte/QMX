"""Money-path refusal for a tool descriptor, shared by every host that admits tools."""

from __future__ import annotations

import re
from typing import Any, cast

from qma.core.barriers.money_path import MoneyPathDenyError, match_money_path_act
from qma.core.barriers.parent_surfaces import is_parent_surface_permitted

__all__ = ["check_descriptor", "name_money_act"]

_BOUNDARY = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])"
)


def _suffixes(words: list[str]) -> list[str]:
    return ["_".join(words[index:]) for index in range(len(words))]


def name_money_act(name: str) -> str | None:
    """The denied act a name ends in, testing every word suffix of two splits. The plain split
    breaks only at separators. The humped split also breaks at camelCase humps and letter-digit
    seams and drops digit words and a `v` before them, so `placeOrder`, `PlaceOrderV2` and
    `place_order2` read as `place_order`. Testing both keeps every name the plain split refuses
    refused, whatever its casing."""
    plain = [word for word in re.split(r"[\W_]+", name.casefold()) if word]
    raw = [word for word in re.split(r"[\W_]+", _BOUNDARY.sub("_", name).casefold()) if word]
    humped = [
        word
        for word, after in zip(raw, [*raw[1:], ""], strict=True)
        if not word.isdigit() and not (word == "v" and after.isdigit())
    ]
    return next(
        (
            matched
            for suffix in _suffixes(plain) + _suffixes(humped)
            if (matched := match_money_path_act(suffix)) is not None
        ),
        None,
    )


def check_descriptor(name: str, metadata: dict[str, Any]) -> None:
    """The same resolved barrier applies to LangChain and hosted MCP tools."""
    if metadata.get("money_path"):
        raise MoneyPathDenyError(f"Money-path tool refused: {name}")
    tokens: list[str] = [name]
    sources: list[dict[str, Any]] = [metadata]
    while sources:
        source = sources.pop()
        for key in ("mcp", "tool", "annotations", "_meta"):
            nested = source.get(key)
            if isinstance(nested, dict):
                sources.append(cast("dict[str, Any]", nested))
        if "parent_library" in source and not is_parent_surface_permitted(
            str(source["parent_library"]), str(source.get("parent_surface", ""))
        ):
            raise MoneyPathDenyError(f"Parent surface refused: {name}")
        if source.get("record_family") is not None:
            raise MoneyPathDenyError(f"Parent record mutation refused: {name}")
        if source.get("money_path"):
            raise MoneyPathDenyError(f"Money-path tool refused: {name}")
        for key in ("act", "acts", "name", "tool_name"):
            value = source.get(key)
            if isinstance(value, str):
                tokens.append(value)
            elif isinstance(value, (list, tuple, set)):
                tokens.extend(str(item) for item in cast("list[Any]", value))
    if any(name_money_act(token) is not None for token in tokens):
        raise MoneyPathDenyError(f"Money-path act refused: {name}")
