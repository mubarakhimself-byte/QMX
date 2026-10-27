"""A backup place on disk: a pool holding each file once by sha256, and one manifest per copy.

```
<place>/
  backup.toml                  which QMX folder sends here, and its last copy
  pool/ab/cd/<sha256>          each file once
  pool/<name>.qmx-copying      a file still being written
  snapshots/<stamp>/
    manifest.jsonl             written last; one line per file, a header first and a trailer last
    keys.sealed.json           the sealed key copy, on a target only (B7)
```

The quick undo in `backups/quick/` and a folder target at `<target>/QMX-backup/<home_id>/` use
this one layout. A manifest is whole only with its trailer, `{"end": true, "lines": n, "sha256":
...}`, which names the lines before it and their hash; one without it is unreadable, is never
thinned and stops the pool sweep. A copy folder with no manifest at all is what a killed round
leaves, and `clean` removes it. Nothing here needs a hard link, so an exFAT USB disk works.

Pool files are not flushed to the disk one by one, as a plain file copy does not flush them;
the manifest, `backup.toml` and the sealed key copy are. A power cut mid round can leave a
pooled file that is named but not whole; the monthly drill (B2) hashes pooled files, removes a
damaged one, and the next round that holds it pools it again.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final, Literal, Protocol, cast

from qmx_home.files import PARTIAL, copy_file, long_path, plain

FORMAT: Final = "qmx-backup/1"
MANIFEST: Final = "manifest.jsonl"
ABOUT: Final = "backup.toml"
STAMP: Final = re.compile(r"\d{8}T\d{12}Z")
"""A copy's folder name; nothing else in `snapshots/` is QMX's, so nothing else is listed or
removed."""

type Kind = Literal["store", "log", "file", "once"]
"""A SQLite store copied by `VACUUM INTO`, a log copied up to its last full line, any other file
copied whole, and a file written once and never rewritten in place."""
type At = Literal["pool", "live"]
"""Where the bytes are: in the place's pool, or (quick undo only) still in `data/` itself."""


class Unreadable(Exception):
    """A manifest that is not whole. The message names the copy."""


class Mismatch(Exception):
    """A file's bytes did not hash to what its manifest line says. The message names it."""


@dataclass(frozen=True, slots=True)
class Entry:
    """One file of a copy. `path` is relative to `data/`, with `/` between names. `seen` is the
    live file's size and `mtime_ns` when it was read (and its `-wal`'s for a store), so the next
    round need not read an unchanged file again."""

    path: str
    sha256: str
    size: int
    kind: Kind
    seen: tuple[int, ...]
    at: At = "pool"
    tables: Mapping[str, int] = field(default_factory=dict[str, int])
    """A store's row count per table, as copied."""
    version: int | None = None
    """A store's own `user_version`, read from the copy."""
    min_reader: int | None = None
    """A store's own `min_reader` row, read from the copy."""

    def document(self) -> dict[str, object]:
        line: dict[str, object] = {
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
            "kind": self.kind,
            "seen": list(self.seen),
            "at": self.at,
        }
        if self.kind == "store":
            line |= {"tables": dict(self.tables), "version": self.version}
            line["min_reader"] = self.min_reader
        return line

    @classmethod
    def parse(cls, line: Mapping[str, object]) -> Entry:
        tables = cast("dict[str, int]", line.get("tables") or {})
        version, floor = line.get("version"), line.get("min_reader")
        return cls(
            str(line["path"]),
            str(line["sha256"]),
            int(cast("int", line["size"])),
            cast("Kind", line["kind"]),
            tuple(int(n) for n in cast("list[int]", line["seen"])),
            cast("At", line.get("at", "pool")),
            {str(k): int(v) for k, v in tables.items()},
            version if isinstance(version, int) else None,
            floor if isinstance(floor, int) else None,
        )


@dataclass(frozen=True, slots=True)
class Manifest:
    """One copy: its header (what folder, when, why, which release and label) and its files in
    the order they were copied."""

    header: Mapping[str, object]
    entries: tuple[Entry, ...]

    @property
    def stamp(self) -> str:
        return str(self.header["stamp"])

    @property
    def files(self) -> frozenset[tuple[str, str]]:
        """Each file's path and hash: two copies with the same files hold the same data."""
        return frozenset((entry.path, entry.sha256) for entry in self.entries)

    def pooled(self, **header: object) -> Manifest:
        """This copy as a target holds it: every file in the pool, `header` added."""
        entries = tuple(replace(entry, at="pool") for entry in self.entries)
        return Manifest({**self.header, **header}, entries)

    def dump(self) -> bytes:
        body = b"".join(
            json.dumps(line, sort_keys=True).encode() + b"\n"
            for line in (dict(self.header), *(entry.document() for entry in self.entries))
        )
        trailer = {
            "end": True,
            "lines": 1 + len(self.entries),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        return body + json.dumps(trailer, sort_keys=True).encode() + b"\n"

    @classmethod
    def parse(cls, data: bytes, where: str) -> Manifest:
        """The copy `data` holds. Raises Unreadable unless its trailer names exactly the lines
        before it and their hash."""
        body, _, last = data.rstrip(b"\n").rpartition(b"\n")
        try:
            trailer: object = json.loads(last)
            lines = [json.loads(line) for line in body.split(b"\n")] if body else []
        except ValueError:
            raise Unreadable(
                f"the copy {where} is damaged: its list of files is not whole"
            ) from None
        whole = (
            isinstance(trailer, dict)
            and cast("dict[str, object]", trailer).get("end") is True
            and cast("dict[str, object]", trailer).get("lines") == len(lines)
            and cast("dict[str, object]", trailer).get("sha256")
            == hashlib.sha256(body + b"\n").hexdigest()
        )
        if not whole or not lines or not isinstance(lines[0], dict):
            raise Unreadable(f"the copy {where} is damaged: its list of files is not whole")
        header = cast("dict[str, object]", lines[0])
        try:
            entries = tuple(Entry.parse(cast("dict[str, object]", line)) for line in lines[1:])
        except KeyError, TypeError, ValueError:
            raise Unreadable(
                f"the copy {where} is damaged: its list of files is not whole"
            ) from None
        return cls(header, entries)


@dataclass(frozen=True, slots=True)
class Swept:
    removed: int
    blocked: str | None
    """Why the sweep did not run: a copy whose manifest is not whole, named."""


class Repository(Protocol):
    """A place that holds copies. Every method names its place in what it raises."""

    @property
    def where(self) -> str:
        """The place as he reads it."""
        ...

    def pool_has(self, sha256: str) -> bool: ...

    def put_pool(self, sha256: str, source: Path, *, verify: bool = True) -> int:
        """Copy `source` into the pool under `sha256` unless it is there; the bytes written.
        Raises Mismatch when the bytes copied hash to something else. `verify` False copies a
        file another pool holds under that hash without hashing it again."""
        ...

    def put_copy(self, manifest: Manifest, extra: Mapping[str, bytes] | None = None) -> None:
        """Write one copy: its extra files, then its manifest, last."""
        ...

    def copies(self) -> tuple[str, ...]:
        """Every copy that has a manifest file, whole or not, oldest first."""
        ...

    def manifest(self, stamp: str) -> Manifest:
        """Raises Unreadable."""
        ...

    def read_extra(self, stamp: str, name: str) -> bytes | None: ...

    def fetch(self, sha256: str, target: Path) -> str:
        """Copy one pooled file to the new file `target`; the sha256 of what was written."""
        ...

    def drop(self, stamp: str) -> None: ...

    def sweep(self) -> Swept:
        """Remove pool files no copy names, only when every copy's manifest is whole."""
        ...

    def room(self) -> int:
        """Free bytes where the place is, or would be."""
        ...

    def clean(self) -> int:
        """Remove what a killed round left: names ending `.qmx-copying` and copy folders with no
        manifest. The count removed."""
        ...

    def about(self) -> Mapping[str, object] | None:
        """`backup.toml`'s fields, or None when it is not there."""
        ...

    def set_about(self, fields: Mapping[str, str]) -> None: ...


def free_bytes(path: Path) -> int:
    """The free room on the drive that holds `path`, or would hold it."""
    existing = next((p for p in (path, *path.parents) if long_path(p).exists()), path)
    return shutil.disk_usage(long_path(existing)).free


class FolderRepository:
    """A place in a folder: the quick undo, or a folder target on another drive."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.pool = root / "pool"
        self.snapshots = root / "snapshots"
        self._made: set[Path] = set()

    @property
    def where(self) -> str:
        return plain(self.root)

    def pool_path(self, sha256: str) -> Path:
        return self.pool / sha256[:2] / sha256[2:4] / sha256

    def pool_has(self, sha256: str) -> bool:
        return long_path(self.pool_path(sha256)).is_file()

    def temporary(self) -> Path:
        """A fresh name in the pool for a file being written; `clean` removes it if left."""
        self._folder(self.pool)
        return self.pool / f"{uuid.uuid4().hex}{PARTIAL}"

    def _folder(self, folder: Path) -> None:
        if folder not in self._made:
            long_path(folder).mkdir(parents=True, exist_ok=True)
            self._made.add(folder)

    def adopt(self, written: Path, sha256: str) -> None:
        """Move a file this place's `temporary` name holds into the pool as `sha256`; when the
        pool has it already, the new one is removed."""
        final = long_path(self.pool_path(sha256))
        if final.is_file():
            long_path(written).unlink()
            return
        self._folder(self.pool_path(sha256).parent)
        os.replace(long_path(written), final)

    def put_pool(self, sha256: str, source: Path, *, verify: bool = True) -> int:
        if self.pool_has(sha256):
            return 0
        writing = self.temporary()
        try:
            if verify:
                got = copy_file(source, writing, durable=False)
            else:
                shutil.copyfile(long_path(source), long_path(writing))
                got = sha256
        except BaseException:
            long_path(writing).unlink(missing_ok=True)
            raise
        if got != sha256:
            long_path(writing).unlink(missing_ok=True)
            raise Mismatch(
                f"{plain(source)} does not hold the bytes its copy names: it changed while it was "
                "copied, or it is damaged"
            )
        size = long_path(writing).stat().st_size
        self.adopt(writing, sha256)
        return size

    def put_bytes(self, data: bytes) -> str:
        """`data` in the pool; its sha256."""
        digest = hashlib.sha256(data).hexdigest()
        if not self.pool_has(digest):
            writing = self.temporary()
            _write(writing, data, durable=False)
            self.adopt(writing, digest)
        return digest

    def put_copy(self, manifest: Manifest, extra: Mapping[str, bytes] | None = None) -> None:
        folder = self.snapshots / manifest.stamp
        long_path(folder).mkdir(parents=True, exist_ok=True)
        for name, data in (extra or {}).items():
            _write(folder / name, data)
        staged = folder / f"{MANIFEST}.new"
        _write(staged, manifest.dump())
        os.replace(long_path(staged), long_path(folder / MANIFEST))

    def copies(self) -> tuple[str, ...]:
        if not long_path(self.snapshots).is_dir():
            return ()
        return tuple(
            sorted(
                entry.name
                for entry in os.scandir(long_path(self.snapshots))
                if entry.is_dir(follow_symlinks=False)
                and STAMP.fullmatch(entry.name)
                and long_path(self.snapshots / entry.name / MANIFEST).is_file()
            )
        )

    def manifest(self, stamp: str) -> Manifest:
        where = plain(self.snapshots / stamp)
        try:
            data = long_path(self.snapshots / stamp / MANIFEST).read_bytes()
        except OSError as failed:
            raise Unreadable(f"the copy {where} cannot be read ({failed.strerror})") from None
        return Manifest.parse(data, where)

    def read_extra(self, stamp: str, name: str) -> bytes | None:
        try:
            return long_path(self.snapshots / stamp / name).read_bytes()
        except FileNotFoundError:
            return None

    def fetch(self, sha256: str, target: Path) -> str:
        return copy_file(self.pool_path(sha256), target)

    def drop(self, stamp: str) -> None:
        shutil.rmtree(long_path(self.snapshots / stamp))

    def sweep(self) -> Swept:
        named: set[str] = set()
        for stamp in self.copies():
            try:
                manifest = self.manifest(stamp)
            except Unreadable as torn:
                return Swept(0, f"{torn}; QMX removes no file from {self.where} until it is")
            named.update(entry.sha256 for entry in manifest.entries if entry.at == "pool")
        removed = 0
        for path in self._pooled():
            if path.name not in named:
                path.unlink()
                removed += 1
        return Swept(removed, None)

    def room(self) -> int:
        return free_bytes(self.root)

    def clean(self) -> int:
        removed = 0
        if long_path(self.pool).is_dir():
            for entry in os.scandir(long_path(self.pool)):
                if entry.name.endswith(PARTIAL) and entry.is_file(follow_symlinks=False):
                    os.unlink(entry.path)
                    removed += 1
        if long_path(self.snapshots).is_dir():
            for entry in os.scandir(long_path(self.snapshots)):
                if (
                    entry.is_dir(follow_symlinks=False)
                    and STAMP.fullmatch(entry.name)
                    and not os.path.isfile(os.path.join(entry.path, MANIFEST))
                ):
                    shutil.rmtree(entry.path)
                    removed += 1
        return removed

    def about(self) -> Mapping[str, object] | None:
        import tomllib  # noqa: PLC0415

        try:
            return tomllib.loads(long_path(self.root / ABOUT).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except OSError, ValueError:
            return {}

    def set_about(self, fields: Mapping[str, str]) -> None:
        text = "".join(f"{key} = {json.dumps(value)}\n" for key, value in fields.items())
        long_path(self.root).mkdir(parents=True, exist_ok=True)
        staged = self.root / f"{ABOUT}.new"
        _write(staged, text.encode())
        os.replace(long_path(staged), long_path(self.root / ABOUT))

    def _pooled(self) -> Sequence[Path]:
        found: list[Path] = []
        if not long_path(self.pool).is_dir():
            return found
        for first in os.scandir(long_path(self.pool)):
            if not first.is_dir(follow_symlinks=False):
                continue
            for second in os.scandir(first.path):
                if second.is_dir(follow_symlinks=False):
                    found += [
                        Path(entry.path)
                        for entry in os.scandir(second.path)
                        if entry.is_file(follow_symlinks=False) and not entry.name.endswith(PARTIAL)
                    ]
        return found


def _write(path: Path, data: bytes, *, durable: bool = True) -> None:
    with long_path(path).open("wb") as writing:
        writing.write(data)
        writing.flush()
        if durable:
            os.fsync(writing.fileno())
