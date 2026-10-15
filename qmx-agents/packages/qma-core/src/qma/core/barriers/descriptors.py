"""Money-path refusal for a tool descriptor, shared by every host that admits tools."""

from __future__ import annotations

import re
from typing import Any, Final, cast

from qma.core.barriers.money_path import (
    MONEY_PATH_ACT_ALIASES,
    MONEY_PATH_DENIED_ACTS,
    MONEY_PATH_DENY_LIST,
    MONEY_PATH_FAMILY_NOUNS,
    MONEY_PATH_MONEY_VERBS,
    MONEY_PATH_MUTATING_VERBS,
    MoneyPathDenyError,
    match_money_path_act,
)
from qma.core.barriers.parent_surfaces import is_parent_surface_permitted

__all__ = ["check_descriptor", "name_money_act"]

_BOUNDARY = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])"
)
_PHRASES: Final = frozenset(
    phrase
    for phrase in (
        *(act.value for act in MONEY_PATH_DENIED_ACTS),
        *(act.value for act in MONEY_PATH_DENY_LIST),
        *MONEY_PATH_ACT_ALIASES,
    )
    if "_" in phrase
)
"""Acts of two or more words, matched anywhere in a name (`place_order_now`)."""
_WORDS: Final = MONEY_PATH_FAMILY_NOUNS | MONEY_PATH_MUTATING_VERBS


def _splits(name: str) -> tuple[list[str], list[str]]:
    """The plain split breaks only at separators. The humped split also breaks at camelCase
    humps and letter-digit seams and drops digit words and a `v` before them, so `placeOrder`,
    `PlaceOrderV2` and `place_order2` read as `place_order`."""
    plain = [word for word in re.split(r"[\W_]+", name.casefold()) if word]
    raw = [word for word in re.split(r"[\W_]+", _BOUNDARY.sub("_", name).casefold()) if word]
    humped = [
        word
        for word, after in zip(raw, [*raw[1:], ""], strict=True)
        if not word.isdigit() and not (word == "v" and after.isdigit())
    ]
    return plain, humped


def _phrase_act(words: list[str]) -> str | None:
    """An act a word suffix names (the base rule, kept so no refused name is ever allowed), or
    a multi-word act anywhere in the name."""
    count = len(words)
    suffixes = ("_".join(words[start:]) for start in range(count))
    runs = (
        run
        for start in range(count)
        for stop in range(start + 2, count + 1)
        if (run := "_".join(words[start:stop])) in _PHRASES
    )
    return next(
        (matched for run in (*suffixes, *runs) if (matched := match_money_path_act(run))), None
    )


def _fold(word: str) -> str:
    return word[:-1] if word.endswith("s") and word[:-1] in _WORDS else word


def _word_act(words: list[str]) -> str | None:
    """A money verb anywhere, else a family noun with a mutating verb in either order, after
    folding plurals (`cancel_all_orders` is `cancel_order`)."""
    folded = [_fold(word) for word in words]
    money = next((word for word in folded if word in MONEY_PATH_MONEY_VERBS), None)
    if money is not None:
        return money
    noun = next((word for word in folded if word in MONEY_PATH_FAMILY_NOUNS), None)
    verb = next((word for word in folded if word in MONEY_PATH_MUTATING_VERBS), None)
    return f"{verb}_{noun}" if noun and verb else None


def name_money_act(name: str) -> str | None:
    """The denied act a tool name spells, read through both splits: a phrase act first, then
    the word rule. Every name the suffix rule refused stays refused, whatever its casing."""
    splits = _splits(name)
    return next(
        (
            act
            for rule in (_phrase_act, _word_act)
            for words in splits
            if (act := rule(words)) is not None
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
