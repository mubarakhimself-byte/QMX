"""Import the old recorder's calendar files once, into the calendar's bitemporal partitions.

The PC's scheduled task wrote one snapshot per fetch under `recorder/data/calendar/raw/` and one
line per fetch in `manifest.jsonl`. Both formats the provider served are read: the JSON the t3
template read, and the XML the recorder also kept. Every snapshot's own `fetched_at_utc` is its
observation time, which is what orders the rows; a snapshot's sha256 is its revision, so the same
bytes imported twice are one row set and a new snapshot is an append.

    uv run --no-sync python -m scripts.data.import_calendar_files \
        --recorder C:/Users/Mubarak/Desktop/QMX/recorder/data/calendar --root D:/Temp/calendar-import

A rerun adds nothing: the second run recomputes the same rows, gets the same fingerprints and the
store reports the writes idempotent.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from qmf.core import is_refusal
from qmf.data.calendar_feed import (
    CalendarEvent,
    calendar_key,
    decode_calendar_snapshot,
    decode_calendar_xml,
    land_calendar,
)
from qmf.data.series import SeriesStore

FORMATS: Final[tuple[str, ...]] = (".json", ".xml")


def instant_ns(text: str) -> int:
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return int(moment.astimezone(UTC).timestamp() * 1_000_000_000)


def manifest(recorder: Path) -> list[dict[str, object]]:
    path = recorder / "manifest.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text("utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue  # a torn line is the recorder's, not the import's
    return rows


def snapshot(recorder: Path, record: dict[str, object]) -> tuple[bytes, str, str] | None:
    """The bytes, their sha256 and the fetch time of one manifest record, or None."""
    relative = str(record.get("path") or "")
    fetched = str(record.get("fetched_at_utc") or "")
    if relative == "" or fetched == "":
        return None
    path = Path(relative)
    if not path.is_absolute():
        path = recorder.parents[1] / relative
    if not path.is_file() or path.suffix not in FORMATS:
        return None
    return path.read_bytes(), str(record.get("sha256") or path.stem), fetched


def decoded(
    body: bytes, *, known_at_ns: int, revision: str, suffix: str
) -> tuple[CalendarEvent, ...] | None:
    if suffix == ".xml":
        built = decode_calendar_xml(body, known_at_ns=known_at_ns, revision=revision)
    else:
        built = decode_calendar_snapshot(body, known_at_ns=known_at_ns, revision=revision)
    return None if is_refusal(built) else built.value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recorder", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    given = parser.parse_args()
    store = SeriesStore(given.root / "series")
    months: dict[tuple[int, int], list[CalendarEvent]] = {}
    seen = imported = 0
    for record in manifest(given.recorder):
        found = snapshot(given.recorder, record)
        if found is None:
            continue
        seen += 1
        body, revision, fetched = found
        suffix = Path(str(record.get("path"))).suffix
        events = decoded(
            body, known_at_ns=instant_ns(fetched), revision=revision[:12], suffix=suffix
        )
        if events is None:
            print(f"refused: {record.get('path')}", file=sys.stderr)
            continue
        imported += 1
        for event in events:
            moment = datetime.fromtimestamp(event.known_at_ns // 1_000_000_000, tz=UTC)
            months.setdefault((moment.year, moment.month), []).append(event)
    landed = 0
    rows = 0
    for (year, month), events in sorted(months.items()):
        key = calendar_key(year, month)
        if is_refusal(key):
            print(f"refused month {year}-{month:02d}: {key.context}", file=sys.stderr)
            continue
        written = land_calendar(
            store,
            key.value,
            events,
            correction=f"recorder snapshot imported {year}-{month:02d}",
        )
        if is_refusal(written):
            print(f"refused month {year}-{month:02d}: {written.context}", file=sys.stderr)
            continue
        if written.value is None:
            continue
        landed += 1
        rows += written.value.rows
    print(
        json.dumps(
            {
                "files_seen": seen,
                "files_imported": imported,
                "months_landed": landed,
                "rows": rows,
            },
            sort_keys=True,
        )
    )
    return 0 if imported else 1


if __name__ == "__main__":
    sys.exit(main())
