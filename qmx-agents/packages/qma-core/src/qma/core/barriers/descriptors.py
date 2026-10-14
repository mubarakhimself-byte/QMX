"""Money-path refusal for a tool descriptor, shared by every host that admits tools."""

from __future__ import annotations

import re
from typing import Any, cast

from qma.core.barriers.money_path import MoneyPathDenyError, is_money_path_act_denied
from qma.core.barriers.parent_surfaces import is_parent_surface_permitted

__all__ = ["check_descriptor"]


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
    suffixes: list[str] = []
    for token in tokens:
        words = [word for word in re.split(r"[\W_]+", token.casefold()) if word]
        suffixes.extend("_".join(words[index:]) for index in range(len(words)))
    if any(is_money_path_act_denied(suffix) for suffix in suffixes):
        raise MoneyPathDenyError(f"Money-path act refused: {name}")
