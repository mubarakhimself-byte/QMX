"""The Library store: content-addressed objects and blobs, refs moved only by compare-and-swap, and
append-only edge and annotation logs (Library AD-1, AD-2, AD-5, AD-6, AD-7).

Evidence is the files under the store's root:

    objects/ab/cd/<hex>.json    one canonical identity manifest per object, written once
    blobs/ab/cd/<hex>           the bytes of a blob born on this store, written once
    blobs/fetched/ab/cd/<hex>   a cache copy, fetched from another store and evictable (AD-10)
    blobs/transient/<hex>       a transient blob (checkpoints), kept on this store only
    blobs/tombstones/<hex>.json an operator purge: the bytes are gone, this names why (AD-6)
    refs/log.jsonl              every ref move, append-only
    refs/claims.json            the live intent claims, prunable and never bucketed (AD-24)
    edges/<store>.jsonl         after-birth relations, append-only, one stream per writer
    annotations/log.jsonl       tags, authorship and other annotations, append-only
    kinds/<kind>.schema.json    the kinds this store was written with

`catalog.db` is rebuilt from those files whenever it is missing or behind them. One process
writes a store: `open` takes an OS lock on `writer.lock` and refuses a second writer. Every put
passes the redactor first, so the stored bytes are the only bytes (engine AD-37).

A store has a `role` (AD-19). The `writer` is the primary and the only one that moves refs. A
`replica` mirrors the primary's refs and objects and sends its writes to it; a `cache` does the
same and fetches a missing durable blob from its `upstream` and keeps it (AD-10). Claims live in
`refs/claims.json` rather than the append-only log because AD-24 declares them transient and
prunes them when released or expired, which the log can never do.
"""

from __future__ import annotations

import codecs
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import uuid
from collections import deque
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import IO, Any, Final, Literal, Protocol, Self, cast

from pydantic import JsonValue
from qmx_home.versions import too_new

from qmx_library.blame import lines, origins
from qmx_library.fts import Catalog, norm
from qmx_library.kinds import Kind, kind, roster, schema_files
from qmx_library.marks import CLEAR, QUARANTINED, Marks, marks, marks_ref
from qmx_library.port import (
    RELATIONS,
    AsOf,
    Blame,
    BlameLine,
    BlobId,
    BlobRef,
    BlobView,
    Claim,
    Class,
    Commit,
    Draft,
    Grounding,
    HistoryEntry,
    Hit,
    JsonObject,
    LibraryRefused,
    MergeResult,
    ObjectId,
    ObjectView,
    PurgeResult,
    Relation,
    Step,
    StoreRole,
    Strategy,
    normalised,
)
from qmx_library.principal import MAIN, Act, Principal, may_advance, own_ref, state_ref
from qmx_library.status import QUARANTINE, Damage, StoreState, TornTail, inspect_logs

MANIFEST: Final = "qmx.library.object/1"
CHECKOUT_FILE: Final = ".checkout.json"
CHUNK: Final = 1 << 20
"""Bytes one blob read, one blob write or one upload move at a time (Library AD-10, AD-27). No
constant here bounds a file's size: a text blob of any length is indexed whole, in these chunks."""
UPLOAD: Final = "uploads"
"""Where a partial upload waits, `<root>/uploads/<id>.part`, until its last byte arrives (AD-27)."""
TEXT_SLOTS: Final = frozenset({"text", "transcript"})
"""The slots a sync copies (AD-10, N1): a document's words travel so the replica can search them,
and every other blob of the object waits until something on that store opens it."""
PRIMARY_REF: Final = "refs/primary"
PRIMARY_ITEM: Final = "refs/primary"
EPOCH: Final = "epoch.json"
"""The highest primary epoch this store has seen, kept beside the ref log so a restore keeps it."""
MIB: Final = 1024 * 1024
CLAIMS: Final = "claims.json"
CLAIM_KEY: Final = re.compile(r"[A-Za-z0-9_.:+-]{1,200}")
"""An intent key is a fingerprint; a path segment it must also be, so `/` is out."""
UPLOAD_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,128}")
"""An upload id names one partial file under `uploads/`, so it is one path segment."""
CAPTURE_ORIGIN: Final = "capture"
"""The origin a computer or browser capture lands with (AD-27)."""
REDACTED_ACCOUNT: Final = "[redacted account]"
CAPTURE_VERSION: Final = "capture-1"
"""The extractor version a capture's text hash is compared within (AD-27)."""
RENAME_TRIES: Final = 8
"""A rename Windows refuses because the target is open is retried this many times."""
RENAME_WAIT_S: Final = 0.01
"""The first wait between those tries; each doubles, so a held handle has about 1.3 s to close."""
HELD_OPEN: Final = frozenset({5, 32})
"""The two WinError codes for "held open": access denied and sharing violation."""
JSON_MEDIA: Final = "application/json"
"""The one media type besides `text/*` that merges by structure instead of by pick-one (AD-30)."""
CONFLICT_LIMIT: Final = 127
"""`git merge-file`'s largest conflict count; anything above is git's own failure, not a merge."""
log = logging.getLogger(__name__)


ABSENT: Final = object()
"""A JSON key one side does not hold, which is not the same as a key holding null."""
CLASH: Final = object()
"""The answer `_pick_key` gives for a key both sides changed away from the base."""


def _pick_key(ours: object, theirs: object, base: object) -> object:
    """The one side to keep for a JSON key, or `CLASH`: the rule `pick` applies to fields."""
    if theirs in (ours, base):
        return ours
    if ours == base:
        return theirs
    return CLASH


def _json_object(data: bytes) -> JsonObject | None:
    try:
        found = json.loads(data.decode("utf-8"))
    except UnicodeDecodeError, ValueError:
        return None
    return cast(JsonObject, found) if isinstance(found, dict) else None


def _canonical_json(value: JsonObject) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def merge_text(ours: bytes, base: bytes, theirs: bytes) -> tuple[bytes, int]:
    """Three-way text merge through `git merge-file -p --diff3` (AD-30).

    The merged bytes and the number of conflicts. Exit 0 is a clean merge; a positive status is
    git's conflict count and the bytes carry the diff3 markers; anything higher is git failing,
    which is refused rather than reported as a conflict.
    """
    with tempfile.TemporaryDirectory(prefix="qmx-merge-") as folder:
        paths = [Path(folder) / name for name in ("ours", "base", "theirs")]
        for path, data in zip(paths, (ours, base, theirs), strict=True):
            path.write_bytes(data)
        try:
            done = subprocess.run(
                [  # noqa: S607 - git from PATH is the pinned 2.x the contract names
                    "git",
                    "merge-file",
                    "-p",
                    "--diff3",
                    "-L",
                    "ours",
                    "-L",
                    "base",
                    "-L",
                    "theirs",
                    *(str(path) for path in paths),
                ],
                capture_output=True,
                check=False,
            )
        except OSError as error:
            raise LibraryRefused(
                "storage_failure", f"git merge-file is not usable here: {error}"
            ) from error
    if done.returncode < 0 or done.returncode > CONFLICT_LIMIT:
        detail = done.stderr.decode("utf-8", "replace").strip()
        raise LibraryRefused("storage_failure", f"git merge-file failed: {detail}")
    return done.stdout, done.returncode


@dataclass(slots=True)
class _Merged:
    """A three-way merge before anything is minted: the clean result and the entries that clash."""

    kind: str
    title: str
    summary: str
    fields: JsonObject
    blobs: dict[str, BlobRef]
    keyed: dict[str, JsonObject]
    """A JSON slot merged except for its clashing keys, waiting for `resolve` to fill them."""
    entries: list[JsonObject]


class Redactor(Protocol):
    """`qmx_engine.ledger.redact`, passed in by the host so the Library imports no engine code."""

    def redact(self, text: str) -> str: ...

    def redact_json(self, value: object) -> tuple[JsonValue, int]: ...

    def holds_value(self, data: bytes) -> bool: ...


class BlobSource(Protocol):
    """Where a replica or a cache fetches a durable blob it does not hold (AD-10)."""

    def fetch(self, blob_id: str) -> bytes | None: ...


def canonical(value: object) -> bytes:
    """Sorted keys, no whitespace, NFC strings, no NaN: the fp1 recipe, floats and nulls allowed."""

    def nfc(node: object) -> object:
        if isinstance(node, str):
            return unicodedata.normalize("NFC", node)
        if isinstance(node, dict):
            return {nfc(k): nfc(v) for k, v in cast(dict[object, object], node).items()}
        if isinstance(node, list | tuple):
            return [nfc(v) for v in cast(Sequence[object], node)]
        return node

    text = json.dumps(nfc(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def fp1(value: object) -> ObjectId:
    return f"fp1:sha256:{sha256(canonical(value)).hexdigest()}"


def locator(value: JsonObject) -> JsonObject:
    """Where in its source an object came from: `{seconds}`, `{page, paragraph?}` or `{line}`
    (AD-4)."""

    def count(key: str) -> bool:
        found = value.get(key)
        return isinstance(found, int) and not isinstance(found, bool) and found >= 1

    seconds = value.get("seconds")
    match sorted(value):
        case ["seconds"] if isinstance(seconds, int | float) and not isinstance(seconds, bool):
            ok = seconds >= 0
        case ["line"]:
            ok = count("line")
        case ["page"]:
            ok = count("page")
        case ["page", "paragraph"]:
            ok = count("page") and count("paragraph")
        case _:
            ok = False
    if not ok:
        raise LibraryRefused("schema_invalid", f"{value!r} is not a locator")
    return value


def _sharded(root: Path, hexdigest: str, suffix: str = "") -> Path:
    return root / hexdigest[:2] / hexdigest[2:4] / f"{hexdigest}{suffix}"


def _lock(handle: IO[bytes]) -> None:
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _replace(temp: Path, path: Path) -> None:
    """`os.replace`, retried while Windows reports the target held open (WinError 5 or 32).

    The wait doubles from `RENAME_WAIT_S`, so a virus scanner or an indexer that holds the target
    for a moment no longer loses the write. Past the last try the refusal names the path, because
    no other part of the system can say which process holds it.
    """
    for attempt in range(RENAME_TRIES):
        try:
            os.replace(temp, path)
        except PermissionError as held:
            winerror = getattr(held, "winerror", None)
            if winerror not in HELD_OPEN or attempt == RENAME_TRIES - 1:
                raise LibraryRefused(
                    "storage_failure",
                    f"{path.name} could not be replaced after {attempt + 1} tries; "
                    f"a program holds it open ({held})",
                ) from held
            wait = RENAME_WAIT_S * 2**attempt
            log.warning("retrying rename onto %s in %.2f s: %s", path.name, wait, held)
            time.sleep(wait)
        else:
            _fsync_folder(path.parent)
            return


def _fsync_folder(folder: Path) -> None:
    """Make a rename durable: the file was fsynced before it, and the folder entry after it.

    Windows cannot open a folder as a handle from Python, and NTFS commits the directory entry
    itself; on the other systems this is the fsync AD-16 asks for.
    """
    if sys.platform == "win32":
        return
    descriptor = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_once(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise LibraryRefused("collision", f"{path.name} exists with other bytes")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
    with temp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    _replace(temp, path)


def _append(path: Path, record: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(json.dumps(record, sort_keys=True).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _quarantine(root: Path, torn: TornTail) -> None:
    """Keep a torn last line under `quarantine/`, then cut it out of its log (AD-16).

    The quarantine copy is fsynced before the log is cut, so a power cut during the repair leaves
    the line in both places, never in neither.
    """
    target = root / QUARANTINE / torn.log
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("ab") as handle:
        handle.write(torn.tail + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    with (root / torn.log).open("r+b") as handle:
        handle.truncate(torn.start)
        handle.flush()
        os.fsync(handle.fileno())


def _drop_index(path: Path, *, keep: bool, at: datetime) -> None:
    """Take the catalog file away before a rebuild. One that is not QMX's (not SQLite, or another
    program's) is moved aside under its own name with a stamp, never deleted."""
    stamp = at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    for suffix in ("", "-wal", "-shm"):
        found = path.with_name(f"{path.name}{suffix}")
        if keep and found.exists():
            found.rename(path.with_name(f"{path.name}.not-qmx-{stamp}{suffix}"))
        else:
            found.unlink(missing_ok=True)


def _repair_logs(root: Path, damage: Sequence[Damage]) -> StoreState:
    """Quarantine every torn tail and say how the store opened."""
    alarms: list[str] = []
    incident: str | None = None
    for found in damage:
        if isinstance(found, TornTail):
            _quarantine(root, found)
            alarms.append(found.alarm)
        elif incident is None:
            incident = f"{found.log} line {found.line} does not parse"
    return StoreState(
        "read_only" if incident else ("torn" if alarms else "open"), tuple(alarms), incident
    )


def _lines(path: Path) -> Generator[dict[str, Any]]:
    """Every record in an append-only log. A damaged line is skipped and never read as a record;
    `Store.open` has already classified it in the store's `state`."""
    if path.exists():
        with path.open("rb") as handle:
            for line in handle:
                if not line.strip() or b"\x00" in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    yield cast(dict[str, Any], record)


def _decoded(path: Path, *, chunk: int = CHUNK) -> str:
    """The file's UTF-8 text, read in `chunk`-sized pieces so no single read copies it whole."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    pieces: list[str] = []
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            pieces.append(decoder.decode(data))
    pieces.append(decoder.decode(b"", final=True))
    return "".join(pieces)


PREVIEW_CHARS: Final = 200
"""Characters of a capture's text its summary carries, the same cut search previews (AD-8)."""


def redact_accounts(text: str, account_ids: Sequence[str]) -> str:
    """Every account id Connections knows, replaced, longest first so no prefix wins (AD-27)."""
    found = sorted((account for account in account_ids if account), key=len, reverse=True)
    for account in found:
        text = text.replace(account, REDACTED_ACCOUNT)
    return text


def capture_source(
    text: str,
    pixels: bytes,
    *,
    account_ids: Sequence[str] = (),
    title: str = "",
    surface: str = "computer",
    media_type: str = "image/png",
) -> Draft:
    """A screen or browser capture as one `source`: text redacted, pixels kept (AD-27).

    The capture's text is redacted against the account ids in Connections, because a broker
    screen carries them and never should reach a search index; the pixels stay whole, because
    they are the evidence of what he saw. The text hash names the extractor version it was
    compared within, so a better extractor does not read as the same document.
    """
    clean = redact_accounts(text, account_ids)
    digest = sha256(" ".join(clean.split()).encode("utf-8")).hexdigest()
    return Draft(
        "source",
        title=title or f"{surface} capture",
        summary=clean[:PREVIEW_CHARS],
        fields={
            "origin": CAPTURE_ORIGIN,
            "captured_from": surface,
            "media_type": media_type,
            "text_hash": digest,
            "extractor_version": CAPTURE_VERSION,
        },
        blobs={"text": clean.encode("utf-8"), "original": pixels, "frames/0": pixels},
    )


def text_blob_ids(manifest: Mapping[str, Any]) -> set[str]:
    """The blob ids of one manifest's text slots: the only blobs a selective sync copies (N1)."""
    try:
        spec = kind(str(manifest.get("kind") or ""))
    except LibraryRefused:
        return set()
    found: set[str] = set()
    blobs = cast(Mapping[str, Mapping[str, Any]], manifest.get("blobs") or {})
    for slot, blob in blobs.items():
        try:
            pattern = spec.slot(slot).pattern
        except LibraryRefused:
            continue
        if pattern in TEXT_SLOTS:
            found.add(str(blob["sha256"]))
    return found


@dataclass(frozen=True, slots=True)
class Epoch:
    """Which store is primary and how many flips it has taken (AD-14, F12, F15).

    The record lives on `refs/primary` and every store remembers the highest epoch it has seen,
    because a store restored from an old backup has the old record and no memory of the new one.
    """

    primary: str
    epoch: int
    seq: int = 0
    """The ref-log position both sides shared when this store learned it, and so the moves a
    parked store must not replay."""
    stale: bool = False
    """This store held the primary and learned a higher epoch: it stops acting as primary."""
    parked: tuple[str, ...] = ()
    """The `refs/conflicts/*` refs its primary moves were parked on, one per move (N13, N19)."""


class Upload:
    """One resumable upload: an open append handle, the hash of every byte it holds, and its size.

    The partial file is the state, so a closed client or a crash leaves exactly the bytes whose
    hash the next caller re-reads before it appends (AD-27). `write` takes one chunk at a time,
    so a 3 GB recording never sits in memory on either side of the door.
    """

    def __init__(
        self,
        store: Store,
        upload_id: str,
        *,
        offset: int = 0,
        partial_sha256: str | None = None,
    ) -> None:
        self.store = store
        self.upload_id = upload_id
        self.path = store.upload_path(upload_id)
        self.hasher = sha256()
        self.held = 0
        if offset == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.unlink(missing_ok=True)
        else:
            if not self.path.exists() or self.path.stat().st_size != offset:
                raise LibraryRefused(
                    "offset_mismatch",
                    f"{upload_id} does not hold the {offset} bytes resumed from",
                )
            with self.path.open("rb") as handle:
                while data := handle.read(CHUNK):
                    self.hasher.update(data)
                    self.held += len(data)
            if partial_sha256 is not None and self.hasher.hexdigest() != partial_sha256:
                raise LibraryRefused(
                    "hash_mismatch", f"{upload_id} does not hash to what the client resumed"
                )
        self._handle = self.path.open("ab")

    @property
    def sha256(self) -> str:
        """The hash of every byte this upload holds, including bytes it resumed from."""
        return self.hasher.hexdigest()

    def write(self, chunk: bytes) -> int:
        """Append one chunk, hashing it as it lands; returns the bytes now held."""
        if chunk:
            self._handle.write(chunk)
            self.hasher.update(chunk)
            self.held += len(chunk)
        return self.held

    def close(self) -> None:
        if not self._handle.closed:
            self._handle.flush()
            os.fsync(self._handle.fileno())
            self._handle.close()

    def finish(self, expect_sha256: str | None = None) -> str:
        """Close and promote the partial to its blob, refusing a hash the client disagrees with."""
        self.close()
        return self.store.complete_upload(
            self.upload_id,
            expect_sha256=self.sha256 if expect_sha256 is None else expect_sha256,
        )

    def discard(self) -> None:
        """Drop this upload: a partial nobody will resume is not a durable blob (AD-27)."""
        self.close()
        self.store.discard_upload(self.upload_id)


class Store:
    """The writer of one store. Every verb of `LibraryPort` is here; the reads the engine adapter
    needs beside them (`head`, `placed`, `moves`, `read_blob`) are catalog queries."""

    def __init__(
        self,
        root: Path,
        handle: IO[bytes],
        *,
        name: str,
        redactor: Redactor,
        wall: Callable[[], datetime],
        role: StoreRole = "writer",
        upstream: BlobSource | None = None,
        state: StoreState,
        floor_bytes: int = 0,
        too_new: str | None = None,
    ) -> None:
        self.root = root
        self.name = name
        self.engine = Principal("engine", name)
        self.redactor = redactor
        self.wall = wall
        self.role: StoreRole = role
        self.upstream = upstream
        self.state = state
        self.floor_bytes = floor_bytes
        """The room this machine keeps for itself, handed in by its host (D-11). Zero means the
        caller measured no floor, so every write that fits is taken."""
        self._handle = handle
        self._mutex = threading.RLock()
        self.too_new = too_new
        """Why this Library opened read-only: a newer QMX wrote it and raised its `min_reader`
        (design 62 B2 rule 4). Nothing under `root` is written then, its index included."""
        self.catalog = Catalog(None if too_new else root / "catalog.db")
        if self.catalog.found != "current" or self.catalog.stamp() != self._stamp():
            self.rebuild_indexes()
        self._seq = self.catalog.last_seq()
        (edges,) = self.catalog.db.execute(
            "SELECT count(*) FROM relations WHERE origin = 'edge'"
        ).fetchone()
        self._edge_seq = int(edges)
        self._epoch: Epoch | None = self._read_epoch()

    @classmethod
    def open(
        cls,
        root: Path,
        *,
        redactor: Redactor,
        name: str = "pc",
        wall: Callable[[], datetime] | None = None,
        role: StoreRole = "writer",
        upstream: BlobSource | None = None,
        floor_bytes: int = 0,
    ) -> Store:
        root.mkdir(parents=True, exist_ok=True)
        handle = (root / "writer.lock").open("a+b")
        try:
            _lock(handle)
        except OSError:
            handle.close()
            raise LibraryRefused(
                "storage_failure", f"another process writes the Library at {root}"
            ) from None
        newer = too_new(root, "library")
        if newer is not None:
            found = StoreState("read_only", (), newer)
        else:
            kinds = root / "kinds"
            kinds.mkdir(exist_ok=True)
            for schema in schema_files():
                target = kinds / schema.name
                if not target.exists() or target.read_bytes() != schema.read_bytes():
                    shutil.copyfile(schema, target)
            try:
                found = _repair_logs(root, inspect_logs(root))
            except OSError as refused:
                handle.close()
                raise LibraryRefused(
                    "storage_failure", f"cannot repair the logs at {root}: {refused}"
                ) from refused
        try:
            return cls(
                root,
                handle,
                name=name,
                redactor=redactor,
                wall=wall or (lambda: datetime.now(UTC)),
                role=role,
                upstream=upstream,
                state=found,
                floor_bytes=floor_bytes,
                too_new=newer,
            )
        except BaseException:
            handle.close()
            raise

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.catalog.close()
        self._handle.close()

    @property
    def ref_log(self) -> Path:
        return self.root / "refs" / "log.jsonl"

    @property
    def edge_log(self) -> Path:
        return self.root / "edges" / f"{self.name}.jsonl"

    @property
    def annotation_log(self) -> Path:
        return self.root / "annotations" / "log.jsonl"

    @property
    def claims_path(self) -> Path:
        return self.root / "refs" / CLAIMS

    @property
    def tombstones(self) -> Path:
        return self.root / "blobs" / "tombstones"

    def _object_path(self, object_id: ObjectId) -> Path:
        return _sharded(self.root / "objects", object_id.rsplit(":", 1)[-1], ".json")

    def _blob_path(self, blob_id: str, *, transient: bool, fetched: bool = False) -> Path:
        hexdigest = blob_id.removeprefix("sha256:")
        if transient:
            return self.root / "blobs" / "transient" / hexdigest
        if fetched:
            return _sharded(self.root / "blobs" / "fetched", hexdigest)
        return _sharded(self.root / "blobs", hexdigest)

    def _held(self, blob_id: str) -> Path | None:
        """Where this store holds a blob's bytes: its own copy first, then a cache copy (AD-10)."""
        born = self._blob_path(blob_id, transient=False)
        if born.exists():
            return born
        cached = self._blob_path(blob_id, transient=False, fetched=True)
        return cached if cached.exists() else None

    def _stamp(self) -> str:
        logs = [*sorted((self.root / "edges").glob("*.jsonl")), self.ref_log, self.annotation_log]
        sizes = {str(p.relative_to(self.root)): p.stat().st_size for p in logs if p.exists()}
        return json.dumps(sizes, sort_keys=True)

    def rebuild_indexes(self) -> None:
        """Drop `catalog.db` and replay the evidence into a new one (AD-5, FM-9)."""
        with self._mutex:
            foreign = self.catalog.found == "foreign"
            self.catalog.close()
            if self.too_new is None:
                _drop_index(self.root / "catalog.db", keep=foreign, at=self.wall())
            self.catalog = Catalog(None if self.too_new else self.root / "catalog.db")
            with self.catalog.batch():
                for path in sorted((self.root / "objects").rglob("*.json")):
                    manifest = cast(dict[str, Any], json.loads(path.read_bytes()))
                    self._index_object(f"fp1:sha256:{path.stem}", manifest)
                for move in _lines(self.ref_log):
                    self.catalog.index_move(move)
                for log in sorted((self.root / "edges").glob("*.jsonl")):
                    for edge in _lines(log):
                        self.catalog.index_edge(edge)
                for entry in _lines(self.annotation_log):
                    self.catalog.index_annotation(entry)
                self.catalog.set_stamp(self._stamp())

    def _index_object(self, object_id: ObjectId, manifest: Mapping[str, Any]) -> None:
        texts: list[str] = []
        for spec in cast(dict[str, dict[str, Any]], manifest["blobs"]).values():
            path = self._held(str(spec["sha256"]))
            if path is not None:
                with suppress(UnicodeDecodeError, OSError):
                    texts.append(_decoded(path))
        klass = kind(str(manifest["kind"])).klass
        self.catalog.index_object(object_id, manifest, klass, " ".join(texts))

    def _reindex_object(self, object_id: ObjectId, manifest: Mapping[str, Any]) -> None:
        """Index one object again, now that a blob it names has arrived (AD-10, N1). The index is
        never evidence: the object and its manifest are, and they are unchanged."""
        with self._writing():
            self.catalog.db.execute("DELETE FROM search WHERE object_id = ?", (object_id,))
            self.catalog.db.execute("DELETE FROM objects WHERE object_id = ?", (object_id,))
            self._index_object(object_id, manifest)

    def _reindex_blob(self, blob_id: str) -> tuple[str, ...]:
        """Re-index the objects whose text slot this blob is, when its bytes arrive here.

        An object that arrives before its text slots was indexed without their words. The
        arrival is the one moment to read them, and a blob no text slot names re-indexes nothing.
        """
        named = [
            str(row[0])
            for row in self.catalog.db.execute(
                "SELECT object_id FROM objects WHERE blobs LIKE ?", (f"%{blob_id}%",)
            )
        ]
        done: list[str] = []
        for object_id in named:
            try:
                manifest = self.manifest(object_id)
            except LibraryRefused:
                continue
            if blob_id not in text_blob_ids(manifest):
                continue
            self._reindex_object(object_id, manifest)
            done.append(object_id)
        return tuple(done)

    def _now(self) -> str:
        return self.wall().astimezone(UTC).isoformat().replace("+00:00", "Z")

    def _move(
        self,
        who: Principal,
        item: str,
        ref: str,
        new_head: str,
        *,
        reason: str | None = None,
        replaced_by: str | None = None,
        at: str | None = None,
    ) -> Commit:
        self._refuse_read_only("a ref move")
        found = self.catalog.head(item, ref)
        prev = None if found is None else found[0]
        self._seq += 1
        move: dict[str, object] = {
            "seq": self._seq,
            "item": item,
            "ref": ref,
            "principal": str(who),
            "prev_head": prev,
            "new_head": new_head,
            "at": at or self._now(),
        }
        if reason is not None:
            move["reason"] = reason
        if replaced_by is not None:
            move["replaced_by"] = replaced_by
        _append(self.ref_log, move)
        self.catalog.index_move(move)
        return Commit(new_head, item, ref, prev, self._seq)

    def _annotate(self, who: Principal, object_id: ObjectId, values: JsonObject) -> None:
        entry = {"object_id": object_id, "values": values, "principal": str(who), "at": self._now()}
        _append(self.annotation_log, entry)
        self.catalog.index_annotation(entry)

    @contextmanager
    def _writing(self) -> Generator[None]:
        with self._mutex, self.catalog.batch():
            yield
            self.catalog.set_stamp(self._stamp())

    def _blob(self, slot: str, data: bytes | BlobRef, spec: Kind) -> dict[str, JsonValue]:
        media = spec.slot(slot)
        if isinstance(data, BlobRef):
            path = self._blob_path(data.blob_id, transient=media.transient)
            if not path.exists():
                raise LibraryRefused("blob_unavailable", f"no blob {data.blob_id}")
            data = path.read_bytes()
        data = self._redacted(data)
        blob_id = f"sha256:{sha256(data).hexdigest()}"
        _write_once(self._blob_path(blob_id, transient=media.transient), data)
        return {"sha256": blob_id, "size": len(data), "media_type": media.media_type}

    def _redacted(self, data: bytes) -> bytes:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if self.redactor.holds_value(data):
                raise LibraryRefused("secret_in_blob", "a binary blob holds a secret") from None
            return data
        return self.redactor.redact(text).encode("utf-8")

    def _require(self, object_id: ObjectId) -> tuple[Any, ...]:
        row = self.catalog.row(object_id)
        if row is None:
            raise LibraryRefused("not_found", f"no object {object_id}")
        return row

    def _check_owner(self, who: Principal, ref: str, act: Act) -> None:
        if not may_advance(who, ref, act, store=self.name):
            raise LibraryRefused("ref_not_owned", f"{who} may not {act} onto {ref}")

    def _refuse_read_only(self, act: str) -> None:
        """A store whose logs hold a line that cannot be repaired takes no write (AD-16), and nor
        does one a newer QMX marked too new for this one (design 62 B2 rule 4)."""
        self._refuse_too_new(act)
        if self.state.health == "read_only":
            raise LibraryRefused(
                "storage_failure",
                f"this store opened read-only: {self.state.incident}; {act} waits for a restore",
            )

    def _refuse_too_new(self, act: str) -> None:
        if self.too_new is not None:
            raise LibraryRefused(
                "storage_failure", f"{act} refused: the Library opened read-only. {self.too_new}"
            )

    def _check_writer(self, act: str) -> None:
        self._refuse_read_only(act)
        if self._epoch is not None and self._epoch.stale:
            raise LibraryRefused(
                "ref_not_owned",
                f"this store learned epoch {self._epoch.epoch}, whose primary is "
                f"{self._epoch.primary}, so {act} waits for it (library:epoch:{self.name})",
            )
        if self.role != "writer":
            raise LibraryRefused(
                "read_only_replica", f"this store is a {self.role}; {act} goes to the primary"
            )
        self._refuse_full(act)

    def _refuse_full(self, act: str) -> None:
        """A machine below its floor takes no write at all, so no file is ever left half written
        (F22, P-DISKFULL). The Library gives way last: the machine's expendable classes go first,
        and this door opens again when room is back."""
        if self.floor_bytes <= 0:
            return
        free = shutil.disk_usage(self.root).free
        if free < self.floor_bytes:
            raise LibraryRefused(
                "disk_full",
                f"{free // MIB} MB free here, below the {self.floor_bytes // MIB} MB floor this "
                f"machine keeps; {act} was refused whole and nothing was written",
            )

    def _active(self, item: str) -> None:
        if self.catalog.state(item) == "archived":
            raise LibraryRefused("archived", f"item {item} is archived")

    def _mint(
        self, who: Principal, draft: Draft, item: str, parents: Sequence[ObjectId]
    ) -> tuple[ObjectId, Kind]:
        spec = kind(draft.kind)
        fields = cast(JsonObject, self.redactor.redact_json(draft.fields)[0])
        spec.check(fields, set(draft.blobs))
        relations: list[JsonObject] = []
        for relation in draft.relations:
            name, to = normalised(relation[0]), relation[1]
            if name not in RELATIONS:
                raise LibraryRefused("unknown_relation", f"{relation[0]!r} is not a relation")
            self._require(to)
            entry: JsonObject = {"type": name, "to": to}
            if len(relation) == 3:
                entry["locator"] = locator(relation[2])
            relations.append(entry)
        for parent in parents:
            self._require(parent)
        manifest: dict[str, JsonValue] = {
            "schema": MANIFEST,
            "kind": draft.kind,
            "schema_version": spec.schema_version,
            "item_id": item,
            "title": self.redactor.redact(draft.title),
            "summary": self.redactor.redact(draft.summary),
            "fields": fields,
            "blobs": {slot: self._blob(slot, data, spec) for slot, data in draft.blobs.items()},
            "parents": list(parents),
            "relations": cast(list[JsonValue], relations),
            "world": None,
        }
        object_id = fp1(manifest)
        fresh = not self._object_path(object_id).exists()
        _write_once(self._object_path(object_id), canonical(manifest))
        self._index_object(object_id, manifest)
        if fresh:
            author: JsonObject = {"kind": who.who, "id": who.id or who.who}
            values: JsonObject = {"author": author, "created": self._now()}
            if draft.tags:
                values["tags"] = self.redactor.redact_json(list(draft.tags))[0]
            self._annotate(who, object_id, values)
        return object_id, spec

    def put(
        self, who: Principal, draft: Draft, *, on: str, expected_head: ObjectId | None
    ) -> Commit:
        """A new object on `on`, which `who` owns. `expected_head` is the head the caller read,
        None for a ref the item does not have yet; any other head refuses `stale_head`."""
        self._check_writer("put")
        self._check_owner(who, on, "put")
        spec = kind(draft.kind)
        if spec.retired:
            raise LibraryRefused("unknown_kind", f"{draft.kind} is retired")
        if on == MAIN and spec.klass != "record":
            raise LibraryRefused(
                "ref_not_owned", f"a {draft.kind} reaches main only by publish, never by put"
            )
        item = draft.item or str(uuid.uuid7())
        with self._writing():
            self._active(item)
            found = self.catalog.head(item, on)
            head = None if found is None else found[0]
            parents = list(draft.parents) if draft.parents is not None else [h for h in [head] if h]
            object_id, _ = self._mint(who, draft, item, parents)
            if object_id == head:
                return Commit(object_id, item, on, head, self._seq)
            # A replayed save is not a conflict: the ref log says this object was placed here
            # already, whether it is the head or the ref has moved past it (AD-14, F11).
            if head != expected_head and not self.ever_placed(object_id, item, on):
                raise LibraryRefused("stale_head", f"{on} of {item} is at {head}")
            return self._move(who, item, on, object_id)

    def relate(self, who: Principal, from_id: ObjectId, relation: str, to_id: ObjectId) -> str:
        self._check_writer("relate")
        name = normalised(relation)
        if name not in RELATIONS:
            raise LibraryRefused("unknown_relation", f"{relation!r} is not a relation")
        with self._writing():
            self._require(from_id)
            self._require(to_id)
            edge_id = fp1({"from": from_id, "type": name, "to": to_id})
            seen = self.catalog.db.execute(
                "SELECT 1 FROM relations WHERE from_id = ? AND type = ? AND to_id = ? "
                "AND origin = 'edge'",
                (from_id, name, to_id),
            ).fetchone()
            if seen is None:
                self._edge_seq += 1
                edge = {
                    "seq": self._edge_seq,
                    "edge_id": edge_id,
                    "from": from_id,
                    "type": name,
                    "to": to_id,
                    "writer": str(who),
                    "at": self._now(),
                }
                _append(self.edge_log, edge)
                self.catalog.index_edge(edge)
        return edge_id

    def branch(self, who: Principal, item: str, *, from_ref: str, name: str) -> Commit:
        self._check_writer("branch")
        self._check_owner(who, name, "put")
        with self._writing():
            if self.catalog.head(item, name) is not None:
                raise LibraryRefused("stale_head", f"{name} of {item} exists")
            return self._move(who, item, name, self.resolve(who, item, from_ref))

    def annotate(self, who: Principal, object_id: ObjectId, values: JsonObject) -> None:
        """Annotation fields the object's kind accepts; no new version (AD-2). The operator and
        the engine annotate anything, another principal only objects on refs it owns."""
        self._check_writer("annotate")
        with self._writing():
            row = self._require(object_id)
            spec = kind(str(row[2]))
            refused = sorted(set(values) - spec.annotations)
            if refused:
                raise LibraryRefused(
                    "annotation_not_accepted", f"a {spec.name} takes no {refused[0]}"
                )
            if who.who != "operator" and who != self.engine:
                refs = self.catalog.db.execute(
                    "SELECT DISTINCT ref FROM moves WHERE new_head = ?", (object_id,)
                )
                if not any(may_advance(who, str(r), "put", store=self.name) for (r,) in refs):
                    raise LibraryRefused("ref_not_owned", f"{who} owns no ref of {object_id}")
            self._annotate(who, object_id, cast(JsonObject, self.redactor.redact_json(values)[0]))

    def archive(
        self, who: Principal, item: str, reason: str, *, replaced_by: str | None = None
    ) -> None:
        """Archive, never delete (AD-6): a move of `refs/items/<item>/state`; no object changes."""
        self._check_writer("archive")
        self._check_owner(who, state_ref(item), "state")
        with self._writing():
            if self.catalog.state(item) is None:
                raise LibraryRefused("not_found", f"no item {item}")
            self._move(
                who, item, state_ref(item), "archived", reason=reason, replaced_by=replaced_by
            )

    def merge(
        self,
        who: Principal,
        item: str,
        *,
        from_ref: str,
        into: str,
        strategy: Strategy = "auto",
    ) -> MergeResult:
        """Merge `from_ref` into `into`. A fast-forward moves the ref; otherwise `auto` merges
        three ways, field by field and blob slot by slot, and `ff-only` stops. Anything that
        cannot merge cleanly becomes a `merge-conflict` object; a conflict never picks a side.
        The engine merges only to land a run's objects: records onto `main`, every other class
        onto `refs/drafts/<item>` (AD-18)."""
        self._check_writer("merge")
        act: Act = "land" if who == self.engine else "merge"
        self._check_owner(who, into, act)
        with self._writing():
            self._active(item)
            theirs = self.resolve(who, item, from_ref)
            if act == "land":
                klass = cast(Class, self._require(theirs)[3])
                if (into == MAIN) != (klass == "record"):
                    raise LibraryRefused("ref_not_owned", f"a run's {klass} never lands on {into}")
            found = self.catalog.head(item, into)
            ours = None if found is None else found[0]
            if ours == theirs or (ours is not None and self._descends(ours, theirs)):
                return MergeResult("up-to-date", ours or theirs)
            if ours is None or self._descends(theirs, ours):
                self._move(who, item, into, theirs, reason=f"merge {from_ref}")
                return MergeResult("fast-forward", theirs)
            if strategy == "ff-only":
                return self._conflict(who, item, into, None, ours, theirs, [{"path": "history"}])
            return self._three_way(who, item, into, from_ref, ours, theirs)

    def _descends(self, child: ObjectId, ancestor: ObjectId) -> bool:
        return ancestor in self._ancestry(child)

    def _ancestry(self, start: ObjectId) -> dict[ObjectId, int]:
        """Every ancestor of `start` (itself included) and its distance."""
        seen = {start: 0}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for parent in self.catalog.parents(node):
                if parent not in seen:
                    seen[parent] = seen[node] + 1
                    queue.append(parent)
        return seen

    def _three_way(
        self, who: Principal, item: str, into: str, from_ref: str, ours: ObjectId, theirs: ObjectId
    ) -> MergeResult:
        mine, other = self._ancestry(ours), self._ancestry(theirs)
        common = [(mine[o] + other[o], o) for o in mine.keys() & other.keys()]
        base = min(common)[1] if common else None
        merged = self._merged(base, ours, theirs)
        if merged.entries:
            return self._conflict(who, item, into, base, ours, theirs, merged.entries)
        return self._land(who, item, into, merged, ours, theirs, reason=f"merge {from_ref}")

    def _merged(self, base: ObjectId | None, ours: ObjectId, theirs: ObjectId) -> _Merged:
        """The three-way merge of two versions, field by field and slot by slot, with nothing
        minted. `merge` lands it when nothing clashes; `resolve` computes it again and fills in
        the clashing entries, so a resolution keeps every clean change of both sides."""
        b = self._view(base) if base else None
        o, t = self._view(ours), self._view(theirs)
        entries: list[JsonObject] = []

        def pick(path: str, base_v: object, ours_v: object, theirs_v: object) -> object:
            if theirs_v in (ours_v, base_v):
                return ours_v
            if ours_v == base_v:
                return theirs_v
            entries.append({"path": path})
            return ours_v

        fields: JsonObject = {}
        for key in sorted(o.fields.keys() | t.fields.keys()):
            value = pick(
                f"fields.{key}",
                b.fields.get(key) if b else None,
                o.fields.get(key),
                t.fields.get(key),
            )
            if value is not None:
                fields[key] = cast(JsonValue, value)
        title = pick("title", b.title if b else None, o.title, t.title)
        summary = pick("summary", b.summary if b else None, o.summary, t.summary)
        blobs: dict[str, BlobRef] = {}
        keyed: dict[str, JsonObject] = {}
        spec = kind(o.kind)
        for slot in sorted(o.blobs.keys() | t.blobs.keys()):
            ours_b, theirs_b = o.blobs.get(slot), t.blobs.get(slot)
            base_b = b.blobs.get(slot) if b else None
            ours_id, theirs_id = ours_b and ours_b.blob_id, theirs_b and theirs_b.blob_id
            base_id = base_b and base_b.blob_id
            media = cast(BlobView, ours_b or theirs_b).media_type
            mergeable = media.startswith("text/") or media == JSON_MEDIA
            if (
                ours_id
                and theirs_id
                and mergeable
                and ours_id != theirs_id
                and base_id not in (ours_id, theirs_id)
            ):
                landed, partial, found = self._merge_slot(
                    spec, slot, media, base_id, ours_id, theirs_id
                )
                entries.extend(found)
                if landed is not None:
                    blobs[slot] = BlobRef(landed)
                if partial is not None:
                    keyed[slot] = partial
                continue
            chosen = pick(f"blobs.{slot}", base_id, ours_id, theirs_id)
            if isinstance(chosen, str):
                blobs[slot] = BlobRef(chosen)
        return _Merged(o.kind, str(title), str(summary), fields, blobs, keyed, entries)

    def _merge_slot(
        self,
        spec: Kind,
        slot: str,
        media: str,
        base: BlobId | None,
        ours: BlobId,
        theirs: BlobId,
    ) -> tuple[BlobId | None, JsonObject | None, list[JsonObject]]:
        """One slot changed on both sides: keys for a JSON object, lines for any other text.

        A clean merge returns its blob. A JSON clash returns the object merged except for the
        clashing keys, and every clash returns its `merge-conflict` entries (AD-30)."""
        mine, other = self._slot_bytes(spec, slot, ours), self._slot_bytes(spec, slot, theirs)
        before = b"" if base is None else self._slot_bytes(spec, slot, base)
        if media == JSON_MEDIA:
            sides = [_json_object(data) for data in (before or b"{}", mine, other)]
            if all(side is not None for side in sides):
                return self._merge_keys(spec, slot, *cast(list[JsonObject], sides))
        merged, conflicts = merge_text(mine, before, other)
        if not conflicts:
            return self._slot_blob(spec, slot, merged), None, []
        entry: JsonObject = {
            "path": f"blobs.{slot}",
            "slot": slot,
            "media_type": media,
            "conflicts": conflicts,
            "text": merged.decode("utf-8", "replace"),
        }
        return None, None, [entry]

    def _merge_keys(
        self, spec: Kind, slot: str, base: JsonObject, ours: JsonObject, theirs: JsonObject
    ) -> tuple[BlobId | None, JsonObject | None, list[JsonObject]]:
        """A JSON object slot key by key, with one entry per clashing key (AD-30)."""
        merged: JsonObject = {}
        entries: list[JsonObject] = []
        for key in sorted(ours.keys() | theirs.keys()):
            chosen = _pick_key(
                ours.get(key, ABSENT), theirs.get(key, ABSENT), base.get(key, ABSENT)
            )
            if chosen is CLASH:
                entries.append(
                    {
                        "path": f"blobs.{slot}.{key}",
                        "slot": slot,
                        "media_type": JSON_MEDIA,
                        "key": key,
                        "base": base.get(key),
                        "ours": ours.get(key),
                        "theirs": theirs.get(key),
                    }
                )
            elif chosen is not ABSENT:
                merged[key] = cast(JsonValue, chosen)
        if entries:
            return None, merged, entries
        return self._slot_blob(spec, slot, _canonical_json(merged)), None, []

    def _slot_bytes(self, spec: Kind, slot: str, blob_id: BlobId) -> bytes:
        return self.read_blob(blob_id, transient=spec.slot(slot).transient)

    def _slot_blob(self, spec: Kind, slot: str, data: bytes) -> BlobId:
        """Write bytes as the slot's blob and name it, redacted the way `_blob` redacts."""
        return str(self._blob(slot, data, spec)["sha256"])

    def _land(
        self,
        who: Principal,
        item: str,
        into: str,
        merged: _Merged,
        ours: ObjectId,
        theirs: ObjectId,
        *,
        reason: str,
        also: Sequence[Relation] = (),
    ) -> MergeResult:
        """Mint the merged version with both parents and move `into` to it."""
        o, t = self._view(ours), self._view(theirs)
        relations: dict[Relation, None] = dict.fromkeys([*o.relations, *t.relations])
        relations |= dict.fromkeys([("merged-from", ours), ("merged-from", theirs), *also])
        draft = Draft(
            merged.kind,
            item,
            merged.title,
            merged.summary,
            merged.fields,
            merged.blobs,
            list(relations),
            [ours, theirs],
        )
        object_id, _ = self._mint(who, draft, item, [ours, theirs])
        self._move(who, item, into, object_id, reason=reason)
        return MergeResult("merged", object_id)

    def _conflict(
        self,
        who: Principal,
        item: str,
        into: str,
        base: ObjectId | None,
        ours: ObjectId,
        theirs: ObjectId,
        entries: list[JsonObject],
    ) -> MergeResult:
        ref = f"refs/conflicts/{item}/{self.catalog.refs_like(f'refs/conflicts/{item}/') + 1}"
        fields: JsonObject = {
            "item": item,
            "base": base,
            "ours": ours,
            "theirs": theirs,
            "into": into,
            "entries": cast(list[JsonValue], entries),
        }
        draft = Draft("merge-conflict", title=f"Conflict merging into {into}", fields=fields)
        conflict = str(uuid.uuid7())
        object_id, _ = self._mint(who, draft, conflict, [])
        self._move(who, conflict, ref, object_id, reason=f"conflict on {item}")
        return MergeResult("conflict", object_id)

    def checkout(self, who: Principal, item: str, ref: str = MAIN) -> Path:
        """A working copy of `item` at `ref`, in the folder of the ref `who` writes to (AD-20).
        The checkout is never evidence; `commit` reads it back."""
        head = self.resolve(who, item, ref)
        view = self.get(who, head, blobs="fetch")
        target = own_ref(who, item, ref)
        folder = self.root / "checkout" / target / item
        shutil.rmtree(folder, ignore_errors=True)
        (folder / "blobs").mkdir(parents=True)
        manifest = {
            "kind": view.kind,
            "title": view.title,
            "summary": view.summary,
            "fields": view.fields,
        }
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for slot, data in view.data.items():
            path = folder / "blobs" / slot
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        found = self.catalog.head(item, target)
        state = {"item": item, "ref": target, "base": head, "head": found and found[0]}
        (folder / CHECKOUT_FILE).write_text(json.dumps(state), encoding="utf-8")
        return folder

    def conflicts(self, who: Principal, item: str | None = None) -> list[ObjectView]:
        """The open `merge-conflict` objects, newest first, of one item or of the whole store.

        A conflict is open until `resolve` annotates it, so the inbox shows exactly the ones that
        still need a side (AD-30)."""
        rows = self.catalog.db.execute(
            "SELECT head FROM heads WHERE ref LIKE 'refs/conflicts/%' ORDER BY rowid DESC"
        ).fetchall()
        found: list[ObjectView] = []
        with self._mutex:
            for (head,) in rows:
                view = self._view(str(head))
                if item is not None and str(view.fields.get("item")) != item:
                    continue
                if "resolved_by" not in view.annotations:
                    found.append(view)
        return found

    def resolve_conflict(
        self,
        who: Principal,
        conflict: ObjectId,
        *,
        text: str | None = None,
        values: Mapping[str, JsonValue] | None = None,
    ) -> MergeResult:
        """Close a `merge-conflict`: land the merged version on `into` and annotate the conflict.

        `values` answers each entry by its path (`blobs.<slot>.<key>` for a JSON key, `fields.<f>`,
        `title`, `blobs.<slot>` for a text slot's resolved text or a binary slot's chosen blob id).
        `text` is shorthand for the one text slot. The merge is computed again from the conflict's
        base and sides, so every clean change of both sides lands too. An entry left open refuses
        `merge_conflict` naming it, so a resolution never guesses a side (AD-30)."""
        self._check_writer("resolve")
        view = self._view(conflict)
        if view.kind != "merge-conflict":
            raise LibraryRefused("not_found", f"{conflict} is a {view.kind}, not a merge conflict")
        if "resolved_by" in view.annotations:
            raise LibraryRefused("merge_conflict", f"{conflict} is already resolved")
        item, into = str(view.fields["item"]), str(view.fields["into"])
        ours, theirs = str(view.fields["ours"]), str(view.fields["theirs"])
        base = view.fields.get("base")
        if base is None and view.fields["entries"] == [{"path": "history"}]:
            raise LibraryRefused(
                "merge_conflict", f"{conflict} is an ff-only stop; merge again with strategy auto"
            )
        self._check_owner(who, into, "merge")
        with self._writing():
            self._active(item)
            held = self.catalog.head(item, into)
            if held is None or held[0] != ours:
                raise LibraryRefused(
                    "merge_conflict", f"{into} moved since {conflict}; merge again"
                )
            merged = self._merged(None if base is None else str(base), ours, theirs)
            spec = kind(merged.kind)
            given = dict(values or {})
            texts = [str(entry["path"]) for entry in merged.entries if "text" in entry]
            if text is not None:
                if len(texts) != 1:
                    raise LibraryRefused(
                        "merge_conflict",
                        f"{conflict} holds {len(texts)} text slots in conflict; answer each by "
                        "path in values",
                    )
                given[texts[0]] = text
            sides = (self._view(ours), self._view(theirs))
            for entry in merged.entries:
                path = str(entry["path"])
                if path not in given:
                    raise LibraryRefused("merge_conflict", f"{conflict} needs a value for {path}")
                value = given[path]
                slot = str(entry.get("slot", path.removeprefix("blobs.")))
                if "text" in entry:
                    merged.blobs[slot] = BlobRef(self._slot_blob(spec, slot, str(value).encode()))
                elif "key" in entry:
                    merged.keyed[slot][str(entry["key"])] = value
                elif path.startswith("fields."):
                    merged.fields[path.removeprefix("fields.")] = value
                elif path == "title":
                    merged.title = str(value)
                elif path == "summary":
                    merged.summary = str(value)
                else:
                    held_ids = {side.blobs[slot].blob_id for side in sides if slot in side.blobs}
                    if value not in held_ids:
                        raise LibraryRefused(
                            "merge_conflict", f"{path} takes the blob id of one side"
                        )
                    merged.blobs[slot] = BlobRef(str(value))
            for slot, partial in merged.keyed.items():
                merged.blobs[slot] = BlobRef(self._slot_blob(spec, slot, _canonical_json(partial)))
            result = self._land(
                who,
                item,
                into,
                merged,
                ours,
                theirs,
                reason=f"resolve {conflict}",
                also=[("resolves", conflict)],
            )
            self._annotate(who, conflict, {"resolved_by": result.object_id})
        return result

    def history_of(self, who: Principal, item: str, ref: str | None = None) -> list[HistoryEntry]:
        """The item's ref log, oldest first: a READ, answered from the moves this store wrote
        (AD-30). `ref` narrows it to one ref; without it every ref the item moved on is listed."""
        query = "SELECT seq, item, ref, principal, prev_head, new_head, at, reason FROM moves "
        args: tuple[str, ...] = (item,)
        query += "WHERE item = ?"
        if ref is not None:
            query += " AND ref = ?"
            args += (ref,)
        rows = self.catalog.db.execute(query + " ORDER BY seq", args).fetchall()
        return [
            HistoryEntry(
                int(seq),
                str(moved_item),
                str(moved_ref),
                str(principal),
                None if prev is None else str(prev),
                str(new),
                str(at),
                None if reason is None else str(reason),
            )
            for seq, moved_item, moved_ref, principal, prev, new, at, reason in rows
        ]

    def blame(self, who: Principal, item: str, slot: str, ref: str = MAIN) -> Blame:
        """Which version last changed each line of a text slot, computed at read (AD-30).

        A line keeps travelling back through whichever parent the diff says already held it, so
        a line a merge carried in is blamed on the side that wrote it. Nothing is written."""
        head = self.resolve(who, item, ref)
        with self._mutex:
            text: dict[str, list[str]] = {}
            parents: dict[str, tuple[str, ...]] = {}
            pending = [head]
            while pending:
                here = pending.pop()
                if here in text:
                    continue
                view = self._view(here)
                blob = view.blobs.get(slot)
                if blob is None or not blob.media_type.startswith("text/"):
                    continue
                raw = self._slot_bytes(kind(view.kind), slot, blob.blob_id)
                text[here] = lines(raw.decode("utf-8", "replace"))
                parents[here] = view.parents
                pending.extend(view.parents)
            if head not in text:
                raise LibraryRefused("not_found", f"{head} holds no text slot {slot}")
            origin = origins(head, text, parents)
        blamed: list[BlameLine] = []
        for index, line in enumerate(text[head]):
            author, at = self._author(origin[index], item)
            blamed.append(BlameLine(index + 1, line.rstrip("\r\n"), origin[index], author, at))
        return Blame(item, slot, ref, head, tuple(blamed))

    def _author(self, object_id: ObjectId, item: str) -> tuple[str, str]:
        """Who first placed this version, and when: the write that changed the line.

        The first move of the object is its birth, which names the chat or run that made it; a
        later move of the same object (a fast-forward) is another ref carrying it, not an edit."""
        row = self.catalog.db.execute(
            "SELECT principal, at FROM moves WHERE new_head = ? AND item = ? "
            "ORDER BY seq ASC LIMIT 1",
            (object_id, item),
        ).fetchone()
        if row is not None:
            return str(row[0]), str(row[1])
        view = self._view(object_id)
        author = cast(JsonObject, view.annotations.get("author") or {})
        return str(author.get("id", "")), str(view.annotations.get("created", ""))

    def commit(
        self,
        who: Principal,
        checkout: Path,
        message: str = "",
        *,
        expected_head: ObjectId | None = None,
    ) -> Commit:
        """Put the edited working copy onto its ref, parented on the object it was checked out
        from. `expected_head` defaults to the ref's head when it was checked out."""
        state = cast(dict[str, Any], json.loads((checkout / CHECKOUT_FILE).read_text("utf-8")))
        manifest = cast(dict[str, Any], json.loads((checkout / "manifest.json").read_text("utf-8")))
        blobs = {
            path.relative_to(checkout / "blobs").as_posix(): path.read_bytes()
            for path in sorted((checkout / "blobs").rglob("*"))
            if path.is_file()
        }
        draft = Draft(
            str(manifest["kind"]),
            str(state["item"]),
            str(manifest["title"]),
            str(manifest["summary"]),
            cast(JsonObject, manifest["fields"]),
            blobs,
            parents=[str(state["base"])],
        )
        expected = expected_head if expected_head is not None else state["head"]
        done = self.put(who, draft, on=str(state["ref"]), expected_head=expected)
        if message:
            self.annotate(who, done.object_id, {"tags": [f"commit: {message}"]})
        return done

    def resolve(
        self, who: Principal, item: str, ref: str = MAIN, *, as_of: AsOf | None = None
    ) -> ObjectId:
        with self._mutex:
            if as_of is None:
                found = self.catalog.head(item, ref)
                head = None if found is None else found[0]
            else:
                row = self.catalog.db.execute(
                    "SELECT new_head FROM moves WHERE item = ? AND ref = ? AND seq <= ? "
                    "ORDER BY seq DESC LIMIT 1",
                    (item, ref, self._cut(as_of)[0]),
                ).fetchone()
                head = None if row is None else str(row[0])
        if head is None:
            raise LibraryRefused("not_found", f"{item} has no {ref}")
        return head

    def _cut(self, as_of: AsOf) -> tuple[int, str]:
        """The last ref-log position and the time `as_of` names; `(0, "")` before the first."""
        db = self.catalog.db
        if isinstance(as_of, int):
            row = db.execute(
                "SELECT seq, at FROM moves WHERE seq <= ? ORDER BY seq DESC LIMIT 1", (as_of,)
            ).fetchone()
            return (0, "") if row is None else (int(row[0]), str(row[1]))
        at = as_of.astimezone(UTC).isoformat().replace("+00:00", "Z")
        (seq,) = db.execute(
            "SELECT coalesce(max(seq), 0) FROM moves WHERE julianday(at) <= julianday(?)", (at,)
        ).fetchone()
        return int(seq), at

    def _placed_by(self, object_id: ObjectId, seq: int) -> bool:
        """Whether a move at or before `seq` put `object_id` on a ref. The outbox asks the same
        question of one ref by name, in `ever_placed`."""
        row = self.catalog.db.execute(
            "SELECT 1 FROM moves WHERE new_head = ? AND seq <= ? LIMIT 1", (object_id, seq)
        ).fetchone()
        return row is not None

    def ever_placed(self, object_id: ObjectId, item: str, ref: str) -> bool:
        """Whether this store's ref log ever put `object_id` on `item`'s `ref` (AD-14, F11).

        This is the outbox's whole evidence: a save whose reply was lost is done, and the entry
        is dropped, without the head comparison that would call it a conflict.
        """
        row = self.catalog.db.execute(
            "SELECT 1 FROM moves WHERE new_head = ? AND item = ? AND ref = ? LIMIT 1",
            (object_id, item, ref),
        ).fetchone()
        return row is not None

    def _view(self, object_id: ObjectId) -> ObjectView:
        row = self._require(object_id)
        _, item, kind_name, klass, title, summary, fields, blobs, parents, relations = row
        return ObjectView(
            object_id,
            str(item),
            str(kind_name),
            cast(Class, klass),
            str(title),
            str(summary),
            json.loads(fields),
            {
                slot: BlobView(spec["sha256"], spec["size"], spec["media_type"])
                for slot, spec in cast(dict[str, dict[str, Any]], json.loads(blobs)).items()
            },
            tuple(json.loads(parents)),
            tuple((r["type"], r["to"]) for r in json.loads(relations)),
            self.catalog.annotations(object_id),
            {r["to"]: r["locator"] for r in json.loads(relations) if "locator" in r},
        )

    def get(
        self,
        who: Principal,
        object_id: ObjectId,
        *,
        blobs: Literal["meta", "fetch"] = "meta",
        as_of: AsOf | None = None,
    ) -> ObjectView:
        """The object; with `as_of`, refused `not_found` unless a ref held it by then, and its
        annotations as they stood then."""
        with self._mutex:
            view = self._view(object_id)
            if as_of is not None:
                seq, at = self._cut(as_of)
                if not self._placed_by(object_id, seq):
                    raise LibraryRefused("not_found", f"no object {object_id} as of {as_of}")
                rows = self.catalog.db.execute(
                    "SELECT key, value FROM annotations WHERE object_id = ? "
                    "AND julianday(at) <= julianday(?) ORDER BY seq",
                    (object_id, at),
                )
                view = replace(view, annotations={str(k): json.loads(v) for k, v in rows})
        if blobs == "meta":
            return view
        spec = kind(view.kind)
        data: dict[str, bytes] = {}
        purged: set[str] = set()
        for slot, blob in view.blobs.items():
            try:
                data[slot] = self.read_blob(blob.blob_id, transient=spec.slot(slot).transient)
            except LibraryRefused as refused:
                if refused.code != "blob_purged":
                    raise
                purged.add(slot)
        return replace(view, data=data, purged=frozenset(purged))

    def read_blob(self, blob_id: str, *, transient: bool = False) -> bytes:
        """The blob's bytes. A purge tombstone refuses `blob_purged` (AD-6); on a replica or a
        cache a durable blob it does not hold comes from `upstream` and stays cached, as a cache
        copy it may give up at any time (AD-10)."""
        if (self.tombstones / f"{blob_id.removeprefix('sha256:')}.json").exists():
            raise LibraryRefused("blob_purged", f"{blob_id} was purged by the operator")
        path = self._held(blob_id) if not transient else self._blob_path(blob_id, transient=True)
        if path is None or not path.exists():
            if transient or self.upstream is None:
                raise LibraryRefused("blob_unavailable", f"no blob {blob_id}")
            fetched = self.upstream.fetch(blob_id)
            if fetched is None:
                raise LibraryRefused("blob_unavailable", f"no blob {blob_id}")
            if f"sha256:{sha256(fetched).hexdigest()}" != blob_id:
                raise LibraryRefused("corrupt_blob", f"{blob_id} does not hash to its name")
            if self.too_new is None:
                _write_once(self._blob_path(blob_id, transient=False, fetched=True), fetched)
                self._reindex_blob(blob_id)
            return fetched
        data = path.read_bytes()
        if f"sha256:{sha256(data).hexdigest()}" != blob_id:
            raise LibraryRefused("corrupt_blob", f"{blob_id} does not hash to its name")
        return data

    def has_blob(self, blob_id: str) -> bool:
        """Whether the bytes are here, for a replicator deciding what to copy."""
        return self._held(blob_id) is not None

    def blob_class(self, blob_id: str) -> Literal["born", "cache"] | None:
        """`born` when the bytes were made, uploaded or written on this store, `cache` when they
        were fetched or synced here, and None when this store does not hold them (AD-10, N3)."""
        if self._blob_path(blob_id, transient=False).exists():
            return "born"
        if self._blob_path(blob_id, transient=False, fetched=True).exists():
            return "cache"
        return None

    def cached_blob_ids(self) -> list[str]:
        return sorted(
            f"sha256:{path.name}"
            for path in (self.root / "blobs" / "fetched").glob("??/??/*")
            if path.is_file()
        )

    def evict_cache(self, want: int = 0) -> list[str]:
        """Drop cache copies, oldest first, until `want` bytes are back (AD-10; D-11's table).

        A cache copy comes back by hash on the next open. A blob born here never goes: it is one
        of the copies that makes the bytes durable, and only replication removes it.
        """
        taken: list[str] = []
        freed = 0
        for blob_id in self.cached_blob_ids():
            if want > 0 and freed >= want:
                break
            path = self._blob_path(blob_id, transient=False, fetched=True)
            with suppress(OSError):
                size = path.stat().st_size
                path.unlink()
                freed += size
                taken.append(blob_id)
        return taken

    def purged(self, blob_id: str) -> bool:
        """Whether an operator purge tombstoned `blob_id` on this store (AD-6)."""
        return (self.tombstones / f"{blob_id.removeprefix('sha256:')}.json").exists()

    def search(
        self,
        who: Principal,
        text: str,
        *,
        kind: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
        as_of: AsOf | None = None,
    ) -> list[Hit]:
        """FTS5 over the objects; with `as_of`, over the objects that were the head of a ref
        then, and the items active then. `offset` reads the next page of the same answer."""
        with self._mutex:
            if as_of is None:
                return self.catalog.search(text, kind, include_archived, limit, offset)
            words = norm(text).split()
            if not words:
                raise LibraryRefused("invalid_search", "the search names no word")
            seq, _ = self._cut(as_of)
            rows = self.catalog.db.execute(
                "SELECT s.object_id, s.item, s.kind, s.title, bm25(search) AS rank FROM search s "
                "WHERE search MATCH :query AND (:kind IS NULL OR s.kind = :kind) "
                "AND EXISTS (SELECT 1 FROM moves m WHERE m.new_head = s.object_id "
                "  AND m.seq <= :seq AND NOT EXISTS (SELECT 1 FROM moves n WHERE n.item = m.item"
                "  AND n.ref = m.ref AND n.seq > m.seq AND n.seq <= :seq)) "
                "AND (:archived OR coalesce((SELECT new_head FROM moves WHERE item = s.item "
                "  AND ref = 'refs/items/' || s.item || '/state' AND seq <= :seq "
                "  ORDER BY seq DESC LIMIT 1), 'active') <> 'archived') "
                "ORDER BY rank, s.item, s.object_id",
                {
                    "query": " ".join(f'"{word}"' for word in words),
                    "kind": kind,
                    "seq": seq,
                    "archived": include_archived,
                },
            )
            best: dict[str, Hit] = {}
            for object_id, item, found_kind, title, rank in rows:
                best.setdefault(
                    str(item), Hit(str(object_id), str(item), str(found_kind), str(title), -rank)
                )
            return list(best.values())[offset : offset + limit]

    def search_runs(self, who: Principal, text: str, workflow: str | None = None) -> list[Hit]:
        hits = self.search(who, text, kind="workflow-run", limit=1000)
        if workflow is None:
            return hits
        return [h for h in hits if self._view(h.object_id).fields.get("workflow_item") == workflow]

    def walk(
        self,
        who: Principal,
        start: Sequence[ObjectId],
        types: Sequence[str] = (),
        direction: Literal["out", "in", "both"] = "out",
        depth: int = 2,
        *,
        as_of: AsOf | None = None,
    ) -> list[Step]:
        """With `as_of`, only edges written by then, to objects a ref held by then."""
        wanted = {normalised(t) for t in types}
        seen = set(start)
        steps: list[Step] = []
        frontier = list(start)
        with self._mutex:
            cut = None if as_of is None else self._cut(as_of)
            for level in range(1, depth + 1):
                reached: list[str] = []
                for node in frontier:
                    found = [
                        *(self._relations(node, False, cut) if direction != "in" else []),
                        *(self._relations(node, True, cut) if direction != "out" else []),
                    ]
                    for other, relation, origin in found:
                        if (wanted and relation not in wanted) or other in seen:
                            continue
                        seen.add(other)
                        reached.append(other)
                        steps.append(Step(other, relation, cast(Any, origin), level))
                frontier = reached
        return steps

    def _relations(
        self, node: ObjectId, reverse: bool, cut: tuple[int, str] | None
    ) -> list[tuple[str, str, str]]:
        if cut is None:
            return self.catalog.relations_of(node, reverse=reverse)
        mine, other = ("to_id", "from_id") if reverse else ("from_id", "to_id")
        rows = self.catalog.db.execute(
            f"SELECT {other}, type, origin FROM relations WHERE {mine} = ? "  # noqa: S608
            "AND (origin = 'birth' OR julianday(at) <= julianday(?)) "
            f"AND EXISTS (SELECT 1 FROM moves m WHERE m.new_head = {other} AND m.seq <= ?) "
            "ORDER BY coalesce(seq, 0)",
            (node, cut[1], cut[0]),
        )
        return [(str(a), str(b), str(c)) for a, b, c in rows]

    def marks(self, who: Principal, object_id: ObjectId) -> Marks:
        """The worst mark on `object_id` or upstream of it, with its path (AD-22)."""
        with self._mutex:
            self._require(object_id)
            return marks(self.catalog.db, object_id)

    def mark(self, who: Principal, item: str, quarantined: bool, reason: str) -> None:
        """Set or clear `quarantined` on `item`: a move of `refs/items/<item>/marks`, by the
        operator alone (AD-22)."""
        self._check_writer("mark")
        if who.who != "operator":
            raise LibraryRefused("ref_not_owned", f"{who} may not mark {item}; the operator marks")
        with self._writing():
            if self.catalog.state(item) is None:
                raise LibraryRefused("not_found", f"no item {item}")
            value = QUARANTINED if quarantined else CLEAR
            self._move(who, item, marks_ref(item), value, reason=reason)

    def ground(self, who: Principal, text: str) -> Grounding:
        """Items whose title, tag or alias occurs in `text`, longest alias first; no model."""
        rest = f" {norm(text)} "
        items: list[str] = []
        with self._mutex:
            for alias, item in self.catalog.aliases():
                if f" {alias} " in rest and self.catalog.state(item) == "active":
                    rest = rest.replace(f" {alias} ", "  ")
                    if item not in items:
                        items.append(item)
        return Grounding(tuple(items), "grounded" if items else "no_entry_point")

    def find_by_intent(self, who: Principal, intent_key: str) -> list[ObjectId]:
        """Active objects annotated with `intent_key` whose producing run passed (engine L6)."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT a.object_id FROM annotations a "
                "JOIN objects o ON o.object_id = a.object_id "
                "JOIN items i ON i.item = o.item AND i.state = 'active' "
                "WHERE a.key = 'intent_key' AND a.value = ? AND a.seq = ("
                "  SELECT max(seq) FROM annotations WHERE object_id = a.object_id "
                "  AND key = 'intent_key') "
                "AND EXISTS (SELECT 1 FROM relations r JOIN objects run ON run.object_id = r.to_id "
                "  WHERE r.from_id = a.object_id AND r.type = 'produced-by' "
                "  AND json_extract(run.fields, '$.status') = 'passed') "
                "ORDER BY a.seq",
                (json.dumps(intent_key),),
            )
            return [str(object_id) for (object_id,) in rows]

    def head(self, item: str, ref: str) -> tuple[ObjectId, int] | None:
        """The head of `ref` for `item` and how many times it has moved."""
        with self._mutex:
            return self.catalog.head(item, ref)

    def placed(self, item: str, kind_name: str, ref: str | None) -> list[tuple[ObjectId, str]]:
        """Objects of `kind_name` that were ever a head of `item` (on `ref` when given), in the
        order they first became one, each with the first ref it reached."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.new_head, m.ref FROM moves m JOIN objects o ON o.object_id = m.new_head "
                "WHERE m.item = ? AND o.kind = ? AND (? IS NULL OR m.ref = ?) ORDER BY m.seq",
                (item, kind_name, ref, ref),
            )
            seen: dict[str, str] = {}
            for object_id, first in rows:
                seen.setdefault(str(object_id), str(first))
            return list(seen.items())

    def placement(self, object_id: ObjectId) -> tuple[str, str, str] | None:
        """`(ref, principal, at)` of the first move to `object_id`, `main` if it ever reached
        `main`."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT ref, principal, at FROM moves WHERE new_head = ? ORDER BY seq",
                (object_id,),
            ).fetchall()
        if not rows:
            return None
        ref, principal, at = rows[0]
        if any(r[0] == MAIN for r in rows):
            ref = MAIN
        return str(ref), str(principal), str(at)

    def history(self, item: str) -> list[tuple[str, str, str]]:
        """`(kind, ref, principal)` of every move of `item` to an object, oldest first."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT o.kind, m.ref, m.principal FROM moves m "
                "JOIN objects o ON o.object_id = m.new_head WHERE m.item = ? ORDER BY m.seq",
                (item,),
            )
            return [(str(kind), str(ref), str(who)) for kind, ref, who in rows]

    def placements(self, after: int = 0) -> list[dict[str, Any]]:
        """The ref moves after `after` that placed an object for the first time."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.seq, m.item, m.ref, m.new_head, o.kind FROM moves m "
                "JOIN objects o ON o.object_id = m.new_head WHERE m.seq > ? "
                "AND m.seq = (SELECT min(seq) FROM moves WHERE new_head = m.new_head) "
                "ORDER BY m.seq",
                (after,),
            )
            keys = ("seq", "item", "ref", "new_head", "kind")
            return [dict(zip(keys, row, strict=True)) for row in rows]

    def main_moves(self, after: int = 0) -> list[dict[str, Any]]:
        """The moves after `after` that put an object on `main` for the first time. An object
        put on a run's ref first is listed here only once a landing moves it onto `main`."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.seq, m.item, m.ref, m.new_head, o.kind FROM moves m "
                "JOIN objects o ON o.object_id = m.new_head WHERE m.seq > ? AND m.ref = ? "
                "AND m.seq = (SELECT min(seq) FROM moves WHERE new_head = m.new_head "
                "AND ref = m.ref) ORDER BY m.seq",
                (after, MAIN),
            )
            keys = ("seq", "item", "ref", "new_head", "kind")
            return [dict(zip(keys, row, strict=True)) for row in rows]

    def last_seq(self) -> int:
        """The position of the newest ref move this store wrote or took in."""
        with self._mutex:
            return self.catalog.last_seq()

    def park_entry(
        self,
        item: str,
        ref: str,
        *,
        expected_head: str | None,
        intended: str,
        who: Principal | None = None,
    ) -> str:
        """Mint a `merge-conflict` for one save that can no longer apply (AD-26, AD-14).

        The head moved under an entry whose object was never placed, so nobody can say which side
        is right: the entry is parked on `refs/conflicts/<item>/<n>` and he picks.
        """
        self._check_writer("a conflict")
        number = self.catalog.refs_like(f"refs/conflicts/{item}/") + 1
        target = f"refs/conflicts/{item}/{number}"
        fields: JsonObject = {
            "base": expected_head,
            "ours": intended,
            "theirs": "",
            "into": ref,
            "entries": cast(list[JsonValue], [{"path": ref, "item": item}]),
        }
        draft = Draft(
            "merge-conflict",
            title=f"Conflict on {ref} of {item}",
            summary="a save replayed onto a head that had moved; he picks the side",
            fields=fields,
        )
        with self._writing():
            object_id, _ = self._mint(who or self.engine, draft, item, [])
            self._move(who or self.engine, item, target, object_id, reason=f"conflict on {item}")
        return target

    def edges_since(self, after: int = 0) -> list[dict[str, Any]]:
        """The after-birth edges recorded after ref-log position `after`, the sync's edge tail."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT seq, edge_id, from_id, type, to_id, writer, at FROM relations "
                "WHERE origin = 'edge' AND seq > ? ORDER BY seq",
                (after,),
            )
            keys = ("seq", "edge_id", "from", "type", "to", "writer", "at")
            return [dict(zip(keys, row, strict=True)) for row in rows]

    def ingest_edge(self, edge: Mapping[str, Any]) -> bool:
        """Record a peer's after-birth edge here, once. True when this call added it."""
        edge_id = str(edge["edge_id"])
        seen = self.catalog.db.execute(
            "SELECT 1 FROM relations WHERE edge_id = ? AND origin = 'edge'", (edge_id,)
        ).fetchone()
        if seen is not None:
            return False
        self._refuse_too_new("an edge copy")
        with self._writing():
            self._edge_seq += 1
            entry = {
                "seq": self._edge_seq,
                "edge_id": edge_id,
                "from": str(edge["from"]),
                "type": str(edge["type"]),
                "to": str(edge["to"]),
                "writer": str(edge.get("writer") or "hub"),
                "at": str(edge.get("at") or self._now()),
            }
            _append(self.edge_log, entry)
            self.catalog.index_edge(entry)
        return True

    def heads_on(self, ref: str) -> list[tuple[str, ObjectId]]:
        with self._mutex:
            return self.catalog.heads_on(ref)

    def has_item(self, item: str) -> bool:
        with self._mutex:
            return self.catalog.state(item) is not None

    def edges_of(
        self, object_id: ObjectId, *, reverse: bool
    ) -> list[tuple[str, str, str, str, str]]:
        """After-birth edges `(from, type, to, writer, at)` out of `object_id`, or into it."""
        mine = "to_id" if reverse else "from_id"
        with self._mutex:
            rows = self.catalog.db.execute(
                f"SELECT from_id, type, to_id, writer, at FROM relations WHERE {mine} = ? "  # noqa: S608
                "AND origin = 'edge' ORDER BY seq",
                (object_id,),
            )
            return [(str(a), str(b), str(c), str(d), str(e)) for a, b, c, d, e in rows]

    def with_field(self, kind_name: str, key: str, value: str) -> list[ObjectId]:
        """Objects of `kind_name` whose `fields.<key>` is `value`, in the order they were placed."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT o.object_id FROM objects o JOIN moves m ON m.new_head = o.object_id "
                "WHERE o.kind = ? AND json_extract(o.fields, '$.' || ?) = ? "
                "GROUP BY o.object_id ORDER BY min(m.seq)",
                (kind_name, key, value),
            )
            return [str(object_id) for (object_id,) in rows]

    def advance(
        self,
        who: Principal,
        item: str,
        ref: str,
        new_head: ObjectId,
        *,
        expected_head: ObjectId | None,
    ) -> Commit:
        """Move `ref` to an object already stored, by compare-and-swap (AD-2)."""
        self._check_writer("advance")
        self._check_owner(who, ref, "put")
        with self._writing():
            self._require(new_head)
            found = self.catalog.head(item, ref)
            head = None if found is None else found[0]
            if head != expected_head:
                raise LibraryRefused("stale_head", f"{ref} of {item} is at {head}")
            if head == new_head:
                return Commit(new_head, item, ref, head, self._seq)
            return self._move(who, item, ref, new_head)

    def put_transient(self, who: Principal, ref: str, data: bytes) -> str:
        """A transient blob (a checkpoint) for a run that owns `ref`: kept on this store only,
        never bucketed (AD-6)."""
        self._check_writer("put_transient")
        self._check_owner(who, ref, "put")
        with self._mutex:
            data = self._redacted(data)
            blob_id = f"sha256:{sha256(data).hexdigest()}"
            _write_once(self._blob_path(blob_id, transient=True), data)
            return blob_id

    def claim(self, who: Principal, intent_key: str, run_id: str, ttl: int) -> Claim:
        """AD-24's compare-and-swap on the transient ref `refs/claims/<intent_key>`: grant unless
        another live run holds it; a claim past its `expires` may be taken.

        Only an engine instance claims, and only on its own store (`engine:<store>` owns the ref),
        which is why the ownership check is here rather than in `principal.may_advance`: claims
        were added to the store with the Hub, and the second caller (the Hub's batch renewal) is
        the same principal. A replica may claim: AD-24 has it fall back to its own store when the
        primary is unreachable, and a claim is not a ref move or a copy of one.
        """
        if who.who != "engine" or who.id != self.name:
            raise LibraryRefused("ref_not_owned", f"{who} may not claim on {self.name}")
        if not CLAIM_KEY.fullmatch(intent_key) or not run_id or ttl < 1:
            raise LibraryRefused("invalid_claim", f"{intent_key!r} with ttl {ttl} is no claim")
        now = self.wall().astimezone(UTC)
        expires = now + timedelta(seconds=ttl)
        with self._mutex:
            claims = self._claims()
            current = claims.get(intent_key)
            if current and current["run_id"] != run_id:
                held = datetime.fromisoformat(str(current["expires"]))
                if held > now:
                    return Claim(False, str(current["run_id"]), held)
            claims[intent_key] = {
                "ref": f"refs/claims/{intent_key}",
                "run_id": run_id,
                "store": self.name,
                "expires": expires.isoformat(),
            }
            self._save_claims(claims)
        return Claim(True, run_id, expires)

    def release(self, who: Principal, intent_key: str, run_id: str) -> None:
        """Drop a claim this run holds. Another run's claim is left alone; its holder's death is
        what the ttl is for, so a release never steals."""
        if who.who != "engine" or who.id != self.name:
            raise LibraryRefused("ref_not_owned", f"{who} may not release on {self.name}")
        with self._mutex:
            claims = self._claims()
            current = claims.get(intent_key)
            if current is None or current["run_id"] != run_id:
                return
            del claims[intent_key]
            self._save_claims(claims)

    def renew_claims(self, who: Principal, run_id: str, ttl: int) -> list[str]:
        """Extend every claim `run_id` holds, one call per heartbeat (AD-24, engine AD-65)."""
        if who.who != "engine" or who.id != self.name:
            raise LibraryRefused("ref_not_owned", f"{who} may not renew on {self.name}")
        if ttl < 1:
            raise LibraryRefused("invalid_claim", f"ttl {ttl} is no claim")
        now = self.wall().astimezone(UTC)
        expires = (now + timedelta(seconds=ttl)).isoformat()
        with self._mutex:
            claims = self._claims()
            renewed = sorted(key for key, held in claims.items() if held["run_id"] == run_id)
            for key in renewed:
                claims[key]["expires"] = expires
            if renewed:
                self._save_claims(claims)
        return renewed

    def sweep_claims(self) -> int:
        """Prune released and expired claims; they are never bucketed (AD-24)."""
        with self._mutex:
            claims = self._claims()
            now = self.wall().astimezone(UTC)
            live = {
                key: held
                for key, held in claims.items()
                if datetime.fromisoformat(str(held["expires"])) > now
            }
            if len(live) != len(claims):
                self._save_claims(live)
        return len(claims) - len(live)

    def live_claims(self) -> dict[str, str]:
        """Each live intent key and the run that holds it, for the heartbeat row (AD-65)."""
        now = self.wall().astimezone(UTC)
        with self._mutex:
            return {
                key: str(held["run_id"])
                for key, held in self._claims().items()
                if datetime.fromisoformat(str(held["expires"])) > now
            }

    def claim_holder(self, intent_key: str) -> tuple[str, str] | None:
        """The run holding `intent_key` and when that lapses, or None when nobody does."""
        with self._mutex:
            entry = self._claims().get(intent_key)
        if entry is None:
            return None
        return str(entry["run_id"]), str(entry["expires"])

    def _claims(self) -> dict[str, dict[str, Any]]:
        if not self.claims_path.exists():
            return {}
        return cast(dict[str, dict[str, Any]], json.loads(self.claims_path.read_text("utf-8")))

    def _save_claims(self, claims: Mapping[str, Mapping[str, object]]) -> None:
        """One file, replaced whole: claims are transient, so they are not in the ref log."""
        self._refuse_too_new("a claim")
        path = self.claims_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
        with temp.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(claims, sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
        _replace(temp, path)

    def purge(self, who: Principal, blob_id: str, reason: str) -> PurgeResult:
        """AD-6's one exception to archive-never-delete: the operator, for a blob holding a
        secret, drops the bytes on this store and records why on `refs/purges/<hex>`; every
        replica applies the tombstone when it mirrors that ref."""
        self._check_writer("purge")
        if who.who != "operator":
            raise LibraryRefused("purge_refused", f"{who} may not purge; the operator purges")
        if not reason.strip():
            raise LibraryRefused("purge_refused", "a purge names the secret it removes")
        if not blob_id.startswith("sha256:"):
            raise LibraryRefused("purge_refused", f"{blob_id!r} is not a blob id")
        hexdigest = blob_id.removeprefix("sha256:")
        path = self._blob_path(blob_id, transient=False)
        with self._mutex:
            if path.exists():
                data = path.read_bytes()
                if f"sha256:{sha256(data).hexdigest()}" != blob_id:
                    raise LibraryRefused("corrupt_blob", f"{blob_id} does not hash to its name")
            elif not self.purged(blob_id):
                raise LibraryRefused("not_found", f"no blob {blob_id}")
            with self._writing():
                tombstone = self._tombstone(blob_id, reason, who)
                path.unlink(missing_ok=True)
                self._blob_path(blob_id, transient=False, fetched=True).unlink(missing_ok=True)
                ref = f"refs/purges/{hexdigest}"
                found = self.catalog.head(f"purge:{hexdigest}", ref)
                if found is None or found[0] != "purged":
                    self._move(who, f"purge:{hexdigest}", ref, "purged", reason=reason)
        return PurgeResult(blob_id, f"refs/purges/{hexdigest}", tombstone)

    def apply_purge(self, blob_id: str, *, reason: str, at: str) -> bool:
        """A replica's side of `purge`: same tombstone, same missing bytes, no ref move of its
        own. True when this call was the one that removed something."""
        if self.role == "writer":
            raise LibraryRefused("ref_not_owned", "the writer purges; a replica applies")
        if not blob_id.startswith("sha256:"):
            raise LibraryRefused("purge_refused", f"{blob_id!r} is not a blob id")
        if self.purged(blob_id):
            return False
        with self._mutex:
            self._tombstone(blob_id, reason, Principal("operator"), at=at)
            self._blob_path(blob_id, transient=False).unlink(missing_ok=True)
            self._blob_path(blob_id, transient=False, fetched=True).unlink(missing_ok=True)
        return True

    def _tombstone(
        self, blob_id: str, reason: str, who: Principal, *, at: str | None = None
    ) -> Path:
        path = self.tombstones / f"{blob_id.removeprefix('sha256:')}.json"
        entry = {
            "blob_id": blob_id,
            "reason": reason,
            "principal": str(who),
            "at": at or self._now(),
        }
        _write_once(path, canonical(entry))
        return path

    def mirror(
        self,
        item: str,
        ref: str,
        new_head: str,
        *,
        expected_head: str | None,
        who: str = "hub",
        at: str | None = None,
    ) -> Commit:
        """Record another store's move: the ref it owns has a new head here (AD-11, AD-14).

        A mirror is not an act (`may_advance` decides acts), so any role takes one; what it
        cannot do is overwrite a head the caller did not read, which is the compare-and-swap
        AD-14 asks for. `who` is the principal the owner recorded, so the local ref log names the
        true writer.
        """
        with self._writing():
            found = self.catalog.head(item, ref)
            head = None if found is None else found[0]
            if head == new_head:
                return Commit(new_head, item, ref, head, self._seq)
            if head != expected_head:
                raise LibraryRefused("stale_head", f"{ref} of {item} is at {head}")
            return self._move(Principal.parse(who), item, ref, new_head, reason="mirror", at=at)

    def ingest(self, manifest: Mapping[str, Any]) -> ObjectId:
        """Copy one immutable object from a peer, and its blobs as they arrive (AD-11). Objects
        are ownerless, so any role takes one; a collision is a name that does not hash to its
        bytes."""
        object_id = fp1(manifest)
        self._refuse_too_new("an ingest")
        _write_once(self._object_path(object_id), canonical(manifest))
        with self._writing():
            self._index_object(object_id, manifest)
        return object_id

    def store_blob(self, data: bytes) -> str:
        """Copy one durable blob from a peer, verified by its hash (AD-10).

        On the writer the bytes are the main copy; on a store that replicates they are a cache
        copy it may give up, because the peer that sent them holds the born one.
        """
        blob_id = f"sha256:{sha256(data).hexdigest()}"
        self._refuse_too_new("a blob copy")
        _write_once(self._blob_path(blob_id, transient=False, fetched=self.role != "writer"), data)
        self._reindex_blob(blob_id)
        return blob_id

    def upload_path(self, upload_id: str) -> Path:
        """The partial file one upload id names (AD-27). Refuses a name that is not one segment."""
        if UPLOAD_ID.fullmatch(upload_id) is None:
            raise LibraryRefused("invalid_upload", f"{upload_id!r} is not an upload id")
        return self.root / UPLOAD / f"{upload_id}.part"

    def upload_held(self, upload_id: str) -> tuple[int, str]:
        """`(bytes held, sha256 of those bytes)` of a partial upload, re-hashed from disk."""
        path = self.upload_path(upload_id)
        hasher = sha256()
        held = 0
        if path.exists():
            with path.open("rb") as handle:
                while data := handle.read(CHUNK):
                    hasher.update(data)
                    held += len(data)
        return held, hasher.hexdigest()

    def begin_upload(
        self, upload_id: str, *, offset: int = 0, partial_sha256: str | None = None
    ) -> Upload:
        """Open one resumable upload: from zero, or continuing the bytes at `offset` (AD-27)."""
        self._refuse_too_new("an upload")
        return Upload(self, upload_id, offset=offset, partial_sha256=partial_sha256)

    def append_upload(
        self,
        chunks: Iterable[bytes],
        *,
        upload_id: str,
        offset: int = 0,
        partial_sha256: str | None = None,
    ) -> tuple[int, str]:
        """Write the bytes a client sent from `offset` on, hashing as it writes (AD-27).

        A resumed upload re-hashes the partial file before it takes one more byte, and refuses
        `hash_mismatch` when the client's copy of that hash disagrees: the two sides would
        otherwise append different bytes to one name. Returns `(bytes held, sha256 of them)`.
        """
        upload = self.begin_upload(upload_id, offset=offset, partial_sha256=partial_sha256)
        try:
            for chunk in chunks:
                upload.write(chunk)
        finally:
            upload.close()
        return upload.held, upload.sha256

    def complete_upload(self, upload_id: str, *, expect_sha256: str | None = None) -> str:
        """Promote a finished partial to its blob, by hash, in one rename (AD-27).

        The whole part is hashed again before the rename, so a crash mid-upload can never make a
        name stand for bytes it does not hash to. A part whose hash is already held is deleted:
        the bytes and the name are both here.
        """
        path = self.upload_path(upload_id)
        if not path.exists():
            raise LibraryRefused("invalid_upload", f"{upload_id} holds no bytes")
        hasher = sha256()
        with path.open("rb") as handle:
            while data := handle.read(CHUNK):
                hasher.update(data)
        digest = hasher.hexdigest()
        if expect_sha256 is not None and digest != expect_sha256:
            path.unlink(missing_ok=True)
            raise LibraryRefused("hash_mismatch", f"{upload_id} does not hash to the upload's own")
        blob_id = f"sha256:{digest}"
        target = self._blob_path(blob_id, transient=False, fetched=self.role != "writer")
        if target.exists():
            path.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            _replace(path, target)
        self._reindex_blob(blob_id)
        return blob_id

    def discard_upload(self, upload_id: str) -> None:
        """Delete a partial nobody will resume: it is not a durable blob (AD-27)."""
        self.upload_path(upload_id).unlink(missing_ok=True)

    def blob_size(self, blob_id: str) -> int:
        path = self._held(blob_id)
        if path is None or not path.exists():
            raise LibraryRefused("blob_unavailable", f"no blob {blob_id}")
        return path.stat().st_size

    def blob_stream(self, blob_id: str, *, chunk: int = CHUNK) -> Iterator[bytes]:
        """The blob's bytes, one chunk at a time, so a 3 GB recording never sits in memory (AD-27).

        The bytes were verified against their name when they were written; this reads them once.
        """
        path = self._held(blob_id)
        if path is None or not path.exists():
            raise LibraryRefused("blob_unavailable", f"no blob {blob_id}")
        with path.open("rb") as handle:
            while data := handle.read(chunk):
                yield data

    def object_ids(self) -> list[ObjectId]:
        with self._mutex:
            rows = self.catalog.db.execute("SELECT object_id FROM objects ORDER BY object_id")
            return [str(object_id) for (object_id,) in rows]

    def has_object(self, object_id: ObjectId) -> bool:
        """Whether this store holds the object, by its manifest file: one stat, never a listing."""
        return self._object_path(object_id).exists()

    def manifest(self, object_id: ObjectId) -> dict[str, Any]:
        """The object's identity manifest, as it was written."""
        path = self._object_path(object_id)
        if not path.exists():
            raise LibraryRefused("not_found", f"no object {object_id}")
        return cast(dict[str, Any], json.loads(path.read_bytes()))

    def blob_ids(self) -> list[str]:
        """Every durable blob this store holds, cache copies included; transient never."""
        return sorted(
            {
                f"sha256:{path.name}"
                for base in (self.root / "blobs", self.root / "blobs" / "fetched")
                for path in base.glob("??/??/*")
                if path.is_file()
            }
        )

    def refs(self) -> list[tuple[str, str, str, str, str]]:
        """Every ref's head, when it last moved and under which principal, `(item, ref, head,
        at, principal)`, ordered by ref."""
        with self._mutex:
            rows = self.catalog.db.execute(
                "SELECT m.item, m.ref, m.new_head, m.at, m.principal FROM moves m WHERE m.seq = "
                "(SELECT max(seq) FROM moves WHERE item = m.item AND ref = m.ref) "
                "ORDER BY m.item, m.ref"
            )
            return [(str(i), str(r), str(h), str(a), str(p)) for i, r, h, a, p in rows]

    def ancestry_of(self, object_id: ObjectId) -> set[ObjectId]:
        """Every ancestor of `object_id`, itself included: the parent-hash order AD-14 means."""
        return set(self._ancestry(object_id))

    @property
    def epoch(self) -> Epoch | None:
        """The highest primary epoch this store has seen, and which store it names (AD-14)."""
        return self._epoch

    @property
    def alarms(self) -> tuple[str, ...]:
        """Every alarm this store raised: a torn tail it quarantined, a primary epoch it lost."""
        found = list(self.state.alarms)
        if self._epoch is not None and self._epoch.stale:
            found.append(f"library:epoch:{self.name}")
        return tuple(found)

    def versions(self) -> dict[str, int]:
        """Every kind this store reads, with the schema version it was written with (N17)."""
        return {name: found.schema_version for name, found in roster().items() if not found.retired}

    def can_read(self, kind_name: str, version: int) -> bool:
        """Whether this store has the kind and a schema version at least as new as the entry's."""
        found = roster().get(kind_name)
        return found is not None and not found.retired and found.schema_version >= version

    def record_primary(self, who: Principal, primary: str, *, epoch: int | None = None) -> Epoch:
        """The operator's flip: name the primary and raise the epoch in one record (AD-14, F12).

        The record is an object on `refs/primary`, so it replicates like any other ref; each store
        keeps the highest epoch it has seen beside its own log, because a store restored from an
        older backup carries the older record and no memory of the flip.
        """
        self._check_writer("a primary flip")
        if who.who != "operator":
            raise LibraryRefused("ref_not_owned", f"{who} may not flip the primary; he does")
        known = 0 if self._epoch is None else self._epoch.epoch
        raised = known + 1 if epoch is None else int(epoch)
        if raised <= known:
            raise LibraryRefused("stale_head", f"epoch {raised} is not above the seen {known}")
        with self._writing():
            found = self.catalog.head(PRIMARY_ITEM, PRIMARY_REF)
            parents = [] if found is None else [found[0]]
            draft = Draft(
                "note",
                PRIMARY_ITEM,
                title=f"primary = {primary}",
                fields={"primary": primary, "epoch": raised},
                parents=parents,
            )
            object_id, _ = self._mint(who, draft, PRIMARY_ITEM, parents)
            if found is None or found[0] != object_id:
                self._move(who, PRIMARY_ITEM, PRIMARY_REF, object_id, reason="primary flip")
        return self._remember(Epoch(primary, raised, seq=self._seq))

    def learn_epoch(self, other: Epoch, *, shared_seq: int | None = None) -> Epoch:
        """Take a peer's epoch record (AD-14).

        A higher epoch makes this store stop acting as primary, and the moves it made as primary
        since the ref-log position both sides shared are parked as `merge-conflict` items for him
        (N13, N19). A peer that is behind changes nothing here. A store that is already stale made
        no primary move since it learned, so a second higher epoch keeps the parks it has and
        parks nothing twice.
        """
        known = self._epoch
        if known is not None and known.epoch >= other.epoch:
            return known
        shared = other.seq if shared_seq is None else int(shared_seq)
        stale = self.role == "writer" and other.primary != self.name
        if known is not None and known.stale:
            parked = known.parked
        else:
            parked = self.park_primary_moves(shared) if stale else ()
        return self._remember(Epoch(other.primary, other.epoch, shared, stale=stale, parked=parked))

    def park_primary_moves(self, since_seq: int = 0) -> tuple[str, ...]:
        """Mint one `merge-conflict` per ref move this store made as primary after `since_seq`.

        The move stays in this store's log; what it loses is the right to be replayed as if it had
        won. He reads the conflicts and picks a side (AD-14, AD-26).
        """
        rows = self.catalog.db.execute(
            "SELECT item, ref, new_head, prev_head FROM moves WHERE seq > ? "
            "AND ref NOT LIKE 'refs/conflicts/%' AND ref NOT LIKE 'refs/purges/%' "
            "AND ref NOT LIKE 'refs/hub/%' AND ref != ? ORDER BY seq",
            (since_seq, PRIMARY_REF),
        ).fetchall()
        parked: list[str] = []
        with self._writing():
            for item, ref, head, prev in rows:
                number = self.catalog.refs_like(f"refs/conflicts/{item}/") + 1
                target = f"refs/conflicts/{item}/{number}"
                fields: JsonObject = {
                    "base": None if prev is None else str(prev),
                    "ours": str(head),
                    "theirs": "",
                    "into": str(ref),
                    "entries": cast(list[JsonValue], [{"path": str(ref), "item": str(item)}]),
                }
                draft = Draft(
                    "merge-conflict",
                    title=f"Parked {ref} of {item}",
                    summary=f"this store was primary and lost the epoch; {ref} was not replayed",
                    fields=fields,
                )
                object_id, _ = self._mint(self.engine, draft, str(item), [])
                self._move(
                    self.engine, str(item), target, object_id, reason=f"parked {ref} of {item}"
                )
                parked.append(target)
        return tuple(parked)

    def _read_epoch(self) -> Epoch | None:
        path = self.root / "refs" / EPOCH
        try:
            found = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
            return Epoch(
                str(found["primary"]),
                int(found["epoch"]),
                int(found.get("seq", 0)),
                bool(found.get("stale", False)),
                tuple(str(ref) for ref in found.get("parked", [])),
            )
        except OSError, ValueError, KeyError, TypeError:
            return None

    def _remember(self, found: Epoch) -> Epoch:
        path = self.root / "refs" / EPOCH
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "primary": found.primary,
            "epoch": found.epoch,
            "seq": found.seq,
            "stale": found.stale,
            "parked": list(found.parked),
        }
        temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
        temp.write_text(json.dumps(entry, sort_keys=True), encoding="utf-8")
        _replace(temp, path)
        self._epoch = found
        return found
