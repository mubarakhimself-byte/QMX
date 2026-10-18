"""Money-path refusal for a tool descriptor, shared by every host that admits tools."""

from __future__ import annotations

import itertools
import re
from typing import Any, Final, cast

from qma.core.barriers.money_path import (
    MONEY_PATH_ACT_ALIASES,
    MONEY_PATH_BULK_CUTS,
    MONEY_PATH_BULK_OBJECTS,
    MONEY_PATH_BULK_QUALIFIERS,
    MONEY_PATH_BULK_VERBS,
    MONEY_PATH_COMPOUND_NOUNS,
    MONEY_PATH_CONJUNCTIONS,
    MONEY_PATH_DENIED_ACTS,
    MONEY_PATH_DENY_LIST,
    MONEY_PATH_DIRECTION_NOUNS,
    MONEY_PATH_FAMILY_NOUNS,
    MONEY_PATH_MONEY_NOUNS,
    MONEY_PATH_MONEY_VERBS,
    MONEY_PATH_MUTATING_VERBS,
    MONEY_PATH_NON_MONEY_OBJECTS,
    MONEY_PATH_NON_MONEY_QUALIFIERS,
    MONEY_PATH_ORDER_TYPES,
    MONEY_PATH_PROTECTION_NOUNS,
    MONEY_PATH_READ_NOUNS,
    MONEY_PATH_READ_WORDS,
    MONEY_PATH_SCOPES_AFTER,
    MONEY_PATH_SCOPES_BEFORE,
    MONEY_PATH_STOP_NOUN,
    MONEY_PATH_STRONG_BULK_VERBS,
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
        *MONEY_PATH_STRONG_BULK_VERBS,
        *MONEY_PATH_BULK_QUALIFIERS,
        *MONEY_PATH_ORDER_TYPES,
        *MONEY_PATH_NON_MONEY_OBJECTS,
        *MONEY_PATH_NON_MONEY_QUALIFIERS,
    }
)
"""Every word with a role. Plurals fold onto it, and a lowercase run of them splits into it."""


def _splits(name: str) -> tuple[list[str], list[str]]:
    """The plain split breaks only at separators. The humped split also breaks at camelCase
    humps and letter-digit seams and drops digit words and a `v` before them, so `placeOrder`,
    `PlaceOrderV2` and `place_order2` read as `place_order`."""
    plain = [word for word in re.split(r"[\W_]+", name.casefold()) if word]
    raw = [
        word
        for word in re.split(r"[\W_]+", _BOUNDARY.sub("_", name).casefold())
        if word
    ]
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


_BULK_ACTORS: Final = (
    MONEY_PATH_BULK_VERBS | MONEY_PATH_STRONG_BULK_VERBS | MONEY_PATH_MONEY_VERBS
)
_SPLIT_SCOPES: Final = (
    MONEY_PATH_SCOPES_AFTER | MONEY_PATH_SCOPES_BEFORE | MONEY_PATH_ORDER_TYPES
)


def _segment(word: str) -> list[str]:
    """A lowercase run of role words that holds a family noun (`placeorder`, `ordersend`), or
    a bulk or money verb with a scope (`cancelall`, `marketbuy`), as its words; any other word
    unchanged."""
    if _fold(word) in _VOCABULARY or len(word) < 6:
        return [word]
    best: list[list[str] | None] = [[], *([None] * len(word))]
    for stop in range(1, len(word) + 1):
        best[stop] = min(
            (
                [*head, word[start:stop]]
                for start in range(stop)
                if (head := best[start]) is not None
                and _fold(word[start:stop]) in _VOCABULARY
            ),
            key=len,
            default=None,
        )
    pieces = best[-1]
    if pieces is None:
        return [word]
    folded = {_fold(piece) for piece in pieces}
    family = bool(folded & MONEY_PATH_FAMILY_NOUNS)
    bulk = bool(folded & _BULK_ACTORS) and bool(folded & _SPLIT_SCOPES)
    return pieces if family or bulk else [word]


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


_VERBS: Final = MONEY_PATH_MUTATING_VERBS | MONEY_PATH_MONEY_VERBS


def _names_record(words: list[str]) -> bool:
    """The last word names a record and the rest spells no act (`kill_switch_status`,
    `sell_side_research`); `cancel_order_report`, `buy_report` and `arm_kill_switch_report`
    spell one. A money verb before `side` is a noun, and so is a run whose listed verb trails
    its first word (`kill_switch`)."""
    if not words or words[-1] not in MONEY_PATH_READ_NOUNS:
        return False
    nominal = [
        word
        for word, after in zip(words, [*words[1:], ""], strict=True)
        if not (word in MONEY_PATH_MONEY_VERBS and after == "side")
    ]
    acting_runs = (
        run
        for start in range(len(nominal))
        for stop in range(start + 2, len(nominal) + 1)
        if (run := nominal[start:stop])[0] in _VERBS
        or not any(word in _VERBS for word in run)
    )
    if any(
        match_money_path_act("_".join(run))
        for run in acting_runs
        if "_".join(run) in _PHRASES
    ):
        return False
    return _word_act(nominal) is None


def _reads(words: list[str]) -> bool:
    """An allow-signal: a read verb with no mutating verb (`get_open_positions`,
    `get_deposit_history`), or a last word naming a record of no act."""
    if _names_record(words):
        return True
    return any(
        w in MONEY_PATH_READ_WORDS - MONEY_PATH_READ_NOUNS for w in words
    ) and not any(w in MONEY_PATH_MUTATING_VERBS for w in words)


def _run_act(words: list[str]) -> str | None:
    """A multi-word act anywhere in the name, plurals folded (`arm_kill_switches`)."""
    count = len(words)
    runs = (
        run
        for start in range(count)
        for stop in range(start + 2, count + 1)
        if (run := "_".join(words[start:stop])) in _PHRASES
    )
    return next(
        (matched for run in runs if (matched := match_money_path_act(run))), None
    )


_READ_VERBS: Final = MONEY_PATH_READ_WORDS - MONEY_PATH_READ_NOUNS
_BULK_SCOPES: Final = (
    MONEY_PATH_SCOPES_AFTER
    | MONEY_PATH_SCOPES_BEFORE
    | MONEY_PATH_BULK_QUALIFIERS
    | MONEY_PATH_BULK_OBJECTS
)


def _bulk_head(words: list[str]) -> list[str]:
    """`words` up to the first `MONEY_PATH_BULK_CUTS` word, without trailing words or read
    nouns at the end (`close_all_by_symbol` and `cancel_all_report` read `close_all` and
    `cancel_all`)."""
    cut = next(
        (i for i, word in enumerate(words) if word in MONEY_PATH_BULK_CUTS), len(words)
    )
    head = words[:cut]
    while head and head[-1] in MONEY_PATH_TRAILING_WORDS | MONEY_PATH_READ_NOUNS:
        head.pop()
    return head


def _bulk_act(words: list[str]) -> str | None:
    """A strong bulk verb with a scope, qualifier or bulk object anywhere (`cancel_all_open`,
    `mass_cancel`, `flatten_book`), or alone beside other verbs and trailing words, read words
    too when a conjunction joins them (`cancel`, `cancelReplace`, `list_and_flatten`). A read
    noun never lifts it."""
    head = _bulk_head(words)
    strong = next(
        (
            word
            for word, after in zip(head, [*head[1:], ""][: len(head)], strict=True)
            if word in MONEY_PATH_STRONG_BULK_VERBS
            and not (word == "kill" and after == "switch")
        ),
        None,
    )
    if strong is None:
        return None
    scope = next((word for word in words if word in _BULK_SCOPES), None)
    if scope is not None:
        return f"{strong}_{scope}"
    joined = any(word in MONEY_PATH_CONJUNCTIONS for word in head)
    alone = (
        _VERBS
        | MONEY_PATH_STRONG_BULK_VERBS
        | MONEY_PATH_CONJUNCTIONS
        | (MONEY_PATH_READ_WORDS if joined else frozenset[str]())
    )
    return strong if all(word in alone for word in head) else None


def _scope_act(words: list[str]) -> str | None:
    """A bulk verb with a scope after it (`cancel_all`, `close_all_by_symbol`) or before it
    (`market_close_status`, `reqGlobalCancel`), ending the name's `_bulk_head`. Never in a name
    with a read verb, so `is_market_open` reads."""
    if any(word in _READ_VERBS for word in words):
        return None
    head = _bulk_head(words)
    if len(head) < 2:
        return None
    first, last = head[-2], head[-1]
    if first in MONEY_PATH_BULK_VERBS and last in MONEY_PATH_SCOPES_AFTER:
        return f"{first}_{last}"
    if last in MONEY_PATH_BULK_VERBS and first in MONEY_PATH_SCOPES_BEFORE:
        return f"{last}_{first}"
    return None


def _object_noun(words: list[str], index: int, nouns: frozenset[str]) -> bool:
    """`words[index]` is one of `nouns`, not a setting (`set_display_currency`) and not the
    subject of a non-money record right after it (`add_trade_note`, `add_coin_to_watchlist`)."""
    after = words[index + 1 : index + 3]
    record = after == ["to", "watchlist"] or (
        bool(after) and after[0] in MONEY_PATH_NON_MONEY_OBJECTS
    )
    return (
        words[index] in nouns
        and not record
        and (index == 0 or words[index - 1] not in MONEY_PATH_NON_MONEY_QUALIFIERS)
    )


_NAME_NOUNS: Final = (
    MONEY_PATH_FAMILY_NOUNS | MONEY_PATH_MONEY_NOUNS | {MONEY_PATH_STOP_NOUN}
)


def _word_act(words: list[str]) -> str | None:
    """A money verb anywhere; else a mutating verb with a family or money noun at another word,
    or a direction ending the name (`_object_noun`); else a protection noun ending the name;
    else a bulk qualifier or an order type with `order`; else a scoped bulk verb."""
    money = next((word for word in words if word in MONEY_PATH_MONEY_VERBS), None)
    if money is not None:
        return money
    last = len(words) - 1
    pair = next(
        (
            f"{verb}_{words[j]}"
            for i, verb in enumerate(words)
            if verb in MONEY_PATH_MUTATING_VERBS
            for j in range(len(words))
            if j != i
            and (
                _object_noun(words, j, _NAME_NOUNS)
                or (j == last and words[j] in MONEY_PATH_DIRECTION_NOUNS)
            )
        ),
        None,
    )
    if pair is not None:
        return pair
    if words and words[-1] in MONEY_PATH_PROTECTION_NOUNS:
        return "protection"
    family = next((word for word in words if word in MONEY_PATH_FAMILY_NOUNS), None)
    qualifier = next(
        (word for word in words if word in MONEY_PATH_BULK_QUALIFIERS), None
    )
    if family is not None and qualifier is not None:
        return f"{qualifier}_{family}"
    kind = next(
        (
            word
            for pair in itertools.pairwise(words)
            if "order" in pair
            for word in pair
            if word in MONEY_PATH_ORDER_TYPES
        ),
        None,
    )
    if kind is not None:
        return f"{kind}_order"
    return _scope_act(words)


def name_money_act(name: str) -> str | None:
    """The denied act a tool name spells, read through both splits: the base suffix rule
    first; then, unless an allow-signal reads the name, a multi-word act anywhere and the word
    rule; then a bulk act, which no read noun lifts."""
    splits = _splits(name)
    suffix = next((act for words in splits if (act := _suffix_act(words))), None)
    if suffix is not None:
        return suffix
    for raw in splits:
        words = _words(raw)
        act = None if _reads(words) else _run_act(words) or _word_act(words)
        act = act or _bulk_act(words) or _scope_act(words)
        if act is not None:
            return act
    return None


_REACH: Final = 3


def description_money_act(text: str) -> str | None:
    """The act a description names as a verb with its object: a mutating or money verb
    followed, within `_REACH` words, by a family or money noun (`Places a market order`) or by
    the rest of a multi-word act (`Set the book mode`). A lone word (`size`, `transfer`, `buy`),
    a noun without such a verb (`Get the current book mode`) or a setting (`Update the display
    currency`) names none."""
    words = _words(_splits(text)[0])
    verbs = MONEY_PATH_MUTATING_VERBS | MONEY_PATH_MONEY_VERBS
    nouns = MONEY_PATH_FAMILY_NOUNS | MONEY_PATH_MONEY_NOUNS
    for index, verb in enumerate(words):
        if verb not in verbs:
            continue
        for start in range(index + 1, min(index + 1 + _REACH, len(words))):
            if _object_noun(words, start, nouns):
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
