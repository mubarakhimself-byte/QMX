"""Money-path refusal for a tool descriptor, shared by every host that admits tools."""

from __future__ import annotations

import re
from typing import Any, Final, cast

from qma.core.barriers.money_path import (
    MONEY_PATH_ACT_ALIASES,
    MONEY_PATH_BULK_VERBS,
    MONEY_PATH_COMPOUND_NOUNS,
    MONEY_PATH_DENIED_ACTS,
    MONEY_PATH_DENY_LIST,
    MONEY_PATH_DIRECTION_NOUNS,
    MONEY_PATH_FAMILY_NOUNS,
    MONEY_PATH_MONEY_NOUNS,
    MONEY_PATH_MONEY_VERBS,
    MONEY_PATH_MUTATING_VERBS,
    MONEY_PATH_PROTECTION_NOUNS,
    MONEY_PATH_READ_NOUNS,
    MONEY_PATH_READ_WORDS,
    MONEY_PATH_SCOPES_AFTER,
    MONEY_PATH_SCOPES_BEFORE,
    MONEY_PATH_TRAILING_WORDS,
    MoneyPathDenyError,
    match_money_path_act,
)
from qma.core.barriers.parent_surfaces import is_parent_surface_permitted

__all__ = ["check_descriptor", "description_money_act", "name_money_act"]

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
_VOCABULARY: Final = frozenset(
    {
        *(word for phrase in _PHRASES for word in phrase.split("_")),
        *(word for pair in MONEY_PATH_COMPOUND_NOUNS for word in pair),
        *MONEY_PATH_FAMILY_NOUNS,
        *MONEY_PATH_MONEY_NOUNS,
        *MONEY_PATH_MONEY_VERBS,
        *MONEY_PATH_MUTATING_VERBS,
        *MONEY_PATH_READ_WORDS,
        *MONEY_PATH_SCOPES_AFTER,
        *MONEY_PATH_SCOPES_BEFORE,
        *MONEY_PATH_TRAILING_WORDS,
    }
)
"""Every word with a role. Plurals fold onto it, and a lowercase run of them splits into it."""


def _splits(name: str) -> tuple[list[str], list[str]]:
    """The plain split breaks only at separators. The humped split also breaks at camelCase
    humps and letter-digit seams and drops digit words and a `v` before them, so `placeOrder`,
    `PlaceOrderV2` and `place_order2` read as `place_order`."""
    plain = [word for word in re.split(r"[\W_]+", name.casefold()) if word]
    raw = [word for word in re.split(r"[\W_]+", _BOUNDARY.sub("_", name).casefold()) if word]
    humped = [
        word
        for word, after in zip(raw, [*raw[1:], ""][: len(raw)], strict=True)
        if not word.isdigit() and not (word == "v" and after.isdigit())
    ]
    return plain, humped


def _suffix_act(words: list[str]) -> str | None:
    """The base rule: an act a word suffix names. Runs first and no allow-signal lifts it, so
    no name the base refused is ever allowed."""
    return next(
        (
            act
            for start in range(len(words))
            if (act := match_money_path_act("_".join(words[start:])))
        ),
        None,
    )


def _fold(word: str) -> str:
    for ending in ("es", "s"):
        if word.endswith(ending) and word.removesuffix(ending) in _VOCABULARY:
            return word.removesuffix(ending)
    return word


def _segment(word: str) -> list[str]:
    """A lowercase run of role words that holds a family noun (`placeorder`, `ordersend`)
    as its words; any other word unchanged."""
    if _fold(word) in _VOCABULARY or len(word) < 6:
        return [word]
    best: list[list[str] | None] = [[], *([None] * len(word))]
    for stop in range(1, len(word) + 1):
        best[stop] = min(
            (
                [*head, word[start:stop]]
                for start in range(stop)
                if (head := best[start]) is not None and _fold(word[start:stop]) in _VOCABULARY
            ),
            key=len,
            default=None,
        )
    pieces = best[-1]
    if pieces is None or not any(_fold(piece) in MONEY_PATH_FAMILY_NOUNS for piece in pieces):
        return [word]
    return pieces


def _words(raw: list[str]) -> list[str]:
    """`raw` with lowercase runs split, `open` before a listed noun read as an adjective
    (`open_positions`, `get_open_order`), plurals folded and compound nouns joined."""
    split = [piece for word in raw for piece in _segment(word)]
    reading = any(_fold(word) in MONEY_PATH_READ_WORDS for word in split)
    kept = [
        word
        for word, after in zip(split, [*split[1:], ""][: len(split)], strict=True)
        if not (
            word == "open"
            and _fold(after) in MONEY_PATH_FAMILY_NOUNS
            and (after != _fold(after) or reading)
        )
    ]
    folded = [_fold(word) for word in kept]
    joined: list[str] = []
    for word in folded:
        compound = MONEY_PATH_COMPOUND_NOUNS.get((joined[-1], word)) if joined else None
        if compound is not None:
            joined[-1] = compound
        else:
            joined.append(word)
    return joined


def _reads(words: list[str]) -> bool:
    """An allow-signal: a read word with no mutating verb (`get_open_positions`,
    `list_transfers`), or a last word naming a record (`kill_switch_status`)."""
    if words and words[-1] in MONEY_PATH_READ_NOUNS:
        return True
    return any(w in MONEY_PATH_READ_WORDS for w in words) and not any(
        w in MONEY_PATH_MUTATING_VERBS for w in words
    )


def _run_act(words: list[str]) -> str | None:
    """A multi-word act anywhere in the name, plurals folded (`arm_kill_switches`)."""
    count = len(words)
    runs = (
        run
        for start in range(count)
        for stop in range(start + 2, count + 1)
        if (run := "_".join(words[start:stop])) in _PHRASES
    )
    return next((matched for run in runs if (matched := match_money_path_act(run))), None)


def _scope_act(words: list[str]) -> str | None:
    """A bulk verb with a scope after it (`cancel_all`, `close_all_now`) or before it
    (`market_close`, `reqGlobalCancel`), ending the name. Never in a name with a read word, so
    `is_market_open` reads."""
    if any(word in MONEY_PATH_READ_WORDS for word in words):
        return None
    end = len(words)
    while end and words[end - 1] in MONEY_PATH_TRAILING_WORDS:
        end -= 1
    if end < 2:
        return None
    first, last = words[end - 2], words[end - 1]
    if first in MONEY_PATH_BULK_VERBS and last in MONEY_PATH_SCOPES_AFTER:
        return f"{first}_{last}"
    if last in MONEY_PATH_BULK_VERBS and first in MONEY_PATH_SCOPES_BEFORE:
        return f"{last}_{first}"
    return None


def _word_act(words: list[str]) -> str | None:
    """A money verb anywhere; else a family or money noun, or a direction ending the name,
    with any mutating verb in either order; else a protection noun ending the name; else a
    scoped bulk verb."""
    money = next((word for word in words if word in MONEY_PATH_MONEY_VERBS), None)
    if money is not None:
        return money
    verb = next((word for word in words if word in MONEY_PATH_MUTATING_VERBS), None)
    nouns = MONEY_PATH_FAMILY_NOUNS | MONEY_PATH_MONEY_NOUNS
    noun = next((word for word in words if word in nouns), None)
    if noun is None and words and words[-1] in MONEY_PATH_DIRECTION_NOUNS:
        noun = words[-1]
    if verb and noun:
        return f"{verb}_{noun}"
    if words and words[-1] in MONEY_PATH_PROTECTION_NOUNS:
        return "protection"
    return _scope_act(words)


def name_money_act(name: str) -> str | None:
    """The denied act a tool name spells, read through both splits: the base suffix rule
    first, then, unless an allow-signal reads the name, a multi-word act anywhere and the
    word rule."""
    splits = _splits(name)
    suffix = next((act for words in splits if (act := _suffix_act(words))), None)
    if suffix is not None:
        return suffix
    for raw in splits:
        words = _words(raw)
        if _reads(words):
            continue
        act = _run_act(words) or _word_act(words)
        if act is not None:
            return act
    return None


_REACH: Final = 3
"""Words a description's verb may stand before its object (`Places a market order`)."""


def description_money_act(text: str) -> str | None:
    """The act a description names as a verb with its object: a mutating or money verb
    followed, within `_REACH` words, by a family or money noun (`Places a market order`) or by
    the rest of a multi-word act (`Set the book mode`). A lone word (`size`, `transfer`, `buy`)
    or a noun without such a verb (`Get the current book mode`) names none."""
    words = _words(_splits(text)[0])
    verbs = MONEY_PATH_MUTATING_VERBS | MONEY_PATH_MONEY_VERBS
    nouns = MONEY_PATH_FAMILY_NOUNS | MONEY_PATH_MONEY_NOUNS
    for index, verb in enumerate(words):
        if verb not in verbs:
            continue
        for start in range(index + 1, min(index + 1 + _REACH, len(words))):
            if words[start] in nouns:
                return f"{verb}_{words[start]}"
            for stop in range(start + 1, len(words) + 1):
                phrase = "_".join([verb, *words[start:stop]])
                if phrase in _PHRASES and (act := match_money_path_act(phrase)):
                    return act
    return None


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
