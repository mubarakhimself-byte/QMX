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
   runs) on the copy only, then every store read against this release (`check_open`).
5. The report, in plain words, into `data/migration/bring-in-report.txt` beside its facts.

`data/migration/bring-in-unfinished.txt` is written before the first copy and removed last, so a
bring-in that fails or stops part way leaves the new folder marked unfinished, and the Library and
the host refuse it by name (`qmx_control.library.old_library`). A rerun into a finished folder
returns the saved report and copies nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from collections.abc import Callable, Generator, Iterator, Mapping
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Final, cast

from qmx_control.library import OLD_LIBRARY, UNFINISHED, old_library
from qmx_engine.ledger import redact
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
from qmx_home.versions import FLOOR_BYTES, check_open
from qmx_library.migrate.from_library_b import JUNK, switch_over
from qmx_library.port import LibraryRefused

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
}
"""Files at the old folder's top that are not copied, and why. The new folder's lock is held by the
bring-in itself, so the old one cannot be copied over it."""
SWITCHED: Final = frozenset({"library.db", "artifacts.db", "artifacts"})
"""What the switch copies again into `migration/pre/` and imports into `library/`, so the room it
needs is counted twice."""
CLOUD_ONLY: Final = 0x0040_0000 | 0x0004_0000 | 0x0000_1000
"""FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS, RECALL_ON_OPEN and OFFLINE: a file a sync client keeps
only online. Reading it would download it into the old folder, so such a folder is refused."""
CHUNK: Final = 1 << 20
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


def copy_file(source: Path, target: Path) -> str:
    """Copy `source` to the new file `target` byte for byte, keeping its times. `target` must not
    exist, so a copy never lands on a file already there."""
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
    with path.open("rb") as reading:
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
    from qmx_host.host import recorded_host  # noqa: PLC0415 (the host module is heavy)

    pid = recorded_host(old)
    if pid is None:
        return None
    return f"a QMX host is still running on {old} (PID {pid}); stop it, then run the first start"


def _label_at(folder: Path) -> Label | None:
    try:
        return Label.parse((folder / LABEL).read_text(encoding="utf-8"))
    except OSError, ValueError:
        return None


def bring_in(
    old: Path,
    folder: Path,
    *,
    place_refusal: Callable[[Path], str | None],
    lock: Path | None = None,
    copy: Copier = copy_file,
) -> Report:
    """Bring the old folder `old` into the QMX folder `folder`, made here when it is new.

    Raises `Refused` before anything is written. Returns the report: finished, or unfinished with
    the reason, the new folder then marked unfinished and the old one untouched. A rerun into a
    folder whose bring-in finished returns that report and copies nothing. `lock` is the per-user
    file that keeps two first starts from running at once.
    """
    with _held(lock, "another first start is running on this PC; wait for it to end"):
        return _bring_in(old, folder, place_refusal, copy)


def _bring_in(
    old: Path, folder: Path, place_refusal: Callable[[Path], str | None], copy: Copier
) -> Report:
    old, folder = old.absolute(), folder.absolute()
    real_old = old.resolve()
    done = _finished(folder)
    if done is not None:
        return done
    refusal = old_refusal(real_old) or _running(real_old) or place_refusal(folder)
    real_folder = folder.resolve()
    if refusal is None and (
        real_folder.is_relative_to(real_old) or real_old.is_relative_to(real_folder)
    ):
        refusal = f"{folder} and {old} overlap; the new QMX folder must be outside the old one"
    if refusal is not None:
        raise Refused(refusal)
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
        layout = resolve(folder, create=True)
    except NoQmxFolder as refused:
        raise Refused(str(refused)) from None
    started = time.monotonic()
    with _held(layout.data / HOST_LOCK, f"a QMX host is running on {layout.root}; stop it first"):
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
        try:
            why = _carry(real_old, layout, facts, copy, unfinished)
        except (OSError, sqlite3.Error, LibraryRefused, ValueError, KeyError) as failed:
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


def _carry(
    old: Path, layout: Layout, facts: dict[str, object], copy: Copier, unfinished: Path
) -> str | None:
    """Steps 2 to 4. Returns why the bring-in stopped, or None when every check held."""
    before = listing(old)
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
        (layout.root / str(place_in_tree(folder))).mkdir(parents=True, exist_ok=True)
    for entry in before.files:
        target = place_in_tree(entry.path)
        if target is None:
            left_out.append({"path": entry.path, "why": LEFT_OUT[entry.path]})
            continue
        written = layout.root / target
        written.parent.mkdir(parents=True, exist_ok=True)
        if copy(old / entry.path, written) != entry.sha256:
            return f"{entry.path} in your old folder changed while it was copied"
        part = copied.setdefault(target.split("/", 1)[0], [0, 0])
        part[0] += 1
        part[1] += entry.size
        placed.append((entry, written))
    _write(unfinished, "it stopped while checking the copy")
    after = listing(old)
    if after != before:
        return f"your old folder changed while it was copied ({_first_change(before, after)})"
    for entry, written in placed:
        if sha256_of(written) != entry.sha256:
            return f"the copy of {entry.path} does not match your old folder"
    _write(unfinished, "it stopped while moving your old Library into the new one")
    facts["library"] = None
    if (layout.data / OLD_LIBRARY).is_file():
        why = _switch(layout, facts)
        if why is not None:
            return why
    facts["stores"] = [verdict.line for verdict in check_open(layout).verdicts]
    return None


def _switch(layout: Layout, facts: dict[str, object]) -> str | None:
    """The built switch on the copy only, with each copied Library file's own log folded in
    first, so the read-only file it retires holds every row."""
    for name in ("library.db", "artifacts.db"):
        copied = layout.data / name
        if copied.is_file():
            with closing(sqlite3.connect(copied)) as db:
                db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    switched = switch_over(layout.data, redactor=redact)
    facts["library"] = {
        "report": switched.report(),
        "kinds": _kinds_brought_in(layout.data / "migration" / "pre" / OLD_LIBRARY),
    }
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


def _kinds_brought_in(frozen: Path) -> dict[str, int]:
    """Items per old kind in the switch's frozen copy, the test junk left out: what the switch
    imported and then checked against the store."""
    kinds: dict[str, int] = {}
    with closing(sqlite3.connect(f"{frozen.resolve().as_uri()}?mode=ro", uri=True)) as db:
        for (raw,) in db.execute("SELECT data FROM items"):
            row = cast("dict[str, object]", json.loads(raw))
            if str(row["id"]) not in JUNK:
                kinds[str(row["kind"])] = kinds.get(str(row["kind"]), 0) + 1
    return dict(sorted(kinds.items()))


def _survey(old: Path) -> tuple[tuple[str, int, int], ...]:
    """Each file's path, size and Windows attributes (0 elsewhere), from the file system's records
    alone, before any file is read."""
    found: list[tuple[str, int, int]] = []
    for relative, entry in _walk(old):
        if entry.is_file(follow_symlinks=False) and not _is_link(entry):
            record = entry.stat(follow_symlinks=False)
            found.append((relative, record.st_size, getattr(record, "st_file_attributes", 0)))
    return tuple(found)


def listing(old: Path) -> Listing:
    """Every entry of `old`, each file hashed, in one fixed order so two listings compare."""
    files: list[Listed] = []
    folders: list[str] = []
    links: list[tuple[str, str]] = []
    others: list[str] = []
    for relative, entry in _walk(old):
        if _is_link(entry):
            links.append((relative, os.readlink(entry.path).removeprefix("\\\\?\\")))
        elif entry.is_dir(follow_symlinks=False):
            folders.append(relative)
        elif entry.is_file(follow_symlinks=False):
            path = Path(entry.path)
            files.append(Listed(relative, path.stat().st_size, sha256_of(path)))
        else:
            others.append(relative)
    return Listing(tuple(files), tuple(folders), tuple(links), tuple(others))


def _walk(old: Path) -> Iterator[tuple[str, os.DirEntry[str]]]:
    """Each entry below `old`: a folder's entries sorted by name, then its folders' entries in
    turn, never through a link."""
    pending: list[tuple[str, Path]] = [("", old)]
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


def _room(folder: Path, survey: tuple[tuple[str, int, int], ...]) -> None:
    """Refuse a copy that would leave the target's drive below the floor a pre-change copy keeps,
    counting the switch's own second copy of the old Library."""
    library = sum(size for path, size, _ in survey if _switched(path))
    needed = sum(size for _, size, _ in survey) + 2 * library
    existing = next(p for p in (folder, *folder.parents) if p.exists())
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


@contextmanager
def _held(path: Path | None, busy: str) -> Generator[None]:
    """Hold an OS lock on `path` for the block; refused with `busy` while another process holds
    it. The OS lets go when the process ends, so a stopped first start never leaves it held."""
    if path is None:
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        try:
            _lock(handle)
        except OSError:
            raise Refused(busy) from None
        yield
    finally:
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
        where = f" ({error.filename})" if error.filename else ""
        return f"{error.strerror}{where}"
    return str(error) or type(error).__name__


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
            f"{folder} is marked unfinished, and QMX will not start on it. Remove it and run "
            "the first start again.",
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
        retired = cast("list[str]", switched.get("retired", []))
        if retired:
            lines.append(
                f"  The old Library files ({', '.join(retired)}) now sit read-only in "
                f"{Path(folder) / 'data' / 'migration' / 'retired'}."
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
