"""Agents read journals through one door and write notes only (Part B AD-211, journals.md §8).

`journal_query` answers from this machine's journal partitions, which the host's harvester files
every minute on This PC (`qmx_host.records`), closed and open months alike. It takes a required
time window, and a window past the data says where the data stops. Rows written after the fact
(`backfilled`) are left out unless asked for (JR-08). Three views:

- `rows`: the journal rows themselves;
- `trades_with_context`: each unit `signal` and `trade` row with the market journal's `minute`
  row of its market and minute beside it, so "why didn't it trade at 08:00?" reads the reason code
  and the spread at that minute together;
- `digest`: a script-made count per unit, market and UTC day: decisions by outcome and reason,
  trades, and their R.

`notes_write` lands an agent's analysis as a `note` item (version 2), never as a journal row
(JR-11). Neither door writes a trade, a `bot` or a `strategy`.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Final, Literal, cast

from qmf.core import is_refusal
from qmf.data.journal_writer import key_token
from qmf.data.series import STATE_NAME, SeriesKey, SeriesStore
from qmx_library.port import Draft, JsonObject

__all__ = [
    "NOTE_KINDS",
    "STREAMS",
    "JournalRow",
    "journal_query",
    "note_draft",
    "parse_instant",
]

MARKET_FOLDER: Final = "market"
"""The market-data door's root under a QMX folder (`qmx_host.host.MARKET`); its partitions sit in
its `series` folder."""
STREAMS: Final = ("unit", "market", "node", "readings")
ENVELOPE_FILTERS: Final = frozenset(
    {
        "kind",
        "record_id",
        "world",
        "unit_id",
        "unit_version",
        "market_id",
        "venue",
        "account",
        "platform",
        "machine",
        "run_id",
        "trace_id",
        "writer_id",
    }
)
"""The envelope fields a query may filter on, each by equality."""
NOTE_KINDS: Final = ("analysis", "proposal", "lesson", "forecast_ref", "disagreement")
CONTEXT_KINDS: Final = frozenset({"signal", "trade"})
NS_PER_MS: Final = 1_000_000
MS_PER_MINUTE: Final = 60_000

type View = Literal["rows", "trades_with_context", "digest"]


def parse_instant(value: object, name: str) -> int:
    """A window edge as epoch nanoseconds: an ISO 8601 time (`2025-01-02T08:00:00Z`, UTC when it
    names no zone) or a whole number of nanoseconds."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            pass
        else:
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=UTC)
            return int(moment.timestamp()) * 1_000_000_000 + moment.microsecond * 1_000
    raise ValueError(
        f"window.{name} is an ISO 8601 time such as 2025-01-02T08:00:00Z or epoch nanoseconds; "
        f"got {value!r}"
    )


def _iso(t_ms: int) -> str:
    moment = datetime.fromtimestamp(t_ms / 1_000, tz=UTC)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class JournalRow:
    """One journal row as a partition holds it: its key, the writer's `t` and `seq`, the record."""

    key: SeriesKey
    t: int
    seq: int
    record: Mapping[str, Any]

    def concise(self) -> dict[str, Any]:
        found: dict[str, Any] = {"at": _iso(self.t), "kind": self.record.get("kind")}
        for name in ("record_id", "world", "unit_id", "market_id", "machine"):
            if name in self.record:
                found[name] = self.record[name]
        found["body"] = self.record.get("body", {})
        return found

    def detailed(self) -> dict[str, Any]:
        return {"partition": self.key.text, "t": self.t, "seq": self.seq, "record": self.record}


def _series_folders(root: Path, stream: str, filters: Mapping[str, str]) -> list[Path]:
    """The series folders of one stream, narrowed by a subject or kind filter."""
    base = root / f"journal-{stream}"
    if not base.is_dir():
        return []
    subject = filters.get("unit_id") if stream == "unit" else filters.get("market_id")
    if stream not in ("unit", "market"):
        subject = None
    found: list[Path] = []
    for subject_dir in sorted(base.iterdir()):
        if subject is not None and subject_dir.name != key_token(subject):
            continue
        for kind_dir in sorted(subject_dir.iterdir()):
            if "kind" in filters and kind_dir.name != filters["kind"]:
                continue
            found.extend(sorted(path for path in kind_dir.iterdir() if path.is_dir()))
    return found


def _month_key(stream: str, folder: Path, month: Path) -> SeriesKey | None:
    year, _, number = month.name.partition("-")
    if not (year.isdigit() and number.isdigit()):
        return None
    variant = folder.name
    made = SeriesKey.try_create(
        f"journal-{stream}",
        folder.parent.parent.name,
        folder.parent.name,
        int(year),
        int(number),
        "" if variant == "-" else variant,
    )
    return None if is_refusal(made) else made.value


def _matches(record: Mapping[str, Any], filters: Mapping[str, str]) -> bool:
    return all(str(record.get(name)) == value for name, value in filters.items())


def _rows(store: SeriesStore, key: SeriesKey) -> list[JournalRow] | None:
    """One partition's rows, or None when the store cannot read it."""
    read = store.read(key)
    if is_refusal(read):
        return None
    rows: list[JournalRow] = []
    for row in read.value.rows:
        try:
            record = json.loads(str(row["record"]))
        except ValueError:
            return None
        rows.append(
            JournalRow(key, int(cast("int", row["t"])), int(cast("int", row["seq"])), record)
        )
    return rows


@dataclass(frozen=True, slots=True)
class _Found:
    rows: list[JournalRow]
    last_t: int | None
    backfilled: int
    unreadable: list[str]


def _read(
    root: Path,
    stream: str,
    start_ns: int,
    end_ns: int,
    filters: Mapping[str, str],
    backfilled: bool,
) -> _Found:
    store = SeriesStore(root)
    rows: list[JournalRow] = []
    last: int | None = None
    left_out = 0
    unreadable: list[str] = []
    for folder in _series_folders(root, stream, filters):
        months = [
            (key, month)
            for month in sorted(folder.iterdir())
            if (month / STATE_NAME).is_file() and (key := _month_key(stream, folder, month))
        ]
        for index, (key, _month) in enumerate(months):
            overlaps = key.start_ns < end_ns and start_ns < key.end_ns
            newest = index == len(months) - 1
            if not (overlaps or newest):
                continue
            found = _rows(store, key)
            if found is None:
                unreadable.append(key.text)
                continue
            for row in found:
                if not _matches(row.record, filters):
                    continue
                last = row.t if last is None else max(last, row.t)
                if not start_ns <= row.t * NS_PER_MS < end_ns:
                    continue
                if row.record.get("backfilled") is True and not backfilled:
                    left_out += 1
                    continue
                rows.append(row)
    rows.sort(key=lambda row: (row.t, row.key.text, row.seq))
    return _Found(rows, last, left_out, unreadable)


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal(0)


def _digest(rows: Iterable[JournalRow]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        kind = row.record.get("kind")
        if kind not in CONTEXT_KINDS:
            continue
        day = _iso(row.t)[:10]
        key = (str(row.record.get("unit_id")), str(row.record.get("market_id")), day)
        group = groups.setdefault(
            key,
            {"outcomes": Counter[str](), "reasons": Counter[str](), "trades": 0, "r": Decimal(0)},
        )
        body = cast("Mapping[str, Any]", row.record.get("body", {}))
        if kind == "signal":
            group["outcomes"][str(body.get("outcome"))] += 1
            if "reason" in body:
                group["reasons"][str(body["reason"])] += 1
        else:
            group["trades"] += 1
            group["r"] += _decimal(body.get("r", 0))
    return [
        {
            "unit_id": unit,
            "market_id": market,
            "day": day,
            "decisions": sum(group["outcomes"].values()),
            "outcomes": dict(sorted(group["outcomes"].items())),
            "reasons": dict(sorted(group["reasons"].items())),
            "trades": group["trades"],
            "r": str(group["r"]),
        }
        for (unit, market, day), group in sorted(groups.items())
    ]


def _with_context(root: Path, rows: Sequence[JournalRow], start_ns: int, end_ns: int) -> list[Any]:
    minutes: dict[tuple[str, int], JournalRow] = {}
    widened = _read(
        root,
        "market",
        start_ns - MS_PER_MINUTE * NS_PER_MS,
        end_ns + MS_PER_MINUTE * NS_PER_MS,
        {"kind": "minute"},
        backfilled=True,
    )
    for row in widened.rows:
        minutes[str(row.record.get("market_id")), row.t // MS_PER_MINUTE] = row
    answered: list[Any] = []
    for row in rows:
        if row.record.get("kind") not in CONTEXT_KINDS:
            continue
        found = row.concise()
        minute = minutes.get((str(row.record.get("market_id")), row.t // MS_PER_MINUTE))
        found["market_minute"] = None if minute is None else minute.concise()
        answered.append(found)
    return answered


def journal_query(
    home: Path,
    *,
    stream: str,
    window: Mapping[str, object] | None,
    filters: Mapping[str, object] | None = None,
    view: View = "rows",
    include_backfilled: bool = False,
    detailed: bool = False,
) -> dict[str, Any]:
    """Read one journal stream over a window; the answer says where the data stops when the
    window runs past it."""
    if window is None or "start" not in window or "end" not in window:
        raise ValueError(
            "journal_query needs a time window: pass window = {start, end}, for example "
            '{"start": "2025-01-02T07:00:00Z", "end": "2025-01-02T09:00:00Z"}'
        )
    if stream not in STREAMS:
        raise ValueError(f"stream is one of {', '.join(STREAMS)}; got {stream!r}")
    start_ns = parse_instant(window["start"], "start")
    end_ns = parse_instant(window["end"], "end")
    if end_ns <= start_ns:
        raise ValueError("the window's end comes after its start")
    given = {str(name): str(value) for name, value in (filters or {}).items()}
    unknown = sorted(set(given) - ENVELOPE_FILTERS)
    if unknown:
        raise ValueError(
            f"filters name envelope fields only ({', '.join(sorted(ENVELOPE_FILTERS))}); "
            f"not {', '.join(unknown)}"
        )
    root = home / MARKET_FOLDER / "series"
    found = _read(root, stream, start_ns, end_ns, given, include_backfilled)
    answer: dict[str, Any] = {
        "stream": stream,
        "window": {"start": _iso(start_ns // NS_PER_MS), "end": _iso(end_ns // NS_PER_MS)},
        "view": view,
        "backfilled_left_out": found.backfilled,
    }
    if found.unreadable:
        answer["unreadable"] = found.unreadable
    if found.last_t is None:
        answer["data_stops_at"] = None
        answer["note"] = "this journal holds no rows that match; nothing is recorded yet"
    elif found.last_t * NS_PER_MS < end_ns:
        stops = _iso(found.last_t)
        answer["data_stops_at"] = stops
        answer["note"] = f"the data stops at {stops}; nothing after it is recorded yet"
    if view == "digest":
        answer["rows"] = _digest(found.rows)
    elif view == "trades_with_context":
        answer["rows"] = _with_context(root, found.rows, start_ns, end_ns)
    else:
        answer["rows"] = [row.detailed() if detailed else row.concise() for row in found.rows]
    return answer


def note_draft(
    *,
    title: str,
    text: str,
    note_kind: str,
    about: Sequence[Mapping[str, str]] = (),
    receipts: Sequence[str] = (),
    window: Mapping[str, str] | None = None,
    sources_marked: Sequence[str] = (),
    expires: str | None = None,
    author: str = "agent",
) -> Draft:
    """An agent's note as a `note` item (version 2); the text is its `body.md`."""
    if note_kind not in NOTE_KINDS:
        raise ValueError(f"note_kind is one of {', '.join(NOTE_KINDS)}; got {note_kind!r}")
    if not title.strip():
        raise ValueError("a note has a title")
    fields: dict[str, object] = {
        "note_kind": note_kind,
        "about": [{"rel": str(link["rel"]), "ref": str(link["ref"])} for link in about],
        "receipts": list(receipts),
        "sources_marked": list(sources_marked),
        "author": author,
    }
    if window is not None:
        fields["window"] = {"start": str(window["start"]), "end": str(window["end"])}
    if expires is not None:
        fields["expires"] = expires
    return Draft(
        "note",
        None,
        title=title,
        summary=text.strip().splitlines()[0][:200] if text.strip() else title,
        fields=cast("JsonObject", fields),
        blobs={"body.md": text.encode("utf-8")},
    )
