"""Price-series rules — key, open month, freeze per kind, corrections, (key, range) records (W9).

A price partition is addressed by ``source / subject / kind / variant / year / month`` and
resolves to one typed file (``store/engines/typed.py``). Three rules make that address
mean something across time:

* **The open month is one file under a fixed key.** A month that has not frozen is written
  at ``open.parquet`` in its folder, so each fetch replaces the same file rather than
  leaving a file per attempt. Freezing writes the file under its fingerprint and removes
  the open one, after the replacement exists.
* **Each kind declares its freeze rule.** Ticks freeze on a gap check (a hole longer than
  an hour and shorter than six, so a market closure is not a gap), and a month with such a
  hole freezes only when a re-fetch returns the same hole, which is the one re-fetch the
  plan allows. Bars freeze on the provider's checksum. A fill month freezes at month end
  plus its declared settlement delay, with no gap check. Derived series freeze on the
  checksum of the component that made them.
* **A late row for a frozen month is an automatic correction.** A frozen month takes a
  different file only when the caller marks it a correction with a reason; the correction
  records the old and new fingerprint and the time range it covers, which is what a read
  range is compared against when a result is marked.

Everything here is a plain value or a typed refusal; nothing raises across the boundary.
Stdlib + qmf-core + the typed writer.
"""

# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final

from qmf.core import Ok, Result, Retryability
from qmf.data.store.engines import SeriesFile, StoreEngineError
from qmf.data.store.engines.typed import (
    BAR_COLUMNS,
    JOURNAL_COLUMNS,
    TICK_COLUMNS,
    VALUE_COLUMNS,
    TypedWriter,
)
from qmf.data.store.refusals import (
    invalid_input,
    missing_artifact,
    policy_rejection,
    storage_failure,
    translate_engine_failure,
)

__all__ = [
    "BAR_KIND",
    "BOOK_COLUMNS",
    "BOOK_KIND",
    "GAP_MAX_MS",
    "GAP_MIN_MS",
    "JOURNAL_SETTLE_DAYS",
    "JOURNAL_SOURCE_PREFIX",
    "OPEN_NAME",
    "RULES",
    "STATE_NAME",
    "TICKS_KIND",
    "TRADES_COLUMNS",
    "TRADES_KIND",
    "CommitReceipt",
    "Correction",
    "FreezeKind",
    "KindRule",
    "SeriesKey",
    "SeriesRead",
    "SeriesState",
    "SeriesStore",
    "rule_for",
]

TICKS_KIND: Final[str] = "ticks"
BAR_KIND: Final[str] = "bar-m1"
FILL_KIND: Final[str] = "fill"
TRADES_KIND: Final[str] = "trades"
"""Trade prints: one row per print, from a Binance bulk file or a broker's tape (DR6)."""

BOOK_KIND: Final[str] = "book"
"""A book's levels over time: one row per level reading (DR6)."""

TRADES_COLUMNS: Final[tuple[str, ...]] = ("t", "price", "volume")
"""A trade row: epoch milliseconds, the int64 scaled price, and the size as a float."""

BOOK_COLUMNS: Final[tuple[str, ...]] = ("t", "value", "volume")
"""A book row: epoch milliseconds, the level or percentage, and its notional as a float."""
DERIVED_SOURCE: Final[str] = "derived"
OPEN_NAME: Final[str] = "open.parquet"
STATE_NAME: Final[str] = "state.json"
INCOMING_NAME: Final[str] = ".incoming.parquet"
SETTLEMENT_DAYS: Final[int] = 2
NS_PER_MS: Final[int] = 1_000_000
NS_PER_DAY: Final[int] = 86_400 * 1_000_000_000
# A feed outage inside trading time, not a market closure: longer than an hour, shorter
# than six, so a weekend (48 hours) and a holiday (a day or more) are never gaps.
GAP_MIN_MS: Final[int] = 3_600 * 1_000
GAP_MAX_MS: Final[int] = 6 * 3_600 * 1_000
_TOKEN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_.+-]{1,64}")
RENAME_TRIES: Final[int] = 8
RENAME_WAIT_S: Final[float] = 0.01
HELD_OPEN: Final[frozenset[int]] = frozenset({5, 32})
"""Windows refuses a rename onto a file another handle reads (WinError 5 or 32)."""


class FreezeKind(StrEnum):
    """How a kind decides that its month is closed (DATA-PLAN DR3A)."""

    GAP = "gap"
    CHECKSUM = "checksum"
    MONTH_END = "month-end"


@dataclass(frozen=True, slots=True)
class KindRule:
    """One kind's freeze rule, its typed columns, and the delay its month end carries.

    ``hole_bounds`` is the writer's window for recording a hole between consecutive rows,
    in the file's own time unit. Only a gap-checked kind sets it: the writer records the
    holes it sees and the freeze rule decides what they mean.
    """

    freeze: FreezeKind
    columns: tuple[str, ...]
    settlement_days: int = 0
    hole_bounds: tuple[int, int] | None = None


RULES: Final[dict[str, KindRule]] = {
    TICKS_KIND: KindRule(FreezeKind.GAP, TICK_COLUMNS, hole_bounds=(GAP_MIN_MS, GAP_MAX_MS)),
    BAR_KIND: KindRule(FreezeKind.CHECKSUM, BAR_COLUMNS),
    FILL_KIND: KindRule(FreezeKind.MONTH_END, BAR_COLUMNS, SETTLEMENT_DAYS),
    TRADES_KIND: KindRule(FreezeKind.CHECKSUM, TRADES_COLUMNS),
    BOOK_KIND: KindRule(FreezeKind.CHECKSUM, BOOK_COLUMNS),
}
_DERIVED_RULE: Final[KindRule] = KindRule(FreezeKind.CHECKSUM, VALUE_COLUMNS)
JOURNAL_SOURCE_PREFIX: Final[str] = "journal-"
JOURNAL_SETTLE_DAYS: Final[int] = 1
"""The starting default of ``[journals] settle_days``: late rows from a machine whose clock was off."""
_JOURNAL_RULE: Final[KindRule] = KindRule(
    FreezeKind.MONTH_END, JOURNAL_COLUMNS, JOURNAL_SETTLE_DAYS
)


def rule_for(source: str, kind: str) -> KindRule:
    """The freeze rule of a series: its kind's, or a derived series' value columns.

    A derived series is ``source = derived, kind = <component>-v<version>`` (for example
    ``rsi-v1``), so its columns are ``t`` and ``value`` whatever the component is, and it
    freezes on the checksum of the component version that produced it. A journal series
    (``source = journal-<stream>``) holds ``t``, ``seq`` and the record's canonical JSON
    whatever its kind, and its month freezes at its end plus a settlement day (AD-209).
    """
    if source == DERIVED_SOURCE:
        return _DERIVED_RULE
    if source.startswith(JOURNAL_SOURCE_PREFIX):
        return _JOURNAL_RULE
    return RULES.get(kind, _DERIVED_RULE)


def _month_start_ns(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=UTC).timestamp()) * 1_000_000_000


def _plus_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _replace(source: Path, target: Path) -> None:
    """`os.replace`, retried while Windows reports the target held open, as a backup round's
    copy holds it for the length of its read. The wait doubles from `RENAME_WAIT_S`; past the
    last try the refusal is raised, which the commit reports as a storage failure."""
    for attempt in range(RENAME_TRIES):
        try:
            os.replace(source, target)
        except PermissionError as held:
            if getattr(held, "winerror", None) not in HELD_OPEN or attempt == RENAME_TRIES - 1:
                raise
            time.sleep(RENAME_WAIT_S * 2**attempt)
        else:
            return


def _iso(ns: int) -> str:
    seconds, rest = divmod(ns, 1_000_000_000)
    moment = datetime.fromtimestamp(seconds, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{moment}.{rest // 1_000_000:03d}Z"


@dataclass(frozen=True, slots=True)
class SeriesKey:
    """The ``source / subject / kind / variant / year / month`` address of one partition.

    ``subject`` is the instrument a series is about (``EURUSD``), ``kind`` says what is
    measured (``ticks``, ``bar-m1``, ``fill``, or a derived component such as ``rsi-v1``),
    and ``variant`` separates series of one kind that are not one thing (a bid bar and an
    ask bar). Ticks keep both sides in one row, so they are one series; bid and ask bars
    are two.
    """

    source: str
    subject: str
    kind: str
    year: int
    month: int
    variant: str = ""

    @classmethod
    def try_create(
        cls,
        source: object,
        subject: object,
        kind: object,
        year: object,
        month: object,
        variant: object = "",
    ) -> Result[SeriesKey]:
        """Validate a key, refusing a blank or path-shaped token and a bad month."""
        for name, value in (
            ("source", source),
            ("subject", subject),
            ("kind", kind),
            ("variant", variant),
        ):
            text = "" if value is None else value
            if not isinstance(text, str) or (name != "variant" and text.strip() == ""):
                return invalid_input(
                    name, "a series key names a non-empty token", given=repr(value)
                )
            if text != "" and _TOKEN.fullmatch(text.strip()) is None:
                return invalid_input(
                    name,
                    "a series token is letters, digits, dot, dash, plus or underscore",
                    given=repr(value),
                )
        if isinstance(year, bool) or not isinstance(year, int) or not 1970 <= year <= 9999:
            return invalid_input("year", "a series key names a year from 1970", given=repr(year))
        if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
            return invalid_input(
                "month", "a series key names a month from 1 to 12", given=repr(month)
            )
        return Ok(
            cls(
                source=str(source).strip(),
                subject=str(subject).strip(),
                kind=str(kind).strip(),
                year=year,
                month=month,
                variant="" if variant is None else str(variant).strip(),
            )
        )

    @property
    def series(self) -> str:
        """The series without its month: what one ``dataset`` card stands for."""
        return f"{self.source}/{self.subject}/{self.kind}/{self.variant or '-'}"

    @property
    def text(self) -> str:
        """The partition key, with the month last."""
        return f"{self.series}/{self.year:04d}-{self.month:02d}"

    @property
    def start_ns(self) -> int:
        return _month_start_ns(self.year, self.month)

    @property
    def end_ns(self) -> int:
        year, month = _plus_month(self.year, self.month)
        return _month_start_ns(year, month)

    @property
    def rule(self) -> KindRule:
        return rule_for(self.source, self.kind)


@dataclass(frozen=True, slots=True)
class Correction:
    """One late file accepted for a frozen month, and the range it covers."""

    old: str
    new: str
    reason: str
    at: str
    start_ns: int
    end_ns: int

    def as_json(self) -> dict[str, object]:
        return {
            "old": self.old,
            "new": self.new,
            "reason": self.reason,
            "at": self.at,
            "start_ns": self.start_ns,
            "end_ns": self.end_ns,
        }

    @classmethod
    def from_json(cls, data: dict[str, object]) -> Correction:
        return cls(
            old=str(data["old"]),
            new=str(data["new"]),
            reason=str(data["reason"]),
            at=str(data["at"]),
            start_ns=int(data["start_ns"]),  # type: ignore[arg-type]
            end_ns=int(data["end_ns"]),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class SeriesState:
    """What the store knows about one partition after its last commit."""

    key: str
    fingerprint: str
    rows: int
    bytes: int
    gaps: tuple[str, ...]
    attempts: int
    frozen: bool
    frozen_once: bool
    at: str
    corrections: tuple[Correction, ...] = ()

    def as_json(self) -> dict[str, object]:
        return {
            "key": self.key,
            "fingerprint": self.fingerprint,
            "rows": self.rows,
            "bytes": self.bytes,
            "gaps": list(self.gaps),
            "attempts": self.attempts,
            "frozen": self.frozen,
            "frozen_once": self.frozen_once,
            "at": self.at,
            "corrections": [item.as_json() for item in self.corrections],
        }

    @classmethod
    def from_json(cls, data: dict[str, object]) -> SeriesState:
        return cls(
            key=str(data["key"]),
            fingerprint=str(data["fingerprint"]),
            rows=int(data["rows"]),  # type: ignore[arg-type]
            bytes=int(data["bytes"]),  # type: ignore[arg-type]
            gaps=tuple(str(item) for item in data.get("gaps", [])),  # type: ignore[union-attr]
            attempts=int(data["attempts"]),  # type: ignore[arg-type]
            frozen=bool(data["frozen"]),
            frozen_once=bool(data.get("frozen_once", data["frozen"])),
            at=str(data["at"]),
            corrections=tuple(
                Correction.from_json(item)  # type: ignore[arg-type]
                for item in data.get("corrections", [])  # type: ignore[union-attr]
            ),
        )


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    """What one commit landed, and whether the month is now closed."""

    key: SeriesKey
    fingerprint: str
    rows: int
    bytes: int
    path: Path
    frozen: bool
    gaps: tuple[str, ...]
    attempts: int
    correction: bool = False
    idempotent: bool = False


@dataclass(frozen=True, slots=True)
class SeriesRead:
    """A read of one partition, recorded as its key and the range it asked for."""

    key: SeriesKey
    fingerprint: str
    start_ns: int
    end_ns: int
    rows: tuple[dict[str, object], ...]
    frozen: bool

    @property
    def range_text(self) -> str:
        return f"{self.key.text} [{_iso(self.start_ns)}, {_iso(self.end_ns)})"


def _range_of(written: SeriesFile, key: SeriesKey) -> tuple[int, int]:
    """The half-open ns range a written file covers, for a correction record."""
    start = written.first_t * NS_PER_MS if written.first_t is not None else key.start_ns
    end = (written.last_t * NS_PER_MS if written.last_t is not None else key.end_ns - 1) + 1
    return start, end


class SeriesStore:
    """The price partitions under one root, with their keys, freezes and corrections."""

    def __init__(self, root: Path, *, wall: Callable[[], datetime] | None = None) -> None:
        self._root = root
        self._wall = (
            wall if wall is not None else (lambda: datetime.now(UTC))  # ambient-scan: allow
        )

    @property
    def root(self) -> Path:
        return self._root

    def folder(self, key: SeriesKey) -> Path:
        """Where one partition lives: ``<root>/<series>/<year>-<month>``."""
        return self._root / key.series / f"{key.year:04d}-{key.month:02d}"

    def state(self, key: SeriesKey) -> SeriesState | None:
        """The stored state of a partition, or None when nothing is stored there."""
        path = self.folder(key) / STATE_NAME
        if not path.is_file():
            return None
        return SeriesState.from_json(json.loads(path.read_text(encoding="utf-8")))

    def commit(
        self,
        key: SeriesKey,
        rows: Iterable[Sequence[object]],
        *,
        correction: str | None = None,
        provider_checksum: str | None = None,
    ) -> Result[CommitReceipt]:
        """Write one fetch of a month; return the receipt, or the refusal.

        A frozen month takes a different file only when ``correction`` names why, and then
        the new fingerprint and the range it covers are recorded. The same rows again are
        an idempotent write and leave one file, whether the month is open or frozen.
        """
        rule = key.rule
        folder = self.folder(key)
        temp = folder / INCOMING_NAME
        try:
            folder.mkdir(parents=True, exist_ok=True)
            written = (
                TypedWriter(temp, key.text, rule.columns, hole_bounds=rule.hole_bounds)
                .add(rows)
                .finish()
            )
        except StoreEngineError as exc:
            temp.unlink(missing_ok=True)
            return translate_engine_failure(exc)
        except OSError as exc:
            temp.unlink(missing_ok=True)
            return storage_failure(
                "could not write the partition", context={"key": key.text, "error": str(exc)}
            )
        return self.commit_file(
            key, written, correction=correction, provider_checksum=provider_checksum
        )

    def commit_file(
        self,
        key: SeriesKey,
        written: SeriesFile,
        *,
        correction: str | None = None,
        provider_checksum: str | None = None,
    ) -> Result[CommitReceipt]:
        """Finish a file another process wrote — the importer's child writer — as a commit.

        The file must sit inside the key's folder (the importer writes
        ``<folder>/.incoming.parquet``); the store decides its final name, so a month that
        froze while the child was writing still refuses a different file.
        """
        folder = self.folder(key)
        folder.mkdir(parents=True, exist_ok=True)
        previous = self.state(key)
        gaps = tuple(f"{_iso(a * NS_PER_MS)}/{_iso(b * NS_PER_MS)}" for a, b in written.holes)
        try:
            if previous is not None and previous.frozen:
                return self._commit_frozen(key, folder, previous, written, correction)
            return self._commit_open(
                key, folder, key.rule, previous, written, gaps, provider_checksum
            )
        except OSError as exc:
            # A rename or a state write that the disk refused is a storage failure, never a
            # half-commit reported as success (AC4).
            return storage_failure(
                "could not finish the partition commit",
                retryability=Retryability.YES,
                context={"key": key.text, "error": str(exc)},
            )

    def _commit_frozen(
        self,
        key: SeriesKey,
        folder: Path,
        previous: SeriesState,
        written: SeriesFile,
        correction: str | None,
    ) -> Result[CommitReceipt]:
        final = folder / f"{written.fingerprint}.parquet"
        if written.fingerprint == previous.fingerprint:
            written.path.unlink(missing_ok=True)
            return Ok(
                CommitReceipt(
                    key=key,
                    fingerprint=previous.fingerprint,
                    rows=previous.rows,
                    bytes=previous.bytes,
                    path=final,
                    frozen=True,
                    gaps=previous.gaps,
                    attempts=0,
                    idempotent=True,
                )
            )
        if correction is None or correction.strip() == "":
            written.path.unlink(missing_ok=True)
            return policy_rejection(
                "key",
                "a frozen month takes a different file only as a correction with a reason",
                key=key.text,
                frozen=previous.fingerprint,
            )
        _replace(written.path, final)
        start, end = _range_of(written, key)
        record = Correction(
            previous.fingerprint, written.fingerprint, correction.strip(), self._at(), start, end
        )
        state = replace(
            previous,
            fingerprint=written.fingerprint,
            rows=written.rows,
            bytes=written.bytes,
            at=self._at(),
            corrections=(*previous.corrections, record),
        )
        self._write_state(folder, state)
        return Ok(
            CommitReceipt(
                key=key,
                fingerprint=written.fingerprint,
                rows=written.rows,
                bytes=written.bytes,
                path=final,
                frozen=True,
                gaps=state.gaps,
                attempts=0,
                correction=True,
            )
        )

    def _commit_open(
        self,
        key: SeriesKey,
        folder: Path,
        rule: KindRule,
        previous: SeriesState | None,
        written: SeriesFile,
        gaps: tuple[str, ...],
        provider_checksum: str | None,
    ) -> Result[CommitReceipt]:
        same_as_last = (
            previous is not None
            and previous.fingerprint == written.fingerprint
            and previous.gaps == gaps
        )
        attempts = previous.attempts + 1 if same_as_last and previous is not None else 1
        if not self._should_freeze(key, rule, gaps, attempts, provider_checksum):
            open_path = folder / OPEN_NAME
            _replace(written.path, open_path)
            state = SeriesState(
                key=key.text,
                fingerprint=written.fingerprint,
                rows=written.rows,
                bytes=written.bytes,
                gaps=gaps,
                attempts=attempts,
                frozen=False,
                frozen_once=previous.frozen_once if previous is not None else False,
                at=self._at(),
                corrections=previous.corrections if previous is not None else (),
            )
            self._write_state(folder, state)
            return Ok(
                CommitReceipt(
                    key,
                    written.fingerprint,
                    written.rows,
                    written.bytes,
                    open_path,
                    False,
                    gaps,
                    attempts,
                )
            )
        final = folder / f"{written.fingerprint}.parquet"
        _replace(written.path, final)
        (folder / OPEN_NAME).unlink(missing_ok=True)
        corrections = previous.corrections if previous is not None else ()
        if (
            previous is not None
            and previous.frozen_once
            and previous.fingerprint != written.fingerprint
        ):
            start, end = _range_of(written, key)
            corrections = (
                *corrections,
                Correction(
                    previous.fingerprint,
                    written.fingerprint,
                    "re-opened month re-fetched",
                    self._at(),
                    start,
                    end,
                ),
            )
        state = SeriesState(
            key=key.text,
            fingerprint=written.fingerprint,
            rows=written.rows,
            bytes=written.bytes,
            gaps=gaps,
            attempts=attempts,
            frozen=True,
            frozen_once=True,
            at=self._at(),
            corrections=corrections,
        )
        self._write_state(folder, state)
        return Ok(
            CommitReceipt(
                key, written.fingerprint, written.rows, written.bytes, final, True, gaps, attempts
            )
        )

    def _should_freeze(
        self,
        key: SeriesKey,
        rule: KindRule,
        gaps: tuple[str, ...],
        attempts: int,
        provider_checksum: str | None,
    ) -> bool:
        now_ns = int(self._wall().timestamp() * 1_000_000_000)
        if now_ns < key.end_ns + rule.settlement_days * NS_PER_DAY:
            return False
        match rule.freeze:
            case FreezeKind.GAP:
                # No hole: the month closes as fetched. A hole: only a re-fetch that finds
                # the same hole closes it, which is the one re-fetch the rule allows.
                return not gaps or attempts >= 2
            case FreezeKind.CHECKSUM:
                return provider_checksum is not None or attempts >= 2
            case FreezeKind.MONTH_END:
                return True

    def reopen(self, key: SeriesKey) -> Result[SeriesState]:
        """Re-open a frozen month so it is fetched again; the frozen file stays."""
        state = self.state(key)
        if state is None:
            return missing_artifact("key", "no series is stored under this key", key=key.text)
        if not state.frozen:
            return Ok(state)
        opened = replace(state, frozen=False, attempts=0, at=self._at())
        self._write_state(self.folder(key), opened)
        return Ok(opened)

    def read(
        self,
        key: SeriesKey,
        *,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> Result[SeriesRead]:
        """Read the current file of a month, filtered to the half-open range asked for."""
        state = self.state(key)
        if state is None:
            return missing_artifact("key", "no series is stored under this key", key=key.text)
        path = self._path(key, state)
        if not path.is_file():
            return missing_artifact(
                "key", "the series state names a file that is not there", key=key.text
            )
        start = key.start_ns if start_ns is None else start_ns
        end = key.end_ns if end_ns is None else end_ns
        if end <= start:
            return invalid_input(
                "end_ns", "a read range is half-open and non-empty", given=repr(end_ns)
            )
        try:
            import pyarrow.parquet as pq  # noqa: PLC0415 (only a read needs the library)

            table = pq.read_table(path)
            rows = tuple(
                row for row in table.to_pylist() if start <= int(row["t"]) * NS_PER_MS < end
            )
        except (OSError, ValueError) as exc:
            return storage_failure(
                "could not read the partition", context={"key": key.text, "error": str(exc)}
            )
        return Ok(SeriesRead(key, state.fingerprint, start, end, rows, state.frozen))

    def _path(self, key: SeriesKey, state: SeriesState) -> Path:
        folder = self.folder(key)
        return folder / f"{state.fingerprint}.parquet" if state.frozen else folder / OPEN_NAME

    def _write_state(self, folder: Path, state: SeriesState) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / STATE_NAME
        temp = folder / ".state.tmp"
        temp.write_text(json.dumps(state.as_json(), sort_keys=True), encoding="utf-8")
        descriptor = os.open(temp, os.O_RDWR)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _replace(temp, target)

    def _at(self) -> str:
        return self._wall().isoformat()
