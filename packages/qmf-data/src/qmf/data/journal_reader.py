"""The committed reader: every reader of a live journal stream except its writer (AD-209).

It reads LF-terminated lines across a stream's rotation files and never writes, opens a
lock, or rebuilds an index. A line still in flight (no LF yet) at the tail of the last file
is left alone and read next time. The shipped CT-13 reader cannot be used here: its index
rebuild moves a torn tail to a ``.torn`` sidecar and truncates the data file, so it would
cut a writer's line in flight (``store/engines/jsonl.py``, ``_quarantine_torn_tail``).

A stream folder holds lines of two forms, both written by ``journal_writer``: a journal
record (``series``, ``t``, ``seq``, ``record``) and a series row of a store kind
(``series``, ``t``, ``row``). Stdlib + qmf-core.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qmf.core import Ok, Result, Retryability
from qmf.data.store.refusals import storage_failure

__all__ = ["CommittedLine", "JournalLine", "SeriesLine", "read_committed", "stream_folders"]

_ROTATION_FILE: Final[re.Pattern[str]] = re.compile(r"\A\d{6}\.jsonl\Z")


@dataclass(frozen=True, slots=True)
class JournalLine:
    """One journal record: its partition series, the writer's ``t`` and ``seq``."""

    series: str
    t: int
    seq: int
    record: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SeriesLine:
    """One series row of a store kind, each cell as the writer encoded it."""

    series: str
    t: int
    cells: tuple[str, ...]


CommittedLine = JournalLine | SeriesLine


def stream_folders(root: Path) -> tuple[Path, ...]:
    """Every stream folder under a writer root, sorted by name."""
    if not root.is_dir():
        return ()
    return tuple(sorted(entry for entry in root.iterdir() if entry.is_dir()))


def read_committed(stream_folder: Path) -> Result[tuple[CommittedLine, ...]]:
    """Every committed line of one stream, in append order; the files stay byte for byte."""
    files = sorted(
        entry for entry in stream_folder.iterdir() if _ROTATION_FILE.fullmatch(entry.name)
    )
    lines: list[CommittedLine] = []
    for index, path in enumerate(files):
        try:
            data = path.read_bytes()
        except OSError as exc:
            return storage_failure(
                "could not read a journal stream file",
                context={"file": str(path), "error": str(exc)},
            )
        end = data.rfind(b"\n") + 1
        if end != len(data) and index != len(files) - 1:
            return storage_failure(
                "a journal stream file other than the last ends mid-line",
                retryability=Retryability.NO,
                context={"file": str(path)},
            )
        for raw in data[:end].splitlines():
            line = _parse(raw)
            if line is None:
                return storage_failure(
                    "a journal stream holds a line that is not a journal line",
                    retryability=Retryability.NO,
                    context={"file": str(path), "line": raw[:200].decode("utf-8", "replace")},
                )
            lines.append(line)
    return Ok(tuple(lines))


def _parse(raw: bytes) -> CommittedLine | None:
    try:
        decoded: object = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(decoded, dict):
        return None
    item = cast("dict[str, object]", decoded)
    series, t = item.get("series"), item.get("t")
    if not isinstance(series, str) or not isinstance(t, int):
        return None
    seq, record, row = item.get("seq"), item.get("record"), item.get("row")
    if isinstance(seq, int) and isinstance(record, dict):
        return JournalLine(series, t, seq, cast("dict[str, object]", record))
    if isinstance(row, list):
        cells = cast("list[object]", row)
        if all(isinstance(cell, str) for cell in cells):
            return SeriesLine(series, t, tuple(cast("list[str]", cells)))
    return None
