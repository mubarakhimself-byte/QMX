"""Fan-out by chunk (ruling 78, AD-34): a `chunk` edge splits its item list into chunks, and one
partition runs per chunk, never one per item.

With `by: items` a chunk holds `size` items (falling back to the `chunk.size` setting). With
`by: tokens` a chunk fills to `fill` times the resolved model's context window (falling back to
`chunk.fill` and `context_window`), so a 1M-token model takes about 300k tokens of items at 0.3; an
item larger than that gets a chunk of its own. The window and the token count come from the model's
registry row when there is one: the row's `chars_per_token` when the row does not count tokens
itself, with 10 % headroom (Claude's default 3, AD-34; the built bytes ÷ 4 estimate without a row).
A partition id is the chunk's index, so the same item list always gives the same ids.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final, NamedTuple

from pydantic import JsonValue
from qmx_ledger.journal import encoded

from qmx_engine.definition.model import Chunk
from qmx_engine.ports.router import Row

RUN_SETTINGS: Final = ("chunk.size", "chunk.fill", "context_window")
"""The settings a run records on `run_created` for the core to read."""
CHARS_PER_TOKEN: Final = 4
"""The estimate without a model row: a quarter of an item's canonical JSON bytes."""
HEADROOM: Final = 1.1
"""Byte estimates are conservative by 10 % when the row cannot count its own tokens."""


class ChunkError(ValueError):
    """The chunk spec or the run's settings cannot size a chunk."""


class Span(NamedTuple):
    """Items `start` up to, not including, `end`, and their estimated tokens."""

    start: int
    end: int
    tokens: int


def estimate(item: JsonValue, row: Row | None = None) -> int:
    """Tokens in an item: its canonical JSON bytes over the row's `chars_per_token`, with 10 %
    headroom when the row cannot count its own tokens, else a quarter of the bytes."""
    size = len(encoded(item))
    if row is None:
        return -(-size // CHARS_PER_TOKEN)
    factor = 1.0 if row.count_tokens else HEADROOM
    return math.ceil(size * factor / (row.chars_per_token or CHARS_PER_TOKEN))


def _setting(settings: Mapping[str, JsonValue], key: str) -> float:
    value = settings.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        raise ChunkError(f"the run recorded no positive {key} setting")
    return value


def chunks(
    items: Sequence[JsonValue],
    spec: Chunk,
    settings: Mapping[str, JsonValue],
    row: Row | None = None,
) -> list[Span]:
    sizes = [estimate(item, row) for item in items]
    if spec.by == "items":
        size = spec.size or int(_setting(settings, "chunk.size"))
        return [
            Span(start, min(start + size, len(items)), sum(sizes[start : start + size]))
            for start in range(0, len(items), size)
        ]
    fill = spec.fill or _setting(settings, "chunk.fill")
    window = row.window if row is not None else int(_setting(settings, "context_window"))
    cap = int(fill * window)
    spans: list[Span] = []
    start = total = 0
    for index, size in enumerate(sizes):
        if index > start and total + size > cap:
            spans.append(Span(start, index, total))
            start, total = index, 0
        total += size
    if start < len(items):
        spans.append(Span(start, len(items), total))
    return spans
