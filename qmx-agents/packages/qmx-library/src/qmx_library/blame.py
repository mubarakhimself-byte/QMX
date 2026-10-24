"""Blame a text slot line by line without storing anything (AD-30).

`Store.blame` walks a version's first-parent chain to the root and calls `walk_back` once. A line
the diff says the parent already holds keeps travelling back; a line no ancestor holds was
introduced by the version that holds it, so it keeps that version's name. The answer is computed
at read, from the parents and one line diff per version.
"""

from __future__ import annotations

import difflib
from collections.abc import Sequence


def lines(text: str) -> list[str]:
    """The text as lines, each keeping its newline, so `"".join` gives the text back."""
    return text.splitlines(keepends=True)


def carried(parent: Sequence[str], child: Sequence[str]) -> dict[int, int]:
    """For each line index of `child` the diff calls unchanged, the matching index of `parent`."""
    found: dict[int, int] = {}
    matcher = difflib.SequenceMatcher(None, parent, child, autojunk=False)
    for tag, i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            continue
        for offset in range(j2 - j1):
            found[j1 + offset] = i1 + offset
    return found


def walk_back(chain: Sequence[Sequence[str]]) -> list[int]:
    """Which version of a youngest-first chain introduced each line of the youngest one.

    `chain[0]` is the blamed version's lines and `chain[-1]` the root's; the answer holds one
    index into `chain` per line of `chain[0]`.
    """
    if not chain:
        return []
    origin = [0] * len(chain[0])
    live = dict.fromkeys(range(len(chain[0])), 0) | {
        index: index for index in range(len(chain[0]))
    }
    for version in range(len(chain) - 1):
        kept = carried(chain[version + 1], chain[version])
        moved: dict[int, int] = {}
        for mine, held in live.items():
            if held in kept:
                moved[mine] = kept[held]
                origin[mine] = version + 1
        live = moved
        if not live:
            break
    return origin
