"""Library search, parse-first (Library AD-8): ground, walk, rank, cite. No model runs here.

The grounder maps the question to items by the longest spans that are an item's title, tag or
alias (`bridge`) or the kind of an item (`filter`), over `catalog.db`'s parsed rows. Only plain
facts refuse: nothing matched, only archived items matched, nothing alive as of the date asked.
Everything else is handed on with a confidence and the thin-evidence signals, and the answering
step abstains below `CONFIDENCE_FLOOR`. Grounded items come first, each other result with the
relation that admitted it; within each tier the producer's trust ranks before text and recency,
so fan-out test output never outranks a trusted item.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final, cast

from qmx_library.fts import TRUST, Catalog, norm
from qmx_library.port import (
    Answer,
    AsOf,
    JsonObject,
    LibraryRefused,
    Match,
    ObjectId,
    Refusal,
    Result,
    Role,
    Signal,
)
from qmx_library.principal import MAIN, Principal, state_ref
from qmx_library.store import Store

PREVIEW_CHARS: Final = 200
"""Characters of an item's indexed text the answering step reads per result. Ranking reads the
same preview, so the cut is a tested setting (AD-8 (8)): it must keep every top 5."""
CONFIDENCE_FLOOR: Final = 0.5
"""Claude's default: answer when the matched spans cover at least half the question's content
words."""
FILTER_WEIGHT: Final = 0.5
"""A kind name says what sort of thing is meant, not which one, so it covers half a word."""
MIN_WORD: Final = 4
"""A one-word alias shorter than this never matches (LLD section 5)."""
WALK_DEPTH: Final = 1
PAGE_SLOT: Final = re.compile(r"pages/(\d+)")
"""A slot extraction writes one page of a document into (Library AD-27)."""
STAMP: Final = re.compile(r"\[(?:(\d+):)?(\d{1,2}):(\d{2})\]")
"""A transcript's `[mm:ss]` or `[hh:mm:ss]` marker at the start of a line (AD-4, AD-27)."""
STOP: Final = frozenset(
    {
        "a",
        "about",
        "all",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "by",
        "did",
        "do",
        "find",
        "for",
        "from",
        "have",
        "i",
        "in",
        "is",
        "it",
        "its",
        "last",
        "latest",
        "me",
        "my",
        "named",
        "of",
        "on",
        "open",
        "or",
        "our",
        "result",
        "results",
        "show",
        "that",
        "the",
        "these",
        "this",
        "to",
        "was",
        "we",
        "what",
        "which",
        "with",
    }
)
"""Ordinary words a question carries that name no item."""


def singular(word: str) -> str:
    return word[:-1] if len(word) > MIN_WORD and word.endswith("s") and word[-2] != "s" else word


@dataclass(frozen=True, slots=True)
class Grounded:
    matches: tuple[Match, ...]
    confidence: float


def ground(catalog: Catalog, text: str) -> Grounded:
    """Longest spans first; a matched span's words are not matched again."""
    words = norm(text).split()
    windows = [
        (start, size) for size in range(len(words), 0, -1) for start in range(len(words) - size + 1)
    ]

    def forms(start: int, size: int) -> list[str]:
        window = words[start : start + size]
        if size == 1 and (len(window[0]) < MIN_WORD or window[0] in STOP):
            return []
        return list(dict.fromkeys([" ".join(window), " ".join(map(singular, window))]))

    found: dict[str, list[tuple[str, Role]]] = {}
    for span, item, role in catalog.matching({f for w in windows for f in forms(*w)}):
        found.setdefault(span, []).append((item, role))
    taken: dict[int, Role] = {}
    matches: list[Match] = []
    for start, size in windows:
        positions = range(start, start + size)
        if any(p in taken for p in positions):
            continue
        for form in forms(start, size):
            if form in found:
                hits = sorted(found[form], key=lambda hit: hit[1])
                matches.extend(Match(item, form, role) for item, role in hits)
                role: Role = "bridge" if any(r == "bridge" for _, r in hits) else "filter"
                taken.update(dict.fromkeys(positions, role))
                break
    content = [p for p, w in enumerate(words) if w not in STOP and singular(w) not in STOP]
    weight = {"bridge": 1.0, "filter": FILTER_WEIGHT}
    covered = sum(weight[taken[p]] for p in content if p in taken)
    confidence = covered / len(content) if content else float(bool(matches))
    return Grounded(tuple(matches), round(confidence, 3))


def _entry(
    store: Store, who: Principal, item: str, as_of: AsOf | None, include_archived: bool
) -> tuple[ObjectId | None, bool]:
    """The object a result shows for `item` (its `main` head first) and whether it was archived
    then; `None` when no ref held an object of `item` by `as_of`."""
    refs = store.catalog.placed_refs(item)
    head: ObjectId | None = None
    for ref in sorted(refs, key=lambda r: r != MAIN):
        try:
            head = store.resolve(who, item, ref, as_of=as_of)
        except LibraryRefused:
            continue
        break
    if as_of is None:
        archived = store.catalog.state(item) == "archived"
    else:
        try:
            archived = store.resolve(who, item, state_ref(item), as_of=as_of) == "archived"
        except LibraryRefused:
            archived = False
    return head, archived and not include_archived


def answer(
    store: Store,
    who: Principal,
    text: str,
    *,
    as_of: AsOf | None = None,
    include_archived: bool = False,
    limit: int = 20,
    offset: int = 0,
    preview_chars: int | None = PREVIEW_CHARS,
) -> Answer:
    """`preview_chars` None reads each item's whole indexed text; the truncation check compares.
    `offset` reads the next page of the same ranked answer (AD-27)."""
    catalog = store.catalog
    grounded = ground(catalog, text)
    if not grounded.matches:
        return Answer("no_entry_point", 0.0, True, (), (), ())
    roles: dict[str, Role] = {}
    for match in grounded.matches:
        if roles.get(match.item) != "bridge":
            roles[match.item] = match.role
    entries: dict[str, ObjectId] = {}
    archived = 0
    for item in roles:
        head, hidden = _entry(store, who, item, as_of, include_archived)
        if head is not None and hidden:
            archived += 1
        elif head is not None:
            entries[item] = head
    if not entries:
        refused: Refusal = "only_archived_or_superseded" if archived else "no_evidence_as_of"
        return Answer(refused, grounded.confidence, True, (), grounded.matches, ())

    reached: dict[str, tuple[ObjectId, str, str]] = {}
    for item, head in entries.items():
        for step in store.walk(who, [head], direction="both", depth=WALK_DEPTH, as_of=as_of):
            row = catalog.row(step.object_id)
            other = "" if row is None else str(row[1])
            if other and other not in entries and other not in reached:
                _, hidden = _entry(store, who, other, as_of, include_archived)
                if not hidden:
                    reached[other] = (step.object_id, step.via, item)

    terms = {singular(w) for w in norm(text).split() if w not in STOP}
    ranked: list[tuple[tuple[int, int, int, int, int], Result]] = []
    candidates = [(item, head, None, None) for item, head in entries.items()]
    candidates += [(item, oid, via, source) for item, (oid, via, source) in reached.items()]
    texts = catalog.texts([object_id for _, object_id, _, _ in candidates])
    for item, object_id, via, source in candidates:
        row = catalog.row(object_id)
        if row is None:
            continue
        indexed = texts.get(object_id, "")
        preview = indexed if preview_chars is None else indexed[:preview_chars]
        producer = catalog.producer(object_id)
        cited = catalog.citations(item)
        seen = {singular(w) for w in norm(f"{row[4]} {preview}").split()}
        tier = 2 if via is not None else 0 if roles[item] == "bridge" else 1
        key = (tier, -TRUST[producer], -len(terms & seen), -cited, -catalog.placed_seq(object_id))
        result = Result(
            object_id, item, str(row[2]), str(row[4]), preview, producer, cited, via, source
        )
        ranked.append((key, result))
    ranked.sort(key=lambda pair: pair[0])
    results = tuple(r for _, r in ranked[offset : offset + limit])
    signals: list[Signal] = []
    if all(m.role == "filter" for m in grounded.matches):
        signals.append("too_few_concepts")
    if not reached:
        signals.append("no_path")
    if not any(r.preview for r in results):
        signals.append("no_quotable_terminal")
    return Answer(
        None,
        grounded.confidence,
        grounded.confidence < CONFIDENCE_FLOOR,
        tuple(signals),
        grounded.matches,
        results,
    )


def _slot_text(store: Store, blob: dict[str, Any]) -> str:
    try:
        return store.read_blob(str(blob["sha256"])).decode("utf-8", "replace")
    except (LibraryRefused, KeyError):
        return ""


def locate(store: Store, object_id: ObjectId, phrase: str) -> JsonObject | None:
    """Where in its source a phrase sits: `{"page": n}` or `{"seconds": n}` (AD-4, AD-27).

    A document extraction writes one `pages/<n>` slot per page, so the page is the slot the phrase
    is in and a hit can open there. An audio extraction writes a `transcript` with a `[mm:ss]`
    marker per segment, so the minute is the last marker before the phrase.
    """
    blobs = cast(
        dict[str, dict[str, Any]],
        store.manifest(object_id).get("blobs") or {},
    )
    words = [re.escape(word) for word in phrase.split()]
    if not words:
        return None
    wanted = re.compile(r"\s+".join(words), re.IGNORECASE)
    pages = sorted(
        (int(found.group(1)), slot)
        for slot in blobs
        if (found := PAGE_SLOT.fullmatch(slot)) is not None
    )
    for number, slot in pages:
        if wanted.search(_slot_text(store, blobs[slot])):
            return {"page": number}
    transcript = blobs.get("transcript")
    if transcript is not None:
        text = _slot_text(store, transcript)
        found = wanted.search(text)
        if found is not None:
            stamps = list(STAMP.finditer(text, 0, found.start()))
            if stamps:
                stamp = stamps[-1]
                hours = int(stamp.group(1) or 0)
                return {
                    "seconds": hours * 3600 + int(stamp.group(2)) * 60 + int(stamp.group(3))
                }
    return None
