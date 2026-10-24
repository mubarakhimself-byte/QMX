"""The market-data door: this machine's one way in to price history (Lib AD-28; 55 D-5).

A downloader, an importer or a derived-data step writes finished partition files into a
staging folder and calls `commit(files)`; nothing else writes the store. Every read is
opened with the holdout seal and the split definitions, so a sealed month is refused with
its reason and never with an empty answer, and a read that names a split gets only that
segment, minus its gap. Only the primary's door serves the one journaled final look;
another machine's door forwards a final look to it and waits.

QMB reads through `materialise`, which hands it paths and fingerprints. A read past
`HANDLE_ROWS` comes back as a handle, written by a child process, so a long read does not
sit in the host's memory.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import re
import shutil
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final, cast

import pyarrow.parquet as pq  # pyright: ignore[reportMissingTypeStubs]
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from qmf.core import (
    CalendarIdentity,
    Ok,
    Result,
    TypedRefusal,
    World,
    WriterId,
    is_ok,
    is_refusal,
)
from qmf.data.seal import SEAL_CONTROL_STREAM, HoldoutSeal, OperatorClick, ReadBoundary
from qmf.data.series import CommitReceipt, SeriesKey, SeriesStore
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store.engines.typed import TypedWriter
from qmf.data.store.facade import EvidenceStore
from qmf.data.store.journal import JournalStore
from qmf.data.store.refusals import (
    invalid_input,
    missing_artifact,
    policy_rejection,
    storage_failure,
)
from qmx_engine.control_door import PRINCIPAL

__all__ = [
    "HANDLE_ROWS",
    "SEAL_READ_REASON",
    "MarketDoor",
    "Placement",
    "Purpose",
    "ReadAnswer",
    "SeriesInfo",
]

HANDLE_ROWS: Final[int] = 5_000
"""A read past this many rows comes back as a handle, not as rows in the host's memory."""

SEAL_READ_REASON: Final[str] = "this month is sealed for the final look"
"""The sentence a refused sealed read carries. It is the reason, never an empty answer."""

DEFAULT_HOLDOUT_MONTHS: Final[int] = 12
"""Claude's default (plan Appendix D) when the host's settings name no window."""

DEFAULT_CALENDAR: Final[tuple[str, str, str]] = ("forex-17NY", "v1", "2025a")
"""Claude's default calendar identity, replaced by `[data] calendar` when the host sets one."""

PIN_NAME: Final[str] = ".pinned"
MONTH_NAME: Final = re.compile(r"^(\d{4})-(\d{2})$")
STAGED_MONTH: Final = re.compile(r"^(\d{4})-(\d{2})\.parquet$")
"""A staged file names its month by its name and its key by its place under the staging root."""


class Purpose(StrEnum):
    """Why a read is happening. A read that names no split is exploration (Lib AD-28)."""

    EXPLORATION = "exploration"
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    FINAL_LOOK = "final_look"


_PURPOSE_ROLE: Final[dict[Purpose, SegmentRole]] = {
    Purpose.TRAIN: SegmentRole.TRAIN,
    Purpose.VALIDATION: SegmentRole.VALIDATION,
    Purpose.TEST: SegmentRole.SEALED_TEST,
}


class Placement(StrEnum):
    """Which machine's door this is. The server holds the main copy and is the primary."""

    PC = "pc"
    NODE = "node"
    SERVER = "server"


@dataclass(frozen=True, slots=True)
class SeriesInfo:
    """One series as `instruments()` names it: its key, its months, and whether it is sealed."""

    series: str
    source: str
    subject: str
    kind: str
    variant: str
    partitions: int
    rows: int
    bytes: int
    frozen: int
    sealed: bool

    def as_json(self) -> dict[str, object]:
        return {
            "series": self.series,
            "source": self.source,
            "subject": self.subject,
            "kind": self.kind,
            "variant": self.variant,
            "partitions": self.partitions,
            "rows": self.rows,
            "bytes": self.bytes,
            "frozen": self.frozen,
            "sealed": self.sealed,
        }


@dataclass(frozen=True, slots=True)
class ReadAnswer:
    """What one read served: the rows, or the handle that holds them."""

    series: str
    purpose: Purpose
    months: tuple[str, ...]
    fingerprints: tuple[str, ...]
    rows: tuple[dict[str, object], ...] = ()
    handle: dict[str, object] | None = None

    def as_json(self) -> dict[str, object]:
        served: dict[str, object] = {
            "series": self.series,
            "purpose": self.purpose.value,
            "months": list(self.months),
            "fingerprints": list(self.fingerprints),
            "rows": len(self.rows),
        }
        if self.handle is not None:
            served["handle"] = self.handle
        else:
            served["data"] = list(self.rows)
        return served


@dataclass(frozen=True, slots=True)
class MarketDoor:
    """The one reader and writer of a machine's price store (Lib AD-28).

    ``root`` is the qmf store root: the partitions sit under its ``series`` folder. ``seal``
    is required, because a door without the holdout lock is not a door. ``split`` is the
    split definition a read names its purpose against; a host that has none serves
    exploration only, and a split read is refused by name rather than served without its gap.

    ``primary_forward`` is how a door off the primary reaches it: the host wires the tailnet
    call, and the door forwards a final look and waits for the answer. Left unset, the
    request waits and serves nothing.
    """

    root: Path
    seal: HoldoutSeal
    split: SplitManifest | None = None
    placement: Placement = Placement.PC
    world: World = World.REPLAY
    handles: Path | None = None
    primary_forward: Callable[[Mapping[str, object]], Result[ReadAnswer]] | None = None

    @property
    def primary(self) -> bool:
        """Only the server's door serves the final look (F8)."""
        return self.placement is Placement.SERVER

    @property
    def store_root(self) -> Path:
        return self.root / "series"

    def series_store(self) -> SeriesStore:
        return SeriesStore(self.store_root)

    @classmethod
    def open(
        cls,
        root: Path,
        data: Mapping[str, object],
        *,
        placement: Placement = Placement.PC,
        split: SplitManifest | None = None,
        handles: Path | None = None,
    ) -> Result[MarketDoor]:
        """Build the door the host's `[data]` settings describe, or refuse and stay shut.

        `seal_boundary_ns` is the one setting the door cannot invent: without it the host has
        said nothing about where its holdout starts, so the door refuses to open rather than
        guess a window over his price history.
        """
        boundary_ns = data.get("seal_boundary_ns")
        if not isinstance(boundary_ns, int) or isinstance(boundary_ns, bool):
            return invalid_input(
                "seal_boundary_ns",
                "the market-data door opens only with the seal's boundary: set "
                "[data] seal_boundary_ns in this machine's settings",
                given=repr(boundary_ns),
            )
        months = data.get("holdout_months", DEFAULT_HOLDOUT_MONTHS)
        rule_set, version, tzdata = DEFAULT_CALENDAR
        named = data.get("calendar")
        if isinstance(named, str) and named.count(":") == 2:
            rule_set, version, tzdata = (part.strip() for part in named.split(":"))
        calendar = CalendarIdentity.try_create(rule_set, version, tzdata)
        if is_refusal(calendar):
            return calendar
        boundary = SplitBoundary.try_create(boundary_ns)
        if is_refusal(boundary):
            return boundary
        seal = HoldoutSeal.try_create(
            seal_boundary=boundary.value,
            calendar_identity=calendar.value,
            world=data.get("world", World.REPLAY.value),
            holdout_months=months,
        )
        if is_refusal(seal):
            return seal
        world = seal.value.world
        return Ok(
            cls(
                root=root,
                seal=seal.value,
                split=split,
                placement=placement,
                world=world,
                handles=handles,
            )
        )

    # --- reads -------------------------------------------------------------

    def instruments(self) -> Result[tuple[SeriesInfo, ...]]:
        """Every series this machine holds, with its months and whether any month is sealed."""
        found: list[SeriesInfo] = []
        store = self.series_store()
        for folder in sorted(self.store_root.glob("*/*/*/*")):
            if not folder.is_dir():
                continue
            parts = folder.relative_to(self.store_root).parts
            keys: list[SeriesKey] = []
            for month in sorted(folder.iterdir()):
                if MONTH_NAME.match(month.name) is None:
                    continue
                built = _key_of(*parts, month=month.name)
                if is_ok(built):
                    keys.append(built.value)
            known = [(key, store.state(key)) for key in keys]
            states = [(key, state) for key, state in known if state is not None]
            if not states:
                continue
            first = states[0][0]
            found.append(
                SeriesInfo(
                    series=first.series,
                    source=first.source,
                    subject=first.subject,
                    kind=first.kind,
                    variant=first.variant,
                    partitions=len(states),
                    rows=sum(state.rows for _, state in states),
                    bytes=sum(state.bytes for _, state in states),
                    frozen=sum(1 for _, state in states if state.frozen),
                    sealed=any(self._month_is_sealed(key) for key in keys),
                )
            )
        return Ok(tuple(found))

    def card(self, series: str) -> Result[dict[str, object]]:
        """The dataset card content for one series: its months, fingerprints and windows."""
        keys = self._keys_of_series(series)
        if is_refusal(keys):
            return keys
        store = self.series_store()
        partitions: list[dict[str, object]] = []
        for key in keys.value:
            state = store.state(key)
            if state is None:
                continue
            partitions.append(
                {
                    "key": key.text,
                    "month": f"{key.year:04d}-{key.month:02d}",
                    "fingerprint": state.fingerprint,
                    "rows": state.rows,
                    "bytes": state.bytes,
                    "frozen": state.frozen,
                    "gaps": list(state.gaps),
                }
            )
        payload: dict[str, object] = {
            "card": series,
            "series": series,
            "instruments": [keys.value[0].subject] if keys.value else [],
            "partitions": partitions,
            "digests": [item["fingerprint"] for item in partitions],
            "world": self.world.value,
            "split_fp": self.split.split_id if self.split is not None else "",
            "seal_boundary": self.seal.seal_boundary.label(),
        }
        return Ok(payload)

    def read(
        self,
        series: str = "",
        *,
        fingerprints: Sequence[str] = (),
        start_ns: int | None = None,
        end_ns: int | None = None,
        purpose: Purpose | str = Purpose.EXPLORATION,
        data_scope: Sequence[str] | None = None,
        into: Path | None = None,
    ) -> Result[ReadAnswer]:
        """Serve one read through the seal and the split, or refuse it by name.

        ``data_scope`` is the run pass's dataset scope as the host parsed it. A door that
        answers remote callers refuses a read with no scope; the PC's own door, whose caller
        is the operator and his copilot, needs none. ``purpose`` arrives as a word from a
        route or a tool and is parsed here into the closed vocabulary it names.
        """
        if not isinstance(purpose, Purpose):
            try:
                purpose = Purpose(str(purpose))
            except ValueError:
                return invalid_input(
                    "purpose",
                    "a read states its purpose: exploration, train, validation, test or final_look",
                    given=repr(purpose),
                )
        scoped = self._scope_refusal(series, data_scope)
        if scoped is not None:
            return scoped
        keys = self._keys_of_series(series) if series else self._keys_of_fingerprints(fingerprints)
        if is_refusal(keys):
            return keys
        window_start = -(2**63) if start_ns is None else start_ns
        window_end = 2**63 - 1 if end_ns is None else end_ns
        if window_end <= window_start:
            return invalid_input(
                "end_ns", "a read range is half-open and non-empty", given=repr(end_ns)
            )
        asked = tuple(
            key for key in keys.value if key.start_ns < window_end and key.end_ns > window_start
        )
        if not asked:
            return missing_artifact(
                "window",
                "no partition falls inside the window asked for",
                given=[window_start, window_end],
            )
        if purpose is Purpose.FINAL_LOOK:
            return self._final_look(asked, window_start, window_end, into, data_scope)
        if purpose in _PURPOSE_ROLE:
            clipped = self._split_window(_PURPOSE_ROLE[purpose], window_start, window_end)
            if is_refusal(clipped):
                return clipped
            window_start, window_end = clipped.value
        served: list[SeriesKey] = []
        refused: list[str] = []
        for key in asked:
            sealed = self._month_sealed(key)
            if is_refusal(sealed):
                return sealed
            if sealed.value:
                refused.append(key.text)
            else:
                served.append(key)
        if refused:
            return policy_rejection(
                "seal",
                f"{SEAL_READ_REASON}; a read into the sealed no-peek window is refused at the "
                f"{ReadBoundary.RESEARCH_DOOR.value} boundary, never returned as a silent "
                "empty result",
                months=refused,
                seal_boundary=self.seal.seal_boundary.label(),
            )
        return self._serve(tuple(served), window_start, window_end, purpose, into)

    def materialise(
        self, fingerprints: Sequence[str], *, into: Path | None = None
    ) -> Result[tuple[Path, ...]]:
        """Copy the named partitions to local paths, verifying each fingerprint (QMB's read).

        A sealed partition is never copied into a shared cache: it needs the run's own
        attempt folder, so a sealed month cannot be left lying where the next run finds it.
        """
        keys = self._keys_of_fingerprints(fingerprints)
        if is_refusal(keys):
            return keys
        store = self.series_store()
        folder = into if into is not None else self.handles
        if folder is None:
            return invalid_input(
                "into",
                "materialise needs the run's own attempt folder when the door has no cache",
                given=repr(into),
            )
        paths: list[Path] = []
        for key in keys.value:
            state = store.state(key)
            if state is None:
                return missing_artifact("key", "no series is stored under this key", key=key.text)
            sealed = self._month_sealed(key)
            if is_refusal(sealed):
                return sealed
            if sealed.value and into is None:
                return policy_rejection(
                    "seal",
                    f"{SEAL_READ_REASON}; a sealed partition is materialised only into the "
                    "run's own attempt folder, never into a shared cache",
                    month=key.text,
                )
            source = store.folder(key) / (
                f"{state.fingerprint}.parquet" if state.frozen else ".open.parquet"
            )
            if not source.is_file():
                return missing_artifact(
                    "key", "the series state names a file that is not there", key=key.text
                )
            folder.mkdir(parents=True, exist_ok=True)
            copied = folder / f"{state.fingerprint}.parquet"
            try:
                shutil.copyfile(source, copied)
            except OSError as exc:
                return storage_failure(
                    "could not copy the partition",
                    context={"key": key.text, "error": str(exc)},
                )
            if _sha256(copied) != state.fingerprint:
                copied.unlink(missing_ok=True)
                return storage_failure(
                    "the copied partition does not hash to its fingerprint",
                    context={"key": key.text, "fingerprint": state.fingerprint},
                )
            paths.append(copied)
        return Ok(tuple(paths))

    # --- the one writer ----------------------------------------------------

    def commit(
        self,
        staged: Sequence[Path],
        *,
        staging: Path,
        born_on: Placement = Placement.SERVER,
        correction: str | None = None,
    ) -> Result[tuple[CommitReceipt, ...]]:
        """Verify staged partition files and record them: the door is the only writer.

        Each staged file names its key by its place under ``staging``, and its rows are
        streamed through the typed writer, so the fingerprint the store records is computed
        here and never taken from the file's own claim. A file born on the PC stays pinned
        until the server's commit reports the same fingerprint (`verify`).
        """
        receipts: list[CommitReceipt] = []
        store = self.series_store()
        for path in staged:
            if not path.is_relative_to(staging):
                return invalid_input(
                    "staged", "a staged partition sits under the staging folder", given=str(path)
                )
            relative = path.relative_to(staging).parts
            if len(relative) != 5:
                return invalid_input(
                    "staged",
                    "a staged partition is <source>/<subject>/<kind>/<variant>/<YYYY-MM>.parquet",
                    given=str(path),
                )
            source, subject, kind, variant, name = relative
            month = STAGED_MONTH.fullmatch(name)
            if month is None:
                return invalid_input(
                    "staged", "a staged partition's file name carries its month", given=name
                )
            key = SeriesKey.try_create(
                source,
                subject,
                kind,
                int(month.group(1)),
                int(month.group(2)),
                "" if variant == "-" else variant,
            )
            if is_refusal(key):
                return key
            landed = self._commit_one(store, key.value, path, correction)
            if is_refusal(landed):
                return landed
            receipts.append(landed.value)
            if born_on is Placement.PC:
                self._pin(store, key.value, landed.value)
        return Ok(tuple(receipts))

    def verify(self, fingerprints: Sequence[str]) -> Result[tuple[str, ...]]:
        """Unpin the PC-born partitions the server's commit reported with these fingerprints."""
        cleared: list[str] = []
        for marker in sorted(self.store_root.glob(f"*/*/*/*/*/{PIN_NAME}")):
            try:
                recorded = str(json.loads(marker.read_text(encoding="utf-8"))["fingerprint"])
            except OSError, ValueError, KeyError:
                continue
            if recorded in set(fingerprints):
                month = marker.parent
                marker.unlink(missing_ok=True)
                cleared.append(f"{month.parent.name}/{month.name}")
        return Ok(tuple(cleared))

    def pinned(self) -> tuple[str, ...]:
        """The PC-born partitions still waiting for the server's verification."""
        return tuple(
            f"{marker.parent.parent.name}/{marker.parent.name}"
            for marker in sorted(self.store_root.glob(f"*/*/*/*/*/{PIN_NAME}"))
        )

    def holdout_task(self, at: object) -> Result[dict[str, object] | None]:
        """The inbox task when the sealed span outgrew its setting, filed once (F8, N15)."""
        task = self.seal.overdue_task(self.sealed_months(), at=at)
        if is_refusal(task):
            return task
        if task.value is None:
            return Ok(None)
        return Ok(self._file_task(task.value))

    def sealed_months(self) -> int:
        """How many stored months the seal covers, read from the partitions themselves."""
        count = 0
        for folder in self.store_root.glob("*/*/*/*"):
            for month in folder.iterdir():
                match = MONTH_NAME.match(month.name)
                if match is None or not (month / "state.json").is_file():
                    continue
                built = _key_of(*folder.relative_to(self.store_root).parts, month=month.name)
                if is_ok(built) and self._month_is_sealed(built.value):
                    count += 1
        return count

    def inbox(self) -> tuple[dict[str, object], ...]:
        """Every task the door filed, oldest first. One per seal boundary."""
        path = self._inbox_path()
        if not path.is_file():
            return ()
        return tuple(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

    # --- the seal's move ---------------------------------------------------

    def move_seal(
        self, boundary: object, *, at: object, click: object
    ) -> Result[dict[str, object]]:
        """Move the seal to a new boundary on his click, journaled (55 D-5; F8)."""
        journal = self._journal()
        if is_refusal(journal):
            return journal
        writer = self._writer()
        if is_refusal(writer):
            return writer
        receipt = self.seal.move(journal.value, writer.value, at=at, click=click, boundary=boundary)
        if is_refusal(receipt):
            return receipt
        moved_to = SplitBoundary.try_create(boundary)
        if is_refusal(moved_to):
            return moved_to
        answer: dict[str, object] = {
            "was": self.seal.seal_boundary.label(),
            "sealed": moved_to.value.label(),
        }
        return Ok(answer)

    # --- internals ---------------------------------------------------------

    def _scope_refusal(self, series: str, data_scope: Sequence[str] | None) -> TypedRefusal | None:
        if data_scope is None:
            if self.primary:
                return policy_rejection(
                    "data_scope",
                    "the server's door serves remote callers only through a run pass that "
                    "names the dataset in its data_scope",
                    series=series,
                )
            return None
        scope = tuple(str(item) for item in data_scope)
        if not scope:
            return policy_rejection(
                "data_scope",
                "this run pass carries no data_scope, so the door refuses the read",
                series=series,
            )
        if "*" in scope or series in scope:
            return None
        return policy_rejection(
            "data_scope",
            "this run pass's data_scope does not list the dataset asked for",
            series=series,
            data_scope=list(scope),
        )

    def _sealed(self, position_ns: int) -> Result[bool]:
        position = SplitBoundary.try_create(position_ns)
        if is_refusal(position):
            return position
        return self.seal.is_sealed(position.value)

    def _is_sealed(self, month_start_ns: int) -> bool:
        sealed = self._sealed(month_start_ns)
        return is_ok(sealed) and sealed.value

    def _month_sealed(self, key: SeriesKey) -> Result[bool]:
        """Whether any part of the month is sealed: a month that straddles the boundary is out."""
        start = self._sealed(key.start_ns)
        if is_refusal(start):
            return start
        if start.value:
            return Ok(True)
        return self._sealed(key.end_ns - 1)

    def _month_is_sealed(self, key: SeriesKey) -> bool:
        sealed = self._month_sealed(key)
        return is_ok(sealed) and sealed.value

    def _keys_of_series(self, series: str) -> Result[tuple[SeriesKey, ...]]:
        parts = series.split("/")
        if len(parts) != 4:
            return invalid_input(
                "series",
                "a series is source/subject/kind/variant, with '-' for no variant",
                given=series,
            )
        folder = self.store_root.joinpath(*parts)
        if not folder.is_dir():
            return missing_artifact("series", "no series is stored under this name", series=series)
        keys: list[SeriesKey] = []
        for month in sorted(folder.iterdir()):
            if MONTH_NAME.match(month.name) is None:
                continue
            built = _key_of(*parts, month=month.name)
            if is_refusal(built):
                return built
            keys.append(built.value)
        if not keys:
            return missing_artifact("series", "this series has no partition yet", series=series)
        return Ok(tuple(keys))

    def _keys_of_fingerprints(self, fingerprints: Sequence[str]) -> Result[tuple[SeriesKey, ...]]:
        wanted = {str(item) for item in fingerprints}
        if not wanted:
            return invalid_input(
                "fingerprints", "a read names a series or the fingerprints to read", given=[]
            )
        store = self.series_store()
        found: list[SeriesKey] = []
        for folder in sorted(self.store_root.glob("*/*/*/*")):
            parts = folder.relative_to(self.store_root).parts
            for month in sorted(item for item in folder.iterdir() if item.is_dir()):
                built = _key_of(*parts, month=month.name)
                if is_refusal(built):
                    continue
                state = store.state(built.value)
                if state is not None and state.fingerprint in wanted:
                    found.append(built.value)
        if not found:
            return missing_artifact(
                "fingerprints",
                "no partition is stored under these fingerprints",
                given=sorted(wanted),
            )
        return Ok(tuple(found))

    def _split_window(
        self, role: SegmentRole, start_ns: int, end_ns: int
    ) -> Result[tuple[int, int]]:
        split = self.split
        if split is None:
            return invalid_input(
                "split",
                "a split read needs this host's split definitions; this door has none, so it "
                "serves exploration only",
                purpose=role.value,
            )
        return split.apply_gap(role, start_ns, end_ns)

    def _final_look(
        self,
        keys: Sequence[SeriesKey],
        start_ns: int,
        end_ns: int,
        into: Path | None,
        data_scope: Sequence[str] | None,
    ) -> Result[ReadAnswer]:
        if not self.primary:
            if self.primary_forward is None:
                return policy_rejection(
                    "final_look",
                    "only the primary's door serves the final look; this door forwards the "
                    "request to the primary and waits, and the primary is not reachable",
                    placement=self.placement.value,
                )
            return self.primary_forward(
                {
                    "series": keys[0].series if keys else "",
                    "start_ns": start_ns,
                    "end_ns": end_ns,
                    "into": str(into),
                    "data_scope": list(data_scope or ()),
                }
            )
        if self.split is None:
            return invalid_input(
                "split", "a final look is a read with a split; this door has none", given=None
            )
        if into is None:
            return invalid_input(
                "into",
                "a final look reads into the run's own attempt folder and leaves nothing in a "
                "shared cache",
                given=None,
            )
        journal = self._journal()
        if is_refusal(journal):
            return journal
        writer = self._writer()
        if is_refusal(writer):
            return writer
        allowed = self.seal.authorize_final_look(
            journal.value, writer.value, at=time.time_ns(), split_id=self.split.split_id
        )
        if is_refusal(allowed):
            return allowed
        sealed = [key for key in keys if self._month_is_sealed(key)]
        if not sealed:
            return policy_rejection(
                "final_look",
                "no month of this series is sealed, so there is no final look to take",
                series=keys[0].series if keys else "",
            )
        return self._serve(tuple(sealed), start_ns, end_ns, Purpose.FINAL_LOOK, into)

    def _serve(
        self,
        keys: Sequence[SeriesKey],
        start_ns: int,
        end_ns: int,
        purpose: Purpose,
        into: Path | None,
    ) -> Result[ReadAnswer]:
        store = self.series_store()
        fingerprints: list[str] = []
        estimate = 0
        for key in keys:
            state = store.state(key)
            if state is None:
                return missing_artifact("key", "no series is stored under this key", key=key.text)
            fingerprints.append(state.fingerprint)
            estimate += state.rows
        if estimate > HANDLE_ROWS:
            return self._serve_handle(keys, start_ns, end_ns, purpose, into, fingerprints)
        rows: list[dict[str, object]] = []
        for key in keys:
            read = store.read(key, start_ns=start_ns, end_ns=end_ns)
            if is_refusal(read):
                return read
            rows.extend(read.value.rows)
        return Ok(
            ReadAnswer(
                series=keys[0].series,
                purpose=purpose,
                months=tuple(key.text for key in keys),
                fingerprints=tuple(fingerprints),
                rows=tuple(rows),
            )
        )

    def _serve_handle(
        self,
        keys: Sequence[SeriesKey],
        start_ns: int,
        end_ns: int,
        purpose: Purpose,
        into: Path | None,
        fingerprints: Sequence[str],
    ) -> Result[ReadAnswer]:
        folder = into if into is not None else self.handles
        if folder is None:
            return invalid_input(
                "into",
                "a read this large comes back as a handle, and this door has no folder for it",
                given=len(keys),
            )
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{keys[0].series.replace('/', '_')}-{start_ns}-{end_ns}.jsonl"
        job = (
            str(self.store_root),
            tuple((key.text, start_ns, end_ns) for key in keys),
            str(target),
        )
        try:
            context = multiprocessing.get_context("spawn")
            with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
                handle, rows, summary = pool.submit(_read_in_child, job).result()
        except (OSError, RuntimeError) as exc:
            return storage_failure(
                "the read child process did not finish",
                context={"error": str(exc), "months": len(keys)},
            )
        return Ok(
            ReadAnswer(
                series=keys[0].series,
                purpose=purpose,
                months=tuple(key.text for key in keys),
                fingerprints=tuple(fingerprints),
                handle={"path": handle, "rows": rows, "summary": summary},
            )
        )

    def _commit_one(
        self, store: SeriesStore, key: SeriesKey, path: Path, correction: str | None
    ) -> Result[CommitReceipt]:
        folder = store.folder(key)
        landed = folder / ".incoming.parquet"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            writer = TypedWriter(
                landed, key.text, key.rule.columns, hole_bounds=key.rule.hole_bounds
            )
            writer.add(_rows_of(path, key.rule.columns))
            finished = writer.finish()
        except (OSError, ValueError) as exc:
            landed.unlink(missing_ok=True)
            return storage_failure(
                "could not stage the partition for the commit",
                context={"key": key.text, "error": str(exc)},
            )
        return store.commit_file(key, finished, correction=correction)

    def _pin(self, store: SeriesStore, key: SeriesKey, receipt: CommitReceipt) -> None:
        marker = store.folder(key) / PIN_NAME
        marker.write_text(
            json.dumps(
                {
                    "fingerprint": receipt.fingerprint,
                    "from": "pc",
                    "at": datetime.now(UTC).isoformat(),
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def _journal(self) -> Result[JournalStore]:
        bundle = EvidenceStore(self.root, seal=self.seal).for_world(self.world)
        if is_refusal(bundle):
            return bundle
        return Ok(bundle.value.journal)

    def _writer(self) -> Result[WriterId]:
        return WriterId.try_create("qmx-host", "market-data-door", SEAL_CONTROL_STREAM, "door")

    def _inbox_path(self) -> Path:
        return self.root / "seal-inbox.jsonl"

    def _file_task(self, task: Mapping[str, object]) -> dict[str, object]:
        for row in self.inbox():
            if row.get("seal_boundary") == task.get("seal_boundary"):
                return row
        path = self._inbox_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps(task, sort_keys=True) + "\n")
        return dict(task)


def _refused(refusal: TypedRefusal) -> HTTPException:
    """A typed refusal, as the host's route answers it: the reason, and never an empty 200."""
    return HTTPException(
        status_code=400,
        detail={
            "refused": str(refusal.category),
            "retryability": str(refusal.retryability),
            "context": dict(refusal.context),
        },
    )


class ReadBody(BaseModel):
    series: str = ""
    fingerprints: list[str] = []
    start_ns: int | None = None
    end_ns: int | None = None
    purpose: Purpose = Purpose.EXPLORATION
    data_scope: list[str] | None = None
    into: str | None = None


class MaterialiseBody(BaseModel):
    fingerprints: list[str]
    into: str | None = None


class CommitBody(BaseModel):
    staged: list[str]
    staging: str
    born_on: Placement = Placement.SERVER
    correction: str | None = None


class SealMoveBody(BaseModel):
    boundary_ns: int
    at_ns: int | None = None


class VerifyBody(BaseModel):
    fingerprints: list[str]


def market_router(door: MarketDoor) -> APIRouter:
    """The door's routes, mounted by the host behind its bearer and its principal door.

    The seal's move is the operator's alone: the principal door names a chat `agent:<sid>`
    and a workflow's work `run:<id>`, so neither reaches it.
    """
    router = APIRouter()

    @router.get("/api/data/instruments")
    def instruments() -> dict[str, object]:
        found = door.instruments()
        if is_refusal(found):
            raise _refused(found)
        return {"instruments": [item.as_json() for item in found.value]}

    @router.get("/api/data/card")
    def card(series: str) -> dict[str, object]:
        found = door.card(series)
        if is_refusal(found):
            raise _refused(found)
        return found.value

    @router.post("/api/data/read")
    def read(body: ReadBody) -> dict[str, object]:
        answered = door.read(
            body.series,
            fingerprints=body.fingerprints,
            start_ns=body.start_ns,
            end_ns=body.end_ns,
            purpose=body.purpose,
            data_scope=body.data_scope,
            into=Path(body.into) if body.into else None,
        )
        if is_refusal(answered):
            raise _refused(answered)
        return answered.value.as_json()

    @router.post("/api/data/materialise")
    def materialise(body: MaterialiseBody) -> dict[str, object]:
        copied = door.materialise(body.fingerprints, into=Path(body.into) if body.into else None)
        if is_refusal(copied):
            raise _refused(copied)
        return {"paths": [str(path) for path in copied.value]}

    @router.post("/api/data/commit")
    def commit(body: CommitBody) -> dict[str, object]:
        landed = door.commit(
            [Path(item) for item in body.staged],
            staging=Path(body.staging),
            born_on=body.born_on,
            correction=body.correction,
        )
        if is_refusal(landed):
            raise _refused(landed)
        return {
            "committed": [
                {
                    "key": receipt.key.text,
                    "fingerprint": receipt.fingerprint,
                    "frozen": receipt.frozen,
                }
                for receipt in landed.value
            ]
        }

    @router.post("/api/data/verify")
    def verify(body: VerifyBody) -> dict[str, object]:
        cleared = door.verify(body.fingerprints)
        if is_refusal(cleared):
            raise _refused(cleared)
        return {"unpinned": list(cleared.value)}

    @router.get("/api/data/pinned")
    def pinned() -> dict[str, object]:
        return {"pinned": list(door.pinned())}

    @router.get("/api/data/inbox")
    def inbox() -> dict[str, object]:
        return {"tasks": list(door.inbox())}

    @router.post("/api/data/seal/move")
    def move_seal(body: SealMoveBody) -> dict[str, object]:
        caller = PRINCIPAL.get()
        if caller.principal != "operator":
            raise HTTPException(
                status_code=403,
                detail={
                    "refused": "principal",
                    "context": {
                        "why": "the seal moves only by his click",
                        "caller": caller.principal,
                    },
                },
            )
        at = (
            body.at_ns
            if body.at_ns is not None
            else int(datetime.now(UTC).timestamp()) * 1_000_000_000
        )
        click = OperatorClick.try_create(at)
        if is_refusal(click):
            raise _refused(click)
        moved = door.move_seal(body.boundary_ns, at=at, click=click.value)
        if is_refusal(moved):
            raise _refused(moved)
        return moved.value

    _ = (instruments, card, read, materialise, commit, verify, pinned, inbox, move_seal)
    return router


def _key_of(*parts: str, month: str) -> Result[SeriesKey]:
    """A key from `source, subject, kind, variant, month`, refusing any other shape."""
    if len(parts) != 4:
        return invalid_input(
            "key", "a partition path is source/subject/kind/variant/YYYY-MM", given=list(parts)
        )
    match = MONTH_NAME.match(month)
    if match is None:
        return invalid_input("month", "a partition folder is named YYYY-MM", given=month)
    source, subject, kind, variant = parts
    return SeriesKey.try_create(
        source,
        subject,
        kind,
        int(match.group(1)),
        int(match.group(2)),
        "" if variant == "-" else variant,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows_of(path: Path, columns: Sequence[str]) -> Iterable[tuple[object, ...]]:
    """Stream one staged partition's rows in the typed writer's column order."""
    handle = pq.ParquetFile(path)
    batches = handle.iter_batches(batch_size=50_000)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    for batch in batches:  # pyright: ignore[reportUnknownVariableType]
        rows = cast("list[dict[str, object]]", batch.to_pylist())  # pyright: ignore[reportUnknownMemberType]
        for row in rows:
            yield tuple(row[name] for name in columns)


def _read_in_child(
    job: tuple[str, tuple[tuple[str, int, int], ...], str],
) -> tuple[str, int, dict[str, object]]:
    """Read the months into the handle file, in a child process, and say what was written."""
    store_root, reads, handle = job
    store = SeriesStore(Path(store_root))
    rows = 0
    months: list[str] = []
    with Path(handle).open("w", encoding="utf-8") as sink:
        for text, start_ns, end_ns in reads:
            parts = text.split("/")
            key = _key_of(*parts[:4], month=parts[4])
            if is_refusal(key):
                raise RuntimeError(f"{key.category}: {dict(key.context)}")
            read = store.read(key.value, start_ns=start_ns, end_ns=end_ns)
            if is_refusal(read):
                raise RuntimeError(f"{read.category}: {dict(read.context)}")
            for row in read.value.rows:
                sink.write(json.dumps(row, sort_keys=True) + "\n")
            rows += len(read.value.rows)
            months.append(key.value.text)
    summary: dict[str, object] = {
        "months": months,
        "series": months[0].rsplit("/", 1)[0] if months else "",
    }
    return handle, rows, summary
