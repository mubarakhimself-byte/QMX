"""A storage that keeps copies: packs of files, an index per confirmed batch, and one manifest
per copy (design 06 section 3).

```
<storage>/QMX-backup/<home_id>/
  backup.toml                      which QMX folder sends here, and its last copy (rewritten)
  packs/<ab>/<pack sha256>.pack    many files, one zstd frame each, then the pack's own list
  index/<stamp>-<n>.json           written once per confirmed pack: sha256 -> pack, offset, length
  index/merged-<stamp>.json        written once by a prune: every pack a kept copy uses
  bad/<stamp>-<n>.json             written once by a check or a drill: files found damaged
  pool/ab/cd/<sha256>              loose files: This PC's links to files written once, and copies
                                   made before packs (`qmx-backup/1`), still read
  snapshots/<stamp>/manifest.jsonl written last; a header, one line per file, a trailer
```

A manifest, an index file and a bad list are whole only with their trailer, `{"end": true,
"lines": n, "sha256": ...}`. A copy exists only when its manifest is whole on the storage, and
the write order is packs, then their index, then the manifest. Every file but `backup.toml` is
written once under a name it keeps. QMX deletes a pack only through `prune`: it first writes a
merged index naming every pack it keeps, then removes the index files it replaced, then the packs
no kept copy needs, and only a pack no index has named for the safety window. So every index on
a storage names only packs that exist, and a writer on another machine that is still sending has
the window to see that a pack it meant to reuse is going.

A file's name in a copy stays the sha256 of its bytes. Each file is one zstd frame with its
checksum, or its bytes as they are for formats already compressed (Parquet, PDF, images). A pack
closes at about `PACK_BYTES`, and a larger file has a pack of its own. Nothing here needs a hard
link but This PC's links, which fall back to the file's place in `data/` where a drive refuses
one, so an exFAT USB disk works.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from compression import zstd
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final, Literal, Protocol, cast

from qmx_home import files
from qmx_home.files import (
    PARTIAL,
    copy_file,
    long_path,
    open_shared,
    plain,
    settle,
    sha256_of,
    write_new,
)

if TYPE_CHECKING:
    from qmx_home.rclone import Failure, Rclone

FORMAT: Final = "qmx-backup/2"
READS: Final = frozenset({"qmx-backup/1", FORMAT})
"""The copy formats this QMX restores: loose pools and packs."""
MANIFEST: Final = "manifest.jsonl"
ABOUT: Final = "backup.toml"
STAMP: Final = re.compile(r"\d{8}T\d{12}Z")
"""A copy's folder name; nothing else in `snapshots/` is QMX's, so nothing else is listed or
removed."""
STAMP_FORMAT: Final = "%Y%m%dT%H%M%S%fZ"
SHA256: Final = re.compile(r"[0-9a-f]{64}")
"""A pooled file's name. A manifest naming anything else is unreadable, so no hash a plugged-in
disk carries can name a file outside its pool."""
PACK_BYTES: Final = 16 << 20
"""About where a pack closes. Internal, never a setting."""
STORED_RAW: Final = re.compile(r"\.(parquet|pdf|png|jpe?g|gif|webp|zip|gz|zst|xz|7z)$", re.I)
"""Files already compressed, kept in a pack as they are."""
PACK_TAIL: Final = b"QMXPACK2"
INDEX_NAME: Final = re.compile(r"(merged-)?(\d{8}T\d{12}Z)(-[0-9a-f]+)?\.json")
BAD_NAME: Final = re.compile(r"(\d{8}T\d{12}Z)-[0-9a-f]+\.json")
MERGE_PAST: Final = 16
"""Batch index files on a storage past which a prune writes one merged index in their place, so
reading the index stays a few files. Internal, never a setting."""
CHUNK: Final = 1 << 20

type Kind = Literal["store", "log", "file", "once"]
"""A SQLite store copied by `VACUUM INTO`, a log copied up to its last full line, any other file
copied whole, and a file written once and never rewritten in place."""
type At = Literal["pool", "live"]
"""Where the bytes are: in the storage, or (This PC only, where a drive refuses a link) still in
`data/` itself."""


class Unreadable(Exception):
    """A manifest that is not whole. The message names the copy."""


class Mismatch(Exception):
    """A file's bytes did not hash to what its manifest line says. The message names it."""


class StorageRefused(Exception):
    """A storage that did not answer as it should: `failure` sorts why, and the message is the one
    line to show, naming the storage."""

    def __init__(self, line: str, failure: Failure = "other") -> None:
        super().__init__(line)
        self.failure: Failure = failure


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
        if not isinstance(line["sha256"], str) or not SHA256.fullmatch(line["sha256"]):
            raise ValueError("not a sha256")
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


def dump_lines(lines: Iterable[Mapping[str, object]]) -> bytes:
    """JSON lines and the trailer that makes them whole."""
    body = b"".join(json.dumps(dict(line), sort_keys=True).encode() + b"\n" for line in lines)
    trailer = {
        "end": True,
        "lines": body.count(b"\n"),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    return body + json.dumps(trailer, sort_keys=True).encode() + b"\n"


def parse_lines(data: bytes) -> list[dict[str, object]] | None:
    """The lines `data` holds, or None unless its trailer names exactly the lines before it and
    their hash."""
    body, _, last = data.rstrip(b"\n").rpartition(b"\n")
    try:
        trailer: object = json.loads(last)
        lines = [json.loads(line) for line in body.split(b"\n")] if body else []
    except ValueError:
        return None
    if not (
        isinstance(trailer, dict)
        and cast("dict[str, object]", trailer).get("end") is True
        and cast("dict[str, object]", trailer).get("lines") == len(lines)
        and cast("dict[str, object]", trailer).get("sha256")
        == hashlib.sha256(body + b"\n").hexdigest()
        and all(isinstance(line, dict) for line in lines)
    ):
        return None
    return cast("list[dict[str, object]]", lines)


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
        """This copy as a storage holds it: every file in the storage, `header` added."""
        entries = tuple(replace(entry, at="pool") for entry in self.entries)
        return Manifest({**self.header, **header}, entries)

    def dump(self) -> bytes:
        return dump_lines((dict(self.header), *(entry.document() for entry in self.entries)))

    @classmethod
    def parse(cls, data: bytes, where: str) -> Manifest:
        """The copy `data` holds. Raises Unreadable unless it is whole."""
        lines = parse_lines(data)
        if not lines:
            raise Unreadable(f"the copy {where} is damaged: its list of files is not whole")
        try:
            entries = tuple(Entry.parse(line) for line in lines[1:])
        except KeyError, TypeError, ValueError:
            raise Unreadable(
                f"the copy {where} is damaged: its list of files is not whole"
            ) from None
        return cls(lines[0], entries)


@dataclass(frozen=True, slots=True)
class Location:
    """Where one file's bytes are in a pack: its frame, whether it is stored as it is, and its
    size as a file."""

    pack: str
    offset: int
    length: int
    raw: bool
    size: int

    def document(self, sha256: str) -> dict[str, object]:
        return {
            "sha256": sha256,
            "pack": self.pack,
            "offset": self.offset,
            "length": self.length,
            "raw": self.raw,
            "size": self.size,
        }


@dataclass(slots=True)
class Index:
    """Every whole index file of a storage, read as one: where each file is, when each pack was
    first named, the packs a prune is letting go and since when, and the files found damaged."""

    where: dict[str, list[Location]] = field(default_factory=dict[str, list[Location]])
    named: dict[str, str] = field(default_factory=dict[str, str])
    """Each pack and the stamp of the earliest index file naming it."""
    dropping: dict[str, str] = field(default_factory=dict[str, str])
    files: list[str] = field(default_factory=list[str])
    """The index files read, whole or torn."""
    torn: list[str] = field(default_factory=list[str])
    bad: set[tuple[str, str]] = field(default_factory=set[tuple[str, str]])
    """Each damaged file and the pack it was found damaged in."""
    present: set[str] | None = None
    """The packs the storage holds, as listed when the index was read; None reads every pack
    as there."""

    def add(self, sha256: str, found: Location, stamp: str) -> None:
        held = self.where.setdefault(sha256, [])
        if found not in held:
            held.append(found)
        if found.pack not in self.named or stamp < self.named[found.pack]:
            self.named[found.pack] = stamp

    def good(self, sha256: str) -> list[Location]:
        """The places a file's bytes are, those found damaged left out, newest pack first."""
        found = [
            at
            for at in self.where.get(sha256, ())
            if (sha256, at.pack) not in self.bad
            and (self.present is None or at.pack in self.present)
        ]
        return sorted(found, key=lambda at: self.named.get(at.pack, ""), reverse=True)


@dataclass(frozen=True, slots=True)
class Swept:
    removed: int
    blocked: str | None
    """Why the sweep did not run: a copy whose manifest is not whole, named."""
    torn: tuple[str, ...] = ()
    """Index files found torn and written again."""


@dataclass(frozen=True, slots=True)
class Cleaned:
    removed: int
    torn: tuple[str, ...] = ()
    """The torn manifests removed: each older than the newest whole copy, so never a copy."""


@dataclass(frozen=True, slots=True)
class Pruned:
    """What one prune did."""

    deleted: int = 0
    """Packs removed."""
    written: int = 0
    """Packs written by a rewrite."""
    freed: int = 0
    """Bytes of the packs removed."""
    unused: float = 0.0
    """The share of pack bytes no kept copy needs, after the prune."""
    blocked: str | None = None
    torn: tuple[str, ...] = ()
    """Index files found torn and replaced."""
    rebuilt: int = 0
    """Packs no whole index named, read again from their own lists."""


class Repository(Protocol):
    """A storage that holds copies. Every method names its storage in what it raises."""

    @property
    def where(self) -> str:
        """The storage as he reads it."""
        ...

    @property
    def key(self) -> str:
        """The storage's key in the backup log, stable for a place."""
        ...

    def pool_has(self, sha256: str) -> bool: ...

    def put_pool(self, sha256: str, source: Path, *, path: str = "") -> int:
        """Copy `source` into the storage under `sha256` unless it is there; the bytes written.
        `path` is the file's path in `data/`, which says whether it is stored as it is. Raises
        Mismatch, with nothing kept, when the bytes copied hash to something else."""
        ...

    def seal(self) -> None:
        """Close the pack being written and name it in an index file."""
        ...

    def refresh(self) -> None:
        """Read the storage's index again, as another machine may have changed it."""
        ...

    def put_copy(self, manifest: Manifest, extra: Mapping[str, bytes] | None = None) -> None:
        """Write one copy: the pack being written, its extra files, then its manifest, last."""
        ...

    def copies(self) -> tuple[str, ...]:
        """Every copy that has a manifest file, whole or not, oldest first."""
        ...

    def manifest(self, stamp: str) -> Manifest:
        """Raises Unreadable."""
        ...

    def read_extra(self, stamp: str, name: str) -> bytes | None: ...

    def fetch(self, sha256: str, target: Path) -> str:
        """Copy one file to the new file `target`; the sha256 of what was written. Raises
        FileNotFoundError when the storage holds no such file."""
        ...

    def drop(self, stamp: str) -> None:
        """Remove one copy's manifest. Its packs and index stay for the prune."""
        ...

    def mark_bad(self, sha256: str, *, pack: str | None = None) -> None:
        """Name a file whose bytes are damaged (in `pack`, or where `fetch` reads it) on a bad
        list, so the next round that holds the file sends it again and the next prune drops the
        pack once no kept copy needs it."""
        ...

    def sweep(self, *, safety: timedelta, now: datetime) -> Swept:
        """Let go of what no copy names, only when every copy's manifest is whole."""
        ...

    def room(self) -> int | None:
        """Free bytes where the storage is, or None when its kind does not say."""
        ...

    def total(self) -> int | None:
        """The storage's whole size, or None when its kind does not say."""
        ...

    def clean(self) -> Cleaned:
        """Remove what a killed round left: names ending `.qmx-copying`, copy folders with no
        manifest, and torn manifests older than the newest whole copy."""
        ...

    def about(self) -> Mapping[str, object] | None:
        """`backup.toml`'s fields, or None when it is not there."""
        ...

    def set_about(self, fields: Mapping[str, str]) -> None: ...


def free_bytes(path: Path) -> int:
    """The free room on the drive that holds `path`, or would hold it."""
    existing = next((p for p in (path, *path.parents) if long_path(p).exists()), path)
    return shutil.disk_usage(long_path(existing)).free


def stamp_of(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime(STAMP_FORMAT)


def moment_of(stamp: str) -> datetime:
    return datetime.strptime(stamp, STAMP_FORMAT).replace(tzinfo=UTC)


def stored_raw(path: str) -> bool:
    return STORED_RAW.search(path) is not None


class _Builder:
    """One pack being written in a local file: frames, then its own list, its length and a
    tail, so a pack names what it holds even when every index naming it is lost."""

    def __init__(self, folder: Path, made: str) -> None:
        long_path(folder).mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{uuid.uuid4().hex}.pack{PARTIAL}"
        self.file = files.create_new(self.path, through=False)
        self.made = made
        self.files: dict[str, Location] = {}
        self.size = 0

    def add(self, sha256: str, source: Path, raw: bool) -> int:
        """Append `source` as one frame; its stored length. Raises Mismatch, with the pack as it
        was, when its bytes do not hash to `sha256`."""
        start = self.size
        digest = hashlib.sha256()
        size = 0
        packer = (
            None
            if raw
            else zstd.ZstdCompressor(options={zstd.CompressionParameter.checksum_flag: 1})
        )
        try:
            with open_shared(source) as reading:
                while chunk := reading.read(CHUNK):
                    digest.update(chunk)
                    size += len(chunk)
                    self._write(chunk if packer is None else packer.compress(chunk))
            if packer is not None:
                self._write(packer.flush())
        except BaseException:
            self._back(start)
            raise
        if digest.hexdigest() != sha256:
            self._back(start)
            raise Mismatch(
                f"{plain(source)} does not hold the bytes its copy names: it changed while it was "
                "copied, or it is damaged"
            )
        self.files[sha256] = Location("", start, self.size - start, raw, size)
        return self.size - start

    def add_frame(self, sha256: str, frame: bytes, found: Location) -> None:
        start = self.size
        self._write(frame)
        self.files[sha256] = Location("", start, len(frame), found.raw, found.size)

    def close(self) -> tuple[str, Path, dict[str, Location]] | None:
        """The pack's name, its file and what it holds; None for a pack that holds nothing."""
        if not self.files:
            self.file.close()
            long_path(self.path).unlink(missing_ok=True)
            return None
        listing = json.dumps(
            {
                "made": self.made,
                "files": [
                    [sha, at.offset, at.length, at.raw, at.size] for sha, at in self.files.items()
                ],
            },
            sort_keys=True,
        ).encode()
        self._write(listing + struct.pack("<Q", len(listing)) + PACK_TAIL)
        settle(self.file, through=False)
        self.file.close()
        name = sha256_of(self.path)
        return name, self.path, {sha: replace(at, pack=name) for sha, at in self.files.items()}

    def abandon(self) -> None:
        self.file.close()
        long_path(self.path).unlink(missing_ok=True)

    def _write(self, data: bytes) -> None:
        self.file.write(data)
        self.size += len(data)

    def _back(self, start: int) -> None:
        self.file.seek(start)
        self.file.truncate()
        self.size = start


def pack_list(path: Path) -> tuple[str, dict[str, Location]] | None:
    """A pack's own stamp and list, read from its tail; None when the pack is not whole."""
    try:
        with open_shared(path) as reading:
            end = reading.seek(0, os.SEEK_END)
            if end < 16:
                return None
            reading.seek(end - 16)
            tail = reading.read(16)
            if tail[8:] != PACK_TAIL:
                return None
            (length,) = struct.unpack("<Q", tail[:8])
            if length > end - 16:
                return None
            reading.seek(end - 16 - length)
            found = json.loads(reading.read(length))
    except OSError, ValueError, struct.error:
        return None
    name = path.name.removesuffix(".pack")
    try:
        fields = cast("dict[str, object]", found)
        files = {
            str(row[0]): Location(name, int(row[1]), int(row[2]), bool(row[3]), int(row[4]))
            for row in cast("list[list[int]]", fields["files"])
        }
        return str(fields["made"]), files
    except KeyError, IndexError, TypeError, ValueError:
        return None


def read_frame(path: Path, found: Location) -> bytes:
    """The stored bytes of one frame, as they are in the pack."""
    with open_shared(path) as reading:
        reading.seek(found.offset)
        return reading.read(found.length)


def unpack(path: Path, found: Location, target: Path) -> str:
    """One frame of the pack at `path` written to the new file `target`; the sha256 of what was
    written, which is empty when the frame does not decompress (its checksum failed)."""
    digest = hashlib.sha256()
    with (
        open_shared(path) as reading,
        files.create_new(target, through=found.size < (8 << 20)) as out,
    ):
        reading.seek(found.offset)
        left = found.length
        opener = None if found.raw else zstd.ZstdDecompressor()
        try:
            while left > 0:
                chunk = reading.read(min(CHUNK, left))
                if not chunk:
                    return ""
                left -= len(chunk)
                if opener is None:
                    digest.update(chunk)
                    out.write(chunk)
                    continue
                piece = opener.decompress(chunk, max_length=CHUNK)
                digest.update(piece)
                out.write(piece)
                while not opener.needs_input and not opener.eof:
                    piece = opener.decompress(b"", max_length=CHUNK)
                    digest.update(piece)
                    out.write(piece)
            if opener is not None and not opener.eof:
                return ""
        except zstd.ZstdError:
            return ""
        settle(out, through=found.size < (8 << 20))
    return digest.hexdigest()


class Packed:
    """What every storage kind shares: packs, index files, the bad list, the copies and the
    prune, over a handful of file operations each kind provides. Paths are relative to the
    storage's folder for this QMX folder, with `/` between names."""

    def __init__(self, *, key: str, clock: Callable[[], datetime] | None = None) -> None:
        self._key = key
        self._clock = clock or (lambda: datetime.now(UTC))
        self._index: Index | None = None
        self._open: _Builder | None = None

    @property
    def key(self) -> str:
        return self._key

    @property
    def where(self) -> str:
        raise NotImplementedError

    def copy_where(self, stamp: str) -> str:
        """One copy as he reads it."""
        return f"{self.where}/snapshots/{stamp}"

    # What a kind provides.

    def _store(self, rel: str, local: Path) -> None:
        """Place the local file `local` at `rel`, confirmed there; `local` is gone after."""
        raise NotImplementedError

    def _put_bytes(self, rel: str, data: bytes) -> None:
        raise NotImplementedError

    def _read(self, rel: str) -> bytes | None:
        raise NotImplementedError

    def _read_all(self, folder: str) -> dict[str, bytes]:
        """Every file under `folder`, by its path relative to it."""
        raise NotImplementedError

    def _list(self, folder: str) -> dict[str, int]:
        """Every file under `folder` and its size, by its path relative to it."""
        raise NotImplementedError

    def _remove(self, rel: str) -> None:
        raise NotImplementedError

    def local_pack(self, name: str) -> Path:
        """A local file holding the pack `name`. Raises FileNotFoundError when it is gone."""
        raise NotImplementedError

    def _scratch(self) -> Path:
        """A local folder where a pack is written before it is stored."""
        raise NotImplementedError

    def _step(self, _op: str) -> None:
        """Called before each step that writes or deletes on the storage; a test seam."""
        return None

    # Files.

    def pool_has(self, sha256: str) -> bool:
        if self._open is not None and sha256 in self._open.files:
            return True
        return bool(self.index().good(sha256))

    def index(self) -> Index:
        if self._index is None:
            self._index = self._load()
        return self._index

    def refresh(self) -> None:
        self._index = None

    def put_pool(self, sha256: str, source: Path, *, path: str = "") -> int:
        if self.pool_has(sha256):
            return 0
        size = long_path(source).stat().st_size
        if self._open is not None and (
            self._open.size >= PACK_BYTES or (self._open.files and size >= PACK_BYTES)
        ):
            self.seal()
        if self._open is None:
            self._open = _Builder(self._scratch(), stamp_of(self._clock()))
        stored = self._open.add(sha256, source, stored_raw(path))
        if self._open.size >= PACK_BYTES:
            self.seal()
        return stored

    def put_frames(self, frames: Iterable[tuple[str, bytes, Location]]) -> list[str]:
        """Write frames read from other packs into new packs, as a rewrite does; the new packs'
        names."""
        made: list[str] = []
        builder: _Builder | None = None
        for sha, frame, found in frames:
            if builder is not None and builder.size + len(frame) > PACK_BYTES and builder.files:
                made += self._sealed(builder)
                builder = None
            if builder is None:
                builder = _Builder(self._scratch(), stamp_of(self._clock()))
            builder.add_frame(sha, frame, found)
        if builder is not None:
            made += self._sealed(builder)
        return made

    def seal(self) -> None:
        builder, self._open = self._open, None
        if builder is not None:
            self._sealed(builder)

    def let_go(self) -> None:
        """Remove what this storage fetched to this PC; a folder fetches nothing."""
        return None

    def abandon(self) -> None:
        """Drop the pack being written, as a send that stops does."""
        builder, self._open = self._open, None
        if builder is not None:
            builder.abandon()

    def _sealed(self, builder: _Builder) -> list[str]:
        closed = builder.close()
        if closed is None:
            return []
        name, local, files = closed
        self._step("pack")
        self._store(f"packs/{name[:2]}/{name}.pack", local)
        stamp = stamp_of(self._clock())
        self._step("index")
        self._put_bytes(
            f"index/{stamp}-{uuid.uuid4().hex[:8]}.json",
            dump_lines(
                [
                    {"index": "batch", "stamp": stamp},
                    *(at.document(sha) for sha, at in files.items()),
                ]
            ),
        )
        held = self.index()
        for sha, at in files.items():
            held.add(sha, at, stamp)
        if held.present is not None:
            held.present.add(name)
        return [name]

    def fetch(self, sha256: str, target: Path) -> str:
        places = self.index().good(sha256) or self.index().where.get(sha256, [])
        if not places:
            raise FileNotFoundError(f"{self.where} holds no such file")
        found = places[0]
        return unpack(self.local_pack(found.pack), found, target)

    def frame(self, sha256: str, found: Location) -> bytes:
        return read_frame(self.local_pack(found.pack), found)

    def mark_bad(self, sha256: str, *, pack: str | None = None) -> None:
        good = self.index().good(sha256)
        places = [at for at in good if at.pack == pack] if pack else good[:1]
        if not places:
            return
        stamp = stamp_of(self._clock())
        self._step("bad")
        self._put_bytes(
            f"bad/{stamp}-{uuid.uuid4().hex[:8]}.json",
            dump_lines([{"bad": stamp}, *({"sha256": sha256, "pack": at.pack} for at in places)]),
        )
        self.index().bad.update((sha256, at.pack) for at in places)

    def packs(self) -> dict[str, int]:
        """Every pack on the storage and its size."""
        found: dict[str, int] = {}
        for rel, size in self._list("packs").items():
            name = PurePosixPath(rel).name
            if name.endswith(".pack") and SHA256.fullmatch(name.removesuffix(".pack")):
                found[name.removesuffix(".pack")] = size
        return found

    # Copies.

    def put_copy(self, manifest: Manifest, extra: Mapping[str, bytes] | None = None) -> None:
        self.seal()
        for name, data in (extra or {}).items():
            self._put_bytes(f"snapshots/{manifest.stamp}/{name}", data)
        self._step("manifest")
        self._put_bytes(f"snapshots/{manifest.stamp}/{MANIFEST}", manifest.dump())

    def manifests(self) -> tuple[dict[str, Manifest], list[str]]:
        """Every whole copy by stamp, and the stamps of the torn ones."""
        whole: dict[str, Manifest] = {}
        torn: list[str] = []
        for rel, data in sorted(self._read_all("snapshots").items()):
            stamp, _, name = rel.partition("/")
            if name != MANIFEST or not STAMP.fullmatch(stamp):
                continue
            try:
                whole[stamp] = Manifest.parse(data, self.copy_where(stamp))
            except Unreadable:
                torn.append(stamp)
        return whole, torn

    def sweep(self, *, safety: timedelta, now: datetime) -> Swept:
        pruned = self.prune(safety=safety, now=now)
        return Swept(pruned.deleted, pruned.blocked, pruned.torn)

    # The prune.

    def prune(
        self,
        *,
        safety: timedelta,
        now: datetime,
        past: float | None = None,
        per_run: int | None = None,
        step: Callable[[str], None] | None = None,
    ) -> Pruned:
        """Let go of the packs no copy needs, and with `past` rewrite a pack whose unused share
        is above it or that holds a damaged file, up to `per_run` bytes of packs. A pack younger
        than the window (`safety`, or the two newest copies here, whichever is later) is never
        deleted, its age read from the index file that first named it, and neither is a pack
        some index named in the window. `step` hears each of the four steps as it starts."""
        told = step or _quiet
        manifests, torn = self.manifests()
        if torn:
            return Pruned(
                blocked=f"the copy {self.copy_where(torn[-1])} is damaged: its list of files is "
                f"not whole; QMX removes no file from {self.where} until it is"
            )
        self.refresh()
        held = self.index()
        listing = self.packs()
        rebuilt = 0
        for name in sorted(set(listing) - set(held.named) - set(held.dropping)):
            found = pack_list(self.local_pack(name))
            if found is None:
                continue
            made, files = found
            for sha, at in files.items():
                held.add(sha, at, made)
            rebuilt += 1
        used = {
            entry.sha256 for m in manifests.values() for entry in m.entries if entry.at == "pool"
        }
        chosen = {sha: places[0] for sha in used if (places := self._present(held, sha, listing))}
        window = _window(manifests, safety, now)
        named_by: dict[str, list[tuple[str, Location]]] = {}
        for sha, places in held.where.items():
            for at in places:
                if at.pack in listing:
                    named_by.setdefault(at.pack, []).append((sha, at))
        keep: set[str] = set()
        rewrite: list[str] = []
        letting: set[str] = set()
        budget = per_run
        for name, size in sorted(listing.items()):
            needed = [(sha, at) for sha, at in named_by.get(name, []) if chosen.get(sha) == at]
            born = held.named.get(name)
            if born is None and name in held.dropping:
                letting.add(name)
            elif born is None or born > window:
                keep.add(name)
            elif not needed:
                letting.add(name)
            elif (
                past is not None
                and (
                    any((sha, name) in held.bad for sha, _ in named_by.get(name, []))
                    or 1 - sum(at.length for _, at in needed) / max(size, 1) > past
                )
                and (budget is None or budget >= size)
            ):
                rewrite.append(name)
                if budget is not None:
                    budget -= size
            else:
                keep.add(name)
        written: list[str] = []
        if rewrite:
            told("writing the kept files again, closer together")
            frames = [
                (sha, self.frame(sha, at), at)
                for name in rewrite
                for sha, at in named_by.get(name, [])
                if chosen.get(sha) == at
            ]
            written = self.put_frames(frames)
            letting |= set(rewrite)
        moment = stamp_of(now)
        dropping = {name: held.dropping.get(name, moment) for name in letting}
        gone = {name for name, since in dropping.items() if moment_of(since) <= now - safety}
        told("checking the copies again")
        late, _ = self.manifests()
        for stamp, copy in late.items():
            if stamp in manifests:
                continue
            for entry in copy.entries:
                places = self._present(held, entry.sha256, listing)
                if places and all(at.pack in gone for at in places):
                    gone -= {at.pack for at in places}
                    dropping = {
                        k: v for k, v in dropping.items() if k not in {at.pack for at in places}
                    }
                    keep |= {at.pack for at in places}
        new_index = self.index()
        kept = keep | set(written)
        changed = (
            bool(written)
            or set(dropping) != set(held.dropping)
            or bool(held.torn)
            or rebuilt > 0
            or sum(1 for f in held.files if not f.startswith("merged-")) > MERGE_PAST
            or sum(1 for f in held.files if f.startswith("merged-")) > 1
        )
        if changed:
            told("writing one list of where files are kept")
            lines: list[Mapping[str, object]] = [{"index": "merged", "stamp": moment}]
            for sha, places in new_index.where.items():
                lines += [at.document(sha) for at in places if at.pack in kept]
            lines += [
                {"drop": name, "since": since}
                for name, since in sorted(dropping.items())
                if name not in gone
            ]
            merged = f"merged-{moment}.json"
            self._step("merged")
            self._put_bytes(f"index/{merged}", dump_lines(lines))
            for name in held.files:
                if name != merged:
                    self._step("unindex")
                    self._remove(f"index/{name}")
        told("removing what no copy needs")
        freed = 0
        for name in sorted(gone):
            self._step("unpack")
            self._remove(f"packs/{name[:2]}/{name}.pack")
            freed += listing[name]
        self.refresh()
        total = sum(size for name, size in listing.items() if name not in gone)
        total += sum(self.packs().get(name, 0) for name in written)
        needed = sum(at.length for at in chosen.values())
        return Pruned(
            deleted=len(gone),
            written=len(written),
            freed=freed,
            unused=0.0 if total == 0 else max(0.0, 1 - needed / total),
            torn=tuple(held.torn),
            rebuilt=rebuilt,
        )

    def _present(self, held: Index, sha256: str, listing: Mapping[str, int]) -> list[Location]:
        return [at for at in held.good(sha256) if at.pack in listing]

    def _load(self) -> Index:
        held = Index()
        for name, data in sorted(self._read_all("index").items()):
            found = INDEX_NAME.fullmatch(name)
            if found is None:
                continue
            held.files.append(name)
            lines = parse_lines(data)
            if not lines:
                held.torn.append(name)
                continue
            stamp = found.group(2)
            for line in lines[1:]:
                if "drop" in line:
                    held.dropping[str(line["drop"])] = str(line.get("since", stamp))
                    continue
                try:
                    sha = str(line["sha256"])
                    at = Location(
                        str(line["pack"]),
                        int(cast("int", line["offset"])),
                        int(cast("int", line["length"])),
                        line.get("raw") is True,
                        int(cast("int", line["size"])),
                    )
                except KeyError, TypeError, ValueError:
                    continue
                held.add(sha, at, stamp)
        for name, data in self._read_all("bad").items():
            lines = parse_lines(data) if BAD_NAME.fullmatch(name) else None
            for line in (lines or [])[1:]:
                held.bad.add((str(line.get("sha256")), str(line.get("pack"))))
        for name in list(held.dropping):
            if name in held.named:
                del held.dropping[name]
        held.present = set(self.packs())
        return held


def _window(manifests: Mapping[str, Manifest], safety: timedelta, now: datetime) -> str:
    """The stamp a pack must be named before to be let go: the safety window back from `now`,
    or the second newest copy here, whichever is earlier."""
    edge = stamp_of(now - safety)
    stamps = sorted(manifests)
    if len(stamps) < 2:
        return "0"
    return min(edge, stamps[-2])


class FolderRepository(Packed):
    """A storage in a folder: This PC's copies, or a folder on another drive. `links` makes it
    This PC's: a file written once is kept as a hard link in its loose pool, not packed."""

    def __init__(
        self,
        root: Path,
        *,
        key: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(
            key=key or f"folder:{os.path.normcase(os.path.abspath(root))}", clock=clock
        )
        self.root = root
        self.pool = root / "pool"
        self.snapshots = root / "snapshots"
        self._made: set[Path] = set()

    @property
    def where(self) -> str:
        return plain(self.root)

    def copy_where(self, stamp: str) -> str:
        return plain(self.snapshots / stamp)

    def pool_path(self, sha256: str) -> Path:
        """Where the loose pool holds `sha256`. Raises ValueError for anything not a sha256."""
        if not SHA256.fullmatch(sha256):
            raise ValueError(f"{sha256!r} is not a sha256")
        return self.pool / sha256[:2] / sha256[2:4] / sha256

    def loose(self, sha256: str) -> bool:
        return long_path(self.pool_path(sha256)).is_file()

    def pool_has(self, sha256: str) -> bool:
        return self.loose(sha256) or super().pool_has(sha256)

    def link(self, sha256: str, source: Path) -> bool:
        """Keep a file written once as a hard link in the loose pool; False where the drive
        refuses one, so its copy names it where it is in `data/`."""
        if self.loose(sha256):
            return True
        target = self.pool_path(sha256)
        self._folder(target.parent)
        try:
            os.link(long_path(source), long_path(target))
        except FileExistsError:
            return True
        except OSError:
            return False
        return True

    def temporary(self) -> Path:
        """A fresh name in the loose pool for a file being written; `clean` removes it if
        left."""
        self._folder(self.pool)
        return self.pool / f"{uuid.uuid4().hex}{PARTIAL}"

    def adopt(self, written: Path, sha256: str) -> None:
        """Move a file a `temporary` name holds into the loose pool as `sha256`; when the pool
        has it already, the new one is removed."""
        final = long_path(self.pool_path(sha256))
        if final.is_file():
            long_path(written).unlink()
            return
        self._folder(self.pool_path(sha256).parent)
        os.replace(long_path(written), final)

    def put_bytes(self, data: bytes) -> str:
        """`data` in the loose pool; its sha256."""
        digest = hashlib.sha256(data).hexdigest()
        if not self.loose(digest):
            writing = self.temporary()
            write_new(writing, data)
            self.adopt(writing, digest)
        return digest

    def fetch(self, sha256: str, target: Path) -> str:
        if self.loose(sha256):
            return copy_file(self.pool_path(sha256), target)
        return super().fetch(sha256, target)

    def mark_bad(self, sha256: str, *, pack: str | None = None) -> None:
        if pack is None and self.loose(sha256):
            long_path(self.pool_path(sha256)).unlink(missing_ok=True)
            return
        super().mark_bad(sha256, pack=pack)

    def read_pool(self, sha256: str) -> bytes | None:
        """A small file's bytes, or None when the storage does not hold it."""
        if self.loose(sha256):
            return long_path(self.pool_path(sha256)).read_bytes()
        places = self.index().good(sha256)
        if not places:
            return None
        writing = self.root / "packs" / f"{uuid.uuid4().hex}{PARTIAL}"
        try:
            got = unpack(self.local_pack(places[0].pack), places[0], writing)
            return long_path(writing).read_bytes() if got == sha256 else None
        finally:
            long_path(writing).unlink(missing_ok=True)

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

    def drop(self, stamp: str) -> None:
        self._step("drop")
        shutil.rmtree(long_path(self.snapshots / stamp))

    def sweep(self, *, safety: timedelta, now: datetime) -> Swept:
        swept = super().sweep(safety=safety, now=now)
        if swept.blocked is not None:
            return swept
        named: set[str] = set()
        for stamp in self.copies():
            try:
                named.update(e.sha256 for e in self.manifest(stamp).entries if e.at == "pool")
            except Unreadable:
                return swept
        removed = 0
        for path in self._loose_files():
            if path.name not in named:
                path.unlink()
                removed += 1
        return Swept(swept.removed + removed, None, swept.torn)

    def room(self) -> int | None:
        return free_bytes(self.root)

    def total(self) -> int | None:
        existing = next((p for p in (self.root, *self.root.parents) if long_path(p).exists()), None)
        return None if existing is None else shutil.disk_usage(long_path(existing)).total

    def clean(self) -> Cleaned:
        removed = 0
        folders = (
            self.root,
            self.pool,
            self.root / "packs",
            self.root / "index",
            self.root / "bad",
        )
        for folder in folders:
            if long_path(folder).is_dir():
                for entry in os.scandir(long_path(folder)):
                    if entry.name.endswith(PARTIAL) and entry.is_file(follow_symlinks=False):
                        os.unlink(entry.path)
                        removed += 1
        torn: list[str] = []
        if long_path(self.snapshots).is_dir():
            stamps = sorted(
                entry.name
                for entry in os.scandir(long_path(self.snapshots))
                if entry.is_dir(follow_symlinks=False) and STAMP.fullmatch(entry.name)
            )
            whole = [s for s in stamps if self._whole(s)]
            for stamp in stamps:
                folder = long_path(self.snapshots / stamp)
                if not (folder / MANIFEST).is_file():
                    shutil.rmtree(folder)
                    removed += 1
                elif whole and stamp < whole[-1] and stamp not in whole:
                    shutil.rmtree(folder)
                    torn.append(stamp)
                    removed += 1
        return Cleaned(removed, tuple(torn))

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
        self._put_bytes(ABOUT, text.encode())

    def _whole(self, stamp: str) -> bool:
        try:
            self.manifest(stamp)
        except Unreadable:
            return False
        return True

    def _folder(self, folder: Path) -> None:
        if folder not in self._made:
            long_path(folder).mkdir(parents=True, exist_ok=True)
            self._made.add(folder)

    def _store(self, rel: str, local: Path) -> None:
        target = self.root / rel
        self._folder(target.parent)
        if long_path(target).is_file():
            long_path(local).unlink()
            return
        os.replace(long_path(local), long_path(target))

    def _put_bytes(self, rel: str, data: bytes) -> None:
        target = self.root / rel
        self._folder(target.parent)
        staged = target.with_name(f"{target.name}{PARTIAL}")
        long_path(staged).unlink(missing_ok=True)
        write_new(staged, data)
        os.replace(long_path(staged), long_path(target))

    def _read(self, rel: str) -> bytes | None:
        try:
            return long_path(self.root / rel).read_bytes()
        except FileNotFoundError:
            return None

    def _read_all(self, folder: str) -> dict[str, bytes]:
        found: dict[str, bytes] = {}
        for rel in self._list(folder):
            data = self._read(f"{folder}/{rel}")
            if data is not None:
                found[rel] = data
        return found

    def _list(self, folder: str) -> dict[str, int]:
        base = long_path(self.root / folder)
        found: dict[str, int] = {}
        if not base.is_dir():
            return found
        for parent, _, names in os.walk(base):
            for name in names:
                if name.endswith(PARTIAL):
                    continue
                path = Path(parent, name)
                try:
                    found[path.relative_to(base).as_posix()] = path.stat().st_size
                except FileNotFoundError:
                    continue
        return found

    def _remove(self, rel: str) -> None:
        long_path(self.root / rel).unlink(missing_ok=True)

    def local_pack(self, name: str) -> Path:
        path = self.root / "packs" / name[:2] / f"{name}.pack"
        if not long_path(path).is_file():
            raise FileNotFoundError(f"part of {self.where} is gone")
        return path

    def _scratch(self) -> Path:
        return self.root / "packs"

    def _loose_files(self) -> Sequence[Path]:
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


class RcloneRepository(Packed):
    """A storage behind an rclone remote, written only with `rclone copy`, each arrival checked
    with `lsf`, deleted from only by `drop` and the prune. `root` is the folder on the remote that
    holds this QMX folder's copies. Each pack is written in `work`, and a pack read back lands in
    `fetched`, one at a time, never leaving less than `keep_free` free on that drive. `secrets`
    are the remote's keys, handed to each call in its environment."""

    def __init__(
        self,
        runner: Rclone,
        remote: str,
        root: str,
        *,
        work: Path,
        fetched: Path,
        name: str | None = None,
        key: str | None = None,
        secrets: Mapping[str, str] | None = None,
        keep_free: int = 0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(key=key or f"rclone:{remote}:{root}", clock=clock)
        self.runner = runner
        self.remote = remote
        self.root = root.rstrip("/")
        self.work = work
        self.fetched = fetched
        self.name = name or remote
        self.secrets = dict(secrets or {})
        self.keep_free = keep_free
        self._pack: tuple[str, Path] | None = None

    @property
    def where(self) -> str:
        return self.name

    def _at(self, rel: str = "") -> str:
        return f"{self.remote}:{self.root}/{rel}" if rel else f"{self.remote}:{self.root}"

    def _run(self, args: Sequence[str], *, missing_ok: bool = False) -> str | None:
        ran = self.runner.run(args, secrets=self.secrets)
        if ran.code == 0:
            return ran.out
        if missing_ok and ran.failure == "missing":
            return None
        raise StorageRefused(f"{self.name} {ran.line}", ran.failure or "other")

    def _store(self, rel: str, local: Path) -> None:
        folder, _, name = rel.rpartition("/")
        named = local if local.name == name else local.with_name(name)
        if named != local:
            os.replace(long_path(local), long_path(named))
        size = long_path(named).stat().st_size
        try:
            self._run(["copy", str(named), self._at(folder)])
            listed = self._run(["lsf", "--files-only", "--format", "sp", self._at(folder)]) or ""
        finally:
            long_path(named).unlink(missing_ok=True)
        arrived = {
            line.partition(";")[2]: line.partition(";")[0] for line in listed.splitlines() if line
        }
        if arrived.get(name) != str(size):
            raise StorageRefused(
                f"{self.name} did not keep a file as it was sent; QMX sends it again at the next "
                "sync",
                "other",
            )

    def _put_bytes(self, rel: str, data: bytes) -> None:
        folder = self._scratch() / uuid.uuid4().hex
        long_path(folder).mkdir(parents=True, exist_ok=True)
        local = folder / PurePosixPath(rel).name
        write_new(local, data)
        try:
            self._store(rel, local)
        finally:
            shutil.rmtree(long_path(folder), ignore_errors=True)

    def _read(self, rel: str) -> bytes | None:
        out = self._run(["cat", self._at(rel)], missing_ok=True)
        return None if out is None else out.encode("utf-8")

    def _read_all(self, folder: str) -> dict[str, bytes]:
        local = self.fetched / f"read-{uuid.uuid4().hex}"
        try:
            self._run(["copy", self._at(folder), str(local)], missing_ok=True)
            found: dict[str, bytes] = {}
            if long_path(local).is_dir():
                for parent, _, names in os.walk(long_path(local)):
                    for name in names:
                        path = Path(parent, name)
                        found[path.relative_to(long_path(local)).as_posix()] = path.read_bytes()
            return found
        finally:
            shutil.rmtree(long_path(local), ignore_errors=True)

    def _list(self, folder: str) -> dict[str, int]:
        out = self._run(
            ["lsf", "-R", "--files-only", "--format", "sp", self._at(folder)], missing_ok=True
        )
        found: dict[str, int] = {}
        for line in (out or "").splitlines():
            size, _, rel = line.partition(";")
            if rel and not rel.endswith((".partial", PARTIAL)) and size.isdigit():
                found[rel] = int(size)
        return found

    def _remove(self, rel: str) -> None:
        self._run(["deletefile", self._at(rel)], missing_ok=True)

    def local_pack(self, name: str) -> Path:
        if self._pack is not None and self._pack[0] == name:
            return self._pack[1]
        self.let_go()
        rel = f"packs/{name[:2]}/{name}.pack"
        listed = self._list(f"packs/{name[:2]}")
        size = listed.get(f"{name}.pack")
        if size is None:
            raise FileNotFoundError(f"{self.name} no longer holds part of its copies")
        long_path(self.fetched).mkdir(parents=True, exist_ok=True)
        if free_bytes(self.fetched) - size < self.keep_free:
            raise StorageRefused(
                f"reading a copy from {self.name} needs {size >> 20} MB in {plain(self.fetched)} "
                "and its drive is at the floor QMX keeps free; free some space and try again",
                "full",
            )
        self._run(["copy", self._at(rel), str(self.fetched)])
        path = self.fetched / f"{name}.pack"
        if not long_path(path).is_file():
            raise FileNotFoundError(f"{self.name} did not give back part of its copies")
        self._pack = (name, path)
        return path

    def let_go(self) -> None:
        """Remove the pack fetched last, so the next is the only one on this PC."""
        if self._pack is not None:
            long_path(self._pack[1]).unlink(missing_ok=True)
            self._pack = None

    def _scratch(self) -> Path:
        long_path(self.work).mkdir(parents=True, exist_ok=True)
        return self.work

    def copies(self) -> tuple[str, ...]:
        found = [
            rel.partition("/")[0]
            for rel in self._list("snapshots")
            if rel.endswith(f"/{MANIFEST}") and STAMP.fullmatch(rel.partition("/")[0])
        ]
        return tuple(sorted(found))

    def manifest(self, stamp: str) -> Manifest:
        where = f"{self.name}/snapshots/{stamp}"
        try:
            data = self._read(f"snapshots/{stamp}/{MANIFEST}")
        except StorageRefused as refused:
            raise Unreadable(f"the copy {where} cannot be read ({refused})") from None
        if data is None:
            raise Unreadable(f"the copy {where} cannot be read (it is gone)")
        return Manifest.parse(data, where)

    def read_extra(self, stamp: str, name: str) -> bytes | None:
        return self._read(f"snapshots/{stamp}/{name}")

    def drop(self, stamp: str) -> None:
        self._step("drop")
        for rel in self._list(f"snapshots/{stamp}"):
            self._remove(f"snapshots/{stamp}/{rel}")

    def room(self) -> int | None:
        return self._about("free")

    def total(self) -> int | None:
        return self._about("total")

    def _about(self, field_name: str) -> int | None:
        ran = self.runner.run(["about", self._at(), "--json"], secrets=self.secrets)
        if ran.code or not ran.out.strip():
            return None
        try:
            value = cast("dict[str, object]", json.loads(ran.out)).get(field_name)
        except ValueError:
            return None
        return value if isinstance(value, int) else None

    def clean(self) -> Cleaned:
        whole, torn = self.manifests()
        newest = max(whole, default=None)
        gone = [stamp for stamp in torn if newest is not None and stamp < newest]
        for stamp in gone:
            self.drop(stamp)
        return Cleaned(len(gone), tuple(gone))

    def about(self) -> Mapping[str, object] | None:
        import tomllib  # noqa: PLC0415

        data = self._read(ABOUT)
        if data is None:
            return None
        try:
            return tomllib.loads(data.decode("utf-8"))
        except UnicodeDecodeError, ValueError:
            return {}

    def set_about(self, fields: Mapping[str, str]) -> None:
        text = "".join(f"{key} = {json.dumps(value)}\n" for key, value in fields.items())
        self._put_bytes(ABOUT, text.encode())


def _quiet(_step: str) -> None:
    return None
