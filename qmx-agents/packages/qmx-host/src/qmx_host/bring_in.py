"""Bringing his old QMX data into a new QMX folder on the first start (design 62 F step 4, 62a
gap L4, guard 5, rulings 141 and 142).

The old folder is only read. Nothing in it is opened for writing, renamed, locked or changed in
mode, and no SQLite connection is ever opened on it: every file is read as bytes. The steps, all
in `bring_in`:

1. Refusals before anything is written: an old folder LF2's gate refuses, a target in one of A1's
   "never" places (the caller's `place_refusal`), a target inside the old folder or around it, a
   file the cloud holds only online, and too little room for the copy and the switch.
2. The list: every file of the old folder with its size and sha256, every folder and every link,
   into `data/migration/old-layout-list.json`. A link is never followed and never copied.
3. The copy into the tree (data/, keys/, cache/, logs/ by the layout step's own rows), byte for
   byte, each file hashed as it is written, then the old folder listed and hashed again, then each
   copy hashed again from disk. Any difference stops the bring-in.
4. The switch (`qmx_library.migrate.from_library_b.switch_over`, the one `switch_library.py`
   runs) on the copy only, then every store read against this release (`check_open`). The switch
   archives the items its `TEST_LANES` rule says test runs made.
5. The report, in plain words, into `data/migration/bring-in-report.txt` beside its facts, which
   carry the rule's version as `test_rule`. A folder brought in under an older rule gets the
   archive once at its next host start (`recheck_at_start`).

`data/migration/bring-in-unfinished.txt` is written before the first copy and removed last, so a
bring-in that fails or stops part way leaves the new folder marked unfinished, and the Library and
the host refuse it by name (`qmx_control.library.old_library`). The report's facts are written
beside the marker at once (`finished: false`), so even a bring-in killed mid copy names its old
folder, and `again` can clear QMX's own unfinished copy and bring the same old folder in again. A
rerun into a finished folder returns the saved report and copies nothing.

Every path the bring-in opens goes through `long_path`, so a file deeper than Windows' 260
characters is copied and hashed like any other.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, closing, nullcontext, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Final, cast

from qmx_apps.supervisor import APPS_SCHEMA
from qmx_broker.service import PORTFOLIO_SCHEMA
from qmx_control.library import OLD_LIBRARY, UNFINISHED, old_library
from qmx_control.runs import RUNS_SCHEMA
from qmx_control.service import CONTROL_SCHEMA
from qmx_engine.ledger import redact
from qmx_engine.ledger.inbox_table import APP_INCIDENTS, INCIDENTS
from qmx_engine.ledger.inbox_table import SCHEMA as INBOX
from qmx_engine.ledger.migrations import migrate
from qmx_home import (
    FLAT,
    FLAT_TO_TREE,
    HOST_LOG,
    JOURNAL,
    LABEL,
    Label,
    Layout,
    NoQmxFolder,
    _flat_home,  # pyright: ignore[reportPrivateUsage] - LF2's gate, one rule for both
    _labelled_ancestor,  # pyright: ignore[reportPrivateUsage]
    _refusal,  # pyright: ignore[reportPrivateUsage]
    opens,
    resolve,
)
from qmx_home.stores import STORES
from qmx_home.versions import FLOOR_BYTES, StoreRefused, check_open, folder_of, open_sqlite
from qmx_library.migrate.from_library_b import JUNK, TEST_RULE, recheck_test_runs, switch_over
from qmx_library.store import Store

from qmx_host.jobs import Progress
from qmx_host.process_record import recorded_host

LIST: Final = "migration/old-layout-list.json"
REPORT: Final = "migration/bring-in-report.json"
REPORT_TEXT: Final = "migration/bring-in-report.txt"
OURS: Final = frozenset(f"data/{name}" for name in (LIST, REPORT, REPORT_TEXT, UNFINISHED))
"""The bring-in's own files; an old folder holding one at the same place is refused, so a copy
never lands on them."""
HOST_LOCK: Final = "engine.lock"
LEFT_OUT: Final = {
    HOST_LOCK: "the old QMX's lock file; QMX makes a new one",
    "control-process.json": "the old QMX's record of its running process; QMX makes a new one",
    LABEL: "the old folder's own label; the new folder has its own",
    f"{LABEL}.new": "a label the old QMX was still writing; the new folder has its own",
}
"""Files at the old folder's top that are not copied, and why. The new folder's lock is held by the
bring-in itself, so the old one cannot be copied over it. A label inside `data/` would make every
store's own folder lookup (`folder_of`) stop there and find no QMX folder, so no upgrade could
take its copy first."""
OPENERS: Final[Mapping[str, Callable[[sqlite3.Connection], object]]] = {
    "engine": migrate,
    "inbox": lambda db: open_sqlite(db, "inbox", ((INBOX, INCIDENTS, APP_INCIDENTS),)),
    "control": lambda db: open_sqlite(db, "control", (CONTROL_SCHEMA,)),
    "runs_index": lambda db: open_sqlite(db, "runs_index", (RUNS_SCHEMA,)),
    "apps": lambda db: open_sqlite(db, "apps", (APPS_SCHEMA,)),
    "portfolio": lambda db: open_sqlite(db, "portfolio", (PORTFOLIO_SCHEMA,)),
}
"""Each SQLite store's own versions gate, with the steps its opener passes, so the bring-in's last
check opens a store exactly as the host will: an older store is copied into `backups/` and moved
forward, and one that would refuse fails the bring-in by name."""
PRE: Final = "migration/pre"
"""The switch's frozen copy. One copied from the old folder is an earlier switch's that did not
finish, older than its `library.db`, so it is set aside before the switch freezes a fresh one."""
SWITCHED: Final = frozenset({"library.db", "artifacts.db", "artifacts"})
"""What the switch copies again into `migration/pre/` and imports into `library/`, so the room it
needs is counted twice."""
CLOUD_ONLY: Final = 0x0040_0000 | 0x0004_0000 | 0x0000_1000
"""FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS, RECALL_ON_OPEN and OFFLINE: a file a sync client keeps
only online. Reading it would download it into the old folder, so such a folder is refused."""
CHUNK: Final = 1 << 20
BUSY: Final = "another first start is running on this PC; wait for it to end"
LISTING: Final = "listing your old folder"
COPYING: Final = "copying"
CHECKING: Final = "checking the copy"
SWITCHING: Final = "moving your Library into the new one"
OPENING: Final = "opening the new folder's stores"
TREE_PARTS: Final = (
    ("data", "your work"),
    ("keys", "key files"),
    ("cache", "things QMX can make again"),
    ("logs", "QMX's own diary"),
)


class Refused(Exception):
    """The bring-in did not start. Nothing was written anywhere; the message is the one line."""


@dataclass(frozen=True, slots=True)
class Listed:
    """One file of the old folder: its path relative to the folder, with `/` between names."""

    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class Listing:
    """Everything in the old folder, read without following a link."""

    files: tuple[Listed, ...]
    folders: tuple[str, ...]
    links: tuple[tuple[str, str], ...]
    """Each link or junction and the target it names."""
    others: tuple[str, ...]
    """Entries that are none of a file, a folder or a link."""

    @property
    def size(self) -> int:
        return sum(entry.size for entry in self.files)

    def document(self) -> dict[str, object]:
        return {
            "files": [[e.path, e.size, e.sha256] for e in self.files],
            "folders": list(self.folders),
            "links": [list(link) for link in self.links],
            "others": list(self.others),
        }


@dataclass(frozen=True, slots=True)
class Report:
    """What one bring-in did: the facts, and the same facts in plain words for him."""

    finished: bool
    folder: Path
    lines: tuple[str, ...]
    facts: Mapping[str, object] = field(default_factory=dict[str, object])

    @property
    def text(self) -> str:
        return "\n".join(self.lines) + "\n"


type Copier = Callable[[Path, Path], str]
"""Copies one file and returns the sha256 of the bytes it wrote."""


def long_path(path: Path) -> Path:
    """`path` as Windows opens it past 260 characters: absolute, with `\\\\?\\` before it (and
    `\\\\?\\UNC\\` before a network path). Unchanged on other systems."""
    if os.name != "nt" or str(path).startswith("\\\\?\\"):
        return path
    full = os.path.abspath(path)
    if full.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + full[2:])
    return Path("\\\\?\\" + full)


def _plain(name: object) -> str:
    """A path as he reads it: without the prefix `long_path` adds."""
    text = os.fsdecode(name) if isinstance(name, str | bytes) else str(name)
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text.removeprefix("\\\\?\\UNC\\")
    return text.removeprefix("\\\\?\\")


def copy_file(source: Path, target: Path) -> str:
    """Copy `source` to the new file `target` byte for byte, keeping its times. `target` must not
    exist, so a copy never lands on a file already there."""
    source, target = long_path(source), long_path(target)
    digest = hashlib.sha256()
    with source.open("rb") as reading, target.open("xb") as writing:
        while chunk := reading.read(CHUNK):
            digest.update(chunk)
            writing.write(chunk)
        writing.flush()
        os.fsync(writing.fileno())
    found = source.stat()
    os.utime(target, ns=(found.st_atime_ns, found.st_mtime_ns))
    return digest.hexdigest()


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with long_path(path).open("rb") as reading:
        while chunk := reading.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def place_in_tree(relative: str) -> str | None:
    """Where a file of an old flat home lands in the new folder, relative to it, by the layout
    step's own rows; None for a file that is left out."""
    if relative in LEFT_OUT:
        return None
    if relative == HOST_LOG[0]:
        return HOST_LOG[1]
    for source, target in FLAT_TO_TREE:
        if relative == source or relative.startswith(f"{source}/"):
            return target + relative[len(source) :]
    return f"data/{relative}"


def old_refusal(old: Path) -> str | None:
    """Why `old` cannot be brought in, or None when it is a whole old QMX folder. LF2's gate
    decides, the same one the layout step asks, so nothing that gate refuses is ever read."""
    if not old.is_dir():
        return f"there is no folder at {old}"
    label = _label_at(old)
    if label is not None and opens(label):
        return f"{old} is already a QMX folder; open it instead of bringing it in"
    if label is not None and label.format_version != FLAT:
        return f"{old} is a QMX folder of format {label.format_version}, not an old one"
    if (old / JOURNAL).is_file():
        return (
            f"{old} is a QMX folder whose layout step stopped part way, so its files are half "
            "moved; QMX does not copy a half-moved folder"
        )
    ancestor = _labelled_ancestor(old)
    if ancestor is not None:
        return f"{old} is a part of the QMX folder {ancestor}, not an old QMX folder"
    refused = _refusal(old, label)
    if refused is not None:
        return refused
    if not _flat_home(old):
        return f"{old} holds none of an old QMX folder's own files"
    return None


def _running(old: Path) -> str | None:
    """A QMX host still serving the old folder, read from its process record alone (F step 4.1):
    the old folder's lock is never taken, because taking it would write there."""
    pid = recorded_host(old)
    if pid is None:
        return None
    return f"a QMX host is still running on {old} (PID {pid}); stop it, then run the first start"


def _label_at(folder: Path) -> Label | None:
    try:
        return Label.parse((folder / LABEL).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


type Lock = Path | Held | None
"""The per-user first-start lock: its file, taken here and removed afterwards; or a lock the
caller already holds, released here when the bring-in ends; or None for no lock."""


def bring_in(
    old: Path,
    folder: Path,
    *,
    place_refusal: Callable[[Path], str | None],
    lock: Lock = None,
    copy: Copier = copy_file,
    progress: Progress | None = None,
) -> Report:
    """Bring the old folder `old` into the QMX folder `folder`, made here when it is new.

    Raises `Refused` before anything is written. Returns the report: finished, or unfinished with
    the reason, the new folder then marked unfinished and the old one untouched. A rerun into a
    folder whose bring-in finished returns that report and copies nothing. `lock` keeps two first
    starts from running at once; `progress` hears each step and its counts.
    """
    with _taken(lock):
        return _bring_in(old, folder, place_refusal, copy, progress or _unheard)


def again(
    old: Path,
    folder: Path,
    *,
    place_refusal: Callable[[Path], str | None],
    lock: Lock = None,
    copy: Copier = copy_file,
    progress: Progress | None = None,
) -> Report:
    """`bring_in` into a folder whose bring-in from `old` did not finish, after clearing QMX's own
    unfinished copy there. Refused, with nothing cleared, unless the folder is marked unfinished,
    its saved facts name `old`, and `old` is still an old folder with the files its saved list
    names. His own files are never in that copy: the copy is cleared only of what the bring-in
    wrote, and a file outside `data/` only when its bytes match the old folder's."""
    with _taken(lock):
        heard = progress or _unheard
        _clear_unfinished(old.absolute(), folder.absolute(), heard)
        return _bring_in(old, folder, place_refusal, copy, heard)


def refusal_before_copy(
    old: Path, folder: Path, place_refusal: Callable[[Path], str | None]
) -> str | None:
    """Why bringing `old` into `folder` is refused before anything is read in bulk, or None: an
    old folder LF2's gate refuses, a host still running on it, one of A1's "never" places, the
    two folders overlapping, and a folder that already holds a bring-in from another old folder.
    Fast, so the first-start card answers it at once."""
    old, folder = old.absolute(), folder.absolute()
    real_old = old.resolve()
    done = _finished(folder)
    if done is not None:
        brought = Path(str(done.facts.get("old_is") or done.facts.get("old")))
        if brought.resolve() != real_old:
            return (
                f"{folder} already holds the old data brought in from {done.facts.get('old')}, "
                f"not {old}; bring {old} into another new folder"
            )
        return None
    refusal = old_refusal(real_old) or _running(real_old) or place_refusal(folder)
    real_folder = folder.resolve()
    if refusal is None and (
        real_folder.is_relative_to(real_old) or real_old.is_relative_to(real_folder)
    ):
        refusal = f"{folder} and {old} overlap; the new QMX folder must be outside the old one"
    return refusal


def unfinished_facts(folder: Path) -> Mapping[str, object] | None:
    """The saved facts of a bring-in into `folder` that did not finish, or None when the folder
    is not marked unfinished. Empty when the marker is there but the facts cannot be read."""
    data = folder / "data"
    if not (data / UNFINISHED).is_file():
        return None
    try:
        facts: object = json.loads((data / REPORT).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return cast("dict[str, object]", facts) if isinstance(facts, dict) else {}


def _bring_in(
    old: Path,
    folder: Path,
    place_refusal: Callable[[Path], str | None],
    copy: Copier,
    progress: Progress,
) -> Report:
    old, folder = old.absolute(), folder.absolute()
    real_old = old.resolve()
    refusal = refusal_before_copy(old, folder, place_refusal)
    if refusal is not None:
        raise Refused(refusal)
    done = _finished(folder)
    if done is not None:
        return done
    try:
        survey, layout = _prepared(old, real_old, folder)
    except OSError as failed:
        raise Refused(
            f"the bring-in did not start: {_reason(failed)}. Nothing was copied; fix that, then "
            "bring your old data in again"
        ) from None
    started = time.monotonic()
    with hold(layout.data / HOST_LOCK, f"a QMX host is running on {layout.root}; stop it first"):
        if (layout.data / UNFINISHED).is_file():
            raise Refused(str(old_library(layout.data)))
        if {e.name for e in layout.data.iterdir()} - {HOST_LOCK}:
            raise Refused(
                f"{layout.root} already holds QMX data; bring your old data into a new, empty "
                "folder"
            )
        facts: dict[str, object] = {
            "old": str(old),
            "old_is": str(real_old) if real_old != old else None,
            "folder": str(layout.root),
            "started": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        unfinished = layout.data / UNFINISHED
        _write(unfinished, "it stopped while copying")
        _write(layout.data / REPORT, json.dumps({**facts, "finished": False}, indent=1))
        meter = _Meter(progress, survey)
        try:
            why = _carry(real_old, layout, facts, copy, unfinished, meter)
        except Exception as failed:  # every failure ends as an unfinished report, never a traceback
            why = f"it stopped with an error: {_reason(failed)}"
        facts["seconds"] = round(time.monotonic() - started, 3)
        facts["finished"] = why is None
        facts["why"] = why or ""
        report = Report(why is None, layout.root, tuple(_lines(facts)), facts)
        _write(layout.data / REPORT, json.dumps(facts, indent=1, sort_keys=True))
        _write(layout.data / REPORT_TEXT, report.text)
        if why is None:
            unfinished.unlink()
        else:
            _write(unfinished, why)
        return report


type Survey = tuple[tuple[str, int, int], ...]
"""Each file of the old folder: its path, size and Windows attributes."""


def _prepared(old: Path, real_old: Path, folder: Path) -> tuple[Survey, Layout]:
    """The checks that read the old folder's records and the target's drive, then the new QMX
    folder made or opened. Raises `Refused`, or the `OSError` that stopped a read, before the
    unfinished marker exists."""
    survey = _survey(real_old)
    cloud = [path for path, _, attributes in survey if attributes & CLOUD_ONLY]
    if cloud:
        raise Refused(
            f"{len(cloud)} files of {old} are kept online only (the first is {cloud[0]}); "
            "reading them would download them into it. Mark the folder to be kept on this "
            "device in your sync program, then run the first start again"
        )
    clash = sorted(OURS & {place_in_tree(path) or "" for path, _, _ in survey})
    if clash:
        raise Refused(f"{old} already holds {clash[0]}, a file the bring-in writes")
    _room(folder, survey)
    try:
        return survey, resolve(folder, create=True)
    except NoQmxFolder as refused:
        raise Refused(str(refused)) from None


class _Meter:
    """The bring-in's counts, told to `progress` as they change. `done` of `total` is the current
    step's own count."""

    def __init__(self, progress: Progress, survey: Survey) -> None:
        self._progress = progress
        self._step = ""
        self._done = 0
        self._total = 0
        self.counts = {
            "files_hashed": 0,
            "files_total": len(survey),
            "files_copied": 0,
            "bytes_copied": 0,
            "bytes_total": sum(size for _, size, _ in survey),
            "versions_switched": 0,
            "versions_total": 0,
        }

    def at(self, step: str, total: int = 0) -> None:
        self._step, self._done, self._total = step, 0, total
        self._tell()

    def hashed(self) -> None:
        self.counts["files_hashed"] += 1
        self.step_done()

    def copied(self, size: int) -> None:
        self.counts["files_copied"] += 1
        self.counts["bytes_copied"] += size
        self.step_done()

    def switched(self, done: int, total: int) -> None:
        self.counts["versions_switched"], self.counts["versions_total"] = done, total
        self._done, self._total = done, total
        self._tell()

    def step_done(self) -> None:
        self._done += 1
        self._tell()

    def _tell(self) -> None:
        self._progress(self._step, done=self._done, total=self._total, **self.counts)


def _unheard(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
    """The progress of a bring-in nobody watches."""


def _carry(
    old: Path,
    layout: Layout,
    facts: dict[str, object],
    copy: Copier,
    unfinished: Path,
    meter: _Meter,
) -> str | None:
    """Steps 2 to 4. Returns why the bring-in stopped, or None when every check held."""
    meter.at(LISTING, meter.counts["files_total"])
    before = listing(old, on_file=meter.hashed)
    _write(layout.data / LIST, json.dumps(before.document(), indent=1))
    facts["listed"] = {"files": len(before.files), "bytes": before.size}
    facts["links"] = [{"path": path, "target": target} for path, target in before.links]
    facts["others"] = list(before.others)
    copied: dict[str, list[int]] = {}
    left_out: list[dict[str, str]] = []
    placed: list[tuple[Listed, Path]] = []
    facts["copied"] = copied
    facts["left_out"] = left_out
    for folder in before.folders:
        long_path(layout.root / str(place_in_tree(folder))).mkdir(parents=True, exist_ok=True)
    meter.at(COPYING, sum(1 for entry in before.files if place_in_tree(entry.path) is not None))
    for entry in before.files:
        target = place_in_tree(entry.path)
        if target is None:
            left_out.append({"path": entry.path, "why": LEFT_OUT[entry.path]})
            continue
        written = layout.root / target
        long_path(written.parent).mkdir(parents=True, exist_ok=True)
        if copy(old / entry.path, written) != entry.sha256:
            return f"{entry.path} in your old folder changed while it was copied"
        part = copied.setdefault(target.split("/", 1)[0], [0, 0])
        part[0] += 1
        part[1] += entry.size
        placed.append((entry, written))
        meter.copied(entry.size)
    _write(unfinished, "it stopped while checking the copy")
    meter.at(CHECKING, len(before.files) + len(placed))
    after = listing(old, on_file=meter.step_done)
    if after != before:
        return f"your old folder changed while it was copied ({_first_change(before, after)})"
    for entry, written in placed:
        if sha256_of(written) != entry.sha256:
            return f"the copy of {entry.path} does not match your old folder"
        meter.step_done()
    _write(unfinished, "it stopped while moving your old Library into the new one")
    facts["library"] = None
    facts["set_aside"] = None
    facts["test_rule"] = TEST_RULE
    facts["test_runs"] = []
    if (layout.data / OLD_LIBRARY).is_file():
        meter.at(SWITCHING)
        stale = layout.data / PRE
        if stale.exists():
            kept = stale.with_name(f"pre-from-the-old-folder-{datetime.now(UTC):%Y%m%dT%H%M%SZ}")
            stale.rename(kept)
            facts["set_aside"] = kept.relative_to(layout.data).as_posix()
        why = _switch(layout, facts, meter.switched)
        if why is not None:
            return why
    _write(unfinished, "it stopped while opening the new folder's stores")
    meter.at(OPENING)
    why = _opens(layout)
    if why is not None:
        return why
    facts["stores"] = [verdict.line for verdict in check_open(layout).verdicts]
    return None


def _opens(layout: Layout) -> str | None:
    """Open every SQLite store of the new folder the way its opener does when a host starts:
    found from its own file through `folder_of`, then through its versions gate. Returns why one
    would not open, by name, or None."""
    for store in STORES.values():
        path = layout.data / store.path
        if store.kind != "sqlite" or not path.is_file():
            continue
        found = folder_of(path)
        if found is None or found.root != layout.root:
            return (
                f"the {store.words} at {path} does not sit in the QMX folder {layout.root} as "
                "QMX finds it, so it could not be upgraded"
            )
        opener = OPENERS.get(store.name)
        if opener is None:
            continue
        try:
            with closing(sqlite3.connect(path, isolation_level=None, timeout=30)) as db:
                opener(db)
        except StoreRefused as refused:
            return f"the {store.words} would not open in the new folder: {refused}"
    return None


def _switch(
    layout: Layout, facts: dict[str, object], on_item: Callable[[int, int], None]
) -> str | None:
    """The built switch on the copy only."""
    switched = switch_over(layout.data, redactor=redact, on_item=on_item)
    tests = switched.imported.tests
    kinds, test_items = _kinds_brought_in(layout.data / PRE / OLD_LIBRARY, tests)
    facts["test_runs"] = list(tests)
    facts["test_items"] = test_items
    facts["library"] = {"report": switched.report(), "kinds": kinds}
    if switched.ok:
        return None
    checked = switched.verification
    differences = [
        *(
            f"{r.name} {r.before} before, {r.after} after"
            for r in checked.rows
            if r.before != r.after
        ),
        *(f"a stored file differs ({bad})" for bad in checked.bad_blobs),
        *(f"a version chain differs ({bad})" for bad in checked.bad_chains),
    ]
    return "the new Library does not match your old one: " + "; ".join(differences)


def _kinds_brought_in(
    frozen: Path, tests: tuple[str, ...] | list[str]
) -> tuple[dict[str, int], int]:
    """Items per old kind in the switch's frozen copy, the test junk and the archived test runs
    left out: what the switch imported for him. Then how many items the test runs' versions
    `tests` make. An item is one old root, however many versions it has."""
    kinds: dict[str, set[str]] = {}
    made_by_tests: set[str] = set()
    with closing(sqlite3.connect(f"{frozen.resolve().as_uri()}?mode=ro", uri=True)) as db:
        for (raw,) in db.execute("SELECT data FROM items"):
            row = cast("dict[str, object]", json.loads(raw))
            if str(row["id"]) in tests:
                made_by_tests.add(str(row["root_id"]))
            elif str(row["id"]) not in JUNK:
                kinds.setdefault(str(row["kind"]), set()).add(str(row["root_id"]))
    return {kind: len(roots) for kind, roots in sorted(kinds.items())}, len(made_by_tests)


def _survey(old: Path) -> Survey:
    """Each file's path, size and Windows attributes (0 elsewhere), from the file system's records
    alone, before any file is read."""
    found: list[tuple[str, int, int]] = []
    for relative, entry in _walk(old):
        if entry.is_file(follow_symlinks=False) and not _is_link(entry):
            record = entry.stat(follow_symlinks=False)
            found.append((relative, record.st_size, getattr(record, "st_file_attributes", 0)))
    return tuple(found)


def listing(old: Path, on_file: Callable[[], None] | None = None) -> Listing:
    """Every entry of `old`, each file hashed, in one fixed order so two listings compare.
    `on_file` is called once each file is hashed."""
    files: list[Listed] = []
    folders: list[str] = []
    links: list[tuple[str, str]] = []
    others: list[str] = []
    for relative, entry in _walk(old):
        if _is_link(entry):
            links.append((relative, _plain(os.readlink(entry.path))))
        elif entry.is_dir(follow_symlinks=False):
            folders.append(relative)
        elif entry.is_file(follow_symlinks=False):
            path = Path(entry.path)
            files.append(Listed(relative, path.stat().st_size, sha256_of(path)))
            if on_file is not None:
                on_file()
        else:
            others.append(relative)
    return Listing(tuple(files), tuple(folders), tuple(links), tuple(others))


def _walk(old: Path) -> Iterator[tuple[str, os.DirEntry[str]]]:
    """Each entry below `old`: a folder's entries sorted by name, then its folders' entries in
    turn, never through a link."""
    pending: list[tuple[str, Path]] = [("", long_path(old))]
    while pending:
        prefix, folder = pending.pop()
        with os.scandir(folder) as entries:
            ordered = sorted(entries, key=lambda e: e.name)
        children: list[tuple[str, Path]] = []
        for entry in ordered:
            relative = f"{prefix}{entry.name}"
            yield relative, entry
            if entry.is_dir(follow_symlinks=False) and not _is_link(entry):
                children.append((f"{relative}/", Path(entry.path)))
        pending.extend(reversed(children))


def _is_link(entry: os.DirEntry[str]) -> bool:
    return entry.is_symlink() or entry.is_junction()


def _first_change(before: Listing, after: Listing) -> str:
    was = {e.path: e for e in before.files}
    now = {e.path: e for e in after.files}
    for path in sorted(was.keys() | now.keys()):
        if path not in now:
            return f"{path} went away"
        if path not in was:
            return f"{path} appeared"
        if was[path] != now[path]:
            return f"{path} changed"
    return "its folders or links changed"


def _room(folder: Path, survey: Survey) -> None:
    """Refuse a copy that would leave the target's drive below the floor a pre-change copy keeps,
    counting the switch's own second copy of the old Library."""
    library = sum(size for path, size, _ in survey if _switched(path))
    needed = sum(size for _, size, _ in survey) + 2 * library
    existing = next(p for p in (folder, *folder.parents) if long_path(p).exists())
    free = shutil.disk_usage(existing).free
    if free - needed < FLOOR_BYTES:
        raise Refused(
            f"bringing your old data in needs {_size(needed)} and the drive holding {folder} has "
            f"{_size(free)} free; QMX keeps at least {_size(FLOOR_BYTES)} free there. Free some "
            "space or pick a folder on another drive"
        )


def _switched(path: str) -> bool:
    top = path.split("/", 1)[0]
    return top in SWITCHED or top.removesuffix("-wal") in SWITCHED


def recheck_at_start(home: Path, store: Store) -> int | None:
    """The host's one pass over a folder whose bring-in finished under an older `TEST_RULE`, or
    before there was one: archive what the rule matches, stamp the saved report with the rule's
    version and add the count to its text. Returns the count, or None when nothing was due.

    A finished bring-in with no frozen Library copy left to judge by is left alone, unstamped.
    Archiving skips what is archived already, so a pass stopped part way is finished by the next
    start."""
    done = _finished(home.parent)
    stamp = None if done is None else done.facts.get("test_rule")
    if done is None or (isinstance(stamp, int) and stamp >= TEST_RULE):
        return None
    tests: tuple[str, ...] = ()
    if done.facts.get("library") is not None:
        found = recheck_test_runs(store, home)
        if found is None:
            return None
        tests = found
    items = _kinds_brought_in(home / PRE / OLD_LIBRARY, tests)[1] if tests else 0
    facts = {**done.facts, "test_rule": TEST_RULE, "test_runs": list(tests), "test_items": items}
    lines = list(done.lines)
    if tests:
        when = f"{datetime.now(UTC):%Y-%m-%d}"
        lines += ["", f"Checked again when QMX started on {when}: {_made_by_tests(items)}"]
    _write(home / REPORT_TEXT, Report(True, home.parent, tuple(lines)).text)
    _write(home / REPORT, json.dumps(facts, indent=1, sort_keys=True))
    return items


def _made_by_tests(count: int) -> str:
    return (
        f"{_count(count, 'item')} made by test runs, not by you, {'is' if count == 1 else 'are'} "
        "in the new Library but archived: search and recall leave them out, and nothing was "
        "deleted."
    )


def brought_from(folder: Path) -> Mapping[str, object] | None:
    """The facts of the bring-in that finished into the QMX folder `folder`, or None."""
    done = _finished(folder)
    return None if done is None else done.facts


def _finished(folder: Path) -> Report | None:
    """The saved report of a bring-in that finished into `folder`, or None."""
    data = folder / "data"
    try:
        facts = cast("dict[str, object]", json.loads((data / REPORT).read_text(encoding="utf-8")))
        lines = (data / REPORT_TEXT).read_text(encoding="utf-8").splitlines()
    except OSError, ValueError:
        return None
    if facts.get("finished") is not True or (data / UNFINISHED).exists():
        return None
    return Report(True, folder, tuple(lines), facts)


class Held:
    """An OS lock on a file, held until `release` or the end of a `with` block, from any thread.
    The OS lets go when the process ends, so a stopped first start never leaves it held."""

    def __init__(self, path: Path, handle: IO[bytes], *, removed: bool, made: bool) -> None:
        self._path = path
        self._handle: IO[bytes] | None = handle
        self._removed = removed
        self._made = made

    def __enter__(self) -> Held:
        return self

    def __exit__(self, *_: object) -> None:
        self.release()

    def release(self) -> None:
        """Let go, once; a second call does nothing."""
        handle, self._handle = self._handle, None
        if handle is None:
            return
        if self._removed and os.name != "nt":
            self._path.unlink(missing_ok=True)
        handle.close()
        if self._removed and os.name == "nt":
            with suppress(OSError):
                self._path.unlink(missing_ok=True)
        if self._removed and self._made:
            with suppress(OSError):
                self._path.parent.rmdir()


def hold(path: Path, busy: str, *, removed: bool = False) -> Held:
    """Take an OS lock on `path`; refused with `busy` while another process or handle holds it.
    `removed` takes the file (and its folder, when this made it) away on release, so nothing but
    the pointer stays beside the pointer (ruling 143). A holder checks that its file is still the
    one at `path`, because a file removed under a waiting process is not a lock."""
    made = not path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    return Held(path, _locked(path, busy), removed=removed, made=made)


def _taken(lock: Lock) -> AbstractContextManager[object]:
    if isinstance(lock, Held):
        return lock
    return nullcontext() if lock is None else hold(lock, BUSY, removed=True)


def _clear_unfinished(old: Path, folder: Path, progress: Progress) -> None:
    """Clear QMX's own unfinished copy of `old` from `folder` (`again`), or refuse with nothing
    cleared."""
    facts = unfinished_facts(folder)
    if facts is None:
        raise Refused(f"{folder} holds no unfinished bring-in; nothing was cleared")
    named = facts.get("old_is") or facts.get("old")
    if not named:
        raise Refused(
            f"{folder} is marked unfinished, but its record of the old folder cannot be read, so "
            "QMX cannot tell its own copy there; nothing was cleared. Remove the folder yourself "
            "and bring your old data in again"
        )
    if Path(str(named)).resolve() != old.resolve():
        raise Refused(
            f"{folder} holds an unfinished copy of {facts.get('old')}, not of {old}; nothing was "
            "cleared"
        )
    refusal = old_refusal(old.resolve())
    if refusal is not None:
        raise Refused(f"{refusal}; nothing was cleared")
    data = folder / "data"
    try:
        saved: object = json.loads((data / LIST).read_text(encoding="utf-8"))
    except FileNotFoundError:
        saved = None
    except (OSError, ValueError) as unreadable:
        raise Refused(
            f"the list of your old folder in {folder} cannot be read ({unreadable}); nothing "
            "was cleared"
        ) from None
    if saved is not None:
        progress(LISTING)
        now = listing(old.resolve())
        if json.loads(json.dumps(now.document())) != saved:
            raise Refused(
                f"your old folder {old} changed since the bring-in stopped, so QMX cannot tell "
                f"its own copy in {folder}; nothing was cleared. Remove {folder} yourself and "
                "bring your old data in again"
            )
    with hold(data / HOST_LOCK, f"a QMX host is running on {folder}; stop it first"):
        for entry in long_path(data).iterdir():
            if entry.name == HOST_LOCK:
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry, onexc=_writable_then_again)
            else:
                _writable_then_again(os.unlink, str(entry), None)
    if isinstance(saved, dict):
        _clear_outside_data(folder, cast("dict[str, object]", saved))


def _clear_outside_data(folder: Path, saved: Mapping[str, object]) -> None:
    """Remove the copies the bring-in placed outside `data/`: each listed file whose copy still
    holds the old file's bytes, then each folder it made that is left empty."""
    for row in cast("list[list[object]]", saved.get("files", [])):
        target = place_in_tree(str(row[0]))
        if target is None or target.startswith("data/"):
            continue
        copy = folder / target
        if long_path(copy).is_file() and sha256_of(copy) == row[2]:
            long_path(copy).unlink()
    made = [place_in_tree(str(name)) for name in cast("list[object]", saved.get("folders", []))]
    for target in sorted((t for t in made if t and not t.startswith("data/")), reverse=True):
        with suppress(OSError):
            long_path(folder / target).rmdir()


def _writable_then_again(
    remove: Callable[[str], object], path: str, _error: BaseException | None
) -> None:
    """Remove `path`, making it writable first when the switch left it read-only."""
    with suppress(OSError):
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    remove(path)


def _locked(path: Path, busy: str) -> IO[bytes]:
    while True:
        handle = path.open("a+b")
        try:
            _lock(handle)
        except OSError:
            handle.close()
            raise Refused(busy) from None
        try:
            same = os.path.samestat(os.fstat(handle.fileno()), os.stat(path))
        except OSError:
            same = False
        if same:
            return handle
        handle.close()


def _lock(handle: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f"{path.name}.new")
    staged.write_text(text, encoding="utf-8")
    staged.replace(path)


def _reason(error: BaseException) -> str:
    if isinstance(error, OSError) and error.strerror:
        where = f" ({_plain(error.filename)})" if error.filename else ""
        return f"{error.strerror}{where}"
    return _plain(str(error)) or type(error).__name__


def _count(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _size(count: int) -> str:
    for unit, scale in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if count >= scale:
            return f"{count / scale:.1f} {unit}"
    return f"{count} bytes"


def _lines(facts: Mapping[str, object]) -> list[str]:
    """The report in plain words: what moved where, what was left out and why, what was checked,
    and what happens to his old folder."""
    old, folder = str(facts["old"]), str(facts["folder"])
    if not facts.get("finished"):
        return [
            f"Bringing your old QMX data in did not finish: {facts.get('why')}.",
            f"Your old folder {old} was not changed.",
            f"{folder} is marked unfinished, and QMX will not start on it. Bring your old data "
            "in again into the same folder from the first start; QMX first clears only its own "
            "unfinished copy there.",
        ]
    listed = cast("dict[str, int]", facts["listed"])
    lines = [f"Your old QMX data is in {folder} now."]
    if facts.get("old_is"):
        lines.append(
            f"Your old folder {old} is a link; its files were read from {facts['old_is']}."
        )
    lines += [
        f"Your old folder {old} was only read, never changed: its "
        f"{_count(listed['files'], 'file')} ({_size(listed['bytes'])}) were checked file by file "
        "before and after.",
        "",
        "What moved, and where:",
    ]
    copied = cast("dict[str, list[int]]", facts.get("copied", {}))
    for part, meaning in TREE_PARTS:
        if part in copied:
            files, size = copied[part]
            lines.append(f"  {_count(files, 'file')} ({_size(size)}) into {part}, {meaning}")
    library = cast("dict[str, object] | None", facts.get("library"))
    junk: list[str] = []
    if library is not None:
        kinds = cast("dict[str, int]", library["kinds"])
        switched = cast("dict[str, object]", library["report"])
        junk = cast("list[str]", switched.get("junk", []))
        lines += ["", f"Your Library: {_count(sum(kinds.values()), 'item')} in the new Library."]
        lines += [f"  {kind}: {count}" for kind, count in kinds.items()]
        tests = cast("list[str]", facts.get("test_runs", []))
        made = facts.get("test_items")
        if tests:
            lines.append(f"  {_made_by_tests(made if isinstance(made, int) else len(tests))}")
        retired = cast("list[str]", switched.get("retired", []))
        if retired:
            lines.append(
                f"  The old Library files ({', '.join(retired)}) now sit read-only in "
                f"{Path(folder) / 'data' / 'migration' / 'retired'}."
            )
        if facts.get("set_aside"):
            lines.append(
                "  Your old folder held the frozen copy of an earlier move of the Library that "
                f"did not finish. It is kept as {Path(folder) / 'data' / str(facts['set_aside'])}, "
                "and the Library was frozen afresh from library.db, so no item is left out."
            )
    left: list[str] = []
    if junk:
        left.append(
            f"  {_count(len(junk), 'test result')} named remote-flow, made by test runs and not "
            "by you, left in your old folder."
        )
    left += [f"  {r['path']}: {r['why']}." for r in cast("list[dict[str, str]]", facts["left_out"])]
    left += [
        f"  {r['path']}: a link to {r['target']}, not a file; QMX makes it again if it needs it."
        for r in cast("list[dict[str, str]]", facts["links"])
    ]
    left += [f"  {path}: not a file or a folder." for path in cast("list[str]", facts["others"])]
    lines += ["", "What was left out, and why:", *(left or ["  Nothing."])]
    checked = "Checked: every file's fingerprint (sha256), in your old folder and in the copy"
    if library is not None:
        checked += (
            ", and in the Library the items per kind, version chains, links, saved results and "
            "every stored file"
        )
    lines += ["", f"{checked}."]
    held = [line for line in cast("list[str]", facts.get("stores", [])) if "refuse" in line]
    lines += [f"  {line}" for line in held]
    lines += [
        "",
        f"What happens to your old folder: nothing. It stays at {old} exactly as it was. QMX does "
        f"not use it any more; once QMX has worked from {folder} for a while, you can remove it "
        "yourself.",
    ]
    return lines
