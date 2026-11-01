"""Re-check stored units with the current checker and mark the verdicts a changed rule touches.

A corpus folder holds each unit as ``<name>.json`` and its stored ``qmx.check/1`` verdicts,
oldest first, as ``<name>.verdicts.json`` (UT-03, AD-119). A verdict another checker gave is
re-checked. When the problems it found are unchanged, it stays current and records
``rechecked_with``. When they changed, it is marked ``superseded`` with the checker that
superseded it, and the new verdict is appended. A rerun with the same checker changes nothing.

    uv run python tools/qml/recheck_units.py CORPUS --records RECORDS [--blocks BLOCKS]

``RECORDS`` holds instrument record files, matched to each unit's markets by venue and symbol.
``BLOCKS`` holds ``<entry_id>/<version>/entry.json`` and ``block.py``, by default QML's own.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import cast

from qmf.core.refusal import is_refusal
from qml.check import check
from qml.check.result import checker_version
from qml.compile import CompileContext
from qml.numbers import InstrumentRecord, parse_record

import qml

_VERDICTS = ".verdicts.json"


class Status(StrEnum):
    CURRENT = "current"
    """Already checked by this checker; nothing ran."""
    CONFIRMED = "confirmed"
    """Re-checked by this checker, which found the same problems."""
    SUPERSEDED = "superseded"
    """Re-checked by this checker, which found other problems."""
    FIRST = "first"
    """No verdict was stored, so this is its first."""


def standing(verdicts: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    """The latest verdict not superseded, or ``None`` when none was stored."""
    kept = [v for v in verdicts if v.get("status") != Status.SUPERSEDED.value]
    return kept[-1] if kept else None


def recheck(
    verdicts: Sequence[Mapping[str, object]],
    version: str,
    current: Callable[[], Mapping[str, object]],
) -> tuple[Status, list[dict[str, object]]]:
    """The stored ``verdicts`` after re-checking under ``version``.

    ``current`` gives the current checker's ``qmx.check/1`` for the unit; it runs only when
    the standing verdict came from another checker.
    """
    stored = [dict(v) for v in verdicts]
    latest = cast("dict[str, object] | None", standing(stored))
    if latest is not None and latest.get("rechecked_with", latest["checker_version"]) == version:
        return Status.CURRENT, stored
    result = current()
    if latest is not None and latest.get("problem_set") == result.get("problem_set"):
        latest["rechecked_with"] = version
        return Status.CONFIRMED, stored
    if latest is not None:
        latest["status"] = Status.SUPERSEDED.value
        latest["superseded_by"] = version
    stored.append(dict(result))
    return (Status.FIRST if latest is None else Status.SUPERSEDED), stored


def _read(path: Path) -> object:
    return json.loads(path.read_text("utf-8"))


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", "utf-8")


def _records(folder: Path) -> dict[tuple[str, str], InstrumentRecord]:
    found: dict[tuple[str, str], InstrumentRecord] = {}
    for path in sorted(folder.glob("*.json")):
        parsed = parse_record(_read(path))
        if is_refusal(parsed):
            raise ValueError(f"{path}: {parsed.context}")
        found[(parsed.value.venue, parsed.value.symbol)] = parsed.value
    return found


def _context(
    document: object, blocks: Path, records: Mapping[tuple[str, str], InstrumentRecord]
) -> CompileContext:
    sources: dict[str, bytes] = {}
    entries: dict[str, bytes] = {}
    for entry in sorted(blocks.glob("*/*/entry.json")):
        pin = f"{entry.parent.parent.name}@{entry.parent.name}"
        entries[pin] = entry.read_bytes()
        if (entry.parent / "block.py").is_file():
            sources[pin] = (entry.parent / "block.py").read_bytes()
    by_market: dict[str, InstrumentRecord] = {}
    markets = cast("Mapping[str, object]", document).get("markets")
    for market in cast("list[Mapping[str, object]]", markets if isinstance(markets, list) else []):
        ref = cast("Mapping[str, object]", market.get("instrument_ref") or {})
        record = records.get((str(ref.get("venue")), str(ref.get("symbol"))))
        if record is not None:
            by_market[str(market.get("market_id"))] = record
    return CompileContext(sources=sources, entries=entries, records=by_market)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-check stored units and mark superseded verdicts."
    )
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument(
        "--blocks", type=Path, default=Path(qml.__file__).parent / "blocks" / "stdlib"
    )
    args = parser.parse_args(argv)
    corpus, blocks = cast("Path", args.corpus), cast("Path", args.blocks)
    records = _records(cast("Path", args.records))
    version = checker_version()
    counts = dict.fromkeys(Status, 0)
    for path in sorted(p for p in corpus.glob("*.json") if not p.name.endswith(_VERDICTS)):
        name = path.stem
        store = corpus / f"{name}{_VERDICTS}"
        document = _read(path)
        verdicts = cast("list[Mapping[str, object]]", _read(store) if store.is_file() else [])
        status, after = recheck(
            verdicts,
            version,
            lambda d=document: check(d, _context(d, blocks, records)).to_json(),
        )
        counts[status] += 1
        before, now = standing(verdicts), standing(after)
        was = "none" if before is None else before.get("verdict")
        print(f"{status.value} {name}: {was} -> {now.get('verdict') if now else 'none'}")
        if after != verdicts:
            _write(store, after)
    print(", ".join(f"{status.value} {count}" for status, count in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
