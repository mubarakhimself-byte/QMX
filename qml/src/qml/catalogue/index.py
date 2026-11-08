"""The dictionary's one-line index, and the search and sentence match over it (Part A AD-113).

``row`` turns an entry into one index row. ``find`` ranks rows by the words they share with a
query. ``match`` reads a text sentence by sentence and names the entry each sentence states, so a
source's every sentence is either known or comes back as an append request; a sentence matches an
entry only when it holds every word of one of the entry's names, so a match is never a guess.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, cast

from qml.catalogue.entry import Transfer, alias_key

__all__ = ["IndexRow", "Match", "MatchReport", "find", "match", "row", "stem", "words"]

_STOP: Final = frozenset(
    {"a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "and", "or", "is", "are"}
    | {"be", "it", "its", "as", "with", "from", "this", "that", "when", "then", "than", "one", "s"}
)
_USABLE: Final = frozenset({Transfer.NATIVE, Transfer.DIRECT, Transfer.ADAPTED})
_SENTENCE: Final = re.compile(r"[.!?;\n]+")


def stem(word: str) -> str:
    """A light stem so ``crosses``, ``crossed`` and ``crossing`` read as ``cross``."""
    for suffix in ("ing", "ed"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)]
    if word.endswith(("sses", "ches", "shes", "xes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")) and len(word) > 3:
        return word[:-1]
    return word


def words(text: str) -> tuple[str, ...]:
    """The stemmed words of ``text``, with stop words and bare numbers left out."""
    return tuple(stem(w) for w in alias_key(text).split() if w not in _STOP and not w.isdigit())


@dataclass(frozen=True, slots=True)
class IndexRow:
    entry_id: str
    version: int
    aliases: tuple[str, ...]
    family: str
    component_type: str
    output: str | None
    data_level: int | None
    status: str | None
    roles: tuple[str, ...]
    classes: tuple[str, ...]
    definition: str
    terms: frozenset[str]

    @property
    def pin(self) -> str:
        return f"{self.entry_id}@{self.version}"

    def names(self) -> tuple[tuple[str, ...], ...]:
        """Each of the entry's names as stemmed words: its id, then its aliases."""
        return tuple(n for n in (words(self.entry_id), *map(words, self.aliases)) if n)

    def as_json(self) -> dict[str, object]:
        level = "-" if self.data_level is None else str(self.data_level)
        return {
            "entry_id": self.entry_id,
            "version": self.version,
            "aliases": list(self.aliases),
            "family": self.family,
            "output": self.output,
            "data_level": self.data_level,
            "status": self.status,
            "line": f"{self.pin} | {self.component_type} | {self.output} | level {level} | "
            f"{self.status} | {self.definition}",
        }


def _strings(value: object) -> tuple[str, ...]:
    items = cast("list[object]", value) if isinstance(value, list) else []
    return tuple(v for v in items if isinstance(v, str))


def _text(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    return value if isinstance(value, str) else ""


def row(raw: Mapping[str, object], status: str | None) -> IndexRow:
    """The index row of one entry; ``data_level`` is the highest level its inputs need."""
    inputs = cast("list[object]", raw.get("inputs")) if isinstance(raw.get("inputs"), list) else []
    levels = [
        int(cast("int", p.get("data_level")))
        for p in (cast("Mapping[str, object]", i) for i in inputs if isinstance(i, Mapping))
        if isinstance(p.get("data_level"), int)
    ]
    output = raw.get("output")
    kind = cast("Mapping[str, object]", output).get("type") if isinstance(output, Mapping) else None
    transfer = raw.get("transfer")
    claims: Mapping[str, object] = (
        cast("Mapping[str, object]", transfer) if isinstance(transfer, Mapping) else {}
    )
    version = raw.get("version")
    entry_id, family, kind_name = (
        _text(raw, "entry_id"),
        _text(raw, "family"),
        _text(raw, "component_type"),
    )
    aliases, roles = _strings(raw.get("aliases")), _strings(raw.get("eligible_roles"))
    text = " ".join(
        [entry_id, *aliases, family, kind_name, *roles]
        + [_text(raw, k) for k in ("definition", "recognition")]
    )
    return IndexRow(
        entry_id=entry_id,
        version=version if isinstance(version, int) else 0,
        aliases=aliases,
        family=family,
        component_type=kind_name,
        output=kind if isinstance(kind, str) else None,
        data_level=max(levels) if levels else None,
        status=status,
        roles=roles,
        classes=tuple(sorted(c for c, t in claims.items() if t in _USABLE)),
        definition=_text(raw, "definition"),
        terms=frozenset(words(text)),
    )


def find(
    rows: Iterable[IndexRow],
    query: str,
    *,
    role: str | None = None,
    data_level: int | None = None,
    market_class: str | None = None,
    limit: int = 20,
) -> list[IndexRow]:
    """The rows sharing most words with ``query``, most first, then by pin. ``role`` keeps rows
    that may play it, ``data_level`` rows a market offering that level can feed, and
    ``market_class`` rows that carry to that class."""
    wanted = set(words(query))
    scored: list[tuple[int, IndexRow]] = []
    for found in rows:
        if role is not None and role not in found.roles:
            continue
        if data_level is not None and (found.data_level or 0) > data_level:
            continue
        if market_class is not None and market_class not in found.classes:
            continue
        score = len(wanted & found.terms) if wanted else 1
        if score:
            scored.append((score, found))
    scored.sort(key=lambda s: (-s[0], s[1].pin))
    return [found for _, found in scored[:limit]]


@dataclass(frozen=True, slots=True)
class Match:
    sentence: str
    entry: str | None


@dataclass(frozen=True, slots=True)
class MatchReport:
    """Each sentence with the pin it states or None, and an append request per unmatched one."""

    sentences: tuple[Match, ...]

    def as_json(self) -> dict[str, object]:
        return {
            "sentences": [
                {"sentence": m.sentence, "entry": m.entry or "unmatched"} for m in self.sentences
            ],
            "append_requests": [
                {"sentence": m.sentence, "words": list(words(m.sentence))}
                for m in self.sentences
                if m.entry is None
            ],
        }


def match(text: str, rows: Sequence[IndexRow]) -> MatchReport:
    """Each sentence of ``text`` and the entry whose longest name it holds every word of."""
    names = [(name, found.pin) for found in rows for name in found.names()]
    names.sort(key=lambda n: (-len(n[0]), n[1]))
    sentences: list[Match] = []
    for sentence in (s.strip() for s in _SENTENCE.split(text)):
        if not sentence:
            continue
        held = set(words(sentence))
        pin = next((p for name, p in names if set(name) <= held), None)
        sentences.append(Match(sentence, pin))
    return MatchReport(tuple(sentences))
