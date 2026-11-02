"""The journal writer: one writer per stream, record ids that survive a re-run (AD-208, AD-209).

Every row an app means for its machine's store goes through here in one of two forms: a
journal record (:meth:`JournalWriter.append`, an envelope around a typed kind body) or a
series row of a store kind (:meth:`JournalWriter.append_series`, a ``bar-*`` or ``ticks``
row under its series key).

**Two modes.** On the hot path (paper, demo, live, shadow) each row is one fsynced line of
a CT-13 one-writer stream in the store's ``live`` room, in process, so the host is never a
step before a send. In bundle mode (backtest, stress, synthetic) the same rows go straight
into partition files in a run's output folder, so a run's journal is one Library record.

**One stream per partition series.** A series is
``journal-<stream> / <subject> / <kind> / <world>.<machine>`` (``lifecycle`` adds the
writer's role), so two writers of different kinds share a subject but never a stream, and
the CT-13 lock refuses a second writer on one stream.

**Record ids.** A kind whose rows a re-run writes again carries its own id (Part A's
``row_id``, the state event's fp1, the lifecycle ``event_id``, a venue's deal id); every
other row is ``<writer_id>/<seq>``. A repeated id with the same body is dropped without
spending a sequence number; one with a different body is kept out and answered with a
``determinism_break`` warning. An append that cannot be written is a refusal, never a
silent drop.

:func:`stage` turns a writer root's committed lines into the market-data door's staging
layout, one partition file per series and month of ``t``.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import contextlib
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol, cast

from qmf.core import (
    Ok,
    Result,
    World,
    WriterId,
    canonical_bytes,
    fingerprint,
    fingerprint_bytes,
    is_refusal,
)
from qmf.data.journal_envelope import (
    BUNDLE_WORLDS,
    HOT_PATH_WORLDS,
    JournalStream,
    JournalWorld,
    RowFacts,
    envelope_json,
)
from qmf.data.journal_kinds import IdRule, KindSpec, kinds_of, spec_for
from qmf.data.journal_reader import JournalLine, SeriesLine, read_committed, stream_folders
from qmf.data.series import JOURNAL_SOURCE_PREFIX, SeriesKey, rule_for
from qmf.data.store.engines import SeriesFile, StoreEngineError
from qmf.data.store.engines.jsonl import jsonl_opener
from qmf.data.store.engines.typed import FLOAT_COLUMNS, TypedWriter
from qmf.data.store.journal import JournalStore
from qmf.data.store.refusals import (
    invalid_input,
    policy_rejection,
    storage_failure,
    translate_engine_failure,
)

__all__ = [
    "AppendOutcome",
    "AppendReceipt",
    "JournalWriter",
    "WriterScope",
    "key_token",
    "stage",
]

Clock = Callable[[], int]
"""The write time in epoch nanoseconds, injected by the composition root."""

_TOKEN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_.+-]{1,64}")
_TOKEN_CHAR: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9_.+-]")
_TOKEN_MAX: Final[int] = 64
_TOKEN_PRINT: Final[int] = 12
_FOLDER_CHAR: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9._-]")
_NS_PER_MS: Final[int] = 1_000_000
_BUNDLE_ROW_GROUP: Final[int] = 4_096


def key_token(identifier: str) -> str:
    """The store token for an id, by one fixed rule.

    A token is ``[A-Za-z0-9_.+-]{1,64}``. ``@`` and ``/`` become ``+``, any other character
    ``_``; past 64 characters the token keeps its first 51, a dash and a 12-character
    fingerprint of the whole id, so two long ids never share a token.
    """
    if _TOKEN.fullmatch(identifier):
        return identifier
    mapped = _TOKEN_CHAR.sub("_", identifier.replace("@", "+").replace("/", "+"))
    if len(mapped) <= _TOKEN_MAX:
        return mapped
    digest = fingerprint_bytes(identifier.encode("utf-8")).digest[:_TOKEN_PRINT]
    return f"{mapped[: _TOKEN_MAX - _TOKEN_PRINT - 1]}-{digest}"


class AppendOutcome(StrEnum):
    APPENDED = "appended"
    REPEAT = "repeat"
    """The id was there with the same body: nothing written, no sequence spent."""
    DETERMINISM_BREAK = "determinism_break"
    """The id was there with a different body: kept out, for the host to log."""


@dataclass(frozen=True, slots=True)
class AppendReceipt:
    outcome: AppendOutcome
    record_id: str
    series: str
    seq: int | None = None
    t: int | None = None
    warning: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class WriterScope:
    """Who writes: one journal of one subject, in one world, on one machine, in one role.

    ``subject`` is the unit id, the market id or the node identity; for reading history it
    is ``<source>.<market id>``. ``role`` names the writer on its machine (``host``,
    ``node``, ``qmb``); a second role reaching for a stream another role holds is refused.
    """

    stream: JournalStream
    subject: str
    world: JournalWorld
    machine: str
    role: str
    build: str

    @property
    def writer_id(self) -> str:
        return f"{self.role}@{self.machine}"

    def series(self, kind: str) -> Result[SeriesKey]:
        """The partition series of one kind (its month is a placeholder until a row has ``t``)."""
        variant = f"{self.world.value}.{key_token(self.machine)}"
        if kind == "lifecycle":
            variant = f"{variant}.{key_token(self.role)}"
        return SeriesKey.try_create(
            self.stream.source, key_token(self.subject), kind, 1970, 1, key_token(variant)
        )


class _Sink(Protocol):
    def write(
        self, key: SeriesKey, line: Mapping[str, object], row: tuple[object, ...]
    ) -> Result[None]: ...

    def close(self) -> Result[tuple[SeriesFile, ...]]: ...


class _HotSink:
    """Appends each line to its series' CT-13 stream with fsync, one writer per stream."""

    def __init__(self, root: Path, writer: WriterId) -> None:
        self._store = JournalStore(World.LIVE, journal_dir=root, open_stream=jsonl_opener())
        self._writer = writer

    def write(
        self, key: SeriesKey, line: Mapping[str, object], row: tuple[object, ...]
    ) -> Result[None]:
        appended = self._store.append(_folder_name(key.series), self._writer, line)
        return appended if is_refusal(appended) else Ok(None)

    def close(self) -> Result[tuple[SeriesFile, ...]]:
        try:
            self._store.close()
        except StoreEngineError as exc:
            return translate_engine_failure(exc)
        return Ok(())


class _BundleSink:
    """Streams each row into its partition file in a run's output folder."""

    def __init__(self, out_dir: Path) -> None:
        self._out = out_dir
        self._open: dict[str, tuple[SeriesKey, TypedWriter]] = {}
        # A failed partition is never reopened: a new writer on its path would overwrite
        # the rows it already held, so its later rows are refused instead.
        self._failed: set[str] = set()

    def write(
        self, key: SeriesKey, line: Mapping[str, object], row: tuple[object, ...]
    ) -> Result[None]:
        if key.text in self._failed:
            return storage_failure(
                "this run's journal partition already failed, so its rows are not written",
                context={"key": key.text},
            )
        opened = self._open.get(key.text)
        try:
            if opened is None:
                target = _staged_path(self._out, key)
                target.parent.mkdir(parents=True, exist_ok=True)
                opened = (
                    key,
                    TypedWriter(
                        target, key.text, key.rule.columns, row_group_rows=_BUNDLE_ROW_GROUP
                    ),
                )
                self._open[key.text] = opened
            opened[1].add([row])
        except StoreEngineError as exc:
            self._fail(key)
            return translate_engine_failure(exc)
        except OSError as exc:
            self._fail(key)
            return storage_failure(
                "could not write the run's journal partition",
                context={"key": key.text, "error": str(exc)},
            )
        return Ok(None)

    def close(self) -> Result[tuple[SeriesFile, ...]]:
        files: list[SeriesFile] = []
        for key, writer in list(self._open.values()):
            try:
                files.append(writer.finish())
            except (StoreEngineError, OSError):
                self._fail(key)
        self._open.clear()
        if self._failed:
            return storage_failure(
                "some of the run's journal partitions could not be written",
                context={"failed": sorted(self._failed)},
            )
        return Ok(tuple(files))

    def _fail(self, key: SeriesKey) -> None:
        """Drop a partition whose write failed, with its partial file."""
        self._failed.add(key.text)
        opened = self._open.pop(key.text, None)
        if opened is not None:
            opened[1].abort()
        with contextlib.suppress(OSError):
            _staged_path(self._out, key).unlink(missing_ok=True)


class JournalWriter:
    """Appends journal records and series rows for one :class:`WriterScope`."""

    def __init__(self, scope: WriterScope, sink: _Sink, clock: Clock) -> None:
        self._scope = scope
        self._sink = sink
        self._clock = clock
        self._next_seq = 0
        self._last_t = 0
        self._seen: dict[str, dict[str, str]] = {}  # series -> record id -> body fingerprint
        self._series_last_t: dict[str, int] = {}
        self._root: Path | None = None
        self._closed = False

    @classmethod
    def open(
        cls, root: Path, scope: WriterScope, *, clock: Clock, boot_epoch_id: str
    ) -> Result[JournalWriter]:
        """The hot-path writer under a machine's journal root, resumed from its own lines."""
        if scope.world not in HOT_PATH_WORLDS:
            return policy_rejection(
                "world",
                "backtest, stress and synthetic records never use the hot path; "
                "open them in bundle mode",
                given=scope.world.value,
            )
        writer_id = WriterId.try_create(
            scope.machine, scope.role, scope.stream.source, boot_epoch_id
        )
        if is_refusal(writer_id):
            return writer_id
        writer = cls(scope, _HotSink(root, writer_id.value), clock)
        writer._root = root
        resumed = writer._resume(root)
        return resumed if is_refusal(resumed) else Ok(writer)

    @classmethod
    def open_bundle(
        cls, out_dir: Path, scope: WriterScope, *, clock: Clock
    ) -> Result[JournalWriter]:
        """A run's writer: rows land as partition files under ``out_dir`` when it closes."""
        if scope.world not in BUNDLE_WORLDS:
            return policy_rejection(
                "world",
                "bundle mode writes backtest, stress and synthetic records only",
                given=scope.world.value,
            )
        return Ok(cls(scope, _BundleSink(out_dir), clock))

    @property
    def scope(self) -> WriterScope:
        return self._scope

    def append(
        self, kind: str, body: Mapping[str, object], facts: RowFacts
    ) -> Result[AppendReceipt]:
        """Append one record, drop a repeat, or keep out a repeat whose body differs."""
        if self._closed:
            return policy_rejection("writer", "the journal writer is closed")
        spec = spec_for(self._scope.stream, kind)
        if spec is None:
            return invalid_input(
                "kind",
                f"the {self._scope.stream.value} journal has no such kind",
                given=kind,
            )
        problem = spec.problem(body) or self._facts_problem(spec, facts)
        if problem is not None:
            return invalid_input("body", problem, kind=kind)
        native = _native(body)
        if is_refusal(native):
            return native
        body_print = fingerprint(native.value)
        if is_refusal(body_print):
            return body_print
        series = self._scope.series(kind)
        if is_refusal(series):
            return series
        seq = self._next_seq
        record_id = _record_id(spec, native.value, facts, self._scope.writer_id, seq)
        if is_refusal(record_id):
            return record_id
        seen = self._seen.setdefault(series.value.series, {})
        earlier = seen.get(record_id.value)
        if earlier is not None:
            return Ok(
                self._repeat(record_id.value, series.value.series, earlier, body_print.value.value)
            )
        ts_write = self._clock()
        t = max(ts_write // _NS_PER_MS, self._last_t)
        record = envelope_json(
            facts,
            record_id=record_id.value,
            stream=self._scope.stream,
            kind=kind,
            schema_version=spec.schema_version,
            writer_id=self._scope.writer_id,
            seq=seq,
            ts_write=ts_write,
            world=self._scope.world,
            machine=self._scope.machine,
            build=self._scope.build,
            body=native.value,
        )
        text = canonical_bytes(record)
        if is_refusal(text):
            return text
        key = _month_key(series.value, t)
        line: dict[str, object] = {"series": key.series, "t": t, "seq": seq, "record": record}
        written = self._sink.write(key, line, (t, seq, text.value.decode("utf-8")))
        if is_refusal(written):
            return written
        self._next_seq = seq + 1
        self._last_t = t
        seen[record_id.value] = body_print.value.value
        return Ok(AppendReceipt(AppendOutcome.APPENDED, record_id.value, key.series, seq, t))

    def append_series(
        self,
        source: str,
        subject: str,
        kind: str,
        row: Sequence[object],
        *,
        variant: str = "",
    ) -> Result[AppendReceipt]:
        """Append one row of a store kind (``bar-m1``, ``ticks``) under its series key."""
        if self._closed:
            return policy_rejection("writer", "the journal writer is closed")
        if source.startswith(JOURNAL_SOURCE_PREFIX):
            return invalid_input("source", "journal records go through append", given=source)
        columns = rule_for(source, kind).columns
        problem = _row_problem(columns, row)
        if problem is not None:
            return invalid_input("row", problem, kind=kind)
        t = cast("int", row[0])
        key = SeriesKey.try_create(source, subject, kind, *_year_month(t), variant)
        if is_refusal(key):
            return key
        last = self._series_last(key.value)
        if is_refusal(last):
            return last
        if t < last.value:
            return invalid_input(
                "row", "rows of one series are time-ordered; t went backwards", t=t, last=last.value
            )
        line: dict[str, object] = {"series": key.value.series, "t": t, "row": _cells(row)}
        written = self._sink.write(key.value, line, tuple(row))
        if is_refusal(written):
            return written
        self._series_last_t[key.value.series] = t
        return Ok(
            AppendReceipt(AppendOutcome.APPENDED, f"{key.value.series}@{t}", key.value.series, t=t)
        )

    def close(self) -> Result[tuple[SeriesFile, ...]]:
        """Release the hot path's streams, or finish a bundle's partition files."""
        if self._closed:
            return Ok(())
        self._closed = True
        return self._sink.close()

    def _repeat(self, record_id: str, series: str, kept: str, offered: str) -> AppendReceipt:
        if kept == offered:
            return AppendReceipt(AppendOutcome.REPEAT, record_id, series)
        return AppendReceipt(
            AppendOutcome.DETERMINISM_BREAK,
            record_id,
            series,
            warning={
                "code": "determinism_break",
                "record_id": record_id,
                "series": series,
                "kept": kept,
                "offered": offered,
            },
        )

    def _facts_problem(self, spec: KindSpec, facts: RowFacts) -> str | None:
        if self._scope.stream is JournalStream.UNIT and not facts.unit_id:
            return "a unit-journal row names its unit_id"
        if spec.id_rule in (IdRule.FILL, IdRule.TRADE) and not facts.venue:
            return f"a {spec.kind} row names its venue, which its record id carries"
        return None

    def _resume(self, root: Path) -> Result[None]:
        """Take up this writer's own sequence, latest ``t`` and recent ids from its streams."""
        for spec in kinds_of(self._scope.stream):
            series = self._scope.series(spec.kind)
            if is_refusal(series):
                return series
            folder = root / _folder_name(series.value.series)
            if not folder.is_dir():
                continue
            lines = read_committed(folder)
            if is_refusal(lines):
                return lines
            mine = [
                line
                for line in lines.value
                if isinstance(line, JournalLine)
                and line.record.get("writer_id") == self._scope.writer_id
            ]
            if not mine:
                continue
            self._next_seq = max(self._next_seq, max(line.seq for line in mine) + 1)
            latest = max(line.t for line in mine)
            self._last_t = max(self._last_t, latest)
            keep_from = _previous_month_start_ms(latest)
            bodies: dict[str, str] = {}
            for line in mine:
                if line.t < keep_from:
                    continue
                body = line.record.get("body")
                printed = fingerprint(body)
                if is_refusal(printed):
                    return printed
                bodies[str(line.record["record_id"])] = printed.value.value
            self._seen[series.value.series] = bodies
        return Ok(None)

    def _series_last(self, key: SeriesKey) -> Result[int]:
        known = self._series_last_t.get(key.series)
        if known is not None:
            return Ok(known)
        last = 0
        if self._root is not None:
            folder = self._root / _folder_name(key.series)
            if folder.is_dir():
                lines = read_committed(folder)
                if is_refusal(lines):
                    return lines
                last = max((line.t for line in lines.value), default=0)
        self._series_last_t[key.series] = last
        return Ok(last)


def stage(root: Path, staging: Path) -> Result[tuple[SeriesFile, ...]]:
    """Write a writer root's committed lines as partitions in the door's staging layout.

    Each series and month of ``t`` becomes ``<staging>/<source>/<subject>/<kind>/<variant>/
    <YYYY-MM>.parquet``, rewritten whole on each call; the live streams are only read.
    """
    staged: list[SeriesFile] = []
    for folder in stream_folders(root):
        lines = read_committed(folder)
        if is_refusal(lines):
            return lines
        months: dict[str, tuple[SeriesKey, list[tuple[object, ...]]]] = {}
        for line in lines.value:
            parts = line.series.split("/")
            key = SeriesKey.try_create(
                parts[0],
                parts[1],
                parts[2],
                *_year_month(line.t),
                "" if parts[3] == "-" else parts[3],
            )
            if is_refusal(key):
                return key
            row = _staged_row(line, key.value.rule.columns)
            if is_refusal(row):
                return row
            months.setdefault(key.value.text, (key.value, []))[1].append(row.value)
        for key, rows in months.values():
            written = _write_partition(staging, key, rows)
            if is_refusal(written):
                return written
            staged.append(written.value)
    return Ok(tuple(staged))


def _write_partition(
    staging: Path, key: SeriesKey, rows: list[tuple[object, ...]]
) -> Result[SeriesFile]:
    target = _staged_path(staging, key)
    temp = target.with_name(f".{target.name}.incoming")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        written = TypedWriter(temp, key.text, key.rule.columns).add(rows).finish()
        os.replace(temp, target)
    except StoreEngineError as exc:
        temp.unlink(missing_ok=True)
        return translate_engine_failure(exc)
    except OSError as exc:
        temp.unlink(missing_ok=True)
        return storage_failure(
            "could not stage a journal partition", context={"key": key.text, "error": str(exc)}
        )
    return Ok(
        SeriesFile(
            key=written.key,
            fingerprint=written.fingerprint,
            rows=written.rows,
            bytes=written.bytes,
            path=target,
            columns=written.columns,
            first_t=written.first_t,
            last_t=written.last_t,
            holes=written.holes,
        )
    )


def _staged_row(
    line: JournalLine | SeriesLine, columns: tuple[str, ...]
) -> Result[tuple[object, ...]]:
    if isinstance(line, JournalLine):
        text = canonical_bytes(dict(line.record))
        if is_refusal(text):
            return text
        return Ok((line.t, line.seq, text.value.decode("utf-8")))
    if len(line.cells) != len(columns):
        return invalid_input("row", "a series line does not match its kind's columns")
    return Ok(tuple(_decode(name, cell) for name, cell in zip(columns, line.cells, strict=True)))


def _record_id(
    spec: KindSpec,
    body: Mapping[str, object],
    facts: RowFacts,
    writer_id: str,
    seq: int,
) -> Result[str]:
    match spec.id_rule:
        case IdRule.ROW_ID:
            return Ok(str(body["row_id"]))
        case IdRule.EVENT_ID:
            return Ok(str(body["event_id"]))
        case IdRule.STATE:
            printed = fingerprint(
                {
                    "scope_id": body["scope_id"],
                    "instant": body["instant"],
                    "ordinal": body["ordinal"],
                }
            )
            return printed if is_refusal(printed) else Ok(printed.value.value)
        case IdRule.FILL:
            return Ok(f"{facts.venue}:{body['deal_id']}")
        case IdRule.TRADE:
            return Ok(f"{facts.venue}:{body['closing_deal_id']}")
        case IdRule.SEQUENCE:
            return Ok(f"{writer_id}/{seq}")


def _native(body: Mapping[str, object]) -> Result[dict[str, object]]:
    """The body as canonical JSON-native values; a float or a null is refused."""
    text = canonical_bytes(dict(body))
    if is_refusal(text):
        return text
    return Ok(cast("dict[str, object]", json.loads(text.value)))


def _row_problem(columns: tuple[str, ...], row: Sequence[object]) -> str | None:
    if len(row) != len(columns):
        return f"a row of {len(columns)} columns got {len(row)} values"
    for name, value in zip(columns, row, strict=True):
        if name in FLOAT_COLUMNS:
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int | float)
            ):
                return f"{name} takes a number or null"
        elif isinstance(value, bool) or not isinstance(value, int):
            return f"{name} takes an integer"
    return None


def _cells(row: Sequence[object]) -> list[str]:
    """Each cell as text: an integer's digits, a float's ``float.hex()``, a null as empty."""
    return [
        "" if value is None else value.hex() if isinstance(value, float) else str(value)
        for value in row
    ]


def _decode(name: str, cell: str) -> object:
    if name in FLOAT_COLUMNS:
        return None if cell == "" else float.fromhex(cell)
    return int(cell)


def _folder_name(series: str) -> str:
    """The CT-13 stream folder of one series: readable, case-free and unique."""
    source, _subject, kind, *_rest = series.split("/")
    digest = fingerprint_bytes(series.encode("utf-8")).digest[:16]
    return _FOLDER_CHAR.sub("_", f"{source}.{kind}.{digest}".lower())


def _staged_path(root: Path, key: SeriesKey) -> Path:
    return root.joinpath(*key.series.split("/"), f"{key.year:04d}-{key.month:02d}.parquet")


def _year_month(t_ms: int) -> tuple[int, int]:
    moment = datetime.fromtimestamp(t_ms // 1000, tz=UTC)
    return moment.year, moment.month


def _month_key(series: SeriesKey, t_ms: int) -> SeriesKey:
    year, month = _year_month(t_ms)
    return SeriesKey(series.source, series.subject, series.kind, year, month, series.variant)


def _previous_month_start_ms(t_ms: int) -> int:
    year, month = _year_month(t_ms)
    year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp()) * 1000
