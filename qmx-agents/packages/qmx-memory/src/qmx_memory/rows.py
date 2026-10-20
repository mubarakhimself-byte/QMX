"""One memory row: a Library `memory-row` object as recall reads it (AD-18, SOLUTION-DESIGN 11.1).

The row is the record; the search index is derived from it and can be rebuilt from it at any
time. Identity is `scope`, `tag`, `intent_key`, `when_to_use`, `content` and `refs`, plus the
validity window `valid_from` and `valid_to` that says when the row is in force. `regime` is an
annotation: a row learnt in one market regime is still true evidence in another, so a matching
regime boosts a row instead of hiding it.

A row is never deleted. `forget` archives its item (Library AD-6) and removes it from the index,
so a rebuild reads only live items and cannot bring it back.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

SCOPES: tuple[str, ...] = ("run", "workflow", "home", "operator")
"""Where a row is written and who reads it (§11.1)."""

TAGS: tuple[str, ...] = (
    "built",
    "lesson",
    "dead_end",
    "do_not_retry",
    "negative_result",
    "procedure",
    "preference",
)
"""The closed tag list (§11.1)."""

SNAPSHOT_LINES: Mapping[str, int] = {"run": 100, "workflow": 200, "home": 400, "operator": 200}
"""Most rows one scope contributes to a snapshot (Claude's defaults, §11.1)."""

REGIME_BOOST = 1.25
"""How much a row learnt in the current regime outranks one learnt in another."""

TAINT_WEIGHT = 0.5
"""How much a row whose source is quarantined is down-weighted (Library AD-22)."""

MIN_SCORE = 0.0


def parse_time(text: str) -> datetime:
    """An ISO instant; a bare date reads as midnight UTC."""
    found = datetime.fromisoformat(text)
    return found if found.tzinfo is not None else found.replace(tzinfo=UTC)


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def memory_ref(scope: str, name: str = "") -> str:
    """The ref a row of `scope` lands on (§11.1): one writer per ref, so one namespace per scope."""
    match scope:
        case "run":
            return f"refs/runs/{name}"
        case "workflow":
            return f"refs/memory/wf/{name}"
        case "home":
            return f"refs/memory/home/{name}"
        case "operator":
            return "refs/memory/operator"
        case _:
            raise ValueError(f"{scope!r} is not a memory scope; the scopes are {', '.join(SCOPES)}")


@dataclass(frozen=True, slots=True)
class MemoryRow:
    """One row, read from its object's fields and annotations."""

    object_id: str
    item: str
    scope: str
    tag: str
    content: str
    when_to_use: str = ""
    refs: tuple[str, ...] = ()
    intent_key: str | None = None
    valid_from: str = ""
    valid_to: str | None = None
    regime: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    confidence: float = 1.0
    f: int = 0
    u: int = 0
    source_run_ids: tuple[str, ...] = ()
    learned_at: str = ""
    tainted: bool = False

    @classmethod
    def of(
        cls,
        object_id: str,
        item: str,
        fields: Mapping[str, object],
        annotations: Mapping[str, object] = {},
    ) -> MemoryRow:
        """The row two writers wrote: `fields` is its identity, `annotations` its learned state."""
        return cls(
            object_id=object_id,
            item=item,
            scope=str(fields.get("scope", "run")),
            tag=str(fields.get("tag", "lesson")),
            content=str(fields.get("content", "")),
            when_to_use=str(fields.get("when_to_use", "")),
            refs=tuple(str(ref) for ref in _list(fields.get("refs"))),
            intent_key=_text(fields.get("intent_key")),
            valid_from=str(fields.get("valid_from", "")),
            valid_to=_text(fields.get("valid_to")),
            regime=tuple(str(one) for one in _list(annotations.get("regime"))),
            keywords=tuple(str(word) for word in _list(annotations.get("keywords"))),
            confidence=_number(annotations.get("confidence"), 1.0),
            f=_whole(annotations.get("f")),
            u=_whole(annotations.get("u")),
            source_run_ids=tuple(str(one) for one in _list(annotations.get("source_run_ids"))),
            learned_at=str(annotations.get("learned_at", "")),
        )

    def indexed(self) -> str:
        """What the index holds: the row's own words, and what it is for."""
        return "\n".join(part for part in (self.when_to_use, self.content) if part)

    def tags(self) -> tuple[str, ...]:
        """The index tags a provider filters on: scope and tag first, then keywords, then refs."""
        return (self.scope, self.tag, *self.keywords, *self.refs)

    def live_at(self, at: datetime) -> bool:
        """Whether the row is in force at `at`: from `valid_from` up to, not including, `valid_to`."""
        if not self.valid_from:
            return True
        if parse_time(self.valid_from) > at:
            return False
        return self.valid_to is None or parse_time(self.valid_to) > at

    def weight(self, *, at: datetime, regime: Sequence[str]) -> float:
        """`confidence`, boosted by a matching regime and halved when its source is quarantined."""
        found = self.confidence
        if regime and self.regime and set(self.regime) & set(regime):
            found *= REGIME_BOOST
        if self.tainted:
            found *= TAINT_WEIGHT
        return found

    def tokens(self) -> int:
        """The row's cost against a snapshot or recall budget, in tokens (4 characters each)."""
        return max(1, len(self.indexed()) // 4)


def keep(
    rows: Iterable[MemoryRow],
    *,
    scopes: Sequence[str],
    tags: Sequence[str],
    at: datetime,
    regime: Sequence[str] = (),
) -> list[MemoryRow]:
    """The rows a read may answer from: its scopes, its tags, and live at `at`."""
    wanted = set(scopes)
    asked = set(tags)
    return [
        row
        for row in rows
        if (not wanted or row.scope in wanted)
        and (not asked or asked & {row.tag, *row.keywords})
        and row.live_at(at)
        and row.weight(at=at, regime=regime) > MIN_SCORE
    ]


def rendered(row: MemoryRow) -> str:
    """One line of a snapshot: the tag, what the row says and where it was learnt."""
    parts = [f"[{row.tag}]", row.content]
    if row.refs:
        parts.append(f"({', '.join(row.refs)})")
    return " ".join(parts)


def derived_from(row: Mapping[str, object]) -> tuple[str, ...]:
    """The `derived-from` targets a row names in its `relations` field, when it carries one."""
    found = row.get("derived_from")
    return tuple(str(one) for one in _list(found))


def _list(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)  # pyright: ignore[reportUnknownArgumentType]
    return []


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _number(value: object, default: float) -> float:
    return float(value) if isinstance(value, int | float) else default


def _whole(value: object) -> int:
    return int(value) if isinstance(value, int | float | str) else 0


def digest_text(blocks: Sequence[Mapping[str, object]], limit: int = 8_000) -> str:
    """A session's recorded blocks as one digest: the operator's and the model's words, cut at
    `limit` characters the way P-MEM's digest was."""
    lines: list[str] = []
    for block in blocks:
        text = str(block.get("text", "")).strip()
        if not text:
            continue
        who = str(block.get("role", block.get("type", "note")))
        lines.append(f"{who}: {text}")
    joined = "\n\n".join(lines)
    return joined if len(joined) <= limit else joined[:limit]


def row_fields(
    *,
    scope: str,
    tag: str,
    content: str,
    when_to_use: str,
    refs: Sequence[str] = (),
    intent_key: str | None = None,
    valid_from: str = "",
    valid_to: str | None = None,
) -> dict[str, object]:
    """The identity a row is written with, for a caller that has no Library objects to hand."""
    return {
        "scope": scope,
        "tag": tag,
        "when_to_use": when_to_use,
        "content": content,
        "refs": list(refs),
        "intent_key": intent_key,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


def as_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)
