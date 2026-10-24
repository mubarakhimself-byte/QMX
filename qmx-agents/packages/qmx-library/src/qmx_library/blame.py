"""Blame a text slot line by line without storing anything (AD-30).

A line travels back from the blamed version through whichever parent the diff says already holds
it, first parent first, until no parent holds it; the version it stops in introduced that line.
Walking every parent (not just the first) is what makes a merge honest: a line that arrived from
the second side of a merge is blamed on the version that wrote it, not on the merge that carried
it in. The answer is computed at read, from the parents and one line diff per version and parent.
"""

from __future__ import annotations

import difflib
from collections.abc import Mapping, Sequence


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


def origins(
    target: str,
    text: Mapping[str, list[str]],
    parents: Mapping[str, Sequence[str]],
) -> list[str]:
    """The version that introduced each line of `target`, in line order."""
    diffs: dict[tuple[str, str], dict[int, int]] = {}
    found: list[str] = []
    for index in range(len(text[target])):
        here, at = target, index
        while True:
            moved: tuple[str, int] | None = None
            for parent in parents.get(here, ()):
                if parent not in text:
                    continue
                kept = diffs.get((here, parent))
                if kept is None:
                    kept = diffs[(here, parent)] = carried(text[parent], text[here])
                if at in kept:
                    moved = (parent, kept[at])
                    break
            if moved is None:
                break
            here, at = moved
        found.append(here)
    return found
