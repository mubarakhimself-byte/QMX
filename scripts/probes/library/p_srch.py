"""P-SRCH (Library AD-8, SOLUTION-DESIGN 28.8): the grounder's precision and coverage on his real
`library.db` items, the truncation constants, and ranking under fan-out noise.

The grounder is the AD-8 shape: a normalised alias table (titles, tags, kind names) matched
longest-first against the question, FTS5 over the item text for candidates, a confidence that is
the share of the question's content terms the match covers, and an abstention below a threshold.
Ranking reads the producer's trust before recency (rule 7). The probe answers `questions.json`
on a read-only copy of his store, then reranks with every preview cut to its constant and
compares top 5s, then adds fan-out noise (test-run copies of each item) and checks the trusted
item still ranks first.

    uv run --no-sync --project qmx-agents python scripts/probes/library/p_srch.py
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from common import HIS_LIBRARY, HOMES, Log, Verdict, copy_read_only

QUESTIONS: Final = Path(__file__).with_name("questions.json")
TOP: Final = 5
CONFIDENCE_FLOOR: Final = 0.5
"""Claude's default: answer when the alias match covers at least half the content terms."""
PREVIEW_CHARS: Final = 200
SNIPPET_CHARS: Final = 120
NOISE_PER_ITEM: Final = 20
PASS_PRECISION: Final = 0.85
PASS_COVERAGE: Final = 0.70
TRUST: Final = {"live-run": 3, "operator": 2, "test-run": 0}
FALLBACK: Final = (
    "LIB3 tunes the constants and ranking features and reruns P-SRCH before it is appended."
)
STOP: Final = frozenset(
    [
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "my",
        "me",
        "show",
        "find",
        "open",
        "which",
        "what",
        "did",
        "do",
        "i",
        "have",
        "from",
        "with",
        "about",
        "named",
        "latest",
        "results",
        "result",
        "last",
    ]
)


@dataclass(frozen=True)
class Item:
    item_id: str
    kind: str
    title: str
    tags: tuple[str, ...]
    created: str
    text: str
    producer: str
    """`live-run`, `operator` or `test-run`; an item his store holds with no producer is his."""


@dataclass(frozen=True)
class Answer:
    ids: tuple[str, ...]
    confidence: float


def normalise(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def content_terms(text: str) -> list[str]:
    return [t for t in normalise(text).split() if t not in STOP]


def aliases(items: Iterable[Item]) -> dict[str, set[str]]:
    table: dict[str, set[str]] = {}
    for item in items:
        for alias in (item.title, item.kind, *item.tags):
            if key := normalise(alias):
                table.setdefault(key, set()).add(item.item_id)
    return table


def ground(question: str, items: Sequence[Item], table: Mapping[str, set[str]]) -> Answer:
    """Longest alias match first; FTS5-style term overlap only reorders what matched."""
    words = normalise(question).split()
    terms = content_terms(question)
    for size in range(len(words), 0, -1):
        for start in range(len(words) - size + 1):
            span = " ".join(words[start : start + size])
            if span in table:
                covered = [t for t in terms if t in span.split()]
                confidence = len(covered) / len(terms) if terms else 0.0
                matched = [i for i in items if i.item_id in table[span]]
                return Answer(tuple(i.item_id for i in rank(matched, terms)), confidence)
    return Answer((), 0.0)


def rank(items: Sequence[Item], terms: Sequence[str]) -> list[Item]:
    def key(item: Item) -> tuple[int, int, str]:
        overlap = sum(t in normalise(item.text) for t in terms)
        return (TRUST[item.producer], overlap, item.created)

    return sorted(items, key=key, reverse=True)


def load(path: Path) -> list[Item]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        found = [
            Item(
                item_id,
                str(fields.get("kind", "")),
                str(fields.get("title", "")),
                tuple(json.loads(fields.get("tags") or "[]")),
                str(fields.get("created", "")),
                text or "",
                "operator",
            )
            for item_id, data, text in db.execute(
                "SELECT i.id, i.data, s.text FROM items i LEFT JOIN search s ON s.id = i.id"
            )
            for fields in [json.loads(data)]
        ]
    db.close()
    return found


def distinct(items: Sequence[Item]) -> int:
    return len({(i.kind, i.title, i.tags, i.text) for i in items})


@dataclass(frozen=True)
class Score:
    precision: float
    coverage: float
    answered: int
    answerable: int


def score(answers: Sequence[Answer], expected: Sequence[Sequence[str]]) -> Score:
    """Precision: answered questions whose first id is expected. Coverage: answerable questions
    answered. An answer to a question that expects an abstention counts against precision."""
    answered = [
        (a, e) for a, e in zip(answers, expected, strict=True) if a.confidence >= CONFIDENCE_FLOOR
    ]
    right = sum(bool(a.ids) and a.ids[0] in e for a, e in answered)
    answerable = sum(bool(e) for e in expected)
    covered = sum(bool(e) for _, e in answered)
    return Score(
        right / len(answered) if answered else 0.0,
        covered / answerable if answerable else 0.0,
        len(answered),
        answerable,
    )


def verdict(found: Score, kept_top5: bool, noise_ok: bool, distinct_items: int) -> Verdict:
    """PASS at precision 0.85 or more and coverage 0.70 or more, with no truncation dropping a
    top-5 hit. A store with fewer than two distinct items cannot score a wrong grounding, so its
    numbers measure nothing and the probe fails."""
    numbers = {
        "precision": round(found.precision, 3),
        "coverage": round(found.coverage, 3),
        "answered": found.answered,
        "answerable": found.answerable,
        "truncation_keeps_top5": str(kept_top5),
        "noise_keeps_trusted_first": str(noise_ok),
        "distinct_items": distinct_items,
    }
    if distinct_items < 2:
        reason = "his store holds one distinct item, so no grounding can be wrong"
        return Verdict("P-SRCH", "FAIL", numbers, reason, FALLBACK)
    if found.precision >= PASS_PRECISION and found.coverage >= PASS_COVERAGE and kept_top5:
        return Verdict("P-SRCH", "PASS", numbers, "precision and coverage meet the line")
    return Verdict("P-SRCH", "FAIL", numbers, "precision, coverage or truncation misses", FALLBACK)


def main() -> None:
    log = Log("prb-l-srch-ops")
    home = HOMES / "p_srch"
    copy_read_only([HIS_LIBRARY], home)
    items = load(home / HIS_LIBRARY.name)
    asked = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    table = aliases(items)
    log.say(f"P-SRCH: {len(items)} items, {distinct(items)} distinct, {len(table)} aliases")
    answers = [ground(q["question"], items, table) for q in asked]
    found = score(answers, [q["expected"] for q in asked])

    cut = [replace(i, text=i.text[:PREVIEW_CHARS], title=i.title[:SNIPPET_CHARS]) for i in items]
    cut_table = aliases(cut)
    kept = all(
        ground(q["question"], cut, cut_table).ids[:TOP] == a.ids[:TOP]
        for q, a in zip(asked, answers, strict=True)
    )

    noise = [
        replace(i, item_id=f"{i.item_id}-noise{n}", producer="test-run", created="9999")
        for i in items
        for n in range(NOISE_PER_ITEM)
    ]
    noisy = [*items, *noise]
    noisy_table = aliases(noisy)
    trusted = {i.item_id for i in items}
    first = [ground(q["question"], noisy, noisy_table).ids[:1] for q in asked]
    noise_ok = all(not ids or ids[0] in trusted for ids in first)
    log.say(
        f"  truncation at preview {PREVIEW_CHARS} / title {SNIPPET_CHARS} keeps every top 5: "
        f"{kept}; with {len(noise)} newer test-run copies the first hit stays his: {noise_ok}"
    )
    for q, a in zip(asked, answers, strict=True):
        shown = "abstain" if a.confidence < CONFIDENCE_FLOOR else f"{len(a.ids)} ids"
        log.say(f"  {q['question']!r}: confidence {a.confidence:.2f} -> {shown}")
    log.verdict(verdict(found, kept, noise_ok, distinct(items)))


if __name__ == "__main__":
    main()
